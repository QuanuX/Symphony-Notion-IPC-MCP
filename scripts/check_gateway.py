#!/usr/bin/env python3
"""Explicit read-only MCP connectivity check; never starts services or runs commands."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPSHandler, HTTPRedirectHandler

from notion_publish import write_private

VERSION = "2025-11-25"
MAX_BYTES = 1024 * 1024


def require(value, message):
    if not value:
        raise ValueError(message)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def credential(path):
    require(Path(path).is_absolute(), "Select an absolute credential-file path")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        st = os.fstat(stream.fileno())
        require(stat.S_ISREG(st.st_mode) and st.st_uid == os.geteuid() and not st.st_mode & 0o077,
                "Credential must be an owned regular file, mode 0600 or stricter")
        raw = stream.read(129)
    require(re.fullmatch(rb"[A-Za-z0-9_-]{43,128}", raw), "Invalid gateway credential format")
    return raw.decode("ascii")


def endpoint(url):
    parsed = urlsplit(url)
    require(parsed.hostname and not parsed.username and not parsed.password and
            not parsed.query and not parsed.fragment and parsed.path == "/mcp",
            "Use an exact /mcp URL without credentials, query or fragment")
    require(parsed.scheme == "https" or (parsed.scheme == "http" and parsed.hostname == "127.0.0.1"),
            "Use HTTPS, or explicit 127.0.0.1 HTTP for a local check")
    require(parsed.port is None or 1 <= parsed.port <= 65535, "Invalid endpoint port")
    return url


def probe(url, token_file):
    url = endpoint(url)  # Validate destination before reading a credential.
    token = credential(token_file)
    opener = build_opener(HTTPSHandler(), NoRedirect())
    session = None
    sequence = 0
    closed = False

    def send(method, payload, status):
        headers = {"Authorization": "Bearer " + token,
                   "Accept": "application/json, text/event-stream",
                   "Content-Type": "application/json", "MCP-Protocol-Version": VERSION}
        if session:
            headers["Mcp-Session-Id"] = session
        req = Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                      headers=headers, method=method)
        try:
            with opener.open(req, timeout=15) as response:
                require(response.status == status, "Unexpected MCP HTTP status")
                raw = response.read(MAX_BYTES + 1)
                require(len(raw) <= MAX_BYTES, "MCP response exceeds limit")
                if raw:
                    require(response.headers.get_content_type() == "application/json", "Expected JSON MCP response")
                return response.headers, json.loads(raw) if raw else None
        except HTTPError as exc:
            code = exc.code
            exc.close()
            raise RuntimeError(f"MCP HTTP {code}; no automatic retry") from None

    def rpc(method, params):
        nonlocal sequence, session
        sequence += 1
        headers, body = send("POST", {"jsonrpc": "2.0", "id": sequence, "method": method, "params": params}, 200)
        if method == "initialize":
            # Retain a valid session immediately so malformed initialization
            # results still take the cleanup path below.
            candidate = headers.get("Mcp-Session-Id", "")
            require(re.fullmatch(r"[A-Za-z0-9_-]{1,256}", candidate), "Missing or invalid MCP session")
            session = candidate
        require(isinstance(body, dict) and body.get("jsonrpc") == "2.0" and body.get("id") == sequence and
                "error" not in body and isinstance(body.get("result"), dict), "MCP request failed or response identity mismatched")
        return body["result"]

    try:
        init = rpc("initialize", {"protocolVersion": VERSION, "capabilities": {},
                   "clientInfo": {"name": "symphony-local-readiness-check", "version": "0.1.0"}})
        require(init.get("protocolVersion") == VERSION and init.get("serverInfo", {}).get("name") == "symphony",
                "Unexpected MCP server or protocol version")
        send("POST", {"jsonrpc": "2.0", "method": "notifications/initialized"}, 202)
        tools = rpc("tools/list", {}).get("tools")
        known = {"symphony_connection", "symphony_discover", "symphony_describe", "symphony_read",
                 "symphony_prepare", "symphony_apply"}
        require(isinstance(tools, list) and all(isinstance(t, dict) and t.get("name") in known for t in tools),
                "Unexpected Symphony tool inventory")
        names = [t["name"] for t in tools]
        require(len(names) == len(set(names)) and "symphony_connection" in names, "Missing or duplicate connection tool")
        connection = rpc("tools/call", {"name": "symphony_connection", "arguments": {}})
        require(connection.get("isError") is not True and isinstance(connection.get("structuredContent"), dict),
                "Symphony connection inspection failed")
        # Discard owner output, paths and registry contents; preserve only the
        # bounded protocol evidence. A connection result is not service health.
    finally:
        if session:
            try:
                send("DELETE", None, 204)
                closed = True
            except Exception:
                # Preserve an earlier failure; never replay an RPC to clean up.
                closed = False
    require(closed, "MCP session closure unconfirmed; allow expiry before using single-session IPC")
    return {"schema": "symphony.gateway.access-check.v1", "checked_at": time.time(),
            "protocol_version": VERSION, "authenticated": True, "tools": names,
            "connection_inspected": True, "session_closed": closed,
            "domain_commands_executed": False, "native_service_health_verified": False,
            "notion_agent_verified": False, "publication_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--token-file", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="New private evidence file; never overwrites")
    args = parser.parse_args()
    try:
        result = probe(args.url, args.token_file)
        if args.output:
            write_private(args.output, result)
        print(json.dumps(result))
    except Exception:
        # URLs, credential values, HTTP bodies and owner errors may be private.
        parser.exit(2, "Gateway check failed; inspect local configuration, authentication, protocol and session capacity. No automatic retry.\n")


if __name__ == "__main__":
    main()

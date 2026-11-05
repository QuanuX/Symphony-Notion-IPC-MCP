#!/usr/bin/env python3
"""Prepare/run a connector to an operator's existing Cloudflare Tunnel.

Never creates accounts, tunnels, DNS, routes, Access applications or services.
Never accepts a secret on the command line or starts a Quick Tunnel.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import uuid


def require(value, message):
    if not value:
        raise ValueError(message)


def private_text(path):
    path = Path(path)
    require(path.is_absolute(), "Use absolute private paths")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as f:
        st = os.fstat(f.fileno())
        require(stat.S_ISREG(st.st_mode) and st.st_uid == os.geteuid() and not st.st_mode & 0o077,
                "Private file must be owned and mode 0600 or stricter")
        raw = f.read(1024 * 1024 + 1)
    require(len(raw) <= 1024 * 1024, "Private file too large")
    return raw.decode("utf-8")


def write(path, obj):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def sha(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def gateway(path, hostname):
    cfg = json.loads(private_text(path))
    require(cfg.get("schema") == "symphony.agent.gateway.v1", "Unsupported gateway profile")
    require(hostname in cfg.get("allowed_hosts", []), "Hostname must already be allowed by the selected gateway")
    port = cfg.get("port", 8765)
    require(isinstance(port, int) and not isinstance(port, bool) and 1024 <= port <= 65535, "Invalid gateway port")
    return cfg, {"hostname": hostname, "path": "^/mcp$", "service": f"http://127.0.0.1:{port}",
                 "originRequest": {"httpHostHeader": hostname}}


def prepare(args):
    require(re.fullmatch(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", args.hostname),
            "Use an explicit DNS hostname you control, without a scheme, wildcard or path")
    require(not args.hostname.endswith(".trycloudflare.com"), "Quick Tunnels are not supported; supply your own named tunnel")
    binary = args.cloudflared.resolve(strict=True)
    require(binary.is_file() and os.access(binary, os.X_OK), "Select an executable cloudflared")
    cfg_path = args.gateway_config.absolute()
    cfg, route = gateway(cfg_path, args.hostname)
    credential = args.credentials_file or args.token_file
    require(credential is not None and credential.is_absolute(), "Select a private credential file")
    secret = private_text(credential)
    if args.credentials_file:
        require(args.tunnel_id, "Local mode requires the existing tunnel UUID")
        tunnel = str(uuid.UUID(args.tunnel_id))
        require(json.loads(secret).get("TunnelID") == tunnel, "Credential belongs to another tunnel")
    else:
        require(not args.tunnel_id, "Remote token selects its tunnel; verify its identity in your dashboard")
        require(bool(secret.strip()) and len(secret.strip()) <= 16384 and not re.search(r"\s", secret.strip()), "Invalid token file")
        tunnel = None
    root = args.output.absolute()
    root.mkdir(mode=0o700)  # Preserve existing directories/configurations.
    local_config = root / "cloudflared.yaml"
    ingress = [route, {"service": "http_status:404"}]
    if args.publisher_callback:
        ingress.insert(1, {"hostname": args.hostname, "path": "^/notion/callback$", "service": "http://127.0.0.1:8766"})
    if args.credentials_file:
        # JSON is a YAML subset accepted by cloudflared's YAML reader.
        write(local_config, {"tunnel": tunnel, "credentials-file": str(credential), "ingress": ingress})
    else:
        # Remote config belongs to the user's dashboard. This is a review fragment,
        # never a replacement configuration sent to an existing tunnel's API.
        write(root / "dashboard-route.json", {"ingress": ingress, "apply_automatically": False})
        write(local_config, {})  # Ignore any unrelated default cloudflared config.
    profile = {"schema": "symphony.cloudflare.connector.v1", "mode": "local" if tunnel else "remote",
               "hostname": args.hostname, "installation_id": cfg["installation_id"],
               "gateway_config": str(cfg_path), "gateway_sha256": sha(cfg_path),
               "cloudflared": str(binary), "cloudflared_sha256": sha(binary),
               "credential_file": str(credential), "credential_sha256": sha(credential), "tunnel_id": tunnel,
               "local_config": str(local_config), "local_config_sha256": sha(local_config)}
    write(root / "connector.json", profile)
    return {"profile": str(root / "connector.json"), "notion_url": f"https://{args.hostname}/mcp",
            "cloudflare_owner": "operator", "provisioned": False, "started": False}


def load(path):
    p = json.loads(private_text(path))
    require(p.get("schema") == "symphony.cloudflare.connector.v1", "Unsupported connector profile")
    require(p.get("mode") in ("local", "remote"), "Unsupported connector mode")
    cfg, _ = gateway(p["gateway_config"], p["hostname"])
    require(cfg["installation_id"] == p["installation_id"] and sha(p["gateway_config"]) == p["gateway_sha256"],
            "Gateway binding changed; prepare a new connector explicitly")
    require(Path(p["cloudflared"]).is_absolute() and sha(p["cloudflared"]) == p["cloudflared_sha256"],
            "cloudflared changed; prepare a new connector explicitly")
    secret = private_text(p["credential_file"])
    require(sha(p["credential_file"]) == p["credential_sha256"], "Tunnel credential changed; prepare a new connector explicitly")
    private_text(p["local_config"])
    require(sha(p["local_config"]) == p["local_config_sha256"], "Ingress changed; prepare a new connector explicitly")
    if p["mode"] == "local":
        require(json.loads(secret).get("TunnelID") == p["tunnel_id"], "Tunnel credential binding changed")
    else:
        require(bool(secret.strip()) and len(secret.strip()) <= 16384 and not re.search(r"\s", secret.strip()), "Invalid token file")
    return p


def command(p, validate=False):
    if validate:
        require(p["mode"] == "local", "Remote ingress is controlled by your Cloudflare dashboard; no local validation can prove it")
        return [p["cloudflared"], "tunnel", "--config", p["local_config"], "ingress", "validate"]
    argv = [p["cloudflared"], "tunnel", "--no-autoupdate", "--loglevel", "warn", "--config", p["local_config"]]
    if p["mode"] == "local":
        return argv + ["run", p["tunnel_id"]]
    return argv + ["run", "--token-file", p["credential_file"]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--gateway-config", type=Path, required=True)
    prep.add_argument("--hostname", required=True)
    prep.add_argument("--cloudflared", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    auth = prep.add_mutually_exclusive_group(required=True)
    auth.add_argument("--credentials-file", type=Path)
    auth.add_argument("--token-file", type=Path)
    prep.add_argument("--tunnel-id")
    prep.add_argument("--publisher-callback", action="store_true", help="Also prepare the optional Notion OAuth callback route")
    for name in ("inspect", "validate", "run"):
        child = sub.add_parser(name)
        child.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            print(json.dumps(prepare(args)))
            return
        p = load(args.profile)
        argv = command(p, validate=args.action == "validate")
        if args.action == "inspect":
            print(json.dumps({"installation_id": p["installation_id"], "mode": p["mode"], "argv": argv,
                              "public_url": f"https://{p['hostname']}/mcp", "live_connectivity": "not_probed"}))
            return
        # Do not allow ambient TUNNEL_* variables to select another account,
        # credentials, ingress, or Quick Tunnel. Never invoke a shell.
        env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}
        env.update({k: os.environ[k] for k in ("HOME", "TMPDIR", "SSL_CERT_FILE", "SSL_CERT_DIR") if k in os.environ})
        if args.action == "validate":
            result = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=20)
            require(result.returncode == 0, "cloudflared rejected ingress; inspect your local configuration")
            print(json.dumps({"local_ingress_valid": True, "public_connectivity": "not_probed"}))
        else:
            os.execve(argv[0], argv, env)  # Explicit run is the only activation path.
    except Exception as exc:
        parser.exit(2, f"Cloudflare connector: {exc}\n")


if __name__ == "__main__":
    main()

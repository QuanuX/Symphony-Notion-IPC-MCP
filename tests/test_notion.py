import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import io
from urllib.error import HTTPError
from urllib.parse import urlsplit, parse_qs, urlencode
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("notion_publish", Path(__file__).resolve().parents[1] / "scripts/notion_publish.py")
n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)


class NotionPublishing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.root.chmod(0o700)
        self.c = {"schema": "symphony.notion.publisher.v1", "workspace_id": "selected-workspace",
                  "allowed_parent_pages": ["selected-page"], "client_id": "fixture-client",
                  "client_secret_file": str(self.root / "secret.json"),
                  "redirect_uri": "http://127.0.0.1:8766/notion/callback", "token_file": str(self.root / "token.json")}
        n.write_private(self.c["token_file"], {"access_token": "private-access", "refresh_token": "private-refresh", "workspace_id": "selected-workspace"})
        n.write_private(self.c["client_secret_file"], {"client_secret": "private-client-secret"})
        self.plan = self.root / "publication.json"

    def preview(self, kind="report"):
        return n.prepare(self.c, "selected-page", "Test report", "Synthetic content only.", kind, self.plan)

    def test_preview_never_publishes_and_preserves_unicode(self):
        with patch.object(n, "request") as req:
            n.prepare(self.c, "selected-page", "研究", "π" * 4000, "research", self.plan)
            req.assert_not_called()
        plan = n.read_private(self.plan)
        self.assertGreater(len(plan["payload"]["children"]), 2)
        self.assertEqual(self.plan.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("private-access", self.plan.read_text())

    def test_all_document_kinds(self):
        for kind in ("report", "incident", "research"):
            out = self.root / (kind + ".json")
            n.prepare(self.c, "selected-page", kind, "body", kind, out)
            self.assertIn("Symphony " + kind, n.read_private(out)["payload"]["children"][0]["paragraph"]["rich_text"][0]["text"]["content"])

    def test_publish_once_and_durable_receipt(self):
        p = self.preview()
        def remote(path, payload, auth):
            self.assertTrue(Path(str(self.plan) + ".receipt.json").exists())
            self.assertEqual(path, "/v1/pages")
            self.assertEqual(auth, "Bearer private-access")
            self.assertEqual(payload["parent"], {"page_id": "selected-page"})
            return {"object": "page", "id": "created", "url": "https://notion.so/created"}
        with patch.object(n, "request", side_effect=remote) as req:
            r = n.publish(self.c, self.plan, p["sha256"])
            self.assertEqual(r["outcome"], "published")
            with self.assertRaises(FileExistsError):
                n.publish(self.c, self.plan, p["sha256"])
            self.assertEqual(req.call_count, 1)

    def test_lost_response_never_replays(self):
        p = self.preview()
        with patch.object(n, "request", side_effect=TimeoutError) as req:
            with self.assertRaisesRegex(RuntimeError, "outcome unknown"):
                n.publish(self.c, self.plan, p["sha256"])
            with self.assertRaises(FileExistsError):
                n.publish(self.c, self.plan, p["sha256"])
            self.assertEqual(req.call_count, 1)
        r = n.read_private(str(self.plan) + ".receipt.json")
        self.assertEqual(r["outcome"], "unknown_requires_reconciliation")

    def test_destination_hash_expiry_and_token_binding(self):
        with self.assertRaisesRegex(ValueError, "scope"):
            n.prepare(self.c, "unapproved-page", "title", "body", "report", self.plan)
        p = self.preview()
        with patch.object(n, "request") as req:
            with self.assertRaisesRegex(ValueError, "checksum"):
                n.publish(self.c, self.plan, "incorrect")
            with patch.object(n.time, "time", return_value=10**12):
                with self.assertRaisesRegex(ValueError, "expired"):
                    n.publish(self.c, self.plan, p["sha256"])
            n.write_private(self.c["token_file"], {"workspace_id": "other", "access_token": "different"}, replace=True)
            with self.assertRaisesRegex(ValueError, "binding mismatch"):
                n.publish(self.c, self.plan, p["sha256"])
            req.assert_not_called()

    def test_refresh_rotation_invalidates_preview(self):
        p = self.preview()
        with patch.object(n, "request", return_value={"access_token": "rotated", "refresh_token": "rotated-refresh"}) as req:
            self.assertTrue(n.refresh(self.c)["refreshed"])
            self.assertEqual(req.call_args.args[1]["grant_type"], "refresh_token")
            with self.assertRaisesRegex(ValueError, "Connection changed"):
                n.publish(self.c, self.plan, p["sha256"])
            self.assertEqual(req.call_count, 1)

    def test_refresh_loss_and_revocation(self):
        with patch.object(n, "request", side_effect=TimeoutError) as req:
            with self.assertRaises(TimeoutError):
                n.refresh(self.c)
            with self.assertRaises(FileExistsError):
                n.refresh(self.c)
            self.assertEqual(req.call_count, 1)
        with patch.object(n, "request", return_value={}):
            self.assertTrue(n.revoke(self.c)["revoked"])
        self.assertFalse(Path(self.c["token_file"]).exists())

    def test_private_files_and_redirect_rejection(self):
        token = Path(self.c["token_file"])
        token.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "0600"):
            n.token(self.c)
        token.chmod(0o600)
        alias = self.root / "alias.json"
        alias.symlink_to(token)
        with self.assertRaises(OSError):
            n.read_private(alias)
        self.assertIsNone(n.NoRedirect().redirect_request(None, None, None, None, None, None))
        self.c["redirect_uri"] = "http://remote.example/notion/callback"
        with self.assertRaisesRegex(ValueError, "loopback"):
            n.authorize(self.c)

    def test_config_status_does_not_probe_remote(self):
        path = self.root / "publisher.json"
        n.write_private(path, self.c)
        with patch.object(n, "request") as req:
            c = n.config(path)
            self.assertEqual(n.token(c)["workspace_id"], "selected-workspace")
            req.assert_not_called()

    def test_oauth_state_and_workspace_bound_callback(self):
        Path(self.c["token_file"]).unlink()
        output = io.StringIO()
        responses = []
        owner = self

        class Server:
            def __init__(self, address, handler):
                owner.assertEqual(address, ("127.0.0.1", 8766))
                self.handler = handler
                self.turn = 0
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def handle_request(self):
                url = output.getvalue().splitlines()[-1]
                state = parse_qs(urlsplit(url).query)["state"][0]
                handler = object.__new__(self.handler)
                handler.path = "/notion/callback?" + urlencode({"state": "wrong" if self.turn == 0 else state, "code": "private-code"})
                handler.wfile = io.BytesIO()
                handler.send_response = responses.append
                handler.send_header = lambda *args: None
                handler.end_headers = lambda: None
                self.turn += 1
                handler.do_GET()

        with patch.object(n, "HTTPServer", Server), patch("sys.stdout", output), patch.object(n, "request", return_value={"workspace_id": "selected-workspace", "access_token": "new-token", "refresh_token": "new-refresh"}) as req:
            self.assertTrue(n.authorize(self.c)["connected"])
            self.assertEqual(req.call_count, 1)
            self.assertEqual(req.call_args.args[1]["code"], "private-code")
            self.assertEqual(responses, [400, 200])
        self.assertEqual(n.token(self.c)["access_token"], "new-token")
        self.assertNotIn("private-code", output.getvalue())
        self.assertNotIn("new-token", output.getvalue())
        Path(self.c["token_file"]).unlink()
        output = io.StringIO()
        responses.clear()
        with patch.object(n, "HTTPServer", Server), patch("sys.stdout", output), patch.object(n, "request", return_value={"workspace_id": "wrong-workspace", "access_token": "wrong-token"}):
            with self.assertRaisesRegex(ValueError, "Authorization failed"):
                n.authorize(self.c)
            self.assertEqual(responses, [400, 400])
        self.assertFalse(Path(self.c["token_file"]).exists())

    def test_http_client_pins_origin_version_and_bounded_payload(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b'{"object":"page","id":"created"}'
        with patch.object(n, "build_opener") as factory:
            factory.return_value.open.return_value = Response()
            n.request("/v1/pages", {"text": "π"}, "Bearer private-token")
            req = factory.return_value.open.call_args.args[0]
            self.assertEqual(req.full_url, "https://api.notion.com/v1/pages")
            self.assertEqual(req.get_header("Notion-version"), "2026-03-11")
            self.assertEqual(req.get_header("Authorization"), "Bearer private-token")
            self.assertEqual(json.loads(req.data), {"text": "π"})
            with self.assertRaisesRegex(ValueError, "500KB"):
                n.request("/v1/pages", {"text": "x" * 500001}, "Bearer private-token")
            self.assertEqual(factory.return_value.open.call_count, 1)


class LiveAccessCheck(unittest.TestCase):
    def setUp(self):
        NotionPublishing.setUp(self)
        self.parent = "b55c9c91-384d-452b-81db-d1ef79372b75"
        self.c["allowed_parent_pages"] = [self.parent]
        t = n.token(self.c)
        t["bot_id"] = "selected-bot"
        n.write_private(self.c["token_file"], t, replace=True)
        self.bot = {"object": "user", "type": "bot", "id": "selected-bot", "name": "Private bot name"}
        self.page = {"object": "page", "id": self.parent, "archived": False, "in_trash": False,
                     "properties": {"title": "Private page title"}}

    def test_verify_reads_only_selected_bot_and_page(self):
        before = Path(self.c["token_file"]).read_bytes()
        with patch.object(n, "request", side_effect=[self.bot, self.page]) as req:
            result = n.verify(self.c, self.parent.replace("-", ""))
        self.assertEqual([call.args[0] for call in req.call_args_list],
                         ["/v1/users/me", "/v1/pages/" + self.parent])
        for call in req.call_args_list:
            self.assertEqual(call.kwargs, {"method": "GET"})
            self.assertIsNone(call.args[1])
        self.assertTrue(result["parent_readable"])
        self.assertFalse(result["publication_verified"])
        self.assertFalse(result["writes_performed"])
        self.assertFalse(result["notion_agent_verified"])
        self.assertEqual(result["workspace_evidence"], "stored_oauth_grant")
        text = json.dumps(result)
        for private in ("Private page title", "Private bot name", "private-access", "private-refresh"):
            self.assertNotIn(private, text)
        self.assertEqual(Path(self.c["token_file"]).read_bytes(), before)

    def test_verify_refuses_unselected_or_injected_destinations_before_network(self):
        for parent in ("cf22fcfa-1dd3-445a-9388-13fea7596dc3", "../users/me", self.parent + "?secret=bad",
                       "https://api.notion.com/v1/pages/" + self.parent):
            with self.subTest(parent=parent), patch.object(n, "request") as req:
                with self.assertRaises(ValueError):
                    n.verify(self.c, parent)
                req.assert_not_called()

    def test_verify_refuses_missing_or_changed_bot_before_page_access(self):
        for bot in (dict(self.bot, id="another-bot"), dict(self.bot, type="person"), []):
            with patch.object(n, "request", return_value=bot) as req:
                with self.assertRaisesRegex(ValueError, "identity"):
                    n.verify(self.c, self.parent)
                self.assertEqual(req.call_count, 1)
        t = n.token(self.c)
        del t["bot_id"]
        n.write_private(self.c["token_file"], t, replace=True)
        with patch.object(n, "request") as req:
            with self.assertRaisesRegex(ValueError, "bot_id"):
                n.verify(self.c, self.parent)
            req.assert_not_called()

    def test_verify_refuses_wrong_archived_trashed_or_incomplete_pages(self):
        for page in (dict(self.page, id="cf22fcfa-1dd3-445a-9388-13fea7596dc3"),
                     dict(self.page, archived=True), dict(self.page, in_trash=True),
                     {"object": "page", "id": self.parent}, []):
            with patch.object(n, "request", side_effect=[self.bot, page]):
                with self.assertRaises(ValueError):
                    n.verify(self.c, self.parent)

    def test_verify_never_retries_denial_or_loss(self):
        for error in (RuntimeError("Notion HTTP 403; no automatic retry"), TimeoutError()):
            with patch.object(n, "request", side_effect=error) as req:
                with self.assertRaises(type(error)):
                    n.verify(self.c, self.parent)
                self.assertEqual(req.call_count, 1)

    def test_get_transport_and_endpoint_boundaries(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b'{"object":"user"}'
        with patch.object(n, "build_opener") as factory:
            factory.return_value.open.return_value = Response()
            n.request("/v1/users/me", None, "Bearer private-token", method="GET")
            req = factory.return_value.open.call_args.args[0]
            self.assertEqual(req.get_method(), "GET")
            self.assertIsNone(req.data)
            self.assertEqual(req.get_header("Notion-version"), "2026-03-11")
            self.assertEqual(req.full_url, "https://api.notion.com/v1/users/me")
            for path, payload, method in (("/v1/oauth/token", None, "GET"), ("/v1/users/me", {}, "GET"),
                                          ("/v1/pages/" + self.parent + "/../users/me", None, "GET"),
                                          ("//evil.example", None, "GET"), ("/v1/pages", {}, "DELETE")):
                with self.assertRaises(ValueError):
                    n.request(path, payload, "Bearer private-token", method=method)
            self.assertEqual(factory.return_value.open.call_count, 1)

    def test_get_errors_do_not_leak_response_or_follow_redirects(self):
        for code in (302, 401, 403, 404, 429, 503):
            with patch.object(n, "build_opener") as factory:
                factory.return_value.open.side_effect = HTTPError("https://api.notion.com/v1/users/me", code,
                    "private response", {}, io.BytesIO(b"private-token"))
                with self.assertRaisesRegex(RuntimeError, f"Notion HTTP {code}; no automatic retry"):
                    n.request("/v1/users/me", None, "Bearer private-token", method="GET")
                self.assertEqual(factory.return_value.open.call_count, 1)


if __name__ == "__main__":
    unittest.main()

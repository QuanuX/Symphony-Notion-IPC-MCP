import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/cloudflare_connector.py"
spec = importlib.util.spec_from_file_location("connector", SCRIPT)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class Connector(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.root.chmod(0o700)
        self.gateway = self.root / "gateway.json"
        c.write(self.gateway, {"schema": "symphony.agent.gateway.v1", "installation_id": "fixture",
                              "allowed_hosts": ["symphony.example.org"], "port": 8765})
        self.binary = self.root / "cloudflared"
        self.binary.write_text("#!/bin/sh\nexit 0\n")
        self.binary.chmod(0o700)
        self.credential = self.root / "credentials.json"
        self.tunnel = "00000000-0000-4000-8000-000000000001"
        c.write(self.credential, {"TunnelID": self.tunnel, "TunnelSecret": "fixture-only"})
        self.args = argparse.Namespace(gateway_config=self.gateway, hostname="symphony.example.org",
            cloudflared=self.binary, output=self.root / "connector", credentials_file=self.credential,
            token_file=None, tunnel_id=self.tunnel, publisher_callback=False)

    def test_local_prepare_no_execution_or_secret_copy(self):
        with patch.object(c.subprocess, "run") as run:
            result = c.prepare(self.args)
            run.assert_not_called()
        self.assertFalse(result["provisioned"])
        self.assertFalse(result["started"])
        p = c.load(result["profile"])
        cfg = json.loads(Path(p["local_config"]).read_text())
        self.assertEqual(cfg["ingress"][0]["path"], "^/mcp$")
        self.assertEqual(cfg["ingress"][0]["service"], "http://127.0.0.1:8765")
        self.assertEqual(cfg["ingress"][-1], {"service": "http_status:404"})
        self.assertNotIn("fixture-only", Path(p["local_config"]).read_text())
        self.assertEqual(Path(result["profile"]).stat().st_mode & 0o777, 0o600)
        self.assertEqual(c.command(p)[-2:], ["run", self.tunnel])

    def test_remote_token_is_not_in_argv(self):
        token = self.root / "token"
        token.write_text("fixture-token-not-a-real-credential")
        token.chmod(0o600)
        self.args.credentials_file = None
        self.args.token_file = token
        self.args.tunnel_id = None
        result = c.prepare(self.args)
        p = c.load(result["profile"])
        command = c.command(p)
        self.assertIn("--token-file", command)
        self.assertNotIn(token.read_text(), " ".join(command))
        self.assertEqual(json.loads(Path(p["local_config"]).read_text()), {})
        self.assertFalse(json.loads((self.args.output / "dashboard-route.json").read_text())["apply_automatically"])
        with self.assertRaisesRegex(ValueError, "dashboard"):
            c.command(p, validate=True)

    def test_wrong_tunnel_and_host_rejected(self):
        self.args.tunnel_id = "00000000-0000-4000-8000-000000000002"
        with self.assertRaisesRegex(ValueError, "another tunnel"):
            c.prepare(self.args)
        self.args.hostname = "other.example.org"
        with self.assertRaisesRegex(ValueError, "already be allowed"):
            c.prepare(self.args)
        self.args.hostname = "test.trycloudflare.com"
        with self.assertRaisesRegex(ValueError, "Quick Tunnels"):
            c.prepare(self.args)

    def test_changed_binary_config_and_credentials_rejected(self):
        result = c.prepare(self.args)
        self.binary.write_text("#!/bin/sh\nexit 1\n")
        with self.assertRaisesRegex(ValueError, "cloudflared changed"):
            c.load(result["profile"])
        self.binary.write_text("#!/bin/sh\nexit 0\n")
        self.credential.write_text(json.dumps({"TunnelID": self.tunnel, "TunnelSecret": "rotated"}))
        with self.assertRaisesRegex(ValueError, "credential changed"):
            c.load(result["profile"])

    def test_exclusive_output_and_callback_opt_in(self):
        self.args.publisher_callback = True
        result = c.prepare(self.args)
        p = c.load(result["profile"])
        routes = json.loads(Path(p["local_config"]).read_text())["ingress"]
        self.assertEqual(routes[1]["path"], "^/notion/callback$")
        with self.assertRaises(FileExistsError):
            c.prepare(self.args)

    def test_unsafe_credentials_and_gateway_rejected(self):
        self.credential.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "0600"):
            c.prepare(self.args)
        self.credential.chmod(0o600)
        alias = self.root / "alias"
        alias.symlink_to(self.credential)
        self.args.credentials_file = alias
        with self.assertRaises(OSError):
            c.prepare(self.args)

    def test_cli_inspect_and_validate_are_nonactivating(self):
        result = c.prepare(self.args)
        for action in ("inspect", "validate"):
            run = subprocess.run([sys.executable, str(SCRIPT), action, "--profile", result["profile"]],
                                 capture_output=True, text=True, check=True)
            data = json.loads(run.stdout)
            self.assertNotIn("fixture-only", run.stdout)
            self.assertNotIn("started", data)
        self.assertEqual(c.command(c.load(result["profile"]), True)[-2:], ["ingress", "validate"])


if __name__ == "__main__":
    unittest.main()

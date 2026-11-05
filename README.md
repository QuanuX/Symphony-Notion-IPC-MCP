# Symphony-Notion-IPC-MCP

Connect Notion agents to a self-hosted Symphony quantOS and publish selected
reports, incident records and research into Notion. Publisher: **QuanuX**,
[quanux.org](https://quanux.org).

This is a standalone integration, not a Symphony module. It uses local **IPC** and **MCP — Model Context Protocol**, version
**2025-11-25**.

**Development status:** the native gateway, local IPC, publishing helpers and
connector have automated tests. Actual Notion client acceptance, live OAuth/page
publication and a user-owned tunnel deployment remain unqualified. This repository
has no Notion Marketplace, OpenAI or MCP Registry approval. The separate
[Symphony Codex plugin](https://github.com/QuanuX/symphony-codex-ipc-mcp-and-skills)
retains its own package, submission and registry identity.

## What it provides

- A C++26 MCP bridge that discovers the selected `qxctl` registry and preserves
  native Symphony authority, operation receipts and recovery rules.
- An optional C++ loopback gateway with scoped credentials, sessions, command/tool
  restrictions, private audit metadata and conservative handling of lost responses.
- Direct local bridge execution or connection to an existing same-user Unix IPC
  server, including the bridge build used for the OpenAI demo.
- A connector helper for **your existing Cloudflare Tunnel**, with locally managed
  credentials-file and dashboard-managed token-file modes. QuanuX supplies no
  tunnel, account, DNS, hosted gateway or central relay.
- Explicit Notion publishing with OAuth, workspace/page restrictions, content
  preview/checksum, one-attempt receipts, refresh and revocation handling.
- A [Symphony–Notion skill](skills/symphony-notion/SKILL.md), agent instructions,
  optional service templates and a draft marketplace checklist.

The connection path is Notion → your Cloudflare Tunnel → loopback gateway →
selected bridge/IPC → `qxctl` → Symphony owners. Symphony stays headless and needs
no GUI or TLS listener. Your Cloudflare service handles the public HTTPS edge.
Cloudflare and Notion receive forwarded tool data; see [data handling](docs/privacy.md).

## Build

Use macOS or Linux, CMake 3.30+, a compiler supporting C++26 draft mode, and
Python 3.11+. Linux additionally requires OpenSSL 3 development files. C++
dependencies and their licenses are included; builds download no dependencies.

```sh
git clone https://github.com/QuanuX/Symphony-Notion-IPC-MCP.git
cd Symphony-Notion-IPC-MCP
cmake -S . -B build -DSYMPHONY_BUILD_GATEWAY=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 2
ctest --test-dir build --output-on-failure
```

Building does not start a listener or install a service. Omitting
`SYMPHONY_BUILD_GATEWAY=ON` builds only the local bridge. The executable names
`symphony-mcp` and `symphony-mcp-gateway` retain the actual protocol spelling.
Keep them in a separate prefix if an existing Codex plugin is installed.

## Select and connect your installation

Create a new private directory, then bind the exact trusted `qxctl`:

```sh
mkdir -m 700 /absolute/private/symphony-notion
python3 scripts/configure_connection.py \
  --qxctl /absolute/installation/bin/qxctl \
  --working-directory /absolute/Symphony \
  --output /absolute/private/symphony-notion/connection.json
```

Read-only is the default. The helper verifies the selected executable and pins its
command registry; it never installs or upgrades Symphony. Discover command IDs
from that installation before granting gateway scope. Follow these guides:

1. [Gateway and existing IPC setup](docs/notion-integration.md)
2. [Connect your existing Cloudflare Tunnel](docs/cloudflare-connector.md)
3. [Publish reviewed content into Notion](docs/notion-publishing.md)
4. [Connection profile and native authority](docs/connection-profile.md)

The Cloudflare helper's `prepare`, `inspect` and local `validate` commands do not
start a tunnel. Only explicit `run` starts your selected connector. No command
provisions a tunnel or changes DNS. The publishing helper uses your own Notion
registration and credentials; no shared QuanuX OAuth secret is distributed.

## Available MCP tools

| Tool | Purpose |
|---|---|
| `symphony_connection` | Inspect executable/registry bindings and scope |
| `symphony_discover` | Discover commands in the selected installation |
| `symphony_describe` | Read exact command contracts and recovery guidance |
| `symphony_read` | Run an explicitly scoped read-only command |
| `symphony_prepare` | Preview an enabled non-read operation |
| `symphony_apply` | Apply that preview once, preserving native authority |

A connection badge is not proof of service health or a native grant. Reads and
tool results may contain sensitive information. Shared Notion agents share their
connection's authority. Unknown write outcomes require owner reconciliation,
not automatic retry. See [security](docs/security.md).

## Review package and provenance

```sh
python3 scripts/package_release.py --binary build/symphony-mcp \
  --gateway-binary build/symphony-mcp-gateway \
  --output /absolute/output/symphony-notion-platform-review.zip
```

The ZIP includes the selected binaries and complete source, excludes private
profiles, and is created exclusively with a SHA-256 sidecar. It is a standalone
review/source bundle, **not a Codex plugin installer**. It does not bundle
`cloudflared`, credentials or the separately installed Symphony runtime.

See [verification](docs/notion-verification.md),
[source provenance](docs/provenance.md) and the
[unsubmitted Notion listing checklist](docs/notion-marketplace.md).
Code is licensed under **AGPL-3.0** as supplied in [LICENSE](LICENSE); third-party
licenses remain in [third_party](third_party/NOTICE.md).

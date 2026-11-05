# Local preparation and live acceptance handoff

This is a development integration. Local fixtures, the helper-client checks and
Notion's actual client are separate evidence sources. A catalogue listing is a
further review, not a result of passing tests. No command below provisions a
tunnel, changes DNS, or installs a service automatically.

## 1. Build or obtain a development review bundle

Build the opt-in gateway using the README. The hosted workflow also creates
unsigned development bundles for Ubuntu 24.04 and macOS 15 Apple Silicon after
the native and helper tests pass. Download them from the exact successful GitHub
Actions run, record its commit, and compare the ZIP's SHA-256 sidecar before use.
An Actions artifact is not a signed release or a Notion marketplace installation.

The bundle contains source, docs, scripts, tests, workflows and selected bridge
and gateway binaries. It does not contain Symphony, cloudflared or credentials.
Keep it separate from any installed Codex plugin. Run Python helpers from the
extracted package so adjacent helper imports resolve correctly.

## 2. Prepare the selected installation

Use `configure_connection.py` for the operator's exact trusted qxctl, or select an
already-running same-user IPC bridge with `configure_gateway.py --connect-socket`.
Use the [gateway guide](notion-integration.md) to generate a new private profile.
Default to discovery and scoped read tools. The OpenAI demonstration build can
be selected explicitly; do not silently substitute another qxctl from PATH.

Start only the selected loopback gateway for a local check. For local HTTP tests,
include its exact `127.0.0.1:PORT` Host when preparing the gateway profile. Run
`scripts/check_gateway.py` as documented in the gateway guide. It checks the MCP
handshake, scoped tool inventory and connection inspection, then deletes its own
session. It executes no domain commands. The private evidence file explicitly
marks Notion Agent acceptance and native service health as unverified.

## 3. Supply the operator-owned live prerequisites

Required before live testing:

- An eligible Notion workspace and permission to add the chosen type of MCP
  connection. Custom Agent header-based authentication is documented; separately
  check the personal Notion Agent's available authentication UI.
- An existing operator-owned Cloudflare Tunnel, hostname and credential file.
  Integrate the proposed route with the operator's existing ingress; do not
  replace unrelated routes. Use [connector inspection](cloudflare-connector.md)
  before explicitly starting the chosen connector.
- For publishing, an operator-controlled OAuth registration and registered
  callback, a private publisher profile, and a disposable permitted parent page.
  The MCP bearer token and publishing OAuth token serve different purposes.

No such live destinations are bundled. Configured connections from unrelated
apps cannot prove that this adapter works. Do not copy tokens into tickets,
screenshots, chat, shell history, or Git.

## 4. Check the two directions independently

| Check | Evidence to retain | What it does not establish |
|---|---|---|
| Native build/CTest | Commit, host/compiler, test log | Live provider acceptance |
| Gateway helper | Private access-check JSON | Notion client behavior or native health |
| Notion custom MCP | Client/plan, tool inventory, one scoped native read | OAuth page publication |
| Publishing OAuth consent | Workspace and bot identity, private saved grant | Insert capability |
| Publishing `verify` | Private bot/parent access-check JSON | Successful publication |
| Reviewed synthetic page | Preview checksum and actual page receipt | General write authority or marketplace approval |
| Refresh/revoke/recovery | Observed lifecycle results and owner receipts | Exactly-once execution across failures |

For the publication rehearsal, the included
`adapters/notion/demo-report.txt` contains only synthetic text. After consent and
the explicit `verify` check, prepare a publication using a selected parent:

```sh
python3 scripts/notion_publish.py --config /absolute/private/publisher.json prepare \
  --kind report --parent-page YOUR_ALLOWED_PAGE_UUID \
  --title 'Symphony integration acceptance test — synthetic' \
  --body-file adapters/notion/demo-report.txt \
  --output /absolute/private/demo-publication.json
```

Review the exact preview and only then use the existing `publish` command with
its checksum. Confirm the actual page in Notion, retain the receipt, and manually
archive the disposable test page after evidence capture. No automatic publication
or cleanup is performed. If a response is lost, reconcile by publication ID and
owner state; never delete the durable claim to retry.

## 5. Security checks and distribution

The new CodeQL workflow covers Actions, Python and C/C++ using pinned actions,
on pull requests, main pushes and a weekly schedule once merged. C/C++ uses
`build-mode: none`; native C++26 compilation is independently exercised by the
build workflow. Inspect CodeQL extraction diagnostics and source coverage before
claiming a security result. A passing upload is not a comprehensive audit.

After live acceptance, capture a genuine demo and review the Notion/Cloudflare
data flows against approved privacy and terms coverage. Use the
[listing checklist](notion-marketplace.md) and obtain the appropriate Notion
review path. Operator-managed OAuth registrations are not automatically a single
public Marketplace connection. QuanuX supplies no hosted relay or shared client
secret. Signing, publication and marketplace acceptance remain separate gates.

# Notion adapter development verification — 2026-11-04

Base repository revision: `89bc8f3b615ebc993183086e9cf7189a0d583c64`.
Local host: Intel macOS, AppleClang 21, C++26 mode. Gateway is opt-in;
the existing Codex plugin and its pending public review package are unchanged.
This standalone repository carries the optional Notion integration.

## Passed locally

- Existing transport, bounded hashing, MCP integration and client-adapter CTest
  groups pass after the shared-core extraction. The extracted Bridge implementation
  is byte-for-byte identical to its previous source section; no domain behavior
  was changed during that refactor.
- **12 gateway cases** use real loopback HTTP, the C++ bridge and synthetic qxctl:
  authentication, Host/Origin/version checks, command/tool scope, metadata audit,
  session isolation, token rotation/revocation, ambiguous-token rejection, preview
  isolation, one-use apply, request-ID conflict/replay, deliberate HTTP response
  loss without repeated write, native refusal, expiry/capacity, malformed inputs,
  payload limits, duplicate Authorization headers, private-profile generation,
  existing same-UID IPC and IPC loss/session invalidation.
- The same 12 cases pass with AddressSanitizer and UndefinedBehaviorSanitizer.
- **11 Notion publishing cases** verify content previews, all document kinds,
  Unicode splitting, destination/expiry/checksum/token binding, durable one-attempt
  receipts, response-loss handling, refresh rotation/loss, revocation, private
  files, redirect refusal, bounded requests, exact API headers, and state/workspace
  checks on simulated OAuth callbacks. Notion API responses are fixtures.
- Skill validator, Python compilation, launchd plist syntax, whitespace checks,
  archive CRC, executable modes and exact tested binary bytes pass.

The restricted execution environment initially denied loopback/socket binds;
the affected tests were rerun with local-socket permission and passed. No real
Symphony installation, native grant or Notion workspace was modified.

The vendored HTTP server is cpp-httplib **v0.64.0**, with its upstream MIT license
and SHA-256 in `third_party/NOTICE.md`. The current upstream advisory list was
reviewed; this selection is newer than the published fixes for header decoding,
negative chunk sizes and GET-body request smuggling. This is not a comprehensive
security certification.

## Not established by these tests

Actual Notion Desktop/Agent handshake and permission UX; live Notion OAuth or page
creation; a live operator-owned Cloudflare Tunnel; cross-host identity; WSL/DGX
qualification of this new gateway; native signing; policy approval; marketplace
submission or acceptance. QuanuX-hosted OAuth onboarding and tunnel hosting are
outside this product scope. Hosted results below identify the exact tested source.

See [gateway acceptance](notion-integration.md), [publication recovery](notion-publishing.md)
and [marketplace requirements](notion-marketplace.md) for completing those checks.

## User-owned connector and selected OpenAI build — 2026-11-04

- Seven connector tests pass for both credential-file and token-file modes,
  exact hostname/tunnel binding, changed files, private permissions, exclusive
  configuration creation and nonactivating inspection/validation.
- Genuine **cloudflared 2026.10.0**, SHA-256
  `0560c9ab7281ac3f746055323623ed23bc0405b6dab9400474020cba33a978da`,
  accepts the generated JSON-formatted YAML. Four offline route checks match
  `/mcp`, optional `/notion/callback`, other-path rejection and other-host rejection.
  Its CLI help accepts the selected flags and advertises `--token-file`.
  Synthetic credentials were used only for offline validation; no tunnel was
  created, authenticated or started.
- The exact OpenAI package bridge (SHA-256
  `0d82ef8188bb064283a0734550f8c3e40846d8a46370fdbc00418705e6d406a1`)
  and selected OpenAI demo qxctl (SHA-256
  `dbaec017bab76d403dd359dfe72866d7f6c35e6958aa4068585f380e8e1585b9`)
  pass connection, discovery, description and a bounded read through the new
  loopback gateway and private Unix IPC. The native read returns
  `symphony.sov.remote-template.v1` for `operation=target_configure`.
  An initial missing-operation request returned a command error; supplying `json`
  explicitly was refused because the bridge owns it. The successful check uses
  only the required operation flag.
- Non-read commands remained disabled. Temporary processes and private profiles
  were removed. No installed profile, Symphony state or Notion page was changed.
  Native template output does not establish service health or deployment.

## Hosted baseline

The prior source revision `b70824291284ee48ece951990be4ca07ddeea14a` passed all six
then-existing CTest groups on Ubuntu 24.04 (Clang 19.1.1) and macOS 15 ARM64
(AppleClang 17) in
[run 41951750460](https://github.com/QuanuX/symphony-codex-ipc-mcp-and-skills/actions/runs/41951750460).
The standalone repository adds the seventh connector group and runs its own
workflow; its run results qualify the imported source separately.

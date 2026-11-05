# Standalone Notion integration provenance

Created at Duncan's direction on 2026-11-04 as
`QuanuX/Symphony-Notion-IPC-MCP`. The name identifies local IPC and the Model Context Protocol (MCP).

The local bridge, transport, command contracts and existing tests derive from
[QuanuX/symphony-codex-ipc-mcp-and-skills](https://github.com/QuanuX/symphony-codex-ipc-mcp-and-skills)
at base `89bc8f3b615ebc993183086e9cf7189a0d583c64`.
The Notion gateway, shared Bridge extraction and publishing work were initially
prepared in that repository's draft
[PR #3](https://github.com/QuanuX/symphony-codex-ipc-mcp-and-skills/pull/3),
through commit `b70824291284ee48ece951990be4ca07ddeea14a`.
The user-owned Cloudflare connector and subsequent repository separation are new
work in this repository. Source and license notices are preserved.

This is a curated source import, not a GitHub fork or an assignment as a Symphony
module. It does not inherit the Codex plugin's registry name, OpenAI submission,
release artifacts, marketplace identity or approval claims. Codex/Claude plugin
manifests, registry-publishing workflows and historical submission packets are
deliberately absent. No existing installed plugin profile or sealed OpenAI archive
is replaced by this repository.

The copied bridge core remains equivalent to the tested implementation at the
recorded source revision. Future shared-core changes require explicit comparison
and affected contract tests; the repositories are independently maintained.

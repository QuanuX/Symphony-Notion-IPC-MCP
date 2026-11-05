# Notion listing preparation — draft, not submitted

Publisher: **QuanuX** · Website: https://quanux.org · Source:
https://github.com/QuanuX/Symphony-Notion-IPC-MCP

Proposed listing name: **Symphony for Notion**

Short description: Connect Notion agents to your self-hosted Symphony quantOS,
and publish selected research, reports and incident records to your workspace.

Description draft: Symphony's optional adapter connects an authenticated Notion
agent to an installation you select. Discover available operations, inspect
results and perform authorized administration through qxctl and native Symphony
owners. A separate Notion OAuth connection publishes explicitly reviewed content
to allowed workspace pages. Symphony remains headless and user-hosted. Remote
tool calls and published content pass through Notion; permissions, infrastructure
and available operations depend on your installation and workspace.

## Required before claiming availability

- Real Notion Desktop/Agent testing through an operator-owned Cloudflare Tunnel, including header auth,
  protocol negotiation, scoped reads, authorized disposable writes and recovery.
- Public OAuth connection created with **Any workspace** scope, correct publisher
  identity, registered redirect and reviewed capabilities. Installation scope
  cannot be changed later. The operator-managed helper is implemented; a shared
  QuanuX OAuth secret must never be shipped to end users. Review a
  different distribution design if centralized public onboarding is ever requested.
  The current product provides only operator-managed connections and a connector
  for an existing user-owned Cloudflare Tunnel; QuanuX supplies no tunnel or relay.
- Live OAuth consent, refresh, revoke and publication into a disposable permitted
  page; fixture evidence is not a Notion production receipt.
- Review the published privacy notice (https://quanux.org/privacy) and terms
  (https://quanux.org/symphony-plugin-terms) for Notion/Cloudflare data flows, credentials,
  hosting, retention and revocation. Do not assume prior local-only review covers
  this optional remote path. Publisher approval precedes legal publication.
- Capture actual Notion screenshots and a short demo; use existing QuanuX assets
  only where their license/branding is appropriate. Do not create mock screenshots
  that imply a live connection has passed testing.
- Submit the listing separately in the Notion developer portal after those gates.

Custom MCP server setup and the API public-connection marketplace are separate
distribution paths. This packet establishes neither listing eligibility nor
Notion endorsement. No OpenAI submission or MCP Registry metadata is changed.

[Notion marketplace requirements](https://developers.notion.com/guides/connections-and-tokens/public-integrations/marketplace-listing)
and [public connections](https://developers.notion.com/guides/connections-and-tokens/public-integrations/overview), inspected 2026-11-04.

## Distribution inquiry — 2026-11-05

Notion Support ticket **5511808** received an automated response, not a rejection,
approval or listing submission. QuanuX requested human Marketplace/MCP and
Technology Partnerships review. The remaining questions are:

1. Can a Discover / Add to Notion AI listing accept each customer's own MCP URL?
2. Which team reviews MCP listings, and which authentication, security and demo
   requirements apply? Custom Agent header-auth support does not establish the
   identical requirements for the personal Notion Agent or a catalogue listing.
3. Can an operator-managed OAuth publishing integration be listed, or must one
   publisher-controlled registration provide installation? The existing helper
   does not implement centralized public OAuth onboarding.
4. Is listing review available while Technology Partner enrollment is paused?

The [Technology Partner page](https://www.notion.com/partners/technology-partner-program)
advertises Gallery placement and a live public integration prerequisite, but its
FAQ says applications are paused. Its linked
[interest form](https://form.typeform.com/to/DWbNQjjE) displayed **closed** during
the November 5 browser check. No form was submitted. The support inquiry asks
for routing and registration of interest; it is not a partner application.

The [Notion Agent MCP list](https://www.notion.com/help/connect-mcp-servers-to-your-notion-agent)
and [Custom Agent MCP setup](https://www.notion.com/help/mcp-connections-for-custom-agents)
are distinct from the gallery connecting external AI clients to Notion's own MCP
server. Our inbound gateway belongs to the former direction. Native package
distribution can remain on GitHub; Notion listing and onboarding are separate.
No QuanuX-operated relay, tunnel or OAuth secret distribution is introduced.

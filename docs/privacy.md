# Alpha data handling disclosure

This local adapter does not send telemetry or operate a hosted backend. It launches the operator-selected local qxctl with explicit arguments and forwards its bounded results to the connected agent application. A user-selected qxctl operation may use native provider or remote transports under that operation's own configuration.

Optional development adapters add explicit network flows: the gateway sends
selected tool results through the operator's Cloudflare Tunnel to Notion or another
configured MCP host; the publishing helper sends reviewed content and OAuth
requests to Notion. Gateway credentials, workspace tokens and publication receipts
are stored in operator-selected private files. The gateway audit omits payloads
and credentials; publication previews contain the selected content. No central
QuanuX service or telemetry is automatically activated. See
[gateway disclosure](notion-integration.md) and [publishing lifecycle](notion-publishing.md).
Publisher review of the public notices for these new paths remains required
before marketplace launch; the historical notice verification below is not that review.

The connected agent provider receives tool requests and returned data according to that application's policies. These may include installation paths, repository metadata, identities, operational state, and caller-selected result data. Running locally does not imply that content shown to an AI agent stays on the local machine.

Connection-profile retention and cleanup depend on the selected storage location and the host application. Host-managed `${PLUGIN_DATA}` may be removed when the host uninstalls or resets the plugin; profile survival is not guaranteed. Operator-managed files follow the operator's own cleanup arrangements.

A prepared preview expires for execution after five minutes. Expiry is not a five-minute memory-deletion guarantee: its record may remain held in process memory until an apply attempt consumes it, a later prepare call cleans up expired records, or the bridge session or process ends. The bridge does not persist an independent audit log. Symphony owners may persist their own intents, evidence, receipts and audit records according to their own storage and retention behavior. The bridge does not itself uninstall Symphony or delete native owner records; host-managed storage cleanup is a separate concern.

This disclosure describes implementation behavior. The publisher's existing
[privacy notice](https://quanux.org/privacy) and
[Symphony plugin terms](https://quanux.org/symphony-plugin-terms) belong to QuanuX.
Their prior local-Codex-plugin review does not establish coverage or approval of
this new Notion/Cloudflare integration. Review of the current public notices for
these flows remains a marketplace release requirement. This repository supplies
no central QuanuX service and collects no automatic telemetry.

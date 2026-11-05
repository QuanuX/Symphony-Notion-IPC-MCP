# Connect your own Cloudflare Tunnel

QuanuX distributes a connector helper, not a tunnel service. **You own and operate
the Cloudflare account, named tunnel, hostname/DNS, credentials, routing and host.**
The helper neither provisions nor manages these resources, installs cloudflared,
starts a Quick Tunnel, creates a QuanuX endpoint, nor opens an inbound port.

Notion → your Cloudflare hostname → your outbound cloudflared connector →
loopback Symphony MCP gateway → the selected local bridge/qxctl installation.
Your Cloudflare service handles the public HTTPS connection. The origin is plain
HTTP over loopback; Symphony needs no TLS certificate, HTTPS server or GUI.
The separate same-UID IPC path remains local. C++ owns the MCP bridge/gateway;
Python 3.11+ only prepares and launches the user-selected cloudflared executable.

## Prerequisites

- Your existing named Cloudflare Tunnel and a hostname you control. Its DNS must
  already route to that tunnel. For shared tunnels, integrate the route into your
  existing deployment; never start replicas with inconsistent ingress tables.
- Your own cloudflared executable. Token-file mode requires 2025.4.0 or later.
- A private gateway profile whose `allowed_hosts` contains the exact public
  hostname. Keep the gateway on loopback and retain MCP bearer authentication.
- A 0600 tunnel credentials JSON file (local management), or 0600 token file
  (dashboard/remote management). Keep tokens out of chat, command arguments and Git.

The helper writes a new 0700 directory and 0600 files. It pins the selected
cloudflared binary, gateway profile, ingress and credential digests. After an
intentional upgrade, scope change or credential rotation, prepare a new connector
directory. It never overwrites the existing configuration or the secret file.

## Locally managed named tunnel

```sh
python3 scripts/cloudflare_connector.py prepare \
  --gateway-config /absolute/private/gateway.json \
  --hostname symphony.YOUR_DOMAIN \
  --cloudflared /absolute/path/to/cloudflared \
  --tunnel-id YOUR_EXISTING_TUNNEL_UUID \
  --credentials-file /absolute/private/YOUR_EXISTING_TUNNEL_UUID.json \
  --output /absolute/private/symphony-connector
```

Use a lowercase real DNS hostname, not the uppercase examples. The credentials
must identify that UUID. `cloudflared.yaml` is JSON-formatted YAML with one exact
`/mcp` rule forwarding to the selected gateway's loopback port, a matching Host
override, and a final 404 catch-all. No secret is copied into it.

Validate the configuration locally without contacting or starting a tunnel:

```sh
python3 scripts/cloudflare_connector.py validate \
  --profile /absolute/private/symphony-connector/connector.json
python3 scripts/cloudflare_connector.py inspect \
  --profile /absolute/private/symphony-connector/connector.json
```

Validation invokes cloudflared's own ingress validator. It proves syntax, not DNS,
ownership, edge policies, external connectivity or actual Notion acceptance.

## Dashboard-managed tunnel

Replace `--tunnel-id` and `--credentials-file` with
`--token-file /absolute/private/cloudflared.token`. The token selects its existing
tunnel; verify that identity in your own dashboard. The helper does not parse an
undocumented token format or claim to verify ownership from a token file.

`dashboard-route.json` contains the desired route for **review and integration**
into your existing tunnel configuration. It is not submitted to the Cloudflare
API and must not replace other applications' routes. The matching public hostname
routes `/mcp` to `http://127.0.0.1:GATEWAY_PORT` with HTTP Host Header set to the
same public hostname. Local `validate` is deliberately unavailable for remote
ingress because only your dashboard controls the actual route. `inspect` remains
available and does not connect.

## Start only when selected

Start the configured gateway, then explicitly run the connector:

```sh
python3 scripts/cloudflare_connector.py run \
  --profile /absolute/private/symphony-connector/connector.json
```

The helper executes only the pinned cloudflared binary, without a shell or ambient
`TUNNEL_*` overrides. Secrets remain file-based. It disables automatic binary
updates so the operator controls upgrades. It uses warning-level logging and
does not add payload logs. Stop the foreground process to disconnect; persistence
is managed by your own existing service manager, not automatically installed.

Enter `https://YOUR_HOST/mcp` in Notion with the **MCP gateway bearer token**.
This token differs from the Cloudflare connector token: never give Notion your
tunnel credential. Verify Host/Origin behavior and a bounded read through Notion.
Sharing an agent shares its connection authority; scope tools and commands.

Cloudflare Access is optional user policy. Interactive Access login is not an
MCP authentication flow. If Access protects the hostname, use a service-auth
configuration that the actual Notion client can supply, and test it. Do not add
an undocumented header workaround, weaken Access automatically or assume the
gateway bearer token also authenticates to Cloudflare Access.

## Optional publishing callback and recovery

`prepare --publisher-callback` also prepares `/notion/callback` → loopback 8766.
Use this only for the separate Notion publishing OAuth registration. Its callback
listener runs during explicit authorization; no QuanuX OAuth backend is supplied.
Use the same hostname in the registered redirect URI. The route and credential
lifecycle remain owned by the operator.

Cloudflare and Notion process forwarded tool inputs/results. Disable caching and
payload/Authorization logging for this route. Preserve MCP headers and JSON.
Tunnel reconnection does not mean an admitted native operation failed: keep
request IDs and reconcile unknown writes with their owner before retrying.
Distinct gateway instances behind multiple replicas do not share session state;
use one selected gateway per endpoint unless a qualified routing design provides
session affinity. Do not infer native exactly-once semantics from a tunnel badge.

Official contracts checked 2026-11-04:
[configuration and validation](https://developers.cloudflare.com/tunnel/features/locally-managed-tunnels/configuration-file/),
[token files](https://developers.cloudflare.com/tunnel/reference/run-parameters/#token-file),
[Host header](https://developers.cloudflare.com/tunnel/reference/origin-parameters/#httphostheader),
[credential ownership](https://developers.cloudflare.com/tunnel/features/locally-managed-tunnels/tunnel-permissions/).

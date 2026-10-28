# Managed public access

PandaHome maintains a public entry point for a service already running on your LAN.
It reuses the existing Aliyun DNS and UPnP clients and the official `frpc` binary;
it does not implement a tunnel protocol. Home power, connectivity, DNS caches and
the relay remain availability dependencies.

## Design and evidence

- **Automatic** selects a direct route when the router reports the same global
  IPv4 address observed by an external HTTPS IP service and UPnP is available.
  Shared `100.64.0.0/10`, private WAN addresses, or an address mismatch recommend
  relay. Missing evidence is **unknown**, never proof of public reachability.
- **Direct** maintains an owned UPnP mapping and optionally an Aliyun A record.
- **Relay** writes native frp configuration and supervises `frpc`. The operator
  supplies a reachable `frps` server, authentication and allowed public ports.
  Existing frp reconnect/TLS behavior handles the transport.
- A background reconciler restores persisted services on startup, refreshes DNS
  after address changes, renews mappings, and retries failures. Only its own UPnP
  descriptions may be replaced or removed; unrelated mappings are preserved.
- API reads do not create mappings. Configuration changes require an active
  administrator. A periodic check is independent of the browser being open.
- Local TCP checks, a running tunnel process, and independently verified inbound
  reachability are separate evidence. UDP has no generic connection handshake.
  An optional remote Prometheus blackbox exporter supplies external TCP probes;
  an optional webhook reports sustained failure and recovery transitions.

## Delivery sequence and acceptance

Current work state belongs to [tasks.md](../tasks.md), Feature 07. Atomic commits
deliver this design, network detection, frp integration, persisted reconciliation,
then the management UI. Every implementation commit includes its collaboration
record and relevant tests. Acceptance covers unknown/CGNAT/public classifications,
frpc lifecycle and private configuration, mapping ownership/renewal/recovery,
DNS change detection, active-admin API authorization, disabled/deleted cleanup,
external-evidence boundaries, and a usable localized mobile/desktop flow.

## References

- [Shared address space, RFC 6598](https://www.rfc-editor.org/rfc/rfc6598.html)
- [Official frp client configuration](https://gofrp.org/en/docs/reference/client-configures/)
- [Official frp server configuration](https://gofrp.org/en/docs/reference/server-configures/)
- [Prometheus blackbox exporter](https://github.com/prometheus/blackbox_exporter)

## Setup

1. Run `cd api && alembic upgrade head`. Upgrades create `published_services`;
   user accounts and existing services remain separate. Start a single API worker
   per database/state directory. Background work belongs to the application's
   lifespan and does not depend on an open browser.
2. Visit `/access` with an active administrator account. Add the existing service's
   LAN IPv4, local port and desired public port. Automatic mode is the default;
   explicit direct/relay choices remain available. Relay-only services may target
   `127.0.0.1`; direct services must use a LAN address reachable through the router.
3. Optionally specify an Aliyun DNS zone and host record (for example `example.com`
   and `photos`). Existing Aliyun credentials are reused. Direct uses A; relay
   uses A/AAAA for a public IP or CNAME for a hostname. A hostname-based relay needs
   a subdomain rather than `@`. The selected default-line record is synchronized;
   multiple/conflicting, disabled or locked-to-another-value records fail closed.
4. If relay is recommended, install matching official `frpc`/`frps` binaries.
   On a public server, configure `frps.toml` with a token and allowed forwarding
   ports (choose a token locally; do not commit it):

   ```toml
   bindPort = 7000
   auth.method = "token"
   auth.token = "replace-with-your-private-token"
   transport.tls.force = true
   allowPorts = [{ start = 18080, end = 18089 }]
   ```

   Allow the control port and selected forwarded TCP/UDP ports through that
   server's firewall. Run `frps -c /private/path/frps.toml` using your service
   manager. This deployment is a separate operator action.
5. On the home backend set `RELAY_SERVER_ADDR`, `RELAY_SERVER_PORT`, `RELAY_TOKEN`
   and optionally `RELAY_PUBLIC_HOST` / `RELAY_BINARY`, then restart the API.
   PandaHome supervises its own frpc process with TLS and native reconnects.
   It writes credentials outside the source checkout, in a private 0700 directory
   with a 0600 file, and keeps its authenticated status interface on loopback.

## Settings

All settings are in `api/.env`; their examples are in `api/.env.example`.

| Setting | Default | Purpose |
| --- | --- | --- |
| `ACCESS_CHECK_INTERVAL_SECONDS` | `60` | Maintenance cadence, 15–3600 s; shortened for active leases |
| `ACCESS_PROBE_URL` | empty | Remote HTTPS blackbox exporter `/probe` endpoint with `tcp_connect` module |
| `ACCESS_ALERT_WEBHOOK` | empty | HTTPS JSON webhook for sustained failure and verified recovery |
| `ACCESS_ALERT_FAILURE_THRESHOLD` | `3` | Consecutive failed checks before a failure notification |
| `RELAY_SERVER_ADDR` | empty | Reachable frps control host; empty means relay is not configured |
| `RELAY_SERVER_PORT` | `7000` | frps control port |
| `RELAY_PUBLIC_HOST` | server address | Public IP or hostname for the forwarded port |
| `RELAY_TOKEN` | empty | Private token matching frps |
| `RELAY_BINARY` | `frpc` | Installed frpc executable or absolute path |
| `RELAY_STATE_DIR` | `~/.local/state/pandahome` | Private state directory outside the checkout |

For browser access to a published web service, configure HTTPS/authentication in
that service or an existing reverse proxy. PandaHome forwards TCP/UDP; it does not
terminate HTTPS or issue certificates for applications.

## Maintenance, verification and cleanup

- Every cycle rediscovers unavailable UPnP, compares observed public IPv4 with WAN
  evidence, refreshes owned mappings and updates changed DNS values. A 725 router
  response automatically retries a permanent lease. Lease `0` remains explicit;
  finite leases must be at least 60 seconds. Native frpc reconnects on disconnect,
  and an exited process is relaunched on the next cycle.
- Automatic direct failures can switch to a configured relay. Three failed
  external direct probes trigger a relay trial; direct is reconsidered after a
  ten-minute cooldown. Failed owned-mapping cleanup is retained for retry without
  blocking outbound relay recovery. Unrelated mappings are never deleted.
- The local service, native per-proxy relay registration and remote inbound probe
  are checked separately. **Healthy** requires external TCP success and, for relay,
  registration of this exact proxy. Restarted or stale evidence is not reported
  as current health. UDP and entries without an external probe remain unverified.
- To configure a blackbox exporter, provide an HTTPS endpoint on a separate public
  machine with the standard `tcp_connect` module. Restrict access and allowed probe
  targets at the exporter/reverse proxy. PandaHome adds `module=tcp_connect` and
  `target=host:port`, preserves existing URL query parameters, and accepts only a
  successful bounded response containing `probe_success 1`. NAT loopback from
  the home host is deliberately not used as public proof.
- Optional webhook JSON contains `service_id`, `name`, `event` (`failure` or
  `recovery`) and `reason_code`. Unchanged failures/successes stay quiet; failed
  deliveries retry later. Recovery is announced after independently verified
  external reachability returns.
- Disable or delete entries in `/access` to remove owned routes. Deletion retains
  configuration if cleanup fails, so retry when router control returns. DNS
  records are retained intentionally, including operator-existing records.
  Stopping PandaHome stops its tunnel process; direct mappings follow router
  lease semantics. Disable before shutdown if the entry must close immediately.

## API and validation

All endpoints require an active administrator:

- `GET /api/access/state` — current network evidence, relay state and persisted entries
- `POST /api/access/detect` — bounded read-only detection; wakes maintenance
- `POST /api/access/services` — create desired service configuration
- `PUT /api/access/services/{id}` — replace desired configuration
- `DELETE /api/access/services/{id}` — clean owned routes and delete intent
- `POST /api/access/services/{id}/check` — run reconciliation and return fresh state

Reserved `{public_port, protocol}` pairs and DNS hostnames cannot be shared by
two configured entries. API schemas reject invalid addresses, ports and DNS names.

Run `pytest -q api/tests`, `npm run test --prefix web`, `npm run lint --prefix web`,
`npm run build --prefix web`, and `pre-commit run --all-files` for local acceptance.
For a real **loopback-only** frp integration test, install matching official
binaries outside the checkout and run:

```bash
PYTHONPATH=api python api/tests/integration/frp_smoke.py --bin-dir /path/to/frp
```

That test proves native TCP/UDP integration and reconnect/process recovery; it
does not prove connectivity through a physical home router or a deployed relay.

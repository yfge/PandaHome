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
5. As an administrator, open **Public access → Connection settings and help** and save the relay
   address, control port, token, public host and installed `frpc` path. Set the
   trusted CA and server name when verifying a private relay certificate.
   Existing `RELAY_*` environment settings remain defaults until a profile is
   saved; they are no longer the only configuration path.
   PandaHome supervises its own frpc process with TLS and native reconnects.
   It writes credentials outside the source checkout, in a private 0700 directory
   with a 0600 file, and keeps its authenticated status interface on loopback.

## Relay profile and SSH integration

Relay configuration and an optional SSH control channel are managed by PandaHome.
The retained GPUFree Git entry has been adopted by the normal application;
the original standalone SSH and frpc jobs are both stopped and disabled, with
their exact configuration retained for rollback. Cloud frps remains existing
infrastructure. See [the acceptance checklist](../tasks.md).

The interface is an active-administrator relay configuration screen backed
by `GET`/`PUT /api/access/relay-config`. The profile belongs to the deployment,
while each published service keeps its own target, public port and DNS intent.
The private `relay-profile.json` lives under `RELAY_STATE_DIR`, outside the source
checkout, with directory mode 0700 and file mode 0600. Environment settings remain
defaults when there is no saved profile. Responses report token presence rather
than the token. Omitted or null token input preserves the saved token. The UI
omits an unchanged empty password field and offers an explicit clear action;
`clear_token=true` or an explicit API empty string removes the saved token.

TLS configuration must carry the trusted CA file and server name through to the
native client. A wrong CA or name must reject registration without silently
disabling verification. These deployment file paths are not application-service
credentials and must not be copied into public response bodies or shared logs.

For a relay control socket exposed only on the remote server's loopback address,
PandaHome may own an SSH local forward as part of the relay lifecycle. The SSH
host/user/port, existing identity and known-hosts paths, remote frps address/port
and local loopback port are explicit configuration. Use non-interactive
authentication and strict host-key checking. PandaHome starts the SSH channel
before frpc, stops frpc before the channel, and guards both process identities
across backend death. With no enabled relay service it must start neither child.
The existing remote frps remains operator-managed infrastructure.

### Retained-service adoption and rollback

1. Freeze and review the feature source, normal quality gates and the exact
   existing DNS, cloud frps and local service-manager identities. Snapshot only
   the owned configuration needed for rollback; keep secrets private.
2. Prepare a normal PandaHome deployment with a fresh private database/state and
   one API worker. Run migrations, administrator bootstrap and the API from the
   same deployed `api/` directory against the same configured database. Do not
   migrate, relocate or reset an unrelated existing database. Keep management
   API and web listeners on loopback and build outside the shared checkout.
3. Save the profile and a disabled service through the real UI. Confirm persisted
   reads without starting SSH/frpc or competing for the existing public port.
4. In the reviewed cutover window, verify and stop **both** owned standalone SSH
   and frpc jobs and persistently disable their automatic restart. Retain their
   exact original bytes. Only then enable the service in PandaHome and verify
   that its guarded SSH/frpc children own the runtime; do not replace cloud frps.
5. Use an independent external client with normal DNS/FQDN access to verify
   application content and authorization boundaries. Save disabled and confirm
   loss of access, then re-enable and confirm recovery. Restart the API against
   the same database/profile and verify old-child cleanup and restored ownership.
6. Keep the original DNS record ID and stable fields unchanged throughout.
   Same-value synchronization must not add, update or delete the retained
   record. Without a configured external probe, the product's unverified status
   remains honest even when a separately recorded external acceptance succeeds.

If takeover fails, stop the product-owned SSH/frpc children first and verify
their ports are released before restoring the original standalone SSH then frpc
jobs. Never keep both owners enabled. Preserve DNS, cloud frps, the new database
and evidence; a successful rollback is not a successful PandaHome takeover.
The retained cloud entry proves relay ingress, not company physical-WAN ingress
or native peer-to-peer traversal.

### Retained GPUFree Git acceptance: 2026-10-29

Feature commit `950d4412c0d24fd01aa33f9660d2a0f22b69ca30` was deployed from a
frozen source copy with a fresh private database/state, one API worker and
loopback-only management listeners. Through the real UI, the administrator saved
the profile and disabled service before either native transport was started.
The same database/profile survived normal API restoration and one controlled
API `SIGKILL`: old guarded SSH/frpc identities disappeared, new children belonged
to the restored application and home-client access recovered.

Home 1.81 used normal system DNS and the real FQDN
`gpufree-code.lets-gpt.com:8081`. Homepage, version, login page and anonymous-user
authorization returned the expected 200/200/200/401 results. A random anonymous
request marker was correlated with the unchanged cloud frps process's incoming
TCP connection; no packet payload or cookie was retained. UI pause removed the
owned public listener and made home access fail; UI re-enable restored it.

An initial strict probe compared an unrelated HTTPS IP-observation route with
the business connection. The home client's VPN split routing made these differ,
so that probe remained failed and the reviewed rollback restored the original
entry. The later nonce-correlated checks supply the accepted evidence; the
initial failure and rollback evidence were preserved.

Without `ACCESS_PROBE_URL`, the application still reports `pending`,
`relay_unverified` and `external_verified=false`. This is distinct from the
separately recorded manual external acceptance. The cloud address is a relay,
not a claim about the company router's physical WAN address.

In this environment, a reconciliation can take about 13 seconds. Saving intent
and requesting a manual check can queue behind an active reconciliation; a
25-second client deadline did not cover two successive detection cycles. Wait
for ordinary state/transport convergence instead of stacking immediate manual
checks. The first rollback's approved exact-process fallback was verified.

The final provider read matched the complete original DNS record, including its
ID and creation/update timestamps. Together with the reviewed same-value return
path and zero application Add/Update/Delete log entries, this supports the
no-DNS-write result; log counts alone would not establish it. Cloud configuration
hashes and frps process identity matched the original snapshot. Both old local
jobs remained disabled, while the managed App/web/SSH/frpc and original DNS/cloud
entry were deliberately retained. Temporary browser, authentication profile,
packet observers and cutover watchdogs were closed.

Detailed evidence and retained-resource policy are recorded in
[`20261029-043527-managed-relay-integration.md`](../agent_chats/20261029-043527-managed-relay-integration.md).

## Settings

Environment defaults are configured in `api/.env`, with examples in
`api/.env.example`. A saved administrator relay profile overrides relay defaults;
it does not override the database, state directory or unrelated P2P settings.

| Setting | Default | Purpose |
| --- | --- | --- |
| `ACCESS_CHECK_INTERVAL_SECONDS` | `60` | Maintenance cadence, 15–3600 s; shortened for active leases |
| `ACCESS_PROBE_PROVIDER` | `https` | External observer: existing HTTPS exporter or explicitly configured `ssh` |
| `ACCESS_PROBE_URL` | empty | Remote HTTPS blackbox exporter `/probe` endpoint with `tcp_connect` module |
| `ACCESS_PROBE_SSH_CONFIG_FILE` | empty | Owner-only ordinary JSON configuration outside the checkout; required for SSH provider |
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
- Public and private frp transports reuse one process guard. It captures process
  creation identities and cleans owned native processes if the backend or either
  monitor disappears, preventing old clients from blocking restored entries.
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

## External TCP observer over SSH

The default `https` provider retains the existing remote HTTPS exporter contract.
Use `ACCESS_PROBE_PROVIDER=ssh` only with a trusted host in a separate network
that can normally resolve and reach the published FQDN. Set
`ACCESS_PROBE_SSH_CONFIG_FILE` to an owner-only (0600 or stricter), non-symlink
ordinary JSON file outside the checkout; keep its parent directory private.
Restart the API after changing these environment settings. No UI configuration,
extra dependency, remote listener, installation or network-rule change is needed.

Example configuration (replace paths and the independently verified hostname hash):

```json
{
  "host": "observer.example.net",
  "user": "observer",
  "port": 22,
  "binary": "/usr/bin/ssh",
  "identity_file": "/private/observer-key",
  "known_hosts_file": "/private/probe-known_hosts",
  "allowed_targets": ["service.example.net:8081"],
  "expected_hostname_sha256": "<sha256-of-verified-remote-platform.node()>"
}
```

Reference an existing authorized identity and an independently verified SSH host
key. Use a probe-specific known-hosts copy so probe maintenance cannot affect
relay-control SSH. Credentials and private-key contents are never returned or
copied by the probe. Missing or malformed private configuration fails startup;
missing runtime trust, SSH failure, timeout or invalid evidence fails the check
without a local or HTTPS fallback. The target must exactly match the allowlist.

Each natural maintenance cycle sends a new nonce and target as JSON stdin to a
fixed `/usr/bin/python3` program. Strict SSH trust and the expected remote hostname
hash identify the observer. The program uses normal DNS, rejects non-global
answers, connects to an actual resolved peer, and returns fresh UTC evidence.
PandaHome requires matching nonce/target/hostname, actual successful SSH exit and
validated global DNS/peer before marking TCP reachability verified. Logs contain
safe structured evidence and a nonce hash, not credentials or raw SSH payloads.
Remote execution has a six-second alarm; local execution has a ten-second
operation deadline plus bounded process cleanup. Temporary SSH/guard children
are reaped each cycle; the remote host receives no files or persistent service.

Automatic verification proves a TCP connection from that observer, not HTTP
semantics, authorization, UDP, company-router ingress or direct P2P traversal.
Verify at least two new natural cycles, then exercise a controlled probe failure
and restoration. If only the observer's trust is temporarily unavailable while
the published service remains healthy, `probe_failed` and removal of verified
status demonstrate conservative handling of probe infrastructure failure, not
proof of a business outage. Keep trust-restoration protection and exact bytes.

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
`api/tests/test_relay.py` includes a real subprocess regression using a Python
listener: kill the backend, confirm every owned process and the listener stop,
then restart with the same state directory, proxy name and port and exchange data.
`api/tests/test_process_guard.py` also covers individual guard/watchdog death and
forced shutdown. These tests require no frp binary or real router.
For a real **loopback-only** frp integration test, install matching official
binaries outside the checkout and run:

```bash
PYTHONPATH=api python api/tests/integration/frp_smoke.py --bin-dir /path/to/frp
```

That test proves native TCP/UDP integration and reconnect/process recovery; it
does not prove connectivity through a physical home router or a deployed relay.
The crash-recovery check finds the actual native frpc descendant and kills it,
keeping its PID distinct from the shared guard.

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

Setup and API details are extended with the corresponding implementation commits.

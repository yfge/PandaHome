# Field acceptance — field-20261028-183427Z

The new field task starts from `d19968e`; the accepted product source remains
`4efe286`. Existing 373/103 tests, UI sign-off and earlier real DNS cleanup evidence
are preserved. This run does not reopen resolved UI findings. Task status lives
in `tasks.md`; each original owner records its own evidence. Access owns the
shared resource register, index and final documentation commits. PM only
coordinates, reviews read-only and independently validates.

## Current acceptance

| Field item | Owner | Status | Required observation |
| --- | --- | --- | --- |
| Actual public application, direct route | Access + UPnP | Not exercised; preflight in progress | Independent external DNS + nonce request, actual application receipt/time/source, update and revocation through the real PandaHome API |
| Actual public application, frp relay route | Access | Not exercised; preflight in progress | Existing suitable public frps, isolated managed service, same end-to-end nonce/update/revocation evidence |
| Physical-router ingress | UPnP | Not exercised; preflight in progress | Controlled real router, original mapping state, run-owned expiring mapping, external request and deletion verification |
| Direct P2P across separate networks | P2P | Not exercised; preflight in progress | Distinct provider/visitor networks, actual direct transfer, fallback distinguished and revocation/cleanup verified |

## Scope and ownership

Prefer a current PandaHome Docker deployment, already authorized SSH connections
and existing Aliyun CLI configuration. Report configuration locations and whether
usable; never publish credentials, private keys or whole environments. Saved
configuration, a listening port, DNS resolution, loopback, same-LAN traffic,
hairpin traffic and ordinary relay success are distinct from the required field
evidence. Existing applications, administrators, processes, mappings and security
settings are not replaced or stopped.

Only necessary reversible resources explicitly owned by this run may be created.
Before each write record original state, ownership, expiry and cleanup procedure.
Use finally cleanup plus a bounded lifetime/watchdog, then independently verify
deletion. A missing external client, suitable public relay or controlled ingress
router is an environment gap, not a passed field check.

## Resource coordination

Access ports 58110–58139 and P2P 58310–58339 are exclusive reservations;
UPnP owns TCP 58471 and UDP 58472. P2P owns the existing ECS temporary frps
lifecycle on an independently rechecked idle 8081, with run-specific private TLS
materials and token. Access and UPnP use that host only as isolated external clients. Check actual host/port availability and ownership before
use; never take over an existing listener or mapping. DNS uses unique fresh
per-owner names. Every created resource must be linked to this run_id and a
specific cleanup record. No management dashboard is published to the Internet.

## Live preflight findings

Existing Aliyun CLI configuration at `~/.aliyun/config.json` is usable; the
original project DNS service completed a read-only cloud request. Local Docker
is reachable but no PandaHome container was identified. An existing user-owned
ECS and existing SSH identity were verified by the UPnP owner and are available
for independent external requests; no new credentials are needed.

The physical Huawei gateway reports a public WAN address. Local default routing
uses a VPN and reports a different observed egress. Explicit direct publication
therefore needs the gateway WAN selection fix; the conservative automatic mode
is unchanged. No API detector override is permitted.

UPnP first-attempt cleanup returned ambiguous XML, then independent specific
lookups returned fault 714 for both owned ports; the original 39 rules remained.
`upnp/recovery-cleanup.json` records verified recovery. A later private-candidate
TCP/UDP attempt transferred three nonces per protocol and verified removal; it
remains candidate evidence until bound to a committed fix and genuine API replay.
The original 42-character ManagedMappings ownership description requires its own
real readback check; short test labels cannot replace that check.

Cloud private NIC/source routing and distinct public egress are real observations.
P2P must establish independent cloud-side NAT from NIC/provider/STUN evidence
and transfer actual data directly; the precise eligible topology is home NAT to
cloud VPC NAT. STCP, loopback control connections and STUN alone do not pass it.

## Evidence register

Access evidence root:
`/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/field-20261028-183427Z/`.

- `run-context.json`: UTC start, baseline, owners and separate acceptance states.
- `source-sha256.json`: actual inspected source/config/test fingerprints.
- `resources.json`: original state, run ownership, expiry and cleanup/verification.
- `preflight-local/`, `source-topology/`: live configuration/deployment/host and
  network-capability observations with sanitized commands and exit codes.
- `api-harness/`: isolated genuine-API/nonce test candidates and their review.

External-client requests and actual application receipts must share run_id,
unique random nonce and UTC timestamps. Record actual payloads, source-network
evidence and before/after/revocation results. Preserve previous UI/DNS artifacts;
this run uses new directories and does not promote historical results to current
field acceptance.

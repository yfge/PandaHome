# Field acceptance — field-20261028-183427Z

The new field task starts from `d19968e`; the accepted product source remains
`4efe286` for the unchanged frontend. Backend field fixes are `65dc3a8`
(direct WAN selection) and `fe17a0f` (both UPnP clients). Earlier 373/103, UI
sign-off and real DNS cleanup evidence remain preserved; current full native
hooks pass 393 backend and 103 frontend tests, plus type checking/default build.
This run does not reopen resolved UI findings. Task status lives
in `tasks.md`; each original owner records its own evidence. Access owns the
shared resource register, index and final documentation commits. PM only
coordinates, reviews read-only and independently validates.

## Current acceptance

| Field item | Owner | Status | Required observation |
| --- | --- | --- | --- |
| Actual public application, direct route | Access + UPnP | **PASS on fe17a0f** | Real API + original DnsSync, independent ECS normal DNS/HTTP nonce, same-row 58111→58112, old-port failure, new-port success, inaccessibility after disable and exact owned cleanup; 4/4 external proofs |
| Actual public application, frp relay route | Access | **Public ingress unpassed; runtime diagnostic PASS** | Real API/native frpc registered through public 8081 and transferred nonce through the cloud host's loopback 58131; that test port lacks SG public ingress and an off-frps external client is still required |
| Physical-router ingress | UPnP + Access | **Committed-source TCP/UDP transport PASS** | Actual independent ECS→public Huawei WAN→run-owned mapping→LAN nonce app, exact native 42-character description, change/removal, Access window original 39 stable fields unchanged; final committed TCP/UDP each 3/3 and owned cleanup pass, with later historical baseline drift tracked below |
| Direct P2P across separate networks | P2P | **Not passed** | Independent cloud VPC NAT confirmed; real native direct attempts failed to transfer nonce. STCP/SSH and cloud coordinator/visitor loopback are kept separate |

## Committed-source application evidence

`api-harness/native42-20261028-195333Z-4dd43f/` records the original API-generated
UUID and `ManagedMappings.spec`, full 42-character GetSpecific readback, actual 60s
lease, disable/delete, missing mappings, original 39 stable fingerprint and
private API/database/admin removal. Parent actual exit is 0. No DNS was configured.
The hardware supports this 42-character marker; no mapping-ownership relaxation
or shorter product description was introduced. The separately observed 50-byte
cleared description remains historical diagnostic evidence.

`api-harness/active-20261028-195637Z-d5d4f8/` records the full real application:

1. Fresh unique RR is absent before enable. The original project DnsSync writes
   the physical WAN, rather than the different VPN observer; both authoritative
   A replies agree. No detector, DNS or router response is fabricated.
2. A Python client launched on the independently verified ECS resolves the real
   hostname normally, connects using that hostname and checks the actual WAN
   peer, HTTP200 and fresh random nonce. The LAN application logs the same nonce,
   Host, body hash, actual ECS source and UTC. SSH launches the client only;
   there is no SSH forward on this application path.
3. A full real API update moves the same service from 58111 to 58112. Independent
   requests prove old 58111 unreachable and new 58112 returning the exact nonce.
   Disable then proves 58112 unreachable while DNS still resolves.
4. Main, observer and independent watchdog all exit 0. Cleanup verifies API/DB
   rows absent, local listeners closed, both exact mappings absent, original 39
   stable fingerprint unchanged, exact captured DNS RecordId deletion, two
   provider-absence reads and both authoritative NXDOMAIN replies. The private
   DB/admin/control work directory is deleted. A fresh process independently
   repeats the original cloud read and native GetSpecific 714 for both ports.

The API HTTPS blackbox probe was not configured. Its honest state remains
`pending` / `inbound_unverified`, `external_verified=false`; the separate external
content acceptance does not force its health status green. This run changes the
service port with a fixed WAN; earlier real DDNS value-update evidence remains
a separate preserved run. Current DNS writes are one Add and one exact Delete.

Recursive cache observations are retained: after publication one public resolver
returned A with 600s TTL while another retained NXDOMAIN with 557s; after disable
both returned A while ingress was closed; after deletion both returned NXDOMAIN
with 600/494s. Provider/authority and ECS content proof passed. This does not claim
instantaneous propagation to every resolver.

`api-harness/relay-diag-20261028-201253Z/` uses an isolated real API/native frpc and
P2P's leased public 8081 frps. The original registration completed and cloud-local
HTTP 58131 received the actual home nonce; disabling closed that registration and
cloud-local connection. Actual driver/SSH proofs and cleanup return 0. The
application port has no SG public Accept and the observer is co-located with
frps. Public-relay ingress, public DNS and certificate CA pinning are unproved by
this diagnostic. No DNS or UPnP write was made. Access native/API/nonce children,
DB/admin/control/frpc credential state are removed; Access issued the explicit
shared-frps release. P2P independently confirmed 8081/58131 closed, recorded PIDs
and directory absent and local private token/TLS directory removed.

## Later router baseline discrepancy

UPnP's `udp-committed-20261028-204037Z/` repeats the real committed full API
Add/Delete 200 and physical UDP 58472 data path. Three distinct ECS/LAN nonce
pairs match: 267 request payload bytes and 654 reply bytes. The own 60s rule,
receiver, API, DB/admin and watchdog are removed. The current window's original
38 stable entries agree before and after.

The stricter comparison against the initial 39 **returns exit 1**: original
UDP 32783 was already absent before this late UDP window and reads 714. Its
initially requested lease was 21600s; the disappearance cause is unproven. The
remaining 38 stable fields match. Last original 39 verification was 20:15:25 UTC;
the late UDP pre-test snapshot already has 38. No owner restored/adopted/deleted
that unknown rule. `baseline-drift-review.json` preserves the raw failed audit.
TCP/UDP transport and owned cleanup passed in their stated windows; the global
initial 39 preservation check remains unresolved, and current table state is not
reported as 39. See the UPnP owner's `20261028-204556` field log.

The final independent window `final-api-nonce-20261028-204901Z/` again binds
all 49 application source files to `fe17a0f` and uses the normal authenticated
full project API, with no dependency overrides. TCP and UDP each return three
ECS nonce replies. This explicit-gateway window uses 31-character run labels;
the separate native42/Access application runs prove the 42-character ownership
marker. Both Add and Delete calls return 200; final own-specific reads
return 714, listeners stop and external requests fail after revocation. The
independent cleanup process exits 0 against its recorded current 38 baseline,
whose stable hash agrees before and after. This newer cleanup pass does not
change the earlier failed initial-39 audit or explain UDP 32783's disappearance.
The released `20261028-205324` owner log retains the final raw evidence links.

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
lifecycle on 8081, with run-specific private TLS materials and token. That
lease has ended and was independently cleaned; a historical handoff is not a
currently available relay. ECS roles are recorded separately: the external
direct/UDP client and P2P-owned relay/coordinator; Access's relay diagnostic
client was co-located with frps. Check actual host/port availability and ownership
before use; never take over an existing listener or mapping. DNS uses unique fresh
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
uses the committed gateway WAN selection fix; conservative automatic mode
is unchanged. No API detector override is permitted.

UPnP first-attempt cleanup returned ambiguous XML, then independent specific
lookups returned fault 714 for both owned ports; the original 39 rules remained.
`upnp/recovery-cleanup.json` records verified recovery. A later private-candidate
TCP/UDP attempt transferred three nonces per protocol and verified removal; it
remains attributed private-candidate evidence. The committed genuine API replays
are recorded above.
The original 42-character ManagedMappings description has now passed its own
committed-source real API readback and deletion; short-label and 50-byte historical
diagnostics remain separate observations.

Cloud private NIC/source routing and distinct public egress are real observations.
P2P established independent cloud-side NAT from NIC/provider/STUN evidence.
Actual direct data transfer is still required; the actual provider egress must
be identified. Home NAT to cloud VPC NAT is
eligible when traffic uses the home WAN. The isolated Docker/VPN NAT to cloud
VPC NAT path was also accepted as a precisely described test topology, but its
bounded native QUIC/KCP attempts transferred no direct nonce. A usable provider
egress preserving peer identity and bidirectional UDP remains required; a
non-VPN LAN node is one option, not a demand for a second household router.
STCP, loopback control connections and STUN alone do not close this check.

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

## Validation and remaining deployment inputs

On `fe17a0f`, actual `pre-commit run --all-files --verbose` with the verified
native frp release enabled passes **393 backend tests and 103 frontend tests**,
Ruff, ESLint and all remaining hooks. Type checking and the default Next 16.1.6
Turbopack production build pass. Evidence: `shared-validation/results.json` and
its three command logs. The frontend source remains identical to accepted
`4efe286`; old UE/UI issues are closed and were not reopened.

Independent read-only reviews are in `source-topology/`:
`active-publication-independent-review.json`,
`direct-cleanup-supplement-review.json` and
`relay-diagnostic-independent-review.json`. They compare all 49 product source
files to `fe17a0f`, raw proof/source hashes, nonce/source/UTC and cleanup evidence.
The reviewers did not perform network mutations themselves.

`upnp-final-api-window-independent-review.json` additionally checks all 27 final
UPnP manifest hashes, 49 committed sources, six matched request/reply bodies and
the independent current-38 cleanup exit 0. It does not invent an absent raw outer
driver exit record, promote this window's 31-character labels to native42 proof,
or erase the initial-39 failed audit.

A public relay field pass still needs a permitted application data port and an
external client on a different host/network from frps. The current security
group does not accept TCP 58131; no SG, firewall, VPN route or management setting
was changed. Native P2P direct still needs actual successful UDP/nonce transfer
on the precisely identified independent NAT boundaries. Do not mark either item
passed from control login, STCP/SSH, DNS alone or cloud-local relay content.
No persistent deployment, router reboot or WAN-address change was performed.

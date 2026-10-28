# P2P real-network field acceptance

## Summary

Run `field-20261028-183427Z` continued real execution without reopening closed
UX work. Starting baseline: `d19968e596c1cee81736c1eae4760586baecdce3`.
Both runtime controllers captured actual execution HEAD
`65dc3a8c1bceee073caf426b04ab04b8b8e057e5`. Prior product/UI/DNS evidence is retained.

Real remote STCP fallback passed four nonce exchanges and three negative
controls. The physical-home macOS XTCP attempt produced three nonce timeouts.
The subsequently authorized actual Docker/VPN NAT to cloud VPC NAT experiment
also ran real sessions: three QUIC and three KCP nonce requests timed out, with
actual STUN/candidate exchange and UDP header evidence. **Cross-NAT XTCP direct
is not passed for either topology.**
Earlier experiment listeners, processes, credentials and cloud directory were
cleaned and independently checked. A subsequently authorized Access shared-frps
lease is tracked by `access-shared-frps/status.json`; its current cleanup state
must be read separately from those historical results. The final public8081
QUIC/KCP complete-window phase also finished: both initial native windows reached
UDP wait timeout, both nonce user streams reset, and XTCP direct remains NOT
accepted. Both public leases are now independently cleaned with no live handoff.
Final frozen delivery: external `access-final-handoff.json`, with authoritative
`public-direct-complete-window/frozen-conclusion.json` and refreshed `resources.json`.
Historical runtime result `final-field-receipt.json` is retained unchanged. Final
independent freeze review verified16/16 input hashes; QUIC/KCP nonce0/2 remains
XTCP NOT accepted. All live run-owned resources are0, with last independent
read-only cleanup verification21:09:35UTC. Log/manifest custody is released to
Access for shared final integration; P2P does not stage/commit or continue editing
after this handoff. Earlier preparation/rebuild instructions below are historical
and superseded by the final freeze. The subsequently
requested exact /32 alternative is now a prepared, unapproved candidate only;
current review handoff is external `route-candidate/handoff.json`. No route
mutation/watchdog/new frps was run during its preparation. No product source,
shared tasks, index, build or commit changed.

## Changes

- `agent_chats/20261028-183427-p2p-field-preflight.md`: this own field log.
- External evidence root:
  `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a1831f-835d-7713-946f-226b1c2259b0/field-20261028-183427Z/`.
  Private acceptance scripts and redacted observations record UTC, command exit
  codes, source SHA, official hashes, topology, nonce receipts and lifecycle.
- `runtime/`: actual STCP fallback lifecycle and independent review.
- `runtime-direct/`: actual native XTCP attempt and independent review.
- `coordination/`: own capability, clock and port/lifecycle handoffs for peer review.
  No direct cross-chat messaging tool is available; delivery to another chat is
  not claimed. PM/Access/UPnP may read the own handoff artifacts.

Only this own log and external artifacts were written. Access owns shared index
and final docs. No original process, account, business mapping, production
service, security group or system route was changed. Temporary CA/server keys,
token, service keys, exported TOML and private SQLite state were deleted. No
secret, private key or complete environment was printed.

## Outcome

### Fresh configuration and topology

Docker Desktop was reachable: 18 original containers, three running, no identified
PandaHome deployment. All original container IDs were preserved. Checked sources
`api/.env`, root `.env`, `web/.env.local` and existing P2P/frps configuration were
absent. The NAS alias freshly proved Git-only, not an executable system shell.
Current Aliyun profile `~/.aliyun/config.json` supports identity/ECS/DNS reads.
Existing root SSH to the user-owned ECS used UPnP's private handoff and existing
key with BatchMode, IdentitiesOnly and StrictHostKeyChecking; credentials and
addresses are not reproduced here.

Physical LAN-bound official native STUN returned EasyNAT/BehaviorNoChange;
mapped fingerprint `80eb73a95266` matches Huawei IGD WAN. The default route uses
VPN utun8; default native discovery timed out. Docker native STUN mapped to VPN
fingerprint `1546a16219be`; that branch stopped and its container was independently
removed. A successful explicitly bound discovery is not runtime XTCP proof.

Cloud eth0 has private fingerprint `0e3b76789bb1`; actual native STUN maps to
public `7309b30197e6`, matching ECS API public fields. VPC/private ENI/public
mapping and native STUN agree. This is a distinct **cloud VPC NAT with fixed
public IP**, not EIP or another household broadband line. It meets the second-NAT
topology criterion, while topology alone cannot prove traversal.

### Real native execution

Official frp 0.71.1 darwin_arm64/linux_amd64 executables were release-manifest and
binary SHA verified. Actual project P2PManager/FrpRelay/shared process guard ran
against isolated state; project rendering produced provider/visitor TOML.
Field-only debug logging, disableAssistedAddrs, visitor control-port translation
and absolute visitor CA path are recorded. This is not default-deployment proof.

Coordinator and visitor shared the ECS. Frps listened on cloud loopback58330;
home provider reached it through owned SSH forward58332 over existing public SSH.
Cloud visitor used58320, wrong-key visitor58321, home nonce echo58310. These do
not overlap Access58110-58139 or UPnP TCP58471/UDP58472. No ingress rule changed.
Control loopback and SSH are disclosed and are never called direct-data proof.

First run, 19:29:03Z-19:29:46Z: deliberately unavailable local STUN forced actual
STCP fallback. Four fresh nonce/body exchanges passed: initial, after killing
only the verified owned native frpc and periodic manager recovery, after key
rotation/new export, and after re-enabling. Three fresh connections failed as
expected: wrong service key, old key after rotation, and disabled service.
Four visitor receipts match four provider echo records by nonce/body SHA; no
rejected nonce reached the echo. Native logs contain fallback dispatch and four
STCP business joins on provider/frps. This proves remote fallback carried over
SSH, not externally exposed frps-port acceptance or XTCP direct.

Second run, 19:31:24Z-19:32:18Z: actual stun.easyvoip.com:3478, fallback disabled,
assisted LAN candidates excluded. Cloud visitor STUN succeeded repeatedly with
its real cloud mapping. Home provider STUN preparation timed out; frps/visitor
reported missing NatHoleClient/NatHoleRespMsg. Three nonce requests timed out,
provider echo/peer events were empty, and no QUIC/direct/business join or STCP
fallback occurred. Native XTCP has no exposed UDP source-bind option in this
version; standalone discover's bind flag does not apply to actual XTCP. No route
override was authorized or performed. No product defect is inferred from this
network result alone.

### Subsequent accepted Docker/VPN-to-cloud topology: actual sessions

The PM clarified that Docker's actual VPN egress NAT is acceptable as the
provider topology. P2P therefore ran the real project P2PManager/shared guard in
an isolated Python3.12 Docker container using the official linux_arm64 frpc and
an original 50-file product-source snapshot at `76df0824`. No existing container
was modified. Field harness, source hashes, dependencies and image identities
are recorded in `runtime-docker/`; product source was not patched.

Cloud8081 was checked free before writes. Run-owned directory/bin and private
TLS/token configuration used an explicit20:09:11UTC cutoff; provider containers
had900-second internal TTLs plus run/expiry labels. The resource ledger was
marked cleanup=false during the new lifecycle, not left green from old cleanup.
The actual P2P execution owner, never PM, owned all finally/TTL cleanup.

Two public native TLS control windows failed before authentication (EOF/session
shutdown). Attempt01 terminated and cleaned before any STUN/nonce session.
Attempt02 additionally captured IPv4 TCP8081 headers on cloud eth0 and retained
zero packet records; this does not uniquely identify an upstream blocking layer.
Its Docker provider then authenticated through an owned host.docker.internal:
58332 SSH control forward to cloud loopback8081. TLS remained enabled; UDP used
the actual VPN egress NAT. No public frps or Access relay acceptance is claimed.

Attempt02 ran six fresh16KiB payload requests, three QUIC and three KCP, with
public STUN and fallback disabled. Request bodies/nonces were retained and
independently rehashed against sent digests. Both actual native STUN preparations
and exchanged SID/candidates are logged. All six requests timed out; provider
echo and business_work_connection counts are zero. Two provider pre-business
hole-success messages returned77.72.*.* peers at3478/3479, differing from target
cloud fingerprint7309b30197e6; the visitor never completed a corresponding hole.
Official native code decodes the message and validates SID, so the observation
must not be described as an unauthenticated plain-STUN false positive.

Strict header-only capture used Ethernet/IPv4-IHL5/UDP snaplen42, excluding
STUN3478 and filtering the actual provider-mapped IP. Retained2000 records are
all cloud-private0e3b76789bb1 to provider-egress1546a16219be, across1987 target
ports; no reverse record appears in the captured windows. The packet-limit
stop and late refresh leave a12.829841-second gap affecting the final KCP
request. Zero kernel drops does not establish zero network loss. Neither the
sample nor the unexpected returned peer identifies one unique failing layer.
The source-confirmed NAT controller uses STUN/message candidates, rather than
control TCP remote IP, for this analysis; shared loopback control is not itself
the reason it would classify the actual NATs as identical.

No direct payload succeeded, so neither direct reconnect/revocation nor a
successful frps-free payload path was signed. Old STCP checks stay separate.
`attempt-02/summary-correction.json` records correction of template wording
from public-frps to the actual SSH control path; raw logs/helpers remain intact.
Independent session and peer reviews agree on direct=false.

All listeners/providers/captures/SSH forward/container/images/private state and
cloud directory were cleaned. Independent final checks compare recorded Linux
PID+start_ticks (including tcpdump), exact arguments, ports, Docker image labels
and original container IDs. Zero owned survivors/images remain; all original18
containers remain. `runtime-docker/attempt-02/independent-final-cleanup.json`
passed before the top-level resource ledger was marked cleanup=true. New own
handoff `runtime-docker/final-receipt.json` supersedes older current-status notes.

## Verification

- `local-preflight/`, `ssh-preflight/`, `aliyun-readonly-preflight.json`,
  `stun-preflight.json`: bounded live configuration/network/host observations,
  native exit codes, fingerprints and reaped probe processes.
- `coordination/cloud-topology.json`, `cloud-native/cloud-nat.json`: live API
  and guest/native STUN proof of the distinct VPC mapping.
- `cloud-native/release-downloads.json`, `native-binary-preflight.json`:
  official release/executable checksums.
- `network-research/`: versioned official source references/native verify
  explaining UDP bind and actual business-peer evidence boundaries.
- `runtime/execution.json`: controller exit0, execution SHA and helper hashes.
  `events.json`, `provider-events.jsonl`, native logs and independent review:
  seven probes, four transfers, three rejections, native replacement, STCP only.
- `runtime-direct/execution.json`: controller exit0 denotes experiment/cleanup
  completion, not XTCP success. `result.json` explicitly reports zero transfers
  and xtcp_direct_acceptance=false.
- Both `sanitization.json` files record hostname-to-node-hash redaction with
  before/after SHA; nonce, body digest, peer markers and native text are retained.
  Executed helper hashes remain intact.
- Cross-host clocks are not assumed synchronized. UTC skew remains recorded;
  `coordination/clock-comparison.json` holds three read-only offset bounds.
  Correlation uses nonce/body hashes and same-controller ordering. Original
  generated body bytes were removed with private state; stored two-sided hashes
  are not called a retained full-body transcript.
- Both `cleanup.json` files verify deleted remote/private dirs, closed ports
  and waited provider/SSH children. `final-cleanup-verification.json` independently
  scanned exact-owned cloud/local process arguments: zero survivors; cloud
  58320/58321/58330 and local58310/58332 closed. No P2P DNS/UPnP mapping was created.
- `runtime-docker/attempt-02/{nonce-requests,independent-proof-review,peer-evidence-review,independent-final-cleanup}.json`: actual bounded QUIC/KCP session evidence, independently recalculated payloads, observed peer mismatch/capture limits and final resource checks. Attempt01 public-control failure remains preserved separately.
- Product tests/build/hooks were not repeated because no product/shared build
  changed. Private scripts passed syntax checks and actual runtime execution;
  prior product test evidence stays separate. No staging/commit was performed.

## Next steps

Final state: completed evidence is frozen and released to Access. Do not rerun
identical sessions or rebuild services from historical queues. The existing
non-VPN-node question remains unanswered; the passive /32 proposal is optional,
unapproved and nonblocking. PM may later review a user choice; P2P performs no
route/SG/VPN mutation or resource allocation. Historical next-step notes follow.

The latest PM review explicitly accepts the actual Docker/VPN NAT as the
provider topology, and this topology was now tested through real sessions rather
than excluded for differing from the physical WAN. Required next condition is a
runnable owned node/egress that preserves the actual UDP peer source and sustains
bidirectional UDP with the cloud peer. A non-VPN LAN node is one candidate, not
a mandatory second household line. Current observations do not uniquely identify
which VPN/host/upstream layer causes the mismatch or missing reverse traffic.
VPN/routes/firewall/SG remain unchanged. No new ECS credentials are required;
Access owns its alias investigation and P2P does not treat an alias as proof.

After that path exists, require actual nonce transfer plus native business-peer
or UDP evidence matching home WAN/cloud fingerprints. Process readiness, STUN,
disabled fallback, control loopback or relay success cannot close direct.
Long-lived established TCP revocation was not tested: this run verifies fresh
access after rotation/disable. PM independently reviews; Access owns final shared
docs/index. P2P does not stage or commit this field work.

Shared relay coordination update: `coordination/frps-sharing-contract.json` names
the existing trusted SSH metadata source, historical loopback control58330/SSH
forward58332 and deleted run-only auth/TLS source paths. No public frps control
endpoint/data ports are currently allocated by P2P. Access direct candidates
58111/58110/58120 remain with Access and physical IGD writes with UPnP coordination.
Any shared public frps must first establish a real public endpoint and exact
control/data allocation without SG/firewall/business-service changes, with
independent Access/P2P frpc configurations/processes/state. This handoff starts
no service and does not repeat the completed topology preflight.

Final sharing update: the8081 public-control experiment has ended and all its
auth/TLS sources/listeners are removed. `coordination/frps-sharing-contract.json`
records public authentication=false and no current public control/data allocation.
Access must not reuse the stopped service as a public relay. No SG, firewall,
VPN, route, business mapping, shared build, index or commit was changed.

### Newly authorized Access shared-frps lease

User explicitly requested a new independently owned frps8081/random-token/CA
handoff after the prior cleaned direct attempts. This is a new lifecycle, not
reuse of deleted credentials or a claim the previous service was still alive.
At19:56:41Z, the running ECS attached-SG inventory was read again: all ingress
pages, TCP8081 publicAny Accept; TCP/UDP58131 no matching ingress Accept/Drop.
No SG/firewall change was made. Before writes, cloud directory and listeners
8081/58131/58320 were absent. New owner sourcefe17a0f3, expires20:17:07UTC.

P2P actual execution owner started official frps with forced TLS, a new random
token and allowPorts restricted numerically to58131 (Access maps TCP only).
New server certificate includes actual public-IP SAN. A bounded official native
frpc verified the private CA/IP SAN and authenticated through public TCP8081.
Using a numeric tls.serverName suppresses DNS SNI; this new success does not
uniquely explain the prior invalid-name public EOF observations. This establishes
a real public control entry, not SG58131 reachability, API payload success or
XTCP direct. The cloud guest/API/STUN topology evidence remains separate.

Private0600 Access credentials/CA/source pointers were handed off only as a file
path under access-shared-frps/.private, never printed. Independent Access frpc
configuration/process/state is required; API management must remain private.
Current RelayConfig has no CA/serverName setting entry, so P2P_TLS settings cannot
be substituted and CA verification cannot be claimed from RELAY env alone. The
client contract documents this for the Access owner without product changes.

The status and top resource ledger are explicitly cleanup=false while this lease
is active. Access's latest-use deadline is20:16:30UTC; the cloud supervisor has
independent hard expiry20:17:07UTC. Access can stop its own clients and request
release from its own artifact; P2P owns frps shutdown, cloud/local credential
deletion and independent port/process/directory verification. PM does none of
those actions. Current lease truth is access-shared-frps/status.json and
coordination/frps-sharing-contract.json; do not reuse the older completed-stage
cleanup=true as current-service state. Shared docs/index/build/commit untouched.

Shared lease supervision review corrected three exception/release boundaries:
logs failure no longer skips shutdown; unverified cleanup is reported as
cleanup_unverified/active unknown; early release requires matching run_id plus
release_shared_frps=true and access_frpc_stopped=true. Only the known local
controller/observer identities were replaced; remote frps PID/start_ticks and
private handoff hash stayed unchanged. One handover helper incorrectly read
psutil.Process.returncode; it was corrected to the wait return value, audited
in controller-handover.json, and process counts independently confirmed exactly
one current manager and one observer. Earlier source/initial-resume records were
retained and original native-control proof events preserved. Current supervision
is manage_shared_frps_v2.py plus finalize_shared_lease_v2.py. The independent
observer stays bounded through TTL when cleanup is unverified and updates the
current ledger only after real post-delete checks. All three fixes were read-only
reviewed by a separate agent; frps/token/CA and Access client runtime were not
restarted or replaced. Lease closure will append a measured result separately.

Access binding clarification: local data target58131 and management API58120
are explicitly restricted to127.0.0.1; neither is a public backend listener.
20:10:59Z fresh attached-SG reads again allow controlTCP8081 but have no Accept
forTCP/UDP58131. No public data remotePort is selected/verified; local target58131
and cloud remote58131 are distinct roles. Existing publicAny Accept rules for
22/80/443/8080/8081 do not prove availability/ownership and were not repurposed.
Private handoff metadata was updated atomically with token/CA unchanged; source
checksums are in handoff-binding-update.json. No SG, listener, business process,
product source, shared task/docs/index or commit was changed by this update.

Shared Access lease closure at 2026-10-28T20:15:21.639982+00:00: separate post-delete SSH identity,
port/directory and local private-source verification passed.
Evidence: `access-shared-frps/independent-final-cleanup.json`. No product,
shared tasks/docs/index/build or commit was changed by the observer.

### Public-control XTCP window review and bounded follow-up

The new public8081 CA/IP-SAN control was authenticated by actual Docker native
frpc without SSH control. Attempt02 made two QUIC and one KCP 16KiB nonce
requests, all timed out. Independent review recalculated all body hashes,
confirmed zero provider echo/business joins, and captured1277 cloud-to-VPN
UDP headers with no reverse header in the45-second window. Two provider
prebusiness hole messages named a different peer fingerprint from cloud.
They are not target-peer or business success.

Review also found the7-second application waits and early protocol switch/stop
did not cover the complete native35/38-second traversal window. This observation
cannot be called exhaustive failure of those NATs or either protocol. A final
separate public-direct-complete-window phase is being prepared with fresh
credentials, a300-second server TTL,240-second provider TTL, one90-second
application wait per native protocol and94-second metadata capture per window.
Only its new run-owned image currently exists; the old shared Access lease is
closed, private handoff deleted, and independent cleanup passed at20:15:21UTC.
Old evidence is retained; no Access handoff/release file is reused.

### Final complete native windows and measured closure

New phase `public-direct-complete-window/` is independent of the deleted Access
shared lease. Fresh remote before-state at20:36:22UTC confirmed its directory
absent and8081/58320/58339 unbound in all TCP/TCP6/UDP/UDP6 tables. New owner TTL
was300seconds; provider TTL240seconds. A new run-only token/CA/IP-SAN certificate
and independent P2P-only configuration were created. Actual official native
frpc authenticated through public8081 without SSH control. Access credentials,
release file, API state and existing business resources were not reused.

Controller sourcefe17a0f3 and immutable Docker snapshot76df0824 are recorded
separately. Six relevant P2P/relay/guard/config/model/schema component hashes
match the checkout; this is not a claim the whole historical snapshot equals
current HEAD. Official native binary SHA and immutable image ID are retained.
The executed helper was independently reviewed before use. Its final capture
wait escalation and cleanup-result exit-code checks were strengthened before
execution; source hashes are captured at runtime. No product code changed.

Each protocol was retained for94seconds with an application read ceiling90s.
Actual QUIC and KCP application failures occurred at about20s as native visitor
`open tunnel timeout` / ConnectionResetError, not90-second application timeout.
Both initial native SID windows then independently reached `wait detect message`
UDP i/o timeout; later keepTunnelOpenWorker reported `no tunnel session` before
the protocol window ended. Automatic second SIDs near window end are recorded
as partial retries, not additional complete-window failures. No fallback was
configured. Both16KiB payload bodies remain in nonce-requests.json, and exact
canonical body hashes/lengths match the two sent records. Nonce success0/2,
provider business joins0, provider echo receipts0. Direct reconnect/revocation
cannot be signed without an established direct business session; previous STCP
recovery/rotation/disable results stay separate.

QUIC94-second UDP metadata capture contains1041 cloud-to-VPN headers and no
reverse header; KCP94-second capture contains1002 cloud-to-VPN headers and no
reverse header. Both ended naturally, reported no metadata truncation/kernel
drops, and independently reaped their precise children. These exact-peer,
single-interface header captures do not uniquely locate packet loss or rule
out source rewriting. Provider prebusiness hole messages still named77.72.*.*
peers differing from the intended cloud fingerprint. Native decode/SID checks
are acknowledged; those messages are never business/direct proof. Actual UDP
topology remains Docker/VPN NAT1546a16219be to cloud VPC fixed-public-IP NAT
7309b30197e6. Physical home WAN80eb73a95266 is not claimed as the UDP provider
exit merely because public TCP control can use that exit. Coordinator and
visitor are disclosed as cohosted on the ECS.

Owner cleanup ended20:39:44UTC and session exited0. Independent verifier ran
only after release and exited0 at20:39:51UTC: all6 recorded stable process
identities absent, exact-owned-path processes0, remote directory removed,
8081/58320/58339 free in all four proc network tables, local private state/
container/image absent. Historical18 original container IDs are all retained.
The immediate complete-window full container baseline was not persisted, so
independent preservation evidence is explicitly limited to those historical18;
root's in-memory before-list self-check is recorded separately, not promoted
to independent proof. No resource cleanup responsibility was handed to PM.

Authoritative sources: external `final-field-receipt.json`,
`public-direct-complete-window/{result,events,nonce-requests,component-source-comparison,cleanup,independent-final-cleanup}.json`,
per-protocol `*-native-after-window.json` and `quic/capture.json`,
`kcp/capture.json`. The current own resource ledger became cleanup=true only
after independent deletion checks. Prior UI/DNS/STCP/raw field evidence remains.

Real public8081 native TLS control is passed historically. Public Access data
port58131 still has no verified external acceptance: complete attached-SG read
at20:10:59UTC found no ingress Accept. Native server cloud-loopback business
joins are distinct from an external data client. Both leases and all private
handoffs are now deleted; no current endpoint is offered for reuse.

Next required condition is an executable owned LAN/provider node whose UDP
avoids the current VPN path, or another verified owned egress sustaining
bidirectional UDP with the cloud peer. Existing ECS SSH remains usable; no new
ECS password is needed. A text-only request asks for node role and existing SSH
alias/private config path, without credentials. No answer/approval is assumed.
No further identical-condition retries, global routing/security changes,
product tests/builds, staging or commits were performed. Shared tasks/final docs
and index remain Access-owned; the final receipt is available for PM read-only
review without claiming cross-chat direct message delivery.

### Prepared exact /32 alternative, no route execution

The latest instruction explicitly retained the accepted Docker/VPN HardNAT to
cloud VPC EasyNAT option. That real project/native session had already run,
including full QUIC/KCP initial visitor detection windows, real nonce requests,
peer headers and independent review; it was not skipped because the physical
Mac default STUN failed. `public-direct-complete-window/independent-proof-review.json`
now captures the separate review: initial visitor35s+3s delay ends in UDP timeout,
nonce0/2, provider business join/echo0. Provider38s timeout is not asserted:
provider accepted a mismatching prebusiness source earlier. Old STCP evidence
was retained without rerunning it. No other topology is declared impossible.

Current requested next work is a reviewable route candidate, not permission to
modify routes. External `route-candidate/route_window.py` defaults to read-only
plan; `test_route_window.py`, `verify_rollback.py`, `run_mac_validation.py`,
`README.md`, `PM-REVIEW.md`, `handoff.json` and independent semantic/review records
supply the concrete implementation, runtime gates, risks and rollback design.
Only this own agent log and own external artifacts changed. No shared tasks,
docs, index, build, stage or commit was performed by P2P.

Read-only capability checks recorded current defaultutun8 and consistent en0
physical gateway/DHCP router. All three noninteractive sudo checks returned1
with password-required, so future approved execution requires user local
terminal authentication. P2P does not ask for or read passwords. Existing
ECS trusted SSH/key metadata remains usable, no new ECS credential is needed.
The public snapshot's initially missed IPv6 metadata was hash-redacted with a
repair manifest; original raw snapshots are private0600 and no env/key/token
was printed.

Native STUN discovery also contacts its response's alternate address. Existing
artifacts did not retain that address; a new bounded en0/IP_BOUND_IF Binding
reader supplemented only this missing proposal evidence, without routing writes.
The initial reader parsed only newer OTHER-ADDRESS; it retained a real primary
response but did not parse legacy type5. v2 added RFC3489 CHANGED-ADDRESS and
both real primary/alternate responses succeeded. Their mapped fingerprint80eb
matches physical WAN, but this standalone Binding is not XTCP proof. The
minimal deduplicated targets are STUN main79d7f78d794c, actual alternate
dc334e12d1dd:3479, and owned ECS7309b30197e6: exactly3 public IPv4 /32s. The
main and alternate are both in the observed project STUN A set; native runtime
must pin the approved numeric main and must not silently add discovered peers.

The candidate refuses any observed pre-existing exact normal/scoped/cloned/ARP
host route using netstat-rn-a. It only adds ordinary unscoped host routes via
en0 gateway, writes no/0 or VPN configuration, and rechecks actual lookup. A
separate root watchdog is the sole route writer. It persists stable worker and
watchdog identities and before lookups before ready; worker activation follows
ACK. Activity240s plus cleanup30s are bounded by both fixed monotonic/UTC caps.
Durable intent/add ACK/signature and per-entry rollback/readback protect owned
additions; successful ACK followed by transient lookup/journal failure gets a
bounded recovery cleanup attempt. Foreign/mismatching/ambiguous routes are
retained and explicitly unverified rather than deleted without provenance.

Independent review found and closed two real candidate defects before any
execution: the internal watchdog initially lacked the full approval/eligibility
checks, and select followed by blocking readline could stall TTL on partial
IPC. Both entrypoints now share the approval/hash/root/Darwin/age/eligibility
gate; nonblocking deadline framing is bounded to4096 bytes and the active loop
rechecks liveness. Stable route identity ignores counters/expiry and rejects
abnormal route flags. Final route script SHA4504ec0ab4389056bd4f0e9c25fba652f99896e3db363e6153100dd977c74407
was independently reviewed with no new definite blocker.

Root reran `python3 route-candidate/test_route_window.py`:24 in-memory tests,
exit0; subprocess.run/Popen/socket/DNS are blocked by the fake suite. Syntax
checks passed. `verify_rollback.py` default dryrun exited0 and performed no
route/netstat/ps queries. These are not live route writes, root SIGKILL, TTL
rollback or new physical-WAN field acceptance. Final independent verifier is
prepared for future explicit read-only post-delete verification only.

A separately gated Mac native controller is prepared: defaultdryrun returns
before credentials/private dirs/SSH/services, actual mode requires the exact
planSHA, three installed ordinary en0 host routes, approved numeric STUN pin
and215..240s remaining. It runs ordinary-user Conda Python with the existing
unchanged enhanced FieldHarness/P2PManager and official Darwin frpc, without
Docker lifecycle. Original-user known_hosts/key ownership and strict host key
checks are explicit. Only in-memory metadata changes its old Docker label.
Actual mapped WAN must match80eb, but accepted direct still requires nonce/body
reconciliation, native intended peer and actual bidirectional UDP; no automatic
direct flag is set. The future mode was not run. Slow setup can abort before
both94s protocol windows; the script cannot promise completion at every215s
starting budget. Existing frps services/credentials were not resurrected.

The latest exact plan/hash and source manifests are in route-candidate/handoff.json.
It expires with current STUN proof at21:19:42.290505UTC; expiry or source changes
require read-only refresh and review of the new exact hash. Eligible is not
approved. PM alone will present the choice and obtain user approval; P2P does
not launch another authorization question or modify routes now. If a no-VPN
LAN-node option is preferred, missing input is a usable existing system-shell/
SSH alias for that owned node, not another ECS password.

Residual risk is explicit: a single watchdog SIGKILL, all monitor loss, permanent
kernel/filesystem blocking, ambiguous CLI result or concurrent identical-route
replacement can prevent automatic rollback and require manual recovery. Kernel
RTM_ADD clone replacement and RTM_DELETE check/delete races cannot be eliminated
by CLI signature checks. These3 destination /32s affect all processes to those
IPs, including ECS SSH/control, despite leaving default/VPN configuration intact.
No unconditional five-minute kernel lease is claimed. All statements await
actual authorized route and native-session evidence; no such success is invented.

Final delivery checks: all seven handoff file hashes match; JSON/Python syntax
valid; root re-ran the final Mac controller defaultdryrun with existing Conda,
exit0/noSSH/no.private/no services. Independent reviewer confirmed final
2e868cc8 minor SSH-file ownership hardening without weakened gates. Index
observed empty; P2P performed no staging/commit. Route proposal remains
unapproved and unexecuted; PM-only decision handoff is ready.

### Latest Access public-relay status, read-only

Latest user reports Access physical direct business4/4 and cleanup passed at
fe17a0f/active-20261028-195637Z-d5d4f8. P2P preserved that owner result and did
not rerun direct, STCP or XTCP. Prior cross-NAT direct failures remain unaccepted.
Current request was status/SG/client capability only: no frps restart, route
change, network-security write, shared build/index/stage/commit was performed.

Real trusted SSH snapshot21:04:56UTC exited0: no frps processes, no exact-owned
path processes; known p2p/p2p-complete/p2p-route cloud dirs absent;8081/58131/
58132 unbound in TCP/TCP6/UDP/UDP6. Old private Access handoff remains deleted;
no token/CA was regenerated. Lifecycle remains exclusively with P2P; Access
would own only its separate frpc/config/state. Historical public8081 native
TLS login is retained, while SSH-only58330 is never offered as public relay.

Existing Aliyun CLI config remained usable, DescribeInstances identified the
same one Running VPC ECS by exact trusted SSH IP. Initial SG helper accidentally
used unsupported PageSize/PageNumber flags. Local official CLI help exposes
MaxResults/NextToken for this API; v2 corrected pagination and exhausted all
attached-group ingress pages, exit0. The failed attempt is preserved as a helper
error, not interpreted as missing credentials or a network/SG failure. Latest
SG read showsTCP8081 public-any Accept; TCP/UDP58131 and58132 have no matching
ingress Accept. No SG, firewall, listener or business port was changed. This
capability conclusion does not itself prove effective public data ingress.

Independent topology review confirms existing Mac is an executable off-frps
client, even if it also hosts app/provider/frpc. Historical native public8081
login remote80eb73a95266 (darwin/arm64) differs from cloud7309b30197e6. Historical
Access58131 workConn also used80eb but its userConn was cloudloopback12ca17b49af2,
so that relay join is not public data-port acceptance. Future actual API relay
must send a nonce HTTP request from Mac with proxy variables disabled, record
frps userConn/guest incoming path identifying an off-frps egress, and reconcile
API mapping/frpc/app nonce. ECS calling its own public IP is retained only as
hairpin/cloud-local evidence. Mac Docker VM is not an additional independent
external host. No other third authorized execution machine is confirmed.

Own raw-command/status/SG/client-review evidence and peer-readable handoff are
in external access-relay-status-20261028T2103Z/, with entry handoff.json. It is
also linked from own coordination/access-relay-current-status.json and current
frps-sharing-contract.json. No direct send into independent chat IDs is claimed.
Blocking data-entry capability is58131/58132 SG ingress, not lack of an off-frps
client or ECS password. No unknown business port is repurposed to bypass this.

### Access release confirmed again, no recreation

Access reported its real API relay registration/native frpc/nonce/revocation
runtime diagnostics and cleanup complete, explicitly ECS-loopback58131 only,
field_public_acceptance=false and TLS enabled without an Access CA-pin claim.
P2P preserved that classification and Access's separate direct-field PASS. No
Access/P2P direct or relay diagnostic was rerun.

The valid matching run_id/release_shared_frps/access_frpc_stopped request was
already written20:15:11, observed by the owned controller20:15:15.652956UTC,
finally cleanup completed20:15:18.535052 and independent deletion review passed
20:15:21.629940. This latest notification did not reopen or extend the lease.
Server/private token/CA configs/handoff remained absent, so there was no new
resource to delete or unknown process to terminate.

A separate newly executed trusted SSH verifier completed21:09:35UTC, exit0 and
verified=true: both old lease identities and six later complete-window identities
were checked by PID+start_ticks, none matching alive. Three exact-owned cloud
dirs absent; exact-owned-path processes0, allfrps0;8081/58131/58132 unbound in all
TCP/TCP6/UDP/UDP6 tables. Eight local runtime-private dirs absent, extra runtime
private dirs0. Passive route-plan/IP metadata files were explicitly preserved;
they are neither live services nor token/CA directories. The verifier only read
state, never launched, killed or deleted resources.

New evidence: external access-release-confirmation-20261028T2108Z/
independent-final-cleanup.json, verify_release.py and release-receipt.json;
coordination/p2p-frps-release-confirmed.json points peers to the current receipt.
Lifecycle remains P2P-exclusive. No product, shared task/doc/build/index/stage/
commit, SG/firewall/route or existing service changed. No direct independent-chat
message send is claimed; the artifact and final reply supply the release receipt.

### Final independent freeze and Access custody release

Final independent audit used local retained evidence only: no network/SSH,
services, captures, cleanup, route commands or tests were started. New external
`public-direct-complete-window/freeze-review.json` reports freeze_ready=true:
16/16 inputs match exact SHA/byte counts, both canonical nonce bodies match sent
length/hash records, and successful application receipt is0/2. Original runtime
result and reviews remain unchanged; their historical pending-review marker is
explicitly superseded by `frozen-conclusion.json`, not silently rewritten.

Initial visitor SIDs naturally reached35s+3s UDP wait timeout and then no tunnel
session within each94s window. Assigned provider38s was not observed as a timeout:
provider returned about4.2s after response on unexpected keyed/SID-valid peers
3478/3479 rather than negotiated cloud7309b30197e6. Actual application streams
reset at20.004451s/20.000859s with native open-tunnel timeout; business read90s
and outer SSH/RPC110s were ceilings, not early7s harness termination. Later
automatic SIDs had partial windows only.

QUIC/KCP retained1041/1002 header rows across94.016s each, duration-limit stops,
metadata limit250000 not reached, no old2000-packet cap. QUIC filter-received1046
versus captured1041 is explicit. One-sided exact-peer IPv4/IHL5/UDP42-byte header
sampling and zero reported kernel drops cannot prove a complete reverse census,
rule out rewritten sources, or locate a unique loss point. This freezes direct
NOT accepted for these actual Docker/VPN-to-cloud-VPC sessions only; it does not
declare all topologies or permanent traversal impossible. Physical home-WAN
direct and direct reconnect/revocation remain unpassed; old STCP stays separate.

Refreshed external `resources.json` removes stale pending cleanup text, retains
closed phase history, lists no live run-owned service/container/process/directory/
credential resources, and binds its state to the existing independent verification
at21:09:35.240316UTC rather than inventing a new probe. The passive /32 scripts/
plans are retained artifacts, not a running watchdog or live token/CA. No routes,
SG/VPN settings, product source, shared tasks/docs/build/index or commit changed.

`access-final-handoff.json` is the final integration entry: exact own log SHA,
resource ledger, frozen conclusion, audit and cleanup hashes. Access receives
log/manifest custody for shared docs/index integration; PM remains review-only.
P2P will make no further edits after delivery. The no-VPN existing-node question
and optional exact /32 review do not delay this completed evidence handoff. Any
future expired plan needs fresh read-only evidence and review of its exact SHA;
no current authorization, silent refresh or route execution is inferred. Product
tests/build/hooks are not repeated because this step only seals documentation
and retained evidence; no commit is performed by P2P.

# Coordinated delivery review

Current work status remains in `tasks.md`. This document records the integration
acceptance contract for the three concurrent implementations and their reviewer.

## Subsequent field acceptance — field-20261028-183427Z

Field backend fixes are `65dc3a8` and `fe17a0f`; accepted frontend source stays
`4efe286`. Actual full native hooks pass **393 backend / 103 frontend tests**,
plus Ruff/ESLint, type checking and default Next 16.1.6/Turbopack build. Earlier
local-delivery, UE/UI and real DNS/DDNS records below retain their original scope.

Committed-source direct public application DNS/nonce, same-row port change,
revoke and exact cleanup pass with an independent ECS client. The final committed
full-API window passes TCP and UDP each 3/3, deletion and independent cleanup
against its current 38-rule baseline. Real API/native public-control relay runtime and
cloud-local nonce/revoke pass; public relay ingress remains unpassed because
58131 lacks SG ingress and the observer is co-located with frps. Native P2P direct
still has no successful payload despite real independent NAT evidence and native
attempts. No topology inference or STCP/SSH substitutes for a direct payload.

All run-owned services, mappings, credentials and private test DB/admin state are
cleaned and independently checked. A later historical-router audit remains
**failed**: initial 39 last verified 20:15:25, but UDP-window before/after contains
38 unchanged entries and original UDP 32783 is missing. Requested lease 21600s;
cause is unproven, with no restoration or unknown-rule write. This finding is
separate from successful transport and exact owned cleanup. Current operational
status, full resource/evidence pointers and remaining inputs are in
[field acceptance](field-acceptance-20261028.md) and `tasks.md`. PM only
coordinates/read-only reviews; owners and Access deliver code, scripts, docs and
commits. There is no persistent deployment or push.

## Ownership

| Workstream | Existing chat | Responsibility |
| --- | --- | --- |
| Managed public services | `01a18313-cae5-7420-bc89-6bd65f48116a` | Network classification, native public relay, persisted reconciliation, owned mappings, DDNS, health evidence, `/access` |
| Explicit UPnP gateways | `01a1831d-1a81-7ae2-aef0-34e6c0e417b7` | Request-scoped gateway selection, per-layer mappings, compatibility, localized gateway UI |
| Private P2P | `01a1831f-835d-7713-946f-226b1c2259b0` | XTCP provider and visitor, STCP fallback, secret-bearing downloads, `/p2p` |
| Integration and review | `01a18323-4d6f-7cb1-819a-cf6e1cab4dab` | Cross-workstream contracts, independent verification and acceptance coordination; no remaining coding or commit ownership |
| Independent UE/UI review | `/root/ue_ui_review` | Current-run desktop/mobile screenshots, interaction checks and actionable findings; added with the user's explicit authorization |

Shared `main.py`, configuration, migration metadata, navigation, READMEs and task
entries must preserve all three workstreams. Commit exact paths or reviewed
hunks, keep required collaboration records, and serialize index operations.
The user's final delivery instruction assigns all remaining shared changes and
commits to the public-access owner, with the project manager retaining independent
review. Historical ownership descriptions do not override that assignment.

## Role timeline

Early in this work, the PM directly edited shared code and UI and acknowledged
that this exceeded the agreed division of responsibilities. After the user
required coordination and review only, the PM stopped implementation work and
handed existing drafts to the responsible owners for independent review,
validation and submission. From that correction onward, the PM performed
coordination, read-only review and isolated acceptance checks. All remaining
shared code, documentation and commits were delivered by the Access owner;
this clarification assigns no new coding, documentation or commit work to the PM.

## Acceptance gates

1. Correctness: deterministic network classifications; explicit gateway failures
   never select another router; background work restores persisted intent and
   retries recoverable failures without the browser.
2. Authority: active administrators control new management APIs; public status
   does not expose credentials; visitor exports are protected and not cached.
3. Resource ownership: automatic maintenance cannot replace or remove unrelated
   mappings; public relay and P2P processes/configuration have distinct ownership;
   stop, disable, delete and credential rotation have tested behavior.
4. Compatibility: one linear Alembic head; fresh and existing databases can
   upgrade; existing auth, domain, monitoring and UPnP tests pass.
5. User experience: English and Chinese copy, meaningful loading/error/empty
   states, useful setup feedback, usable small screens, no false online claim.
6. Quality: full backend and frontend tests, Ruff, ESLint, TypeScript and the
   complete production build pass on the integrated source; all pre-commit hooks
   pass on an index containing code and its collaboration records.
7. Delivery: setup/environment examples and operations docs match code; commits
   are atomic and do not incorporate another stream's unfinished work.

## Evidence boundaries

Mocked tests, loopback native frp transfer, an active local child, external TCP
probes and successful XTCP traversal between separate networks are distinct
evidence. Local delivery can pass only the checks actually run. Real router
changes and cross-network traversal remain deployment acceptance items. The user
separately authorized temporary DNS records; both real service-layer and DDNS
integration evidence below use unique owned records and completed cleanup. They
do not establish public application reachability.

## Review record

Initial baseline: 239 backend tests passed and three access API tests failed due
to the shared test session lifecycle. All 26 frontend tests and ESLint passed.
The gateway owner also identified a production-build blocker in the existing
domain-record route: its synchronous `params` prop violates Next.js 16's page
contract. Those initial failures are historical: the access owner fixed session
ownership and delivered the shared promised-params correction atomically. The
current validation and ownership records below supersede the initial schedule.

## Integrated results — 2026-10-28 UTC

Validated final product source: `4efe286`, including all commits in the delivery
table below. Source hashes confirm only the two UPnP source/test files changed
after `2ef29ac`; backend implementation remains identical.
Latest command output, timestamps and exit codes are retained outside the checkout
under the Access evidence root in `final-acceptance-20261028/`.

| Check | Observed result | Evidence boundary |
| --- | --- | --- |
| Full backend with official frp 0.71.1 | 373 passed, no skips; latest all-files hooks 45.37 s | Includes four native P2P cases and the real subprocess public-relay backend-SIGKILL/same-state/same-port replacement regression |
| Frontend | 103 passed across 10 test files | Includes Access/UPnP rapid-close navigation, failure focus, pending requests, outer-menu exit and stale-error correction regression tests |
| Static and production checks | Ruff, ESLint, standalone TypeScript and default Next.js 16.1.6 Turbopack build passed; 11 pages generated | Complete integrated source, no webpack fallback |
| Fresh dependency installation | 369 passed, four optional native cases skipped; config parsing, password verification, TestClient, netifaces and pip check passed | New Python 3.13.5 venv without global packages; this host needed a process-local compatible SDK, documented in the dependency audit |
| Shared lifecycle/transport contracts | Four lifecycle and one transport-isolation tests included in the full suite | All owners unwind after partial startup/cleanup failure; public and private relay credentials/state remain distinct |
| Existing-user migration | Independent PM upgrade/downgrade/re-upgrade passed; fresh migration tests pass in the full suite | Disposable SQLite database with existing users; no operator database moved or migrated |
| Native public relay | Updated-guard smoke passed in `9fe7623`: TCP/UDP, reconnect, actual native-child SIGKILL/re-registration, owned cleanup | Local loopback official binaries, distinct from an Internet endpoint |
| Access UE/UI | Independent frozen `e3775d1` production browser recheck passed | EN/ZH × 390/1440; 48 native rapid groups, eight complete stale-error correction paths, 28 screenshots viewed; mock API |
| Other UE/UI | Independent overall UI sign-off passed: original four P2s plus both UPnP follow-ups closed; final UPnP `4efe286` passed 48 pending-request groups, 12 inline-error/retry groups and four ordinary-menu controls, with 25 screenshots viewed | EN/ZH × 390/1440, real production Next rendering with mock API; original rapid-close 48-group proof remains valid |
| All-files hooks | All passed on `4efe286`, UTC 17:50:13–17:51:09; native backend 373 and frontend 103 included | Actual `pre-commit run --all-files --verbose`; no skip environment or bypass |

The independent reviewer rebuilt the final UPnP production copy, verified
`/upnp` HTTP 200 and matching runtime/test/commit hashes, and stopped its owned
preview/Chrome processes. The final report and its log preserve the initial
findings, intermediate failed candidates and successful affected-path rechecks.
All local integration gates are closed. Every atomic code commit passed its
applicable normal hooks; the final documentation commit also runs normal hooks.

## Real DNS and DDNS results

The unchanged `AliyunDNSService` was independently exercised on
`pan-qa-gw-20261028163933-7fd3de`: absence, CNAME create, cloud/authoritative/public
recursive readback, and exact-owned-ID deletion all passed. That run made no
update call and is not the proof for DDNS IP changes.

The public-access owner used a different unique RR,
`pan-qa-ddns-20261028165501-cc7ba5`, through the original `DnsSync` and real SDK:

1. Cloud and both authorities proved absence before creation.
2. Create A `192.0.2.17`; cloud, both authoritative servers, Cloudflare and Google
   read the expected value. Repeating input caused no write and kept the ID.
3. Change A to `198.51.100.29`: one real `UpdateDomainRecord`, including RecordId,
   original RR, Type and Value, retained that ID. All four DNS servers and the
   cloud API read the changed value. Repeating input again caused no write.
4. Finally delete only that captured ID. Two cloud reads proved absence and both
   authoritative servers returned NXDOMAIN with AA. Add/Update/Delete counts
   were exactly 1/1/1; no recovery resource remains.

The update P1 is closed by `e2e4b22`, five official-SDK-request regressions and this
live update proof. See `agent_chats/20261028-165120-p1-ddns-rr.md` for provider
RequestIds, source/artifact hashes and the sanitized artifact directory. The
gateway owner's separate cloud evidence is preserved in
`agent_chats/20261028-163933-real-dns-acceptance.md`.

Credentials were read from the already available Aliyun CLI current AK profile
into one process; no profile, application configuration, password, existing DNS
record or deployment changed. The bounded Docker-location check found no local
PandaHome deployment source. No credentials, raw zone or raw record IDs were
persisted. Positive recursive caches may survive deletion until TTL; cleanup is
established at the provider and authorities, without claiming a global cache purge.

TEST-NET DNS values do not host an application. **External application access,
physical-router ingress and traversal between separate NATs are unverified and
not passed.** No applicable running PandaHome public application endpoint was
found in the established scope. These environment-dependent acceptance items
remain open in `tasks.md` and do not imply a missing implementation was accepted.

## Atomic delivery

| Commit | Scope |
| --- | --- |
| `2e440ad` / `9fe7623` | One shared guard for Access/P2P; real backend death, guard death and restart proof |
| `63c4b99` | Original UPnP feedback/focus correction; rapid-close follow-up is tracked separately |
| `47425d8` / `ffbeaa8` | P2P cancellation/error feedback and independent production UI evidence |
| `e2e4b22` | DDNS original RR, actual SDK request regression and live update/cleanup |
| `22872f7` | Document language synchronization and its test |
| `e3775d1` | Access rapid-close/Tab focus and stale-error typing correction, independently rechecked |
| `d7c682a` | Next.js promised domain-page parameters |
| `1d4b3d0` | Five shared lifecycle/transport isolation regressions |
| `6ddc0a1` | Login client EOF only |
| `2ef29ac` | Same-cwd bilingual setup, valid environment template, reproducible dependency install and test portability |
| `e8be058` | Original UPnP owner's minimal rapid-close fix and regression tests, reviewed and atomically delivered by Access |
| `4efe286` | Preserve user navigation when a pending UPnP menu finishes its exit animation; two failure regressions and an ordinary Escape control |

The final documentation commit includes this review, the independent UE/UI report
and log without replacing its historical evidence, both real-DNS records, and
the current task status. No shared-file commit is delegated back to the PM.

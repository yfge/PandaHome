## Summary

Integrate the retained GPUFree Git publication into PandaHome's administrator
configuration and original application lifecycle. Backend and UE/UI owners
implemented their assigned paths; the integration owner prepared the deployment,
field drivers and documentation and held the only staging/commit window.
PM coordinated and independently reviewed without coding, staging or committing.
Feature commit: `950d4412c0d24fd01aa33f9660d2a0f22b69ca30`.

## Changes

- `tasks.md`: record managed relay/profile/TLS/SSH delivery and the later real
  public-relay acceptance, while preserving the original field-run boundaries
  and open native P2P, company physical-WAN and mapping-drift follow-ups.
- `docs/public-access.md`: document administrator profile settings, native TLS
  trust, product-owned SSH lifecycle, controlled adoption/rollback and field
  verification with the honest external-verification state.
- `README.md` and `README.zh.md`: replace the pending/manual-environment-only
  setup text with the working administrator configuration flow.
- `agent_chats/20261029-043527-managed-relay-integration.md`: record integration
  ownership, source-bound deployment, actual gates, field evidence, incident
  boundaries and retained-resource delivery.
- Backend implementation paths remain recorded by
  `agent_chats/20261029-044233-managed-relay-profile.md`; frontend implementation
  paths by `agent_chats/20261029-044318-relay-settings-ui.md`. Those feature-time
  logs remain frozen; subsequent field acceptance is recorded here and in the
  private evidence manifests.

## Outcome

The retained `gpufree-code.lets-gpt.com:8081` entry now runs through the normal
PandaHome application. Its service targets `192.168.31.16:80` in explicit relay
mode. The cloud address is an existing relay, not a claim about the company's
physical public-WAN address. The original cloud frps service remains existing
infrastructure. Both old standalone local SSH/frpc launchd jobs were stopped
and disabled after exact PID/create-time/argv/executable and configuration checks;
original configuration bytes remain available for rollback.

The feature was committed with normal hooks before deployment. An exact source
archive was installed in the private `~/Library/Application Support/PandaHome/managed-access`
runtime, with a fresh virtual environment, private database/state, one API worker
and loopback API/web at 8033/3013. Migrations, bootstrap and API all used the same
deployed `source/api` working directory and configured database. The deployed
288 tracked-file hashes matched the committed source. No unrelated database or
shared Next build directory was used.

Through the real UI, the administrator saved the full profile and a disabled
service. This created no SSH/frpc child. Normal API restoration retained the
same database/profile and service identity. In the accepted second cutover,
PandaHome owned the full API → guard/watchdog → SSH/frpc parent chains.
Home 1.81 was only a read-only client: normal system DNS and FQDN requests returned
homepage/version/login/anonymous-user statuses 200/200/200/401 with the expected
GPUFree Git content. Each of three positive windows correlated a fresh anonymous
request nonce with the unchanged cloud frps process's incoming TCP four-tuple
and owned ESTABLISHED socket. UI pause removed the owned public listener and
made the home request fail; UI re-enable restored the business chain.

One controlled API `SIGKILL` removed the old API and all six transport/guard
identities. Launchd restored the same source/database/profile under API 63226,
with new SSH 63303 and frpc 63308 descendants; the home business/nonce proof passed
again. The product correctly remains `pending` / `relay_unverified` /
`external_verified=false` because no automatic external probe was configured.
Manual field acceptance is separate from that background state.

The final real-UI invalid-host request returned 422, and retrying the full original
profile with token omitted returned 200. Profile tuples and SSH/frpc PID,
create-time and executable identities were unchanged. The saved-token indication
persisted while the password input stayed empty. EN/ZH × 390/1440 checks passed.
The browser examiner reviewed 19 accepted PNGs, closed its owned Chrome and
descendants/CDP port and removed its isolated authentication profile. No shared
backend/UE log was appended during field work.

The final original provider record, including exact ID and creation/update
timestamps, matched the first snapshot. This stable provider evidence, the
reviewed original same-value DnsSync return path and application mutation logs
Add/Update/Delete 0/0/0 jointly support DNS no-write acceptance. The cloud frps
PID/start ticks, systemd state and all six owned configuration/binary hashes and
metadata matched the original snapshot. Both old local jobs remained disabled
and absent, while the new API/web, guarded native transports, private database,
profile, existing DNS/cloud frps and target Gitea were intentionally retained.
Resources are intentionally nonzero; temporary cutover watchdogs, observers and
the isolated browser are closed.

The private evidence root is `pandahome-takeover-20261029-043527Z` under the
integration owner's 2026-10-29 visualization directory. Original snapshots,
first-attempt candidates, failed proof and rollback evidence remain unchanged.
Second-attempt drivers and watchdog markers use separate directories. Key/token
values were never committed or printed. The existing bootstrap administrator's
unchanged login information was copied to the stable private runtime's
`admin-login.json` (0600, parent 0700); its original private artifact was retained.
No account reset or additional account was performed.

## Verification

- Exact owner manifests: backend 13/13 and frontend/log 11/11 SHA/byte checks
  matched before staging. PM independently reviewed both implementations.
- Normal feature commit hooks: passed, no skip or bypass.
- `PANDAHOME_FRP_BIN_DIR=<private-run>/native-bin pre-commit run --all-files --verbose`:
  actual exit 0; official native enabled, 428 API tests passed, 0 skipped
  (54.16 s), 121 web tests/11 files passed, Ruff/ESLint/all hooks passed.
- `npx tsc --noEmit`: actual exit 0. Normal default Next.js 16.1.6 Turbopack
  production build in the private runtime: actual exit 0.
- Fresh deployment dependency install:
  `"$RUNTIME/venv/bin/python" -m pip install -c "$RUN/environment-constraints.txt" -e "$RUNTIME/source/api[test]"`:
  actual exit 0. `$RUNTIME` is the managed runtime above; `$RUN` is the private
  evidence root. Exact expanded argv/cwd/exit and output hashes are in
  `preparation-command-events.jsonl`. No fallback or global dependency change.
- Same deployed API directory: `python -m alembic upgrade head`, original
  `bootstrap-admin` CLI entrypoint with password supplied in memory, and single
  worker `python -m uvicorn src.app.main:app --host 127.0.0.1 --port 8033 --workers 1`.
  Each preparation stage succeeded; no test-variable or injected-detector bypass.
- Native isolated TLS tests: trusted CA/server name accepted registration;
  wrong CA and wrong name rejected registration without fallback. These were
  isolated tests, not changes to the retained cloud certificate.
- Private `home-attempt2-initial.json`, `home-attempt2-reenabled.json` and
  `home-attempt2-crashrecovered.json`: each actual home/cloud-observer exit 0/0,
  four expected HTTP results and exact nonce/owned TCP-flow correlation passed.
- `home-attempt2-paused.json`: actual exit 0, no home HTTP response and no owned
  cloud 8081 listener. `attempt2/*-native-convergence.json` proves zero product
  children when paused and newly owned children when enabled.
- Independent backend final lifecycle review: PASS,
  `backend-implementation/final-lifecycle-independent-review.json`, SHA256
  `a217ef16cbb35ef9cfd75d4a310dc6a7224954bb618937ccb0d72348ee733d26`.
- Final UI report: PASS, `ui-final-report.md`, SHA256
  `fc3dc2d3d62d46024b310ee9836147deda62893bc7da020a4279c4cd6c9da84e`;
  final manifest SHA256
  `473eade021a58682a62ff704b0a1e62b80a80eefd2a5bb17b41c11c022f82768`.
  The integration owner independently verified 32/32 manifest files, including
  19 accepted PNGs. PM independently reviewed the report and relevant images.
- Original final read-only audit: actual exit 1/false due solely to the
  `launchctl print-disabled` format interpretation described below. Its frozen
  provider/cloud/source/profile/listener conditions were all true.
- Reviewed fixed-input local interpretation: actual exit 0, all 16 checks passed;
  `final-readonly-audit-reviewed-conclusion.json` retains the original false and
  references both immutable input hashes. No repeated site probe or resource
  mutation was performed to produce this conclusion.
- Final documentation uses the mandatory normal commit hooks. Exact invocation,
  actual result and final HEAD/clean/index/source-diff assertions are recorded in
  the private final delivery manifest; no hooks are bypassed.
- The five-path acceptance documentation commit `7ba7e29` passed normal hooks.
  A late PM consistency review found the duplicate Feature 07 public-relay
  checklist still described the old diagnostic-only state. A separate exact
  `tasks.md` plus this-log follow-up corrects that entry; the original commit and
  historical evidence remain intact. No product or runtime change is involved.

## Incident

The first cutover's four home business requests all succeeded, but its strict
proof remained false. The probe incorrectly required a fresh HTTPS IP-observation
result to equal the unrelated business connection's source. The home VPN split
routing produced observation 45.78.13.236 and actual owned business peer
123.113.237.250. `home-initial-managed.json` preserves `HTTP_positive=true` and
`peer_correlated=false`; it was not rewritten as a pass.

At 05:04:56 UTC the reviewed rollback completed: product API/guard/SSH/frpc
identities were gone and the original SSH/frpc jobs were restored only after
58356 was free. The first independent watchdog exited with `rolled-back`.
The API save itself returned 200; an additional manual check exceeded the
field driver's 25-second deadline and used the approved exact-process fallback.
Independent source/log review found no new deadlock: two original serialized
network-detection cycles took about 13.49 + 13.09 seconds. Request-to-cycle
attribution is supported by source/log ordering, not distributed tracing.
Subsequent UI checks used normal state convergence without stacking manual checks.

The second cutover used a newly reviewed anonymous nonce observer: a 20-second
read-only cloud AF_PACKET socket with a kernel IPv4/TCP destination-8081 filter,
ready handshake, exact nonce query/header matching and same owned TCP four-tuple.
It saved no raw payload, packet file or cookie. Its successful initial proof
released the separate 180-second rollback watchdog at 05:11:31 UTC. Later
pause/re-enable and crash windows ran after that watchdog release.

The second API-resume invocation returned exit 1 only while reading the newly
bootstrapped process's command line: macOS briefly returned `psutil.AccessDenied`.
A subsequent read-only check verified exact API argv/executable/cwd, disabled
row and zero children before any old owner was stopped. This exception was
retained in `attempt2/resume-followup-readonly.json`; the action was not repeated
and no process-ownership guard was weakened.

The original final audit expected `launchctl print-disabled` to spell disabled
as `=> true`; this macOS version reports `=> disabled` and `=> enabled`. The
original exit 1/false and raw output are preserved. PM reviewed a separate local
interpreter that locks both input SHA256 values, parses the exact four labels
and recomputes all 16 conditions. Its PASS is a derived interpretation, not a
rewritten original execution result. It did not access the cloud or change any
resource.

## Next steps

- Keep the managed deployment, unchanged original DNS/cloud frps and target
  Gitea. Preserve exact old standalone rollback bytes; keep both old jobs disabled.
- All implementation and field owners have released their work. Subsequent ACKs
  stay private; do not reopen frozen shared logs or repeat completed probes.
- Native P2P direct traversal, company physical-WAN/router ingress and the older
  unexplained 39→38 / UDP 32783 discrepancy remain open. No route, VPN, security
  group, firewall, router rule, unknown resource, Gitea data or home service was
  changed. The old 2026-10-28 relay diagnostics remain historical non-passes;
  the later managed public-relay business requirement is closed by this run.

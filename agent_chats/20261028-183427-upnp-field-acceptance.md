## Summary

Run `field-20261028-183427Z`: physical Huawei IGD ingress investigation and
original-project HTTP API compatibility verification. PM remains coordination /
read-only review; Access exclusively applies and commits shared changes.

The first strict-source field attempt remains failed historical evidence. No
final ingress acceptance is claimed. Real nonce transport was observed on a
private candidate; signed/shipped-source field acceptance awaits review and
integrated replay. The original and candidate HTTP API investigations are
separate directories and do not rewrite the earlier failed attempt.

## Changes

- `api/src/app/services/upnp_gateway.py`: private one-line SDK
  `UpnpFactory(..., non_strict=True)` compatibility setting for malformed router
  SOAP namespaces. All existing explicit target, timeout, collision and API
  validation contracts remain unchanged.
- `api/src/app/services/upnp.py`: same setting in the original default-service
  factory. Actual HTTP replay confirmed that this original path is affected too.
- `api/tests/test_upnp_gateway.py`: existing tracked file, real local-HTTP
  parser/factory regressions for explicit and legacy clients. Each receives the
  actual captured malformed-success response, normal SOAP714/718 faults, or non-XML data.
  Synthetic discovery/cache setup is confined to the unit legacy test; field API
  evidence uses the normal project lifespan without dependency overrides.
- `agent_chats/20261028-183427-upnp-field-acceptance.md`: domain-owner evidence and
  private four-path handoff. The original owner prepared this candidate privately; Access independently reviewed and applied these four exact paths for atomic shared delivery.

Private copy: `/var/folders/rc/ffg_cryd6jsbjc2srvhbqnc40000gn/T/pandahome-field-upnp-candidate-jzahg1jg`.
External artifacts: `/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a1831d-1a81-7ae2-aef0-34e6c0e417b7/field-20261028-183427Z/upnp`.
Original base: `d19968e596c1cee81736c1eae4760586baecdce3`.
The prior three-path candidate and report remain in `candidate-v1/`.

## Outcome

**Confirmed product compatibility defect; private correction validated through
both real project HTTP API paths. Final ingress signoff remains pending.**

Original full project app + normal real-device startup + real login:
explicit `/api/upnp/gateways/mappings/...` DELETE returns502; legacy
`/api/upnp/mappings/...` DELETE returns500. The physical router has actually
removed each rule, confirmed by independent new-session GetSpecific714 reads.
The raw Delete success body uses undeclared `u:` while declaring `u0:`. Neither
error is reinterpreted as original product success by the harness.

With the two-factory private correction, both actual HTTP DELETE endpoints
return200, and independent router reads confirm absence. This is a real local
HTTP control-plane test against the real physical router, not an external
application/API ingress claim. Access still owns external application + DNS +
project API integrated acceptance.

The earlier independent ECS -> Huawei public WAN -> Mac en0 data-plane probe
recorded TCP3/UDP3 matching nonces, 654 request bytes and1581 reply bytes. It used
the private explicit-client candidate; that observation is retained separately
and does not sign off the original product or prove multiple physical NATs.
The 100-second same-entry sharing window was published, but no Access-authored
same-entry proof has yet been linked by this owner.

## Verification

- Real gateway discovered by project SSDP bound to en0/LAN192.168.1.6:
  `http://192.168.1.1:5431/5431gatedesc.xml`. Router WAN is public and differs from
  the VPN HTTPS exit. Route-to-gateway is en0. No VPN, global route, firewall,
  business mapping or management setting was changed. Only one physical NAT
  layer is currently established.
- Existing user-owned ECS was verified through current Aliyun account metadata,
  trusted known-host SSH and existing key. Python route/public-egress facts and
  independent LAN peer addresses establish the external nonce sender. Existing
  CLI credentials were never exported; Docker/env preflight is recorded without
  env values. No DNS RR was created by this owner.
- The first attempt's unique TCP Add applied, then ownership-description
  assertion failed; UDP was never written. Its cleanup initially refused the
  untagged tuple. Recovery first proved origin by immediate absence, persisted
  prewrite journal, unique reserved tuple/IP/port/600s lease, then deleted only
  that rule. Parser failure was followed by independent714/complete enumeration.
  Original failed files remain intact with later recovery linked separately.
- **Description correction:** the first planned long description is50 bytes,
  not54 as an earlier narrative stated. The first attempt was not instrumented
  for wire capture; no reconstructed packet is presented as an original capture.
  A fresh original-API reproduction with the same50-byte shape stores actual
  Add/GetSpecific/GetGeneric/Delete wire and API returns BEFORE assertions:
  `attempt-03-api/original/router-wire.jsonl`, `readback-wire.jsonl` and
  `api-result.json`. Both GetSpecific and GetGeneric return an empty description:
  **cleared**, not a nonempty truncation or rewrite. The26-byte run-id/protocol
  description is retained. Requested/readback lease is600 seconds in all cases;
  no lease change or permanent rule was used. No global description limit is
  inferred from these two observed lengths.
- Private API command:
  `python3.13 /Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a1831d-1a81-7ae2-aef0-34e6c0e417b7/field-20261028-183427Z/upnp/field_api_check.py original`, then `candidate`.
  Each starts original `src.app.main:app`, normal lifespan and real UPNPService
  discovery, with an isolated temporary database/admin/JWT/state directory.
  `/api/auth/token` returns200; `server-runtime.json` records source paths/SHA and
  zero dependency overrides. No existing account/password or deployment is used
  or changed. Bearer tokens/passwords/keys are absent from evidence.
- Original API control results: Gateway DELETE502 and legacy DELETE500, each
  followed by actual router714; private candidate results: both HTTP200 and714.
  Candidate wire resides in `attempt-03-api/candidate/`. Full parsed Add and
  specific/generic readbacks are saved before any ownership assertion.
- Source/hash provenance is recorded per API process. The legacy service uses
  natural netifaces IPv4 gateway fallback to en0 despite a VPN default route;
  there is no route override, mocked requester, factory override or service stub
  in these two field API processes. The HTTP observation wrapper records the
  unmodified actual request/response and returns it unchanged.
- All temporary servers, isolated accounts/databases/state, mappings and bounded
  watchdogs are gone. Total run so far: Add7/Delete7 applied owned mappings,
  all600s lease. Only run-reserved TCP58471 and UDP58472 were used. Cleanup checks
  exact tuple and observed description, or preserved prewrite-absence + actual
  matching Add200 wire proof for the description-cleared diagnostic tuple; this
  is not a product-wide relaxation of mapping ownership.
- `attempt-03-api/final-cleanup.json`: both exact mapping keys return714, local
  binds succeed, both private API runtime directories are removed and watchdogs
  exited. All original39 rules are compared by stable fields including hashed
  descriptions, excluding lease countdown. Stable SHA256:
  `3a78461ab93d19a60d6e9e2a87fef0667e914527439708c9c44a1a2deb0b9c59`.
  Other-owner additions are allowed and are never deleted (currently0 extras).
- Private original-factory regression: **2 failed /4 control cases passed**.
  Private corrected focused command with explicit `PYTHONPATH=api`:
  `python3.13 -m pytest -q api/tests/test_upnp_gateway.py api/tests/test_upnp.py`:
  **54 passed**. Ruff on both services and the tracked test passed.
  Logs: `candidate-v2-baseline-tests.log`, `candidate-v2-focused-tests.log`,
  `candidate-v2-ruff.log`. Explicit PYTHONPATH prevents the machine editable
  install from selecting the shared checkout during private tests.
- Read-only patch application check passes. Full shared backend/frontend/build/
  hooks: Not run – Access owns those gates; this owner stages/commits nothing.
  Previously closed UI behavior and accepted UI source remain untouched.

## Next steps

Access: review and precisely apply the four-path private patch if accepted, run
required affected gates, and coordinate a fresh short same-entry app/API/DNS
window using the reserved owner ports. PM only reviews/coordinates and does not
implement or commit. This owner keeps all shared paths and index unchanged.

Final field signoff remains pending review/committed-source integration. A
second NAT boundary is now independently evidenced on the cloud VPC side by
private NIC/routing plus native STUN; an extra household router is not required.
Actual P2P direct data remains a separate unpassed check. The earlier missing
second-physical-router hypothesis is superseded by the current handoff. Router-specific long-description loss
must stay visible to mapping/controller owners; untagged existing rules may
never be adopted. No owned resource cleanup is outstanding.

Access application note: the double-factory fix was reviewed against actual original API DELETE failures and the independently checked SDK fault matrix. Native 42-character ownership and committed-source public application replay remain pending; this commit does not sign off ingress.

Access integration verification: 54 original-owner focused tests passed on the shared source; Access added the paired normal SOAP718 conflict cases, with both real SDK paths still rejecting the fault. The domain candidate code is unchanged beyond the two factory flags. Native 42-character ownership is explicitly pending a separate real API test; no short-label pass is promoted.

Shared application gate: `python -m pytest api/tests/test_upnp.py api/tests/test_upnp_gateway.py -q --disable-warnings` — 56 passed; Ruff — passed. Normal commit hooks are required; no hook is skipped.

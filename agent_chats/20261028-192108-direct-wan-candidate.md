## Summary

Apply the independently reviewed Access-owner fix for `field-20261028-183427Z`: when an already selected direct route has a global unicast IPv4 address from the mapping gateway, use that address for DDNS and the public endpoint instead of an HTTP observer's potentially different VPN egress. The Access owner reproduced the mismatch using the unchanged real isolated API before applying the candidate. No API detector was overridden.

## Changes

- `api/src/app/services/access/reconcile.py`: add a small standard-library IPv4 selector used only by the existing direct branch; prefer a global non-multicast gateway WAN, otherwise retain the observed-IP fallback.
- `api/tests/test_access_controller.py`: add six controller test functions (12 cases) checking DNS target, no-domain endpoint, external-probe target, WAN changes, fallback, unchanged auto mismatch/relay behavior and the existing observed-IP prepare requirement.
- `agent_chats/20261028-192108-direct-wan-candidate.md`: owner candidate provenance, isolated red/green validation and the field-evidence boundary.

## Outcome

The old implementation fails three new assertions: it publishes the observer address as a no-domain endpoint, passes that observer address to DDNS for a configured domain, and keeps reusing that address while the gateway WAN changes. The candidate passes all 12 new cases and 199 tests across six existing domain test files. Auto recommendation and mode selection, direct preparation prerequisites, mapping ownership/cleanup, relay routing and UI are unchanged.

The shared source now uses the reviewed candidate. Genuine API preflight `api-harness/20261028-192447Z-eac195/evidence.jsonl` records `upnp_available=true`, `observed_gateway_equal=false`, `public_ip_mismatch`, successful disabled CRUD and deletion/listener cleanup. No service was enabled and no DNS or router write occurred; this is reproduction and isolation evidence, not public ingress acceptance.

## Verification

- Source baseline: `d19968e596c1cee81736c1eae4760586baecdce3`; source/candidate SHA-256 values, command timestamps, exit codes and exact isolated snapshot path are in external `manifest.json`.
- Existing environment only: `/opt/homebrew/Caskroom/miniconda/base/bin/python`, Python 3.13.5; no package installation or environment mutation.
- Old source + new tests: `python -m pytest tests/test_access_controller.py -k "gateway_wan or observed_fallback or global_wan_mismatch or relay_keeps_relay_host or observed_evidence_requirement" -q --disable-warnings` — **3 failed, 9 passed, 35 deselected**; exit 1, expected red.
- Candidate + identical selected tests: same command — **12 passed, 35 deselected**; exit 0.
- Candidate domain suite: `python -m pytest tests/test_access_controller.py tests/test_access_api.py tests/test_access_dns.py tests/test_access_health.py tests/test_network_detection.py tests/test_managed_mappings.py -q --disable-warnings` — **199 passed**; exit 0.
- `python -m ruff check src/app/services/access/reconcile.py tests/test_access_controller.py` — **All checks passed**; exit 0.
- Tests use the existing controller fixture, in-memory SQLite and fake detector/mapping/DNS/probe/relay IO. Their synthetic addresses were not contacted and are not field observations. Probe results remain unverified (`None`), so the tests assert `external_verified=False`.
- Shared source hashes were re-read after validation and still match the frozen baseline. The old UI was not opened, modified or tested. Full repository hooks/build were not run for an unapplied external candidate.

## Next steps

- Access owner: validate the exact committed source through real API publication and independent external DNS/nonce requests after the UPnP owner closes default-path XML compatibility and native 42-character ownership checks.
- Keep actual router/WAN/STUN/VPN observations and synthetic controller regressions distinct. Do not mark public ingress, cross-NAT access, physical recovery or this field task passed based on these tests.
- Leave UPnP-owner TCP58471/UDP58472 and all unrelated router mappings under their owner's control; their first-attempt cleanup is independently verified in `upnp/recovery-cleanup.json`.

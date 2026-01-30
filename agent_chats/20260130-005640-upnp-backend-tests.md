## Summary

- Added backend pytest coverage for the UPnP API routes using a mocked `UPNPService` to exercise success and failure paths.

## Changes

- `api/tests/test_upnp.py`: Added a `StubUPNPService` fixture and tests for `/api/upnp/status`, `/api/upnp/mappings`, add mapping, delete mapping, and error→HTTP status mapping.
- `tasks.md`: Marked Feature 03 Step 3 as complete.

## Outcome

- UPnP API behavior is now covered by automated tests without requiring real router/UPnP devices during CI or local runs.

## Verification

- `pytest -q`
- `ruff check api`

## Next steps

- Add service-layer unit tests for `UPNPService` validation (ports/protocol/IP) by mocking WANIPConnection actions (optional, may require heavier stubs).
- Write `docs/upnp.md` troubleshooting guide and link it from README (Feature 03 Step 6).

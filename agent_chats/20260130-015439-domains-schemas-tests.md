## Summary

- Completed Feature 04 backend steps 1–3: introduced domain/record schemas, switched record creation to JSON bodies, improved Aliyun DNS error handling/logging, and added mocked pytest coverage for the domains API.

## Changes

- `api/src/app/schemas/domains.py`: added Pydantic request/response schemas for domains and DNS records (create/update/write response).
- `api/src/app/schemas/__init__.py`: created schemas package entrypoint.
- `api/src/app/routers/domains.py`: refactored to dependency-inject `AliyunDNSService`, accept JSON bodies for record creation/update, added update endpoint and a new delete path matching README (kept legacy delete path).
- `api/src/app/services/aliyun_dns.py`: added typed `AliyunDNSError`, friendlier error messages, structured logging, and record CRUD support (including update).
- `api/tests/test_domains.py`: added endpoint tests using a stub DNS service via `dependency_overrides` (success + error→HTTP mapping).
- `web/src/components/domain/record-list.tsx`: made record list parsing accept both the legacy Aliyun payload and the new list response.
- `tasks.md`: marked Feature 04 Steps 1–3 complete.

## Outcome

- Domain record create/update now use typed JSON request bodies, Aliyun failures surface as readable API errors, and the domains router has automated test coverage without real Aliyun credentials.

## Verification

- `pytest -q`
- `ruff check api`
- `npm run lint --prefix web`

## Next steps

- Implement Feature 04 Step 4: domain/record CRUD UI (dialogs + validation) leveraging the shared `apiClient` and toast notifications.
- Implement Feature 04 Step 6: write `docs/domains.md` for Aliyun setup (permissions, rate limits) and link from README.

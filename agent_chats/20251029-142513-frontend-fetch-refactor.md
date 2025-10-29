## Summary
- Refactored status, UPnP, and domain data fetching to use the shared API client and consistent state management.

## Changes
- Added `DataStateCard` and `AsyncState` helpers to standardize loading, error, and empty UI states (`web/src/components/common/data-state-card.tsx`, `web/src/lib/async-state.ts`).
- Enhanced `web/src/lib/api-client.ts` with envelope detection and error helpers used across the updated components.
- Migrated `DomainList`, `RecordList`, `UpnpMappingList`, and `ServerStatus` to the API client with polling and unified state rendering (`web/src/components/domain/domain-list.tsx`, `web/src/components/domain/record-list.tsx`, `web/src/components/upnp/mapping-list.tsx`, `web/src/components/server/status.tsx`).
- Added missing locale strings for new UI states and tightened typing in the language provider (`web/src/i18n/locales/en.json`, `web/src/i18n/locales/zh.json`, `web/src/components/providers/language-provider.tsx`).
- Marked Feature 01 Step 5 as complete in `tasks.md`.

## Outcome
- Frontend panels now share a single fetch utility, present consistent skeleton/error/empty treatments, and avoid duplicate state logic.

## Verification
- `npm run lint --prefix web`

## Next steps
- Proceed with Feature 01 Step 6 to align environment docs once backend/frontend env keys are final.

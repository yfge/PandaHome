## Summary

- Implemented UPnP port-mapping CRUD UI (add/edit/delete) with modal dialogs, optimistic list updates, and toast notifications.

## Changes

- `web/src/components/providers/toast-provider.tsx`: added a lightweight toast system (`ToastProvider`, `useToast`) to show success/error notifications.
- `web/src/app/layout.tsx`: mounted `ToastProvider` so toasts are available across the app.
- `web/src/components/upnp/mapping-form-dialog.tsx`: added modal form for creating/updating a port mapping (client-side validation + submit state).
- `web/src/components/upnp/mapping-delete-dialog.tsx`: added delete confirmation dialog for port mappings.
- `web/src/components/upnp/mapping-list.tsx`: added Add button, per-row edit/delete actions, optimistic updates, and toast feedback using `apiClient`.
- `web/src/i18n/locales/en.json`, `web/src/i18n/locales/zh.json`: added `upnp.form.*` and `upnp.toast.*` strings.
- `tasks.md`: marked Feature 03 Step 4–5 as complete.

## Outcome

- The `/upnp` page now supports mapping CRUD via dialogs and provides immediate UI feedback (optimistic list changes + toasts) while persisting changes through the backend API.

## Verification

- `pytest -q`
- `ruff check api`
- `npm run lint --prefix web`
- `pre-commit run --hook-stage pre-commit --files <changed files>`

## Next steps

- Implement Feature 03 Step 3: add backend pytest coverage for UPnP endpoints via mocked device/service layer.
- Implement Feature 03 Step 6: write `docs/upnp.md` (router prerequisites + troubleshooting) and link from README.

# Authentication Lifecycle

This document describes how PandaHome handles authentication end-to-end across the FastAPI backend and the Next.js frontend.

## Backend

- JWT secrets, algorithms, and token lifetime are configured via `api/.env` (`SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`).
- Alembic manages the `users` table (`api/alembic/versions/20251029_01_create_users_table.py`). The default `sqlite:///./app.db` is relative to the process working directory. With the backend virtual environment active, run migrations, bootstrap and the API from the same `api/` directory:

  ```bash
  cd api
  alembic upgrade head
  bootstrap-admin --username admin --password 'replace-with-your-password' --email admin@example.com
  uvicorn src.app.main:app --port 8003
  ```

- `/api/auth/token` issues bearer tokens for valid credentials; `/api/users/*` endpoints are guarded via role-based dependencies.
- These commands do not move or merge an existing database from another directory. Keep an existing configured database URL unchanged unless intentionally selecting another database.

## Frontend

- The login form posts credentials to `/api/auth/token`. On success, the bearer token is cached in `localStorage` and injected into subsequent API calls.
- `/access`, `/p2p`, `/status`, `/upnp`, and `/domains` pages are wrapped in a `Protected` gate that redirects unauthenticated visitors to `/login`.
- Any 401 response triggers automatic logout: the token is cleared and the user is redirected back to the login screen.

## Typical Flow

1. In the backend terminal, run the migration/bootstrap/API sequence above from `api/`.
2. In another terminal at the repository root, start the frontend with `npm run dev --prefix web`.
3. Open http://localhost:3000/login, sign in with the seeded credentials.
4. Navigate the protected sections; if the token expires or is revoked, the UI will route back to `/login`.

## Rotating Credentials

- To change an admin password, rerun `bootstrap-admin` with the same username and new password.
- For additional users, authenticate as admin and use the `/api/users` REST endpoints (UI coming soon) to manage accounts.

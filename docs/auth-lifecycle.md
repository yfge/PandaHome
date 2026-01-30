# Authentication Lifecycle

This document describes how PandaHome handles authentication end-to-end across the FastAPI backend and the Next.js frontend.

## Backend

- JWT secrets, algorithms, and token lifetime are configured via `api/.env` (`SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`).
- Alembic manages the `users` table (`api/alembic/versions/20251029_01_create_users_table.py`). Run migrations with `alembic upgrade head`.
- Use the packaged CLI to create or update an administrator:

  ```bash
  cd api
  bootstrap-admin --username admin --password changeme --email admin@example.com
  ```

- `/api/auth/token` issues bearer tokens for valid credentials; `/api/users/*` endpoints are guarded via role-based dependencies.

## Frontend

- The login form posts credentials to `/api/auth/token`. On success, the bearer token is cached in `localStorage` and injected into subsequent API calls.
- `/status`, `/upnp`, and `/domains` pages are wrapped in a `Protected` gate that redirects unauthenticated visitors to `/login`.
- Any 401 response triggers automatic logout: the token is cleared and the user is redirected back to the login screen.

## Typical Flow

1. Run migrations and seed an admin user (`bootstrap-admin`).
2. Start the backend (`uvicorn ... --port 8003`) and frontend (`npm run dev --prefix web`).
3. Open http://localhost:3000/login, sign in with the seeded credentials.
4. Navigate the protected sections; if the token expires or is revoked, the UI will route back to `/login`.

## Rotating Credentials

- To change an admin password, rerun `bootstrap-admin` with the same username and new password.
- For additional users, authenticate as admin and use the `/api/users` REST endpoints (UI coming soon) to manage accounts.

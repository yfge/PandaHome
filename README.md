# PandaHome

A lazy developer's solution for home server management, featuring dynamic DDNS (Aliyun DNS API) and automatic port mapping via UPnP.

## Features

- **Dynamic DDNS**: Automatically update DNS records using Aliyun DNS API, support for multiple domains, real-time public IP sync, and custom record types.
- **UPnP Port Mapping**: Automatically register port mappings to your router, support TCP/UDP, dynamic port management, and real-time status monitoring.
- **Web UI**: Modern, responsive, and supports both English and Chinese.
- **Multi-language**: Switch between English and Chinese easily.

## Tech Stack

- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS 4, shadcn/ui, next-intl
- **Backend**: FastAPI (Python 3.12+), SQLAlchemy, miniupnpc, Aliyun DNS SDK

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yfge/PandaHome.git
cd PandaHome
```

### 2. Install dependencies

```bash
# Backend (run from repository root)
uv pip install --system -e api
# or
pip install -e api

# Frontend
npm install --prefix web
```

### 3. Configure environment variables

```bash
cp api/.env.example api/.env
cp web/.env.local.example web/.env.local
```

Then edit the files to provide your secrets (see [Environment Variables](#environment-variables)).

### 4. Install developer tooling

```bash
# From repository root
pip install pre-commit
pre-commit install --install-hooks
```

### 5. Prepare the database

```bash
cd api
alembic upgrade head
bootstrap-admin --username admin --password changeme --email admin@example.com
```

### 6. Run the application

```bash
# Backend (port 8003 to match the web client default)
uvicorn src.app.main:app --reload --app-dir api/src --port 8003

# Frontend
npm run dev --prefix web
```

- Web UI: http://localhost:3000
- API Docs: http://localhost:8003/docs

## Development Workflow

- Log every code-producing session in `agent_chats/YYYYMMDD-HHMMSS-topic.md` following the template described in `agent_chats/README.md`.
- Run `pre-commit run --all-files` before opening a PR; hooks enforce Ruff lint/format on `api/` and `npm run lint` for the frontend (when dependencies are installed).
- See `agents.md` for the full engineering handbook covering repository layout, conventions, and incident process.

## Environment Variables

Backend (`api/.env`):

| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy database connection string. | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT signing key; replace in production. | `change-me` |
| `JWT_ALGORITHM` | JWT signing algorithm. | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes. | `30` |
| `AUTH_TOKEN_URL` | OAuth2 token endpoint path. | `/api/auth/token` |
| `AUTH_HASHING_SCHEMES` | Comma-separated Passlib hashing schemes. | `bcrypt` |
| `AUTH_HASHING_DEPRECATED` | Passlib deprecated hashing strategy. | `auto` |
| `ALIYUN_ACCESS_KEY_ID` | Aliyun access key ID. | _(required)_ |
| `ALIYUN_ACCESS_KEY_SECRET` | Aliyun access key secret. | _(required)_ |
| `ALIYUN_REGION_ID` | Aliyun region for DNS API. | `cn-hangzhou` |

Frontend (`web/.env.local`):

| Variable | Description | Default |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of the FastAPI backend. | `http://localhost:8003` |

## Authentication Overview

1. Seed an administrator with `bootstrap-admin --username admin --password changeme --email admin@example.com` (re-run to rotate credentials).
2. Start backend + frontend, then visit `http://localhost:3000/login` to sign in.
3. Successful login stores a bearer token locally; protected routes (`/status`, `/upnp`, `/domains`) require the token.
4. Expired or invalid tokens trigger automatic logout and redirect back to `/login`.

## API Endpoints

### UPnP
- `GET /api/upnp/mappings` - List all port mappings
- `POST /api/upnp/mappings` - Add a new port mapping
- `DELETE /api/upnp/mappings/{id}` - Remove a port mapping

### Domain Management
- `GET /api/domains/domains` - List all domains
- `POST /api/domains/domains` - Add a new domain
- `GET /api/domains/domains/{domain}/records` - List domain records
- `POST /api/domains/domains/{domain}/records` - Add a new record
- `PUT /api/domains/domains/{domain}/records/{record_id}` - Update a record
- `DELETE /api/domains/domains/{domain}/records/{record_id}` - Delete a record

## License

MIT

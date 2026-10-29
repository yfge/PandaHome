# PandaHome

A lazy developer's solution for home server management, featuring dynamic DDNS (Aliyun DNS API) and automatic port mapping via UPnP.

## Features

### Managed public services

Open **Public access** (`/access`) as an administrator to publish an existing LAN
service. Automatic mode detects public IPv4, upstream NAT, CGNAT or insufficient
evidence, then maintains either UPnP + optional Aliyun DDNS or a native frp relay.
Services are persisted and restored without keeping the browser open; mapping
leases, changed IPs, failed checks and relay exits are retried automatically.

Prepare the database as described in Quick Start before starting the API. For relay access,
install the official `frpc` binary and configure your reachable `frps` in
**Public access → Connection settings and help** (`/access/setup`). Administrators can save TLS trust and
an optional PandaHome-owned SSH control channel there. Settings are stored in a
private deployment profile; `RELAY_*` environment variables remain defaults.
Use one API worker per database/state directory. No public server is installed
or provisioned automatically.

The retained GPUFree Git entry is now managed by PandaHome, including its SSH
and frpc lifecycle. Its existing DNS record and cloud frps remain intact; follow
[the integration status](tasks.md#relay-integration-and-retained-service-takeover-2026-10-29)
and [the adoption procedure](docs/public-access.md#relay-profile-and-ssh-integration).

An accepted mapping or tunnel is shown as **awaiting external verification**.
Optional `ACCESS_PROBE_URL` integrates a remote Prometheus blackbox exporter for
TCP verification, and `ACCESS_ALERT_WEBHOOK` reports sustained failures/recovery.
UDP needs application-level external validation. See the complete
[setup and operations guide](docs/public-access.md).

- **Dynamic DDNS**: Automatically update DNS records using Aliyun DNS API, support for multiple domains, real-time public IP sync, and custom record types.
- **UPnP Port Mapping**: Automatically register port mappings to your router, support TCP/UDP, dynamic port management, and real-time status monitoring. Administrators can [select an upstream router and configure each NAT layer](docs/upnp-multiple-routers.md) through `/api/upnp/gateways` and its inspect/mapping endpoints.
- **Web UI**: Modern, responsive, and supports both English and Chinese.
- **Multi-language**: Switch between English and Chinese easily.

## Tech Stack

- **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS 4, shadcn/ui, next-intl
- **Backend**: FastAPI (Python 3.12+), SQLAlchemy, miniupnpc, Aliyun DNS SDK

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yfge/PandaHome.git
cd PandaHome
```

### 2. Install dependencies

Use Python 3.12+ and Node.js 22.x. Run these commands from the repository root:

```bash
# Backend, including dependencies for the required test hooks
python3 -m venv venv
source venv/bin/activate
python -m pip install -e "api[test]"

# Frontend
npm install --prefix web
```

If you use uv, replace the pip installation command with `uv pip install -e "api[test]"` in the activated environment.
For a macOS native dependency build failure, see the verified [SDK compatibility note](docs/backend-dependency-audit.md#macos-native-build-note).

### 3. Configure environment variables

```bash
cp api/.env.example api/.env
cp web/.env.local.example web/.env.local
```

Then edit the files to provide your secrets (see [Environment Variables](#environment-variables)).

### 4. Install developer tooling

```bash
# From repository root
python -m pip install pre-commit
pre-commit install --install-hooks
```

### 5. Prepare the database

The default `DATABASE_URL=sqlite:///./app.db` resolves relative to the current
working directory. Run migrations, administrator bootstrap and the API from the
same `api/` directory so they all use `api/app.db`. These commands do not move or
merge an existing database from another directory. Keep the virtual environment
activated in this terminal.

```bash
# From the repository root
cd api
alembic upgrade head
bootstrap-admin --username admin --password 'replace-with-your-password' --email admin@example.com
```

### 6. Run the application

In the same backend terminal, still inside `api/`:

```bash
# Backend (port 8003 to match the web client default)
uvicorn src.app.main:app --port 8003
```

Add `--reload` for development if needed. Open a second terminal at the repository
root for the frontend:

```bash
npm run dev --prefix web
```

- Web UI: http://localhost:3000
- API Docs: http://localhost:8003/docs

## Development Workflow

- Log every code-producing session in `agent_chats/YYYYMMDD-HHMMSS-topic.md` following the template described in `agent_chats/README.md`.
- Run tests from the repository root with the backend virtual environment active before opening a PR:
  - `python -m pytest -q api/tests`
  - `npm run test --prefix web`
- Run `pre-commit run --all-files` before opening a PR; hooks enforce Ruff lint/fixes on `api/`, backend tests, and frontend ESLint/tests when web dependencies are installed.
- See `AGENTS.md` for the full engineering handbook covering repository layout, conventions, and incident process.

## Environment Variables

Backend (`api/.env`):

| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy database connection string; relative SQLite paths use the process working directory. | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT signing key; replace in production. | `change-me` |
| `JWT_ALGORITHM` | JWT signing algorithm. | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes. | `30` |
| `AUTH_TOKEN_URL` | OAuth2 token endpoint path. | `/api/auth/token` |
| `AUTH_HASHING_SCHEMES` | JSON array of Passlib hashing schemes. | `["bcrypt"]` |
| `AUTH_HASHING_DEPRECATED` | Passlib deprecated hashing strategy. | `auto` |
| `ALIYUN_ACCESS_KEY_ID` | Aliyun access key ID; required for Aliyun DNS management. | _(unset)_ |
| `ALIYUN_ACCESS_KEY_SECRET` | Aliyun access key secret; required for Aliyun DNS management. | _(unset)_ |
| `ALIYUN_REGION_ID` | Aliyun region for DNS API. | `cn-hangzhou` |

Frontend (`web/.env.local`):

| Variable | Description | Default |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of the FastAPI backend. | `http://localhost:8003` |

## Authentication Overview

1. With the backend virtual environment active, run `bootstrap-admin --username admin --password 'replace-with-your-password' --email admin@example.com` from `api/` (re-run to rotate credentials).
2. Start backend + frontend, then visit `http://localhost:3000/login` to sign in.
3. Successful login stores a bearer token locally; protected routes (`/access`, `/p2p`, `/status`, `/upnp`, `/domains`) require the token.
4. Expired or invalid tokens trigger automatic logout and redirect back to `/login`.

See `docs/auth-lifecycle.md` for the full authentication lifecycle (env requirements, CLI bootstrap, login/logout flow).

## API Endpoints

### Status
- `GET /api/status` - System status snapshot
- `GET /health` - Health check

See `docs/monitoring.md` for data sources, update cadence, and troubleshooting tips.

### UPnP
- `GET /api/upnp/mappings` - List all port mappings
- `POST /api/upnp/mappings` - Add a new port mapping
- `DELETE /api/upnp/mappings/{external_port}?protocol=TCP|UDP` - Remove a port mapping (defaults to `TCP`)

See `docs/upnp.md` for router prerequisites, troubleshooting tips, and security notes.

### Domain Management
- `GET /api/domains/domains` - List all domains
- `GET /api/domains/domains/{domain}/records` - List domain records
- `POST /api/domains/domains/{domain}/records` - Add a new record
- `PUT /api/domains/domains/{domain}/records/{record_id}` - Update a record
- `DELETE /api/domains/domains/{domain}/records/{record_id}` - Delete a record

See `docs/domains.md` for Aliyun access key setup, required permissions, and rate limit troubleshooting.

### P2P access

Administrators can manage TCP services at `/p2p` using native frp XTCP hole
punching, with optional automatic STCP relay fallback. A reachable `frps` server
and `frpc` on both the home server and the visitor's computer are required.
Configure the independent `P2P_*` settings in `api/.env`, run `alembic upgrade head`
from `api/`, then download a visitor configuration from the page. The visitor
connects through a local `127.0.0.1` port; a running provider process does not
prove that a direct connection has succeeded.

The active-admin `/api/p2p` endpoints manage services, reconcile processes, rotate
keys and download credential-bearing visitor TOML. See [P2P setup and API](docs/p2p.md)
for server/client commands, TLS trust, firewall requirements and connection evidence.

## License

MIT

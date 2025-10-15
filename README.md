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
# Backend
cd api
pip install -e .

# Frontend
cd web
npm install
```

### 3. Configure environment variables

```bash
# Backend (.env)
ALIYUN_ACCESS_KEY_ID=your_access_key_id
ALIYUN_ACCESS_KEY_SECRET=your_access_key_secret
ALIYUN_REGION_ID=cn-hangzhou

# Frontend (.env.local)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 4. Install developer tooling

```bash
# From repository root
pip install pre-commit
pre-commit install --install-hooks
```

### 5. Run the application

```bash
# Backend
cd api
uvicorn src.app.main:app --reload --app-dir src

# Frontend
cd web
npm run dev
```

- Web UI: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Development Workflow

- Log every code-producing session in `agent_chats/YYYYMMDD-HHMMSS-topic.md` following the template described in `agent_chats/README.md`.
- Run `pre-commit run --all-files` before opening a PR; hooks enforce Ruff lint/format on `api/` and `npm run lint` for the frontend (when dependencies are installed).
- See `agents.md` for the full engineering handbook covering repository layout, conventions, and incident process.

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

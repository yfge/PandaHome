# PandaHome

A lazy developer's solution for home server management, featuring dynamic DDNS (Aliyun DNS API) and automatic port mapping via UPnP.

## Features

- **Dynamic DDNS**: Automatically update DNS records using Aliyun DNS API, support for multiple domains, real-time public IP sync, and custom record types.
- **UPnP Port Mapping**: Automatically register port mappings to your router, support TCP/UDP, dynamic port management, and real-time status monitoring.
- **Web UI**: Modern, responsive, and supports both English and Chinese.
- **Multi-language**: Switch between English and Chinese easily.

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Shadcn UI, next-intl
- **Backend**: FastAPI (Python 3.8+), UPnP library, Aliyun DNS API

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
pip install -r requirements.txt

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

### 4. Run the application

```bash
# Backend
cd api
uvicorn main:app --reload

# Frontend
cd web
npm run dev
```

- Web UI: http://localhost:3000
- API Docs: http://localhost:8000/docs

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
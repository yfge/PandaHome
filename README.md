# Self Host Server

A personal home server management service that provides dynamic DDNS and UPnP port mapping capabilities.

## Features

### Dynamic DDNS
- Automatic Aliyun DNS record updates
- Multi-domain management
- Real-time public IP synchronization
- Custom DNS record type support

### UPnP Port Mapping
- Automatic router port mapping registration
- TCP/UDP protocol support
- Dynamic port management
- Real-time status monitoring

## Tech Stack

### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- shadcn/ui
- next-intl (Internationalization)

### Backend
- FastAPI
- Python 3.8+
- Aliyun DNS API
- UPnP Protocol

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.8+
- Aliyun DNS API credentials
- UPnP-enabled router

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/self-host-server.git
cd self-host-server
```

2. Install backend dependencies:
```bash
cd api
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd web
npm install
```

4. Configure environment variables:

Create `.env` file in the `api` directory:
```env
ALIYUN_ACCESS_KEY_ID=your_access_key_id
ALIYUN_ACCESS_KEY_SECRET=your_access_key_secret
```

Create `.env.local` file in the `web` directory:
```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

### Running the Application

1. Start the backend server:
```bash
cd api
uvicorn app.main:app --reload
```

2. Start the frontend development server:
```bash
cd web
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage Guide

### Dynamic DDNS Configuration
1. Get API credentials from Aliyun Console
2. Configure API credentials in environment variables
3. Add domains to manage in the Web interface
4. System will automatically detect and update public IP

### UPnP Port Mapping
1. Ensure UPnP is enabled on your router
2. Add ports to map in the Web interface
3. System will automatically register port mappings with router
4. Monitor and manage port mapping status anytime

## API Documentation

API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs) when the backend server is running.

### Main Endpoints

#### DDNS
- `GET /api/domains/domains` - Get all domains
- `GET /api/domains/domains/{domain}/records` - Get domain DNS records
- `POST /api/domains/domains/{domain}/records` - Add new DNS record
- `DELETE /api/domains/records/{record_id}` - Delete DNS record

#### UPnP
- `GET /api/upnp/mappings` - Get all UPnP mappings
- `POST /api/upnp/mappings` - Add new UPnP mapping
- `PUT /api/upnp/mappings/{id}` - Update UPnP mapping
- `DELETE /api/upnp/mappings/{id}` - Delete UPnP mapping

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export const API_ENDPOINTS = {
  status: `${API_BASE}/api/status`,
  upnpMappings: `${API_BASE}/api/upnp/mappings`,
  domains: `${API_BASE}/api/domains/domains`
} as const;

export type APIEndpoints = typeof API_ENDPOINTS; 
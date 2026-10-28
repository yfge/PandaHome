import { API_ENDPOINTS } from "@/config/api";
import { apiClient, isApiEnvelope, type ApiEnvelope } from "@/lib/api-client";

export interface UpnpGateway {
  device_url: string;
  host: string;
  name: string;
  external_ip: string | null;
  address_scope: "public" | "private" | "shared" | "unknown";
  is_default: boolean;
  reachable: boolean;
  error: string | null;
}

export const GATEWAY_ENDPOINT = API_ENDPOINTS.upnpMappings.replace(/\/mappings$/, "/gateways");

export async function gatewayRequest<T>(endpoint: string, options?: Parameters<typeof apiClient>[1]): Promise<T> {
  const response = await apiClient<T | ApiEnvelope<T>>(endpoint, options);
  if (isApiEnvelope<T>(response)) {
    if (response.code !== 0 || response.data === undefined) {
      throw new Error(response.message || "UPnP gateway request failed");
    }
    return response.data;
  }
  return response;
}

export function mappingEndpoint(deviceUrl?: string, port?: number, protocol?: string): string {
  const endpoint = deviceUrl ? `${GATEWAY_ENDPOINT}/mappings` : API_ENDPOINTS.upnpMappings;
  const query = new URLSearchParams();
  if (deviceUrl) query.set("device_url", deviceUrl);
  if (protocol) query.set("protocol", protocol);
  return `${endpoint}${port === undefined ? "" : `/${port}`}${query.size ? `?${query}` : ""}`;
}

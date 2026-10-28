import { apiClient, isApiEnvelope, type ApiClientOptions, type ApiEnvelope } from "@/lib/api-client";

export const P2P_ENDPOINT = "/api/p2p";

export interface P2pServiceDraft {
  name: string;
  local_ip: string;
  local_port: number;
  enabled: boolean;
  fallback_enabled: boolean;
}

export interface P2pService extends P2pServiceDraft {
  id: string | number;
  status: "disabled" | "needs_setup" | "awaiting_connection" | "error";
  reason_code: string | null;
  connection_type: "unknown";
}

export interface P2pSnapshot {
  provider: {
    configured: boolean;
    ca_required?: boolean;
    available: boolean;
    running: boolean;
    reason_code: string | null;
    connection_type: "unknown";
  };
  services: P2pService[];
}

export function serviceEndpoint(id: P2pService["id"]) {
  return `${P2P_ENDPOINT}/services/${encodeURIComponent(String(id))}`;
}

export async function p2pRequest<T>(endpoint: string, options?: ApiClientOptions): Promise<T> {
  const response = await apiClient<T | ApiEnvelope<T>>(endpoint, options);
  if (isApiEnvelope<T>(response)) {
    if (response.code !== 0 || response.data === undefined) {
      throw new Error(response.message || "The private access request could not be completed.");
    }
    return response.data;
  }
  return response;
}

export async function downloadVisitor(id: P2pService["id"], port: number, signal: AbortSignal) {
  await downloadConfiguration(`${serviceEndpoint(id)}/visitor?bind_port=${port}`, "visitor.toml", signal);
}

export async function downloadConfiguration(endpoint: string, filename: string, signal: AbortSignal) {
  const content = await apiClient<string>(endpoint, {
    parseAs: "text", cache: "no-store", signal,
  });
  if (signal.aborted) return;
  const url = URL.createObjectURL(new Blob([content], { type: "application/toml" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  const revoke = URL.revokeObjectURL.bind(URL);
  window.setTimeout(() => revoke(url), 1000);
}

import { API_ENDPOINTS } from "@/config/api";
import { apiClient, isApiEnvelope, type ApiClientOptions } from "@/lib/api-client";

export async function accessRequest<T>(path: string, options?: ApiClientOptions): Promise<T> {
  const response = await apiClient<T>(`${API_ENDPOINTS.access}${path}`, options);
  if (isApiEnvelope<T>(response)) {
    if (response.code !== 0 || response.data === undefined) {
      throw new Error(response.message || "The public access request could not be completed.");
    }
    return response.data;
  }
  return response;
}

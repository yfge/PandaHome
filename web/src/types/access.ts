export type AccessMode = "auto" | "direct" | "relay";

export interface NetworkReport {
  topology: "public_ipv4" | "upstream_nat" | "cgnat" | "unknown";
  recommended_mode: "direct" | "relay" | "unknown";
  observed_public_ip: string | null;
  gateway_external_ip: string | null;
  upnp_available: boolean;
  checked_at: string;
  reason_code: string;
}

export interface ServiceDraft {
  name: string;
  local_ip: string;
  local_port: number;
  public_port: number;
  protocol: "TCP" | "UDP";
  mode: AccessMode;
  domain: string;
  rr: string;
  enabled: boolean;
  lease_duration: number;
}

export interface PublishedService extends ServiceDraft {
  id: number;
  status: "pending" | "healthy" | "degraded" | "error" | "needs_setup" | "disabled";
  active_mode: "direct" | "relay" | null;
  public_endpoint: string | null;
  dns_status: string;
  reason_code: string | null;
  last_error: string | null;
  last_checked: string | null;
  external_verified: boolean;
  failure_count: number;
}

export interface AccessState {
  network: NetworkReport | null;
  relay: {
    configured: boolean;
    available: boolean;
    running: boolean;
    public_host: string | null;
    reason_code: string | null;
  };
  services: PublishedService[];
  poll_interval_seconds: number;
}

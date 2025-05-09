export interface UpnpMapping {
  description: string;
  internal_ip: string;
  internal_port: number;
  external_port: number;
  protocol: 'TCP' | 'UDP';
  enabled: boolean;
  lease_duration: number;
} 
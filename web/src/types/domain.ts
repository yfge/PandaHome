export interface Domain {
  domain: string;
  id: string;
  status: string;
}

export interface DomainRecord {
  Status: string;
  RR: string;
  Line: string;
  Locked: boolean;
  Type: string;
  DomainName: string;
  Value: string;
  RecordId: string;
  TTL: number;
  CreateTimestamp: number;
  UpdateTimestamp?: number;
  Priority?: number;
  Weight?: number;
}

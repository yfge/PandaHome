# Aliyun DNS Domain Guide

This guide explains what PandaHome needs to talk to **Aliyun Cloud DNS (AliDNS)** and how to troubleshoot common errors when listing domains and managing DNS records.

## Prerequisites

- Your domain must already be managed in **Aliyun Cloud DNS** (i.e. added in the Aliyun console).
- Create an **AccessKey** (recommended: RAM user + least-privilege policy).
- Ensure the AccessKey has permission to call AliDNS APIs.

## Required Environment Variables

Backend (`api/.env`):

- `ALIYUN_ACCESS_KEY_ID`
- `ALIYUN_ACCESS_KEY_SECRET`
- `ALIYUN_REGION_ID` (default: `cn-hangzhou`)

## Minimal AliDNS Permissions

PandaHome uses AliDNS APIs to:

- list domains
- list records for a domain
- add/update/delete records

At minimum, the AccessKey should be allowed to call:

- `alidns:DescribeDomains`
- `alidns:DescribeDomainRecords`
- `alidns:AddDomainRecord`
- `alidns:UpdateDomainRecord`
- `alidns:DeleteDomainRecord`

Grant broader permissions only if you need additional operations.

## How PandaHome Manages Records

- The domains page reads your domain list from AliDNS.
- The records page lets you manage record fields such as:
  - `RR` (host record), e.g. `www`
  - `Type`, e.g. `A`, `AAAA`, `CNAME`, `TXT`
  - `Value`, e.g. `1.2.3.4`
  - `TTL` (seconds)
  - `Line` (e.g. `default`)
  - `Priority` (for record types that support it)

## API Endpoints

- `GET /api/domains/domains` — list domains
- `GET /api/domains/domains/{domain}/records` — list records
- `POST /api/domains/domains/{domain}/records` — add record
- `PUT /api/domains/domains/{domain}/records/{record_id}` — update record
- `DELETE /api/domains/domains/{domain}/records/{record_id}` — delete record

## Common Errors & Troubleshooting

### 502 “Aliyun credentials are invalid or do not have DNS permissions.”

Checklist:

- Confirm `ALIYUN_ACCESS_KEY_ID` / `ALIYUN_ACCESS_KEY_SECRET` are correct.
- Ensure the AccessKey has AliDNS permissions (see the minimal list above).

### 502 “Aliyun DNS API rate limit reached.”

AliDNS may throttle requests when the UI refreshes too frequently or when multiple clients are active.

Mitigations:

- Reduce page refresh frequency.
- Avoid repeatedly opening the records page in multiple tabs.
- Retry after a short delay.

### 502 “Requested domain/record was not found in Aliyun DNS.”

- Confirm the domain exists in Aliyun Cloud DNS and is spelled correctly.
- If a record was deleted elsewhere, refresh the records list and retry.

# UPnP Port Mapping Guide

This guide explains how PandaHome manages UPnP port mappings (NAT port forwarding) and how to troubleshoot common issues.

## Prerequisites

- Your router must support **UPnP IGD** (Internet Gateway Device) and have UPnP enabled.
- PandaHome and the router must be on the **same LAN**.
- Avoid **double NAT** (e.g., ISP modem/router + your own router) whenever possible.
- If your ISP uses **CGNAT**, port forwarding may not work even if UPnP succeeds locally.

## How PandaHome Uses UPnP

- On API startup, PandaHome discovers UPnP devices via SSDP and looks for an IGD (WANIPConnection service).
- The mappings list is cached for a short TTL; add/delete operations refresh the cache.
- The delete endpoint requires both:
  - `external_port` (path parameter)
  - `protocol` (query parameter, defaults to `TCP`)

## API Endpoints

- `GET /api/upnp/status` — discovery status and gateway info
- `GET /api/upnp/mappings` — list port mappings (may fail on routers that do not expose mapping enumeration)
- `POST /api/upnp/mappings` — add mapping
- `DELETE /api/upnp/mappings/{external_port}?protocol=TCP|UDP` — delete mapping

## Typical Workflow

1. Enable UPnP on your router.
2. Start the backend and open the web UI.
3. Go to the UPnP page and add a mapping:
   - Internal IP: the LAN IP of the service host (for example: `192.168.1.10`)
   - Internal port: the service port (for example: `80`)
   - External port: the internet-facing port (for example: `8080`)
   - Protocol: `TCP` or `UDP`
4. Verify externally:
   - Prefer verifying from an external network (mobile hotspot) or an online port check tool.
   - Some routers will show the new mapping immediately in their admin UI.

## Common Errors & Troubleshooting

### 503 “UPnP service unavailable”

Usually means discovery did not find an IGD device.

Checklist:
- Confirm UPnP is enabled in your router settings.
- Ensure the host running PandaHome is on the correct LAN/VLAN.
- Check local firewall rules (SSDP uses UDP port `1900`).
- If you have multiple network interfaces (Wi-Fi + Ethernet, VPN, Docker bridges), try disabling the unused ones and restart the API.
- Check backend logs under `logs/` for discovery details.

### 409 “Mapping already exists”

- A mapping for the same `{protocol, external_port}` already exists on the router.
- Delete the existing mapping first (or choose a different external port).

### 404 “Mapping not found”

- The mapping might have been removed on the router side, or the wrong protocol was used.
- Retrying a fresh list (`GET /api/upnp/mappings`) can help confirm the current router state (when supported).

### Listing returns empty or fails, but add/delete works

Some routers do not support enumerating mappings via `GetGenericPortMappingEntry`, or they restrict it.

Workarounds:
- Use your router admin UI to confirm the mapping.
- Rely on external reachability checks instead of the list endpoint.

## Security Notes

- UPnP can expose internal services to the internet. Only open ports you need.
- Prefer strong authentication on the exposed service, and keep systems updated.
- If you don’t trust UPnP, disable it and configure port forwarding manually.

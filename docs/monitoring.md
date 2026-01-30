# System Status & Monitoring Guide

This guide describes the data returned by PandaHome’s status endpoints and how the web dashboard refreshes the metrics.

## Endpoints

- `GET /api/status` — returns a snapshot of CPU/memory/disk usage, uptime, and a small set of service states.
- `GET /health` — lightweight health check with process uptime.

## Data Sources

PandaHome uses `psutil` to collect host metrics:

- CPU usage percentage (short sampling window)
- logical CPU core count
- memory totals (bytes)
- disk totals for the `/` filesystem (bytes)
- system uptime derived from OS boot time

Service states are derived from in-process state (e.g. UPnP initialization) or configuration presence (e.g. Aliyun credentials).

## Update Cadence & Caching

- The web UI polls `GET /api/status` on an interval (configurable from the status page).
- The backend caches the latest computed snapshot for a short TTL (defaults to 5 seconds) to avoid expensive repeated sampling.

## Troubleshooting

### 500 when calling `/api/status`

- Ensure backend dependencies are installed (including `psutil`).
- Check backend logs under `logs/` for the exception detail.
- If running inside a restricted container, confirm the process can read system metrics.

### Metrics look incorrect

- CPU usage is sampled over a short window; spikes may appear as you refresh.
- Disk statistics are based on the `/` filesystem; if your data lives on another mount, the numbers may differ from expectations.

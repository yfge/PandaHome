# UPnP with multiple routers

PandaHome can manage a reachable upstream Internet Gateway Device (IGD) without
changing its default-router service. An administrator chooses a router on the
UPnP page, or enters its complete UPnP device description XML URL. Each mapping
request carries that URL, so concurrent browsers can manage different routers.
An unreachable or unsupported target returns an error; it never falls back to
the default router. Manual inspection works even when local discovery failed.

## Finding and selecting an upstream router

1. Sign in as an active administrator and open **Port Mapping**.
2. Click **Discover routers** to run local SSDP discovery. Existing startup
   discovery results are shown on initial load. Discovery does not create rules.
3. Choose the intended router, checking its device address and WAN address.
4. If an upstream router is absent, enter its known device description URL and
   click **Check and select**. For example,
   `http://192.168.1.1:5000/rootDesc.xml` is an example only: ports and paths vary
   by firmware. Obtain the real URL from its SSDP `LOCATION` advertisement,
   firmware documentation or a discovery tool on its LAN. Its login page and
   public IP alone are insufficient.

Local SSDP multicast normally does not traverse a nested home NAT. A known URL
bypasses discovery, but not routing, firewalls or the router's UPnP access policy.
PandaHome must reach the advertised description, service descriptions and SOAP
control endpoint. This implementation supports WANIPConnection v1/v2 and
WANPPPConnection v1. It does not enable UPnP on a router remotely.

The selection lives in the current page only. Reopening the page uses the legacy
default router until another target is explicitly selected. It does not change
the default IGD used by monitoring or managed public-access reconciliation.

These are administrator-operated manual controls. They do not acquire persistent
ownership, reconcile rules in the background or clean up other services' rules.
Creation rejects occupied port/protocol pairs; deletion explicitly removes the
chosen rule on the chosen router. Managed public-access mappings retain the
Access controller's separate ownership and renewal contract. Another client can
still race between a collision query and its subsequent SOAP write.

## Configuring two NAT layers

For this example:

```text
Internet -> router A (public WAN, LAN 192.168.1.1)
         -> router B (WAN 192.168.1.2, LAN 192.168.2.1)
         -> server   (LAN 192.168.2.10, TCP service 80)
```

Configure the inner layer first, then the outer layer:

| Selected router | External port | Internal address | Internal port | Protocol |
| --- | --- | --- | --- | --- |
| B | 8080 | 192.168.2.10 | 80 | TCP |
| A | 8080 | 192.168.1.2 | 8080 | TCP |

For A, use **B's WAN address**, not the server address behind B. Reserve the WAN
and server LAN addresses in DHCP where appropriate. For more NAT layers, repeat
this pattern. Remove the outer mapping first when dismantling the chain. These
are independent operations, not an atomic chain transaction or automatic topology
discovery. Bridge/AP devices do not add a NAT mapping layer.

A private WAN address means another NAT remains upstream. `100.64.0.0/10` is
classified separately as shared address space; it does not prove who owns that
NAT. A globally routable WAN address is only a candidate public endpoint, not
proof that inbound traffic reaches the service. Test from a separate external
network. Ordinary UPnP cannot configure an inaccessible ISP CGNAT; the operator
must provide an appropriate upstream mapping mechanism or another access method.

## API

All new routes require a bearer token for an **active administrator**. Existing
`/api/upnp/status` and `/api/upnp/mappings` routes and their payloads are unchanged.

| Method | Path | Input |
| --- | --- | --- |
| GET | `/api/upnp/gateways` | Optional `refresh=true` for a new local search |
| POST | `/api/upnp/gateways/inspect` | JSON `{"device_url":"http://router:port/device.xml"}` |
| GET | `/api/upnp/gateways/mappings` | Required query `device_url` |
| POST | `/api/upnp/gateways/mappings` | Required query `device_url` and mapping JSON |
| DELETE | `/api/upnp/gateways/mappings/{external_port}` | Required query `device_url`; `protocol=TCP` or `UDP` |

Mapping JSON contains `external_port`, `internal_port`, `protocol`, an explicit
IPv4 `local_ip`, and optional `description`, `lease_duration` (0–4294967295 seconds;
zero means permanent) and `enabled` (must be true). URL-encode the entire
`device_url` query value,
including its own query parameters. Device URLs accept HTTP/HTTPS and reject
embedded credentials and fragments. No credentials or new environment settings
are required by this feature.

The list response reports `enumeration_supported` and `complete`. Unsupported
enumeration is shown explicitly in the UI rather than presented as an empty
router. Add/delete do not require enumeration. Adding checks the exact
port/protocol with `GetSpecificPortMappingEntry`; an existing rule returns 409,
and an unsupported/failed collision check fails without writing. Deleting an
absent rule returns 404. A transport failure returns 502; a bounded operation
timeout returns 504. After a write timeout, verify the router before retrying,
because a lost response does not prove the rule was unchanged.

Inspection and listing do not create rules. Clients and caches are scoped to a
single request, with five-second individual HTTP timeouts and a twenty-second
operation deadline. SSDP searches use a three-second response window and a
five-second total deadline, followed by inspection of at most sixteen devices;
therefore discovery plus inspection has a maximum twenty-five-second budget.
Mapping enumeration is capped at 256 entries. No real router changes are needed
for the local tests.

## References

- [UPnP device architecture](https://upnp.org/specs/arch/UPnP-arch-DeviceArchitecture-v2.0.pdf)
- [UPnP WANIPConnection service](https://upnp.org/specs/gw/UPnP-gw-WANIPConnection-v1-Service.pdf)
- [IGD-PCP interworking, RFC 6970](https://www.rfc-editor.org/rfc/rfc6970.html)

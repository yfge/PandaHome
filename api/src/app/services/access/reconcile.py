"""One service's desired route, evidence and transition notifications."""

import asyncio
import time
from datetime import datetime, timezone
from ipaddress import IPv4Address

from ...schemas.access import ServiceConfig
from ..relay import RelayMapping
from .mappings import ManagedMappings, MappingConflict
from .store import save_runtime


class ServiceReconciler:
    def __init__(self, *, mappings, relay, dns, health, alert_threshold: int = 3):
        self.mappings, self.relay, self.dns, self.health = mappings, relay, dns, health
        self.alert_threshold = alert_threshold

    async def cleanup(self, db, row) -> None:
        spec = (row.runtime or {}).get("mapping")
        if spec:
            await asyncio.wait_for(self.mappings.remove(spec), timeout=10)
            save_runtime(db, row, mapping=None)

    def mode(self, row, network) -> str | None:
        if row.mode != "auto":
            return row.mode
        fallback = (row.runtime or {}).get("fallback_until", 0) > time.time()
        if network and network.recommended_mode == "direct" and not fallback:
            return "direct"
        return "relay" if self.relay.status()["configured"] else None

    async def prepare(self, db, row, network) -> str | None:
        mode = self.mode(row, network) if row.enabled else None
        spec = (row.runtime or {}).get("mapping")
        changed = spec and (
            mode != "direct"
            or spec["external_port"] != row.public_port
            or spec["internal_port"] != row.local_port
            or spec["local_ip"] != row.local_ip
            or spec["protocol"] != row.protocol
        )
        if changed:
            try:
                await self.cleanup(db, row)
            except Exception:
                # Retain owned cleanup intent while a working outbound relay
                # restores availability when router control is unreachable.
                if mode != "relay":
                    raise
        if not row.enabled:
            save_runtime(
                db,
                row,
                status="disabled",
                reason_code="disabled",
                active_mode=None,
                public_endpoint=None,
                external_verified=False,
                failure_count=0,
            )
            return None
        if mode is None:
            save_runtime(db, row, active_mode=None, public_endpoint=None, external_verified=False)
            reason = "relay_not_configured" if network and network.recommended_mode == "relay" else "network_unknown"
            await self.finish(db, row, "needs_setup", reason, None)
            return None
        save_runtime(db, row, active_mode=mode, external_verified=False, public_endpoint=None)
        if mode == "direct":
            if not network or not network.upnp_available or not network.observed_public_ip:
                await self.finish(db, row, "needs_setup", "direct_unavailable", None)
                return None
            try:
                # Persist ownership before sending: the router may accept a write
                # even when its response is lost. Cleanup always rechecks ownership.
                save_runtime(db, row, mapping=ManagedMappings.spec(row))
                spec = await asyncio.wait_for(self.mappings.ensure(row), timeout=10)
            except MappingConflict:
                await self.finish(db, row, "error", "mapping_conflict", None)
                return None
            except Exception:
                if row.mode == "auto" and self.relay.status()["configured"]:
                    try:
                        await self.cleanup(db, row)
                    except Exception:
                        pass  # The persisted spec is retried on the next cycle.
                    save_runtime(db, row, fallback_until=time.time() + 600, active_mode="relay")
                    return "relay"
                await self.finish(db, row, "error", "mapping_failed", None)
                return None
            save_runtime(db, row, mapping=spec)
        return mode

    @staticmethod
    def relay_mapping(row) -> RelayMapping:
        return RelayMapping(row.id, row.local_ip, row.local_port, row.public_port, row.protocol)

    @staticmethod
    def _direct_host(network) -> str | None:
        try:
            gateway = IPv4Address(network.gateway_external_ip or "")
        except ValueError:
            return network.observed_public_ip
        if gateway.is_global and not gateway.is_multicast:
            return str(gateway)
        return network.observed_public_ip

    async def check(self, db, row, network, *, relay_ready: bool = False) -> None:
        mode = (row.runtime or {}).get("active_mode")
        if mode == "relay":
            state = self.relay.status()
            if not state["running"]:
                await self.finish(db, row, "needs_setup", state["reason_code"] or "relay_process_exited", None)
                return
            if not relay_ready:
                await self.finish(db, row, "degraded", "relay_unregistered", None)
                return
            host = state["public_host"]
        else:
            host = self._direct_host(network)
        try:
            dns_status = await self.dns.sync(row, host)
        except Exception:
            save_runtime(db, row, dns_status="error")
            await self.finish(db, row, "error", "dns_failed", None)
            return
        endpoint_host = ServiceConfig.model_validate(row, from_attributes=True).hostname if row.domain else host
        save_runtime(db, row, dns_status=dns_status, public_endpoint=f"{endpoint_host}:{row.public_port}")
        if await self.health.local(row) is False:
            await self.finish(db, row, "error", "local_unreachable", False)
            return
        external = await self.health.external(endpoint_host, row.public_port, row.protocol)
        if external is False:
            if (
                row.mode == "auto"
                and mode == "direct"
                and self.relay.status()["configured"]
                and (row.runtime or {}).get("failure_count", 0) >= 2
            ):
                save_runtime(db, row, fallback_until=time.time() + 600)
            await self.finish(db, row, "degraded", "probe_failed", False)
        elif external is True:
            await self.finish(db, row, "healthy", "ready", True)
        else:
            await self.finish(
                db, row, "pending", "inbound_unverified" if mode == "direct" else "relay_unverified", None
            )

    async def finish(self, db, row, status: str, reason: str, verified: bool | None) -> None:
        previous = row.runtime or {}
        failed = status in {"error", "degraded", "needs_setup"}
        failures = previous.get("failure_count", 0) + 1 if failed else 0
        notified = previous.get("alert_failed", False)
        save_runtime(
            db,
            row,
            status=status,
            reason_code=reason,
            external_verified=verified is True,
            last_checked=datetime.now(timezone.utc).isoformat(),
            failure_count=failures,
            last_error=None,
        )
        event = None
        if failures >= self.alert_threshold and not notified:
            event = "failure"
        elif not failed and verified is True and notified:
            event = "recovery"
        if event and await self.health.notify(service_id=row.id, name=row.name, event=event, reason=reason):
            save_runtime(db, row, alert_failed=event == "failure")

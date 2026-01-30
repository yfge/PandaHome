from __future__ import annotations

import time

import psutil

from ..config import settings
from ..schemas.status import CpuStatus, DiskStatus, MemoryStatus, ServerStatus, ServiceState, ServiceStatus
from .logger import logger
from .upnp import UPNPService


class StatusService:
    def __init__(self, *, upnp_service: UPNPService | None = None, cache_ttl_seconds: float = 5.0) -> None:
        self._upnp_service = upnp_service
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache: ServerStatus | None = None
        self._cache_time: float = 0.0

        # Prime CPU percent sampling so the first request does not always return 0.
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            logger.debug("StatusService: unable to prime psutil cpu_percent")

    def get_status(self) -> ServerStatus:
        now = time.monotonic()
        if self._cache is not None and now - self._cache_time < self._cache_ttl_seconds:
            return self._cache

        status = self._collect()
        self._cache = status
        self._cache_time = now
        return status

    def _collect(self) -> ServerStatus:
        timestamp = int(time.time())
        uptime = self._get_uptime_seconds(timestamp)

        cpu_usage = float(psutil.cpu_percent(interval=0.1))
        cores = int(psutil.cpu_count(logical=True) or 1)

        virtual_mem = psutil.virtual_memory()
        memory = MemoryStatus(
            total=int(virtual_mem.total),
            used=int(virtual_mem.total - virtual_mem.available),
            free=int(virtual_mem.available),
        )

        disk_usage = psutil.disk_usage("/")
        disk = DiskStatus(
            total=int(disk_usage.total),
            used=int(disk_usage.used),
            free=int(disk_usage.free),
        )

        services = self._collect_services()

        return ServerStatus(
            cpu=CpuStatus(usage=cpu_usage, cores=cores),
            memory=memory,
            disk=disk,
            uptime=uptime,
            timestamp=timestamp,
            services=services,
        )

    def _get_uptime_seconds(self, timestamp: int) -> int:
        try:
            boot_time = int(psutil.boot_time())
        except Exception:
            return 0
        return max(0, timestamp - boot_time)

    def _collect_services(self) -> list[ServiceStatus]:
        services: list[ServiceStatus] = [ServiceStatus(name="api", status="running")]

        if settings.ALIYUN_ACCESS_KEY_ID and settings.ALIYUN_ACCESS_KEY_SECRET:
            services.append(ServiceStatus(name="aliyun-dns", status="running"))
        else:
            services.append(ServiceStatus(name="aliyun-dns", status="stopped"))

        services.append(ServiceStatus(name="upnp", status=self._upnp_status()))
        return services

    def _upnp_status(self) -> ServiceState:
        upnp_service = self._upnp_service
        if upnp_service is None:
            return "stopped"

        initialized = getattr(upnp_service, "initialized", False)
        if initialized:
            return "running"

        error_message = getattr(upnp_service, "error_message", "")
        if error_message:
            return "error"

        return "stopped"

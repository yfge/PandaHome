"""One cancellable reconciliation loop per backend process."""

import asyncio
from contextlib import suppress
from datetime import datetime, timezone

from ...config import settings
from ...database.database import SessionLocal
from ...models.published_service import PublishedService
from ..logger import logger
from ..network_detection import NetworkDetector
from ..relay import FrpRelay, RelayConfig
from .dns import DnsSync
from .health import HealthChecks
from .mappings import ManagedMappings
from .reconcile import ServiceReconciler
from .store import list_services


class AccessController:
    def __init__(
        self,
        upnp,
        *,
        session_factory=SessionLocal,
        detector=None,
        relay=None,
        mappings=None,
        dns=None,
        health=None,
        interval=60,
        alert_threshold=3,
    ):
        self.upnp, self.session_factory = upnp, session_factory
        self.detector = detector or NetworkDetector(upnp)
        self.relay = relay or FrpRelay(
            RelayConfig(
                state_dir=settings.RELAY_STATE_DIR,
                binary=settings.RELAY_BINARY,
                server_addr=settings.RELAY_SERVER_ADDR,
                server_port=settings.RELAY_SERVER_PORT,
                public_host=settings.RELAY_PUBLIC_HOST,
                token=settings.RELAY_TOKEN.get_secret_value(),
            )
        )
        self.reconciler = ServiceReconciler(
            mappings=mappings or ManagedMappings(upnp),
            relay=self.relay,
            dns=dns or DnsSync(),
            health=health
            or HealthChecks(probe_url=settings.ACCESS_PROBE_URL, webhook_url=settings.ACCESS_ALERT_WEBHOOK),
            alert_threshold=alert_threshold,
        )
        self.interval = interval
        self.started_at = datetime.now(timezone.utc)
        self.network = None
        self.lock = asyncio.Lock()
        self._wake = asyncio.Event()
        self._task = None
        self._checks_limit = asyncio.Semaphore(8)

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self.started_at = datetime.now(timezone.utc)
            self._task = asyncio.create_task(self._run(), name="public-access-maintenance")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        await self.relay.stop()

    def wake(self) -> None:
        self._wake.set()

    async def detect(self):
        async with self.lock:
            return await self._detect()

    async def _detect(self):
        if not self.upnp.initialized:
            try:
                await asyncio.wait_for(self.upnp.startup(), timeout=12)
            except (Exception, asyncio.CancelledError):
                await self.upnp.close()
                if asyncio.current_task().cancelling():
                    raise
        self.network = await self.detector.detect()
        if not self.network.upnp_available:
            await self.upnp.close()
        return self.network

    async def reconcile(self) -> None:
        async with self.lock:
            network = await self._detect()
            with self.session_factory() as db:
                rows = list_services(db)
                prepared, relay_mappings = [], []
                for row in rows:
                    try:
                        mode = await self.reconciler.prepare(db, row, network)
                        if mode == "relay":
                            relay_mappings.append(self.reconciler.relay_mapping(row))
                        if mode:
                            prepared.append(row.id)
                    except Exception as exc:
                        await self._failed(db, row, exc)
                try:
                    await self.relay.apply(relay_mappings)
                    registration = await self.relay.registration() if relay_mappings else {}
                except Exception:
                    registration = {}
                    logger.warning("Public access relay reconciliation failed")
            await asyncio.gather(*(self._check_one(service_id, network, registration) for service_id in prepared))

    async def _check_one(self, service_id, network, registration) -> None:
        async with self._checks_limit:
            # Health checks can wait on independent networks; do not serialize
            # every service behind a slow probe or share their database sessions.
            with self.session_factory() as db:
                row = db.get(PublishedService, service_id)
                if row is None:
                    return
                try:
                    await self.reconciler.check(db, row, network, relay_ready=registration.get(service_id, False))
                except Exception as exc:
                    await self._failed(db, row, exc)

    async def _failed(self, db, row, exc) -> None:
        db.rollback()
        logger.warning(f"Public access check failed service={row.id} kind={type(exc).__name__}")
        await self.reconciler.finish(db, row, "error", "mapping_failed", None)

    def poll_interval(self) -> float:
        with self.session_factory() as db:
            leases = [r.lease_duration / 2 for r in list_services(db) if r.enabled and r.lease_duration]
        return min(self.interval, *leases) if leases else self.interval

    async def _run(self) -> None:
        while True:
            cycle_started = asyncio.get_running_loop().time()
            self._wake.clear()
            try:
                await self.reconcile()
            except Exception as exc:
                logger.warning(f"Public access cycle failed kind={type(exc).__name__}")
            try:
                delay = self.poll_interval()
            except Exception:
                delay = self.interval
                logger.warning("Public access database unavailable; maintenance will retry")
            try:
                elapsed = asyncio.get_running_loop().time() - cycle_started
                await asyncio.wait_for(self._wake.wait(), timeout=max(0.01, delay - elapsed))
            except TimeoutError:
                pass

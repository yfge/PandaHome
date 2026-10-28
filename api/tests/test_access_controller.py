from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app.database.database import Base
from src.app.models.published_service import PublishedService
from src.app.schemas.network import NetworkReport
from src.app.services.access.controller import AccessController
from src.app.services.access.mappings import MappingConflict
from src.app.services.access.store import service_view


def report(topology="public_ipv4", *, observed="8.8.8.8", upnp=True):
    return NetworkReport(
        topology=topology,
        recommended_mode="direct" if topology == "public_ipv4" else "relay" if topology == "cgnat" else "unknown",
        observed_public_ip=observed,
        gateway_external_ip=observed if topology == "public_ipv4" else "100.64.0.1",
        upnp_available=upnp,
        checked_at=datetime.now(timezone.utc),
        reason_code="public_ipv4_candidate" if topology == "public_ipv4" else "gateway_shared_address",
    )


def owned_spec(row):
    return {
        "external_port": row.public_port,
        "internal_port": row.local_port,
        "local_ip": row.local_ip,
        "protocol": row.protocol,
        "description": f"PandaHome:{row.owner_token}",
    }


@pytest.fixture()
def harness():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    upnp = SimpleNamespace(initialized=True, startup=AsyncMock(), close=AsyncMock())

    async def startup():
        upnp.initialized = True

    async def close():
        upnp.initialized = False

    upnp.startup.side_effect = startup
    upnp.close.side_effect = close
    detector = SimpleNamespace(detect=AsyncMock(return_value=report()))
    relay_state = {
        "configured": True,
        "available": True,
        "running": False,
        "public_host": "relay.example.com",
        "reason_code": "relay_stopped",
    }

    async def apply(mappings):
        relay_state["running"] = bool(mappings) and relay_state["configured"] and relay_state["available"]

    relay = SimpleNamespace(status=Mock(side_effect=lambda: dict(relay_state)), apply=AsyncMock(side_effect=apply))
    relay.stop = AsyncMock()
    relay.registration = AsyncMock(return_value={1: True, 2: True, 3: True})
    mappings = SimpleNamespace(ensure=AsyncMock(side_effect=owned_spec), remove=AsyncMock())
    dns = SimpleNamespace(sync=AsyncMock(return_value="updated"))
    health = SimpleNamespace(local=AsyncMock(return_value=True), external=AsyncMock(return_value=None))
    health.notify = AsyncMock(return_value=True)
    controller = AccessController(
        upnp,
        session_factory=factory,
        detector=detector,
        relay=relay,
        mappings=mappings,
        dns=dns,
        health=health,
        alert_threshold=2,
    )
    yield SimpleNamespace(
        controller=controller,
        factory=factory,
        upnp=upnp,
        detector=detector,
        relay=relay,
        relay_state=relay_state,
        mappings=mappings,
        dns=dns,
        health=health,
    )
    engine.dispose()


def add_service(harness, **updates):
    values = {
        "name": "Home server",
        "local_ip": "192.168.1.10",
        "local_port": 8080,
        "public_port": 18080,
        "protocol": "TCP",
        "mode": "auto",
        "owner_token": "unique-owner",
        "runtime": {},
        **updates,
    }
    with harness.factory() as db:
        row = PublishedService(**values)
        db.add(row)
        db.commit()
        service_id, spec = row.id, owned_spec(row)
    return service_id, spec


def runtime(harness, service_id):
    with harness.factory() as db:
        return dict(db.get(PublishedService, service_id).runtime)


@pytest.mark.asyncio
@pytest.mark.parametrize("with_domain", [False, True])
async def test_explicit_direct_uses_gateway_wan_when_observed_egress_differs(harness, with_domain):
    service_id, _ = add_service(
        harness, mode="direct", **({"domain": "example.com", "rr": "home"} if with_domain else {})
    )
    harness.detector.detect.return_value = report().model_copy(
        update={
            "topology": "upstream_nat",
            "recommended_mode": "relay",
            "gateway_external_ip": "8.8.4.4",
            "reason_code": "public_ip_mismatch",
        }
    )

    await harness.controller.reconcile()

    endpoint_host = "home.example.com" if with_domain else "8.8.4.4"
    state = runtime(harness, service_id)
    assert state["active_mode"] == "direct"
    assert state["public_endpoint"] == f"{endpoint_host}:18080"
    assert state["status"] == "pending"
    assert state["reason_code"] == "inbound_unverified"
    assert state["external_verified"] is False
    assert harness.dns.sync.await_args.args[1] == "8.8.4.4"
    harness.health.external.assert_awaited_once_with(endpoint_host, 18080, "TCP")
    harness.mappings.ensure.assert_awaited_once()
    harness.relay.apply.assert_awaited_once_with([])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("gateway", "topology", "recommended", "reason"),
    [
        (None, "unknown", "unknown", "gateway_ip_unavailable"),
        ("192.168.1.1", "upstream_nat", "relay", "gateway_private_address"),
        ("100.64.0.1", "cgnat", "relay", "gateway_shared_address"),
        ("224.0.0.1", "unknown", "unknown", "gateway_address_not_global"),
        ("2001:4860::8888", "unknown", "unknown", "gateway_ip_unavailable"),
        ("invalid", "unknown", "unknown", "gateway_ip_unavailable"),
    ],
)
async def test_explicit_direct_keeps_observed_fallback_without_global_unicast_wan(
    harness, gateway, topology, recommended, reason
):
    service_id, _ = add_service(harness, mode="direct")
    harness.detector.detect.return_value = report().model_copy(
        update={
            "gateway_external_ip": gateway,
            "topology": topology,
            "recommended_mode": recommended,
            "reason_code": reason,
        }
    )

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["active_mode"] == "direct"
    assert state["public_endpoint"] == "8.8.8.8:18080"
    assert state["external_verified"] is False
    assert harness.dns.sync.await_args.args[1] == "8.8.8.8"
    harness.health.external.assert_awaited_once_with("8.8.8.8", 18080, "TCP")


@pytest.mark.asyncio
async def test_auto_global_wan_mismatch_keeps_conservative_relay_recommendation(harness):
    service_id, _ = add_service(harness)
    harness.detector.detect.return_value = report().model_copy(
        update={
            "topology": "upstream_nat",
            "recommended_mode": "relay",
            "gateway_external_ip": "8.8.4.4",
            "reason_code": "public_ip_mismatch",
        }
    )

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["active_mode"] == "relay"
    assert state["public_endpoint"] == "relay.example.com:18080"
    assert state["external_verified"] is False
    harness.mappings.ensure.assert_not_called()
    assert harness.dns.sync.await_args.args[1] == "relay.example.com"
    harness.health.external.assert_awaited_once_with("relay.example.com", 18080, "TCP")


@pytest.mark.asyncio
async def test_explicit_relay_keeps_relay_host_when_gateway_has_global_wan(harness):
    service_id, _ = add_service(harness, mode="relay")

    await harness.controller.reconcile()

    assert runtime(harness, service_id)["public_endpoint"] == "relay.example.com:18080"
    assert harness.dns.sync.await_args.args[1] == "relay.example.com"
    harness.health.external.assert_awaited_once_with("relay.example.com", 18080, "TCP")
    harness.mappings.ensure.assert_not_called()


@pytest.mark.asyncio
async def test_direct_ddns_tracks_gateway_wan_while_observed_egress_stays_fixed(harness):
    service_id, _ = add_service(harness, mode="direct", domain="example.com", rr="home")
    for gateway in ("8.8.4.4", "1.1.1.1"):
        harness.detector.detect.return_value = report().model_copy(
            update={
                "topology": "upstream_nat",
                "recommended_mode": "relay",
                "gateway_external_ip": gateway,
                "reason_code": "public_ip_mismatch",
            }
        )
        await harness.controller.reconcile()

    assert [entry.args[1] for entry in harness.dns.sync.await_args_list] == ["8.8.4.4", "1.1.1.1"]
    assert runtime(harness, service_id)["public_endpoint"] == "home.example.com:18080"
    assert runtime(harness, service_id)["external_verified"] is False
    assert harness.health.external.await_count == 2
    assert harness.mappings.ensure.await_count == 2


@pytest.mark.asyncio
async def test_direct_keeps_observed_evidence_requirement_even_with_global_gateway(harness):
    service_id, _ = add_service(harness, mode="direct")
    harness.detector.detect.return_value = report(observed=None).model_copy(
        update={
            "topology": "unknown",
            "recommended_mode": "unknown",
            "gateway_external_ip": "8.8.4.4",
            "reason_code": "public_ip_unavailable",
        }
    )

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["status"] == "needs_setup"
    assert state["reason_code"] == "direct_unavailable"
    assert state["public_endpoint"] is None
    assert state["external_verified"] is False
    harness.mappings.ensure.assert_not_called()
    harness.dns.sync.assert_not_called()
    harness.health.external.assert_not_called()


@pytest.mark.asyncio
async def test_direct_candidate_requires_external_verification(harness):
    service_id, spec = add_service(harness)

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["active_mode"] == "direct"
    assert state["mapping"] == spec
    assert state["status"] == "pending"
    assert state["reason_code"] == "inbound_unverified"
    assert state["external_verified"] is False
    assert state["public_endpoint"] == "8.8.8.8:18080"
    harness.relay.apply.assert_awaited_once_with([])
    harness.mappings.remove.assert_not_called()


@pytest.mark.asyncio
async def test_external_success_is_required_for_healthy_status(harness):
    service_id, _ = add_service(harness, domain="example.com", rr="home")
    harness.health.external.return_value = True

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["status"] == "healthy"
    assert state["external_verified"] is True
    assert state["public_endpoint"] == "home.example.com:18080"
    assert harness.dns.sync.await_args.args[1] == "8.8.8.8"
    harness.health.external.assert_awaited_once_with("home.example.com", 18080, "TCP")


@pytest.mark.asyncio
async def test_local_failure_does_not_claim_external_success(harness):
    service_id, _ = add_service(harness)
    harness.health.local.return_value = False
    harness.health.external.return_value = True

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["status"] == "error"
    assert state["reason_code"] == "local_unreachable"
    assert state["external_verified"] is False
    harness.health.external.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("topology", ["cgnat", "unknown"])
async def test_non_direct_network_uses_configured_relay_without_claiming_tunnel_health(harness, topology):
    service_id, _ = add_service(harness)
    harness.detector.detect.return_value = report(topology)

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["active_mode"] == "relay"
    assert state["public_endpoint"] == "relay.example.com:18080"
    assert state["status"] == "pending"
    assert state["external_verified"] is False
    assert state["reason_code"] == "relay_unverified"
    assert harness.relay.apply.await_args.args[0][0].service_id == service_id
    harness.mappings.ensure.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("registration", [{}, {1: False}, {2: True}])
async def test_unregistered_relay_never_claims_health_from_an_unrelated_external_port(harness, registration):
    service_id, _ = add_service(harness)
    harness.detector.detect.return_value = report("cgnat")
    harness.relay.registration.return_value = registration
    harness.health.external.return_value = True

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["status"] == "degraded"
    assert state["reason_code"] == "relay_unregistered"
    assert state["external_verified"] is False
    assert state["public_endpoint"] is None
    harness.health.external.assert_not_called()
    harness.dns.sync.assert_not_called()


@pytest.mark.asyncio
async def test_cgnat_without_relay_explains_setup_requirement(harness):
    service_id, _ = add_service(harness)
    harness.detector.detect.return_value = report("cgnat")
    harness.relay_state["configured"] = False

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["status"] == "needs_setup"
    assert state["reason_code"] == "relay_not_configured"
    assert state["external_verified"] is False
    harness.mappings.ensure.assert_not_called()
    harness.dns.sync.assert_not_called()


@pytest.mark.asyncio
async def test_auto_direct_failure_falls_back_to_relay(harness):
    service_id, _ = add_service(harness)
    harness.mappings.ensure.side_effect = TimeoutError()

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["active_mode"] == "relay"
    assert state["public_endpoint"] == "relay.example.com:18080"
    assert state["fallback_until"] > 0


@pytest.mark.asyncio
async def test_lost_response_keeps_owned_spec_for_disable_cleanup(harness):
    service_id, spec = add_service(harness, mode="direct")
    harness.mappings.ensure.side_effect = TimeoutError()
    await harness.controller.reconcile()
    assert runtime(harness, service_id)["mapping"] == spec
    with harness.factory() as db:
        row = db.get(PublishedService, service_id)
        row.enabled = False
        db.commit()

    await harness.controller.reconcile()

    harness.mappings.remove.assert_awaited_once_with(spec)
    assert runtime(harness, service_id)["status"] == "disabled"


@pytest.mark.asyncio
async def test_explicit_direct_mode_does_not_switch_to_relay(harness):
    service_id, _ = add_service(harness, mode="direct")
    harness.mappings.ensure.side_effect = TimeoutError()

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["status"] == "error"
    assert state["reason_code"] == "mapping_failed"
    assert state["active_mode"] == "direct"
    harness.relay.apply.assert_awaited_once_with([])


@pytest.mark.asyncio
async def test_known_conflict_is_preserved_without_relay_mutation(harness):
    service_id, _ = add_service(harness)
    harness.mappings.ensure.side_effect = MappingConflict("another owner")

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["reason_code"] == "mapping_conflict"
    assert state["status"] == "error"
    harness.mappings.remove.assert_not_called()
    harness.relay.apply.assert_awaited_once_with([])


@pytest.mark.asyncio
async def test_fallback_removes_previous_owned_direct_mapping_in_same_cycle(harness):
    service_id, spec = add_service(harness)
    with harness.factory() as db:
        row = db.get(PublishedService, service_id)
        row.runtime = {"mapping": spec, "active_mode": "direct"}
        db.commit()
    harness.mappings.ensure.side_effect = TimeoutError()

    await harness.controller.reconcile()

    harness.mappings.remove.assert_awaited_once_with(spec)
    assert runtime(harness, service_id).get("mapping") is None
    assert runtime(harness, service_id)["active_mode"] == "relay"


@pytest.mark.asyncio
async def test_network_change_cleans_owned_mapping_before_relay(harness):
    service_id, spec = add_service(harness)
    await harness.controller.reconcile()
    harness.detector.detect.return_value = report("cgnat")
    order = Mock()
    order.attach_mock(harness.mappings.remove, "remove")
    order.attach_mock(harness.relay.apply, "apply")

    await harness.controller.reconcile()

    harness.mappings.remove.assert_awaited_once_with(spec)
    assert [entry[0] for entry in order.mock_calls] == ["remove", "apply"]
    assert runtime(harness, service_id).get("mapping") is None


@pytest.mark.asyncio
async def test_router_cleanup_failure_keeps_relay_available_and_retries_owned_cleanup(harness):
    service_id, spec = add_service(harness)
    await harness.controller.reconcile()
    harness.detector.detect.return_value = report("cgnat")
    harness.mappings.remove.side_effect = [TimeoutError(), None]
    harness.health.external.return_value = True

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["active_mode"] == "relay"
    assert state["status"] == "healthy"
    assert state["mapping"] == spec
    assert state["public_endpoint"] == "relay.example.com:18080"
    await harness.controller.reconcile()
    assert runtime(harness, service_id).get("mapping") is None
    assert harness.mappings.remove.await_count == 2
    assert all(entry.args == (spec,) for entry in harness.mappings.remove.await_args_list)


@pytest.mark.asyncio
async def test_uncertain_direct_write_and_failed_cleanup_can_use_registered_relay(harness):
    service_id, spec = add_service(harness)
    harness.mappings.ensure.side_effect = TimeoutError()
    harness.mappings.remove.side_effect = [TimeoutError(), None]
    harness.health.external.return_value = True

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["status"] == "healthy"
    assert state["active_mode"] == "relay"
    assert state["mapping"] == spec
    await harness.controller.reconcile()
    assert runtime(harness, service_id).get("mapping") is None
    assert harness.mappings.remove.await_count == 2


@pytest.mark.asyncio
async def test_unknown_network_removes_stale_endpoint_and_active_mode(harness):
    service_id, spec = add_service(harness)
    harness.health.external.return_value = True
    await harness.controller.reconcile()
    harness.detector.detect.return_value = report("unknown", observed=None)
    harness.relay_state["configured"] = False

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    harness.mappings.remove.assert_awaited_once_with(spec)
    assert state["status"] == "needs_setup"
    assert state["active_mode"] is None
    assert state["public_endpoint"] is None
    assert state["external_verified"] is False


@pytest.mark.asyncio
async def test_disabled_service_removes_only_its_persisted_owned_spec(harness):
    service_id, spec = add_service(harness)
    await harness.controller.reconcile()
    with harness.factory() as db:
        row = db.get(PublishedService, service_id)
        row.enabled = False
        db.commit()
    harness.mappings.ensure.reset_mock()

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    harness.mappings.remove.assert_awaited_once_with(spec)
    harness.mappings.ensure.assert_not_called()
    assert state["status"] == "disabled"
    assert state["active_mode"] is None
    assert state["public_endpoint"] is None
    assert state["external_verified"] is False


@pytest.mark.asyncio
async def test_failed_cleanup_preserves_spec_and_retries_next_cycle(harness):
    service_id, spec = add_service(harness)
    await harness.controller.reconcile()
    with harness.factory() as db:
        row = db.get(PublishedService, service_id)
        row.enabled = False
        db.commit()
    harness.mappings.remove.side_effect = [TimeoutError(), None]

    await harness.controller.reconcile()
    assert runtime(harness, service_id)["mapping"] == spec
    assert runtime(harness, service_id)["status"] == "error"
    await harness.controller.reconcile()

    assert harness.mappings.remove.await_count == 2
    assert runtime(harness, service_id).get("mapping") is None
    assert runtime(harness, service_id)["status"] == "disabled"


@pytest.mark.asyncio
async def test_ddns_tracks_updated_public_ip(harness):
    service_id, _ = add_service(harness, domain="example.com", rr="home")
    await harness.controller.reconcile()
    harness.detector.detect.return_value = report(observed="8.8.4.4")

    await harness.controller.reconcile()

    assert [entry.args[1] for entry in harness.dns.sync.await_args_list] == ["8.8.8.8", "8.8.4.4"]
    assert runtime(harness, service_id)["public_endpoint"] == "home.example.com:18080"
    assert harness.mappings.ensure.await_count == 2


@pytest.mark.asyncio
async def test_alert_threshold_and_recovery_are_not_repeated(harness):
    service_id, _ = add_service(harness, mode="direct")
    harness.health.external.return_value = False
    for _ in range(3):
        await harness.controller.reconcile()
    assert harness.health.notify.await_count == 1
    assert harness.health.notify.await_args.kwargs["event"] == "failure"
    harness.health.external.return_value = True

    await harness.controller.reconcile()
    await harness.controller.reconcile()

    assert harness.health.notify.await_count == 2
    assert harness.health.notify.await_args.kwargs["event"] == "recovery"
    assert runtime(harness, service_id)["failure_count"] == 0
    assert runtime(harness, service_id)["external_verified"] is True


@pytest.mark.asyncio
async def test_repeated_failed_direct_probes_switch_to_configured_relay(harness):
    service_id, spec = add_service(harness)
    harness.health.external.return_value = False
    for _ in range(3):
        await harness.controller.reconcile()
    assert runtime(harness, service_id)["active_mode"] == "direct"
    harness.health.external.return_value = True

    await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["active_mode"] == "relay"
    assert state["status"] == "healthy"
    assert state["public_endpoint"] == "relay.example.com:18080"
    harness.mappings.remove.assert_awaited_once_with(spec)


@pytest.mark.asyncio
async def test_failed_direct_probes_keep_retrying_when_relay_is_not_configured(harness):
    service_id, _ = add_service(harness)
    harness.relay_state["configured"] = False
    harness.health.external.return_value = False
    for _ in range(4):
        await harness.controller.reconcile()

    state = runtime(harness, service_id)
    assert state["active_mode"] == "direct"
    assert state["reason_code"] == "probe_failed"
    assert not state.get("fallback_until")
    assert harness.mappings.ensure.await_count == 4


@pytest.mark.asyncio
async def test_one_service_failure_does_not_block_other_services_or_future_retry(harness):
    first, _ = add_service(harness, mode="direct")
    second, _ = add_service(harness, name="Second", mode="direct", public_port=18081, owner_token="other-owner")
    failed = True

    def ensure(row):
        if row.id == first and failed:
            raise TimeoutError()
        return owned_spec(row)

    harness.mappings.ensure.side_effect = ensure
    harness.health.external.return_value = True

    await harness.controller.reconcile()
    assert runtime(harness, first)["status"] == "error"
    assert runtime(harness, second)["status"] == "healthy"
    failed = False
    await harness.controller.reconcile()

    assert runtime(harness, first)["status"] == "healthy"
    assert runtime(harness, second)["status"] == "healthy"


@pytest.mark.asyncio
async def test_detector_retries_discovery_after_initial_failure(harness):
    harness.upnp.initialized = False

    assert await harness.controller.detect() == harness.detector.detect.return_value
    await harness.controller.detect()

    harness.upnp.startup.assert_awaited_once()
    harness.upnp.close.assert_not_called()


@pytest.mark.asyncio
async def test_lost_upnp_evidence_closes_discovery_and_retries(harness):
    harness.detector.detect.return_value = report("unknown", upnp=False)
    await harness.controller.detect()
    harness.detector.detect.return_value = report()

    await harness.controller.detect()

    harness.upnp.close.assert_awaited_once()
    harness.upnp.startup.assert_awaited_once()
    assert harness.controller.network.topology == "public_ipv4"


@pytest.mark.asyncio
async def test_discovery_cancellation_closes_upnp_and_propagates(harness):
    harness.upnp.initialized = False
    started = asyncio.Event()

    async def discover():
        started.set()
        await asyncio.Event().wait()

    harness.upnp.startup.side_effect = discover
    task = asyncio.create_task(harness.controller.detect())
    await asyncio.wait_for(started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    harness.upnp.close.assert_awaited_once()
    harness.detector.detect.assert_not_called()


@pytest.mark.asyncio
async def test_background_start_is_idempotent_and_stop_cancels_work(harness):
    started, cancelled = asyncio.Event(), asyncio.Event()

    async def cycle():
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    harness.controller.reconcile = AsyncMock(side_effect=cycle)
    await harness.controller.start()
    first_task = harness.controller._task
    await harness.controller.start()
    await asyncio.wait_for(started.wait(), timeout=1)

    await harness.controller.stop()

    assert first_task.cancelled()
    assert cancelled.is_set()
    harness.controller.reconcile.assert_awaited_once()
    harness.relay.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_wake_rechecks_without_waiting_for_poll_interval(harness):
    first, second = asyncio.Event(), asyncio.Event()

    async def cycle():
        if first.is_set():
            second.set()
        else:
            first.set()

    harness.controller.reconcile = AsyncMock(side_effect=cycle)
    await harness.controller.start()
    try:
        await asyncio.wait_for(first.wait(), timeout=1)
        harness.controller.wake()
        await asyncio.wait_for(second.wait(), timeout=1)
    finally:
        await harness.controller.stop()

    assert harness.controller.reconcile.await_count == 2


@pytest.mark.asyncio
async def test_background_cycle_recovers_after_transient_error(harness):
    retried = asyncio.Event()

    async def cycle():
        if harness.controller.reconcile.await_count == 1:
            raise OSError("temporarily unavailable")
        retried.set()

    harness.controller.reconcile = AsyncMock(side_effect=cycle)
    harness.controller.interval = 0.01
    await harness.controller.start()
    try:
        await asyncio.wait_for(retried.wait(), timeout=1)
    finally:
        await harness.controller.stop()

    assert harness.controller.reconcile.await_count >= 2


@pytest.mark.asyncio
async def test_background_survives_poll_interval_database_error(harness):
    retried = asyncio.Event()

    async def cycle():
        if harness.controller.reconcile.await_count >= 2:
            retried.set()

    def poll():
        if harness.controller.poll_interval.call_count == 1:
            raise OSError("temporary database failure")
        return 0.01

    harness.controller.reconcile = AsyncMock(side_effect=cycle)
    harness.controller.poll_interval = Mock(side_effect=poll)
    harness.controller.interval = 0.01
    await harness.controller.start()
    try:
        await asyncio.wait_for(retried.wait(), timeout=1)
    finally:
        await harness.controller.stop()

    assert harness.controller.reconcile.await_count >= 2


def test_polling_renews_short_leases_before_expiry(harness):
    add_service(harness, lease_duration=10)
    assert harness.controller.poll_interval() == 5


@pytest.mark.asyncio
async def test_slow_health_checks_do_not_serialize_independent_services(harness):
    first, _ = add_service(harness)
    second, _ = add_service(harness, name="Second", public_port=18081, owner_token="second")
    started = set()
    all_started = asyncio.Event()

    async def probe(host, port, protocol):
        started.add(port)
        if len(started) == 2:
            all_started.set()
        await asyncio.wait_for(all_started.wait(), timeout=1)
        return True

    harness.health.external.side_effect = probe
    await asyncio.wait_for(harness.controller.reconcile(), timeout=2)
    assert runtime(harness, first)["status"] == "healthy"
    assert runtime(harness, second)["status"] == "healthy"


@pytest.mark.asyncio
async def test_restart_and_expired_evidence_are_not_current_health(harness):
    service_id, spec = add_service(harness)
    harness.health.external.return_value = True
    await harness.controller.reconcile()
    with harness.factory() as db:
        row = db.get(PublishedService, service_id)
        assert service_view(row).external_verified is True
        restarted = service_view(row, checked_since=datetime.now(timezone.utc))
        assert restarted.status == "pending" and restarted.external_verified is False
        row.runtime = {**row.runtime, "last_checked": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()}
        db.commit()
        stale = service_view(row, stale_after=180)
        assert stale.status == "pending" and stale.external_verified is False
        assert row.runtime["mapping"] == spec

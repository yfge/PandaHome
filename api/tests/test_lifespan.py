"""All owned services must be cleaned up even after partial startup or shutdown."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.app.main import lifespan


@pytest.fixture
def services(monkeypatch):
    monkeypatch.setattr("src.app.main.os", SimpleNamespace(getenv=lambda key: None))
    calls = []

    def operation(name):
        async def run():
            calls.append(name)
        return AsyncMock(side_effect=run)

    state = SimpleNamespace(
        access_controller=SimpleNamespace(start=operation("access_start"), stop=operation("access_stop")),
        p2p_manager=SimpleNamespace(startup=operation("p2p_start"), shutdown=operation("p2p_stop")),
        upnp_service=SimpleNamespace(shutdown=operation("upnp_stop")),
    )
    return SimpleNamespace(state=state), calls


@pytest.mark.asyncio
async def test_success_cleans_up_dependents_before_upnp(services):
    app, calls = services
    async with lifespan(app):
        assert calls == ["access_start", "p2p_start"]
    assert calls == ["access_start", "p2p_start", "p2p_stop", "access_stop", "upnp_stop"]


@pytest.mark.asyncio
@pytest.mark.parametrize("failing_service", ["access", "p2p"])
async def test_partial_startup_releases_resources(services, failing_service):
    app, calls = services
    failing = app.state.access_controller.start if failing_service == "access" else app.state.p2p_manager.startup
    failing.side_effect = RuntimeError("startup failed")
    with pytest.raises(RuntimeError, match="startup failed"):
        async with lifespan(app):
            pytest.fail("Failed startup must not yield a running application")
    assert calls[-2:] == ["access_stop", "upnp_stop"]
    if failing_service == "p2p":
        app.state.p2p_manager.shutdown.assert_awaited_once()
    else:
        app.state.p2p_manager.shutdown.assert_not_awaited()


@pytest.mark.asyncio
async def test_one_shutdown_failure_does_not_skip_other_owners(services):
    app, calls = services
    app.state.p2p_manager.shutdown.side_effect = RuntimeError("shutdown failed")
    with pytest.raises(RuntimeError, match="shutdown failed"):
        async with lifespan(app):
            pass
    assert calls[-2:] == ["access_stop", "upnp_stop"]

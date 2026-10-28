"""Public relay and private P2P must not overwrite or stop each other's owner."""

import asyncio
import tomllib

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.models.p2p_service import P2PService
from src.app.services import relay as relay_module
from src.app.services.p2p import P2PConfig, P2PManager
from src.app.services.relay import FrpRelay, RelayConfig, RelayMapping


class Child:
    def __init__(self):
        self.returncode = None
        self.exited = asyncio.Event()

    def terminate(self):
        self.returncode = -15
        self.exited.set()

    def kill(self):
        self.returncode = -9
        self.exited.set()

    async def wait(self):
        await self.exited.wait()
        return self.returncode


@pytest.mark.asyncio
async def test_shared_state_root_has_independent_configs_credentials_and_shutdown(tmp_path, monkeypatch):
    monkeypatch.setattr(relay_module.shutil, "which", lambda _: "/usr/local/bin/frpc")

    async def spawn(*args, **kwargs):
        return Child()

    monkeypatch.setattr(relay_module.asyncio, "create_subprocess_exec", spawn)
    engine = create_engine(f"sqlite:///{tmp_path / 'services.db'}")
    P2PService.__table__.create(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add(P2PService(name="private", local_ip="127.0.0.1", local_port=8080))
        db.commit()
    public = FrpRelay(RelayConfig(state_dir=tmp_path, server_addr="relay.example.test", token="public-test-token"))
    private = P2PManager(P2PConfig(state_dir=tmp_path, server_addr="relay.example.test", token="private-test-token"), sessions)
    try:
        await asyncio.gather(public.apply([RelayMapping(1, "127.0.0.1", 8080, 18080, "TCP")]), private.reconcile())
        public_child = public._process
        private_child = private.relay._process
        assert public_child is not private_child
        assert public._config_path != private.relay._config_path
        public_config = tomllib.loads(public._config_path.read_text())
        private_config = tomllib.loads(private.relay._config_path.read_text())
        assert public_config["auth"]["token"] == "public-test-token"
        assert private_config["auth"]["token"] == "private-test-token"
        assert [entry["type"] for entry in public_config["proxies"]] == ["tcp"]
        assert {entry["type"] for entry in private_config["proxies"]} == {"xtcp", "stcp"}

        await private.shutdown()
        assert public_child.returncode is None and public._config_path.exists()
        assert private_child.returncode is not None and not private.relay._config_path.exists()

        await private.reconcile()
        await public.stop()
        assert private.status()["running"] and private.relay._config_path.exists()
        assert public_child.returncode is not None and not public._config_path.exists()
    finally:
        await private.shutdown()
        await public.stop()
        engine.dispose()

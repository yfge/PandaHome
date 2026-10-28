"""Opt-in frp binary checks; all service and STUN addresses remain on loopback.

Set PANDAHOME_FRP_BIN_DIR to an independently verified frp release directory.
These tests establish local transport behavior, not cross-NAT reachability.
"""

import asyncio
import json
import os
import secrets
import socket
import struct
import sys
from contextlib import asynccontextmanager, suppress
from dataclasses import asdict
from pathlib import Path

import psutil
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.models.p2p_service import P2PService
from src.app.services.p2p import P2PConfig, P2PManager
from src.app.services.relay import _toml_string

pytestmark = pytest.mark.skipif(
    not os.getenv("PANDAHOME_FRP_BIN_DIR"), reason="Native frp checks require PANDAHOME_FRP_BIN_DIR",
)


class _LoopbackStun(asyncio.DatagramProtocol):
    """Minimal RFC 5389 Binding fixture exposing only the observed loopback peer."""

    other_address = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, address):
        if len(data) < 20 or address[0] != "127.0.0.1":
            return
        message_type, _, cookie = struct.unpack("!HHI", data[:8])
        if message_type != 0x0001 or cookie != 0x2112A442:
            return
        mapped_ip = struct.unpack("!I", socket.inet_aton(address[0]))[0]
        xor_address = struct.pack("!BBHI", 0, 1, address[1] ^ (cookie >> 16), mapped_ip ^ cookie)
        mapped_address = struct.pack("!BBHI", 0, 1, address[1], mapped_ip)
        attributes = struct.pack("!HH", 0x0020, 8) + xor_address
        attributes += struct.pack("!HH", 0x0001, 8) + mapped_address
        if self.other_address is not None:
            other_ip = struct.unpack("!I", socket.inet_aton(self.other_address[0]))[0]
            other_address = struct.pack("!BBHI", 0, 1, self.other_address[1], other_ip)
            attributes += struct.pack("!HH", 0x802C, 8) + other_address
        response = struct.pack("!HHI", 0x0101, len(attributes), cookie) + data[8:20] + attributes
        self.transport.sendto(response, address)


def _unused_port(kind=socket.SOCK_STREAM):
    with socket.socket(socket.AF_INET, kind) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _private_text(path, text):
    path.write_text(text)
    path.chmod(0o600)


async def _stop(process):
    if process.returncode is None:
        with suppress(ProcessLookupError):
            process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=3)
        except TimeoutError:
            process.kill()
            await asyncio.wait_for(process.wait(), timeout=3)


async def _verify(binary, path):
    process = await asyncio.create_subprocess_exec(
        str(binary), "verify", "-c", str(path),
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        result = await asyncio.wait_for(process.wait(), timeout=5)
        assert result == 0, "Native frpc rejected generated configuration; credentials withheld"
    finally:
        await _stop(process)


async def _wait_for_listener(port, process):
    deadline = asyncio.get_running_loop().time() + 8
    while asyncio.get_running_loop().time() < deadline:
        assert process.returncode is None, "Native frp process exited before listener readiness"
        try:
            _, writer = await asyncio.open_connection("127.0.0.1", port)
        except OSError:
            await asyncio.sleep(0.05)
        else:
            writer.close()
            await writer.wait_closed()
            return
    pytest.fail("Native frp listener did not become ready; configuration and logs withheld")


async def _roundtrip(port, payload=b"pandahome-native-tcp-proof", timeout=5):
    reader, writer = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", port), timeout=timeout)
    try:
        writer.write(payload)
        await writer.drain()
        received = await asyncio.wait_for(reader.readexactly(len(payload)), timeout=timeout)
        assert received == payload, "Native tunnel did not return the TCP payload"
        return reader, writer
    except BaseException:
        writer.close()
        with suppress(OSError):
            await writer.wait_closed()
        raise


@asynccontextmanager
async def _native_stack(tmp_path, monkeypatch, *, direct=False):
    binary_dir = Path(os.environ["PANDAHOME_FRP_BIN_DIR"])
    frpc, frps = binary_dir / "frpc", binary_dir / "frps"
    assert frpc.is_file() and frps.is_file(), "Both native frpc and frps binaries are required"
    for variable in ("http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        monkeypatch.delenv(variable, raising=False)
    token = secrets.token_urlsafe(32)
    server_port, visitor_port = _unused_port(), _unused_port()
    # A closed UDP endpoint makes XTCP fail without contacting a public STUN host.
    stun_port = _unused_port(socket.SOCK_DGRAM)
    stun_transports = []
    if direct:
        first_transport, first_stun = await asyncio.get_running_loop().create_datagram_endpoint(
            _LoopbackStun, local_addr=("127.0.0.1", 0),
        )
        second_transport, second_stun = await asyncio.get_running_loop().create_datagram_endpoint(
            _LoopbackStun, local_addr=("127.0.0.1", 0),
        )
        stun_transports.extend([first_transport, second_transport])
        first_stun.other_address = second_transport.get_extra_info("sockname")
        second_stun.other_address = first_transport.get_extra_info("sockname")
        stun_port = first_transport.get_extra_info("sockname")[1]
    writers = set()
    delivered = []

    async def echo(reader, writer):
        writers.add(writer)
        try:
            while data := await reader.read(65536):
                delivered.append(data)
                writer.write(data)
                await writer.drain()
        except OSError:
            pass
        finally:
            writers.discard(writer)
            writer.close()
            with suppress(OSError):
                await writer.wait_closed()

    echo_server = await asyncio.start_server(echo, "127.0.0.1", 0)
    echo_port = echo_server.sockets[0].getsockname()[1]
    engine = create_engine(f"sqlite:///{tmp_path / 'native.db'}")
    P2PService.__table__.create(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions() as db:
        row = P2PService(
            name="Native echo", local_ip="127.0.0.1", local_port=echo_port, fallback_enabled=not direct,
        )
        db.add(row)
        db.commit()
    manager = P2PManager(P2PConfig(
        state_dir=tmp_path / "state", server_addr="127.0.0.1", server_port=server_port,
        token=token, binary=str(frpc), stun_server=f"127.0.0.1:{stun_port}", fallback_timeout_ms=100,
    ), sessions)
    if direct:
        # Restrict native test candidates to fixture-provided STUN addresses.
        # Production defaults retain assisted LAN candidates for actual networks.
        render = manager.relay._render_config
        monkeypatch.setattr(manager.relay, "_render_config", lambda rows: render(rows).replace(
            'type = "xtcp"', 'type = "xtcp"\nnatTraversal.disableAssistedAddrs = true',
        ))
    server_config = tmp_path / "frps.toml"
    _private_text(server_config, "\n".join([
        'bindAddr = "127.0.0.1"', f"bindPort = {server_port}",
        'auth.method = "token"', f"auth.token = {_toml_string(token)}",
        "transport.tls.force = true", 'log.level = "info"', "log.disablePrintColor = true", "",
    ]))
    children = []
    handles = []
    try:
        server_log = (tmp_path / "server.log").open("wb")
        handles.append(server_log)
        server = await asyncio.create_subprocess_exec(
            str(frps), "-c", str(server_config), stdout=server_log, stderr=asyncio.subprocess.STDOUT,
        )
        children.append(server)
        await _wait_for_listener(server_port, server)
        await manager.reconcile()
        assert manager.status()["running"], "Native provider did not start"
        await _verify(frpc, manager.relay._config_path)
        visitor_config = tmp_path / "visitor.toml"
        # The fallback dispatch marker is a DEBUG message in native frp 0.71.1.
        visitor_text = manager.render_visitor(row, bind_port=visitor_port).replace(
            'log.level = "warn"', 'log.level = "debug"',
        )
        if direct:
            visitor_text = visitor_text.replace(
                'type = "xtcp"', 'type = "xtcp"\nnatTraversal.disableAssistedAddrs = true',
            )
        _private_text(visitor_config, visitor_text)
        await _verify(frpc, visitor_config)
        visitor_log_path = tmp_path / "visitor.log"
        visitor_log = visitor_log_path.open("wb")
        handles.append(visitor_log)
        visitor = await asyncio.create_subprocess_exec(
            str(frpc), "-c", str(visitor_config), stdout=visitor_log, stderr=asyncio.subprocess.STDOUT,
        )
        children.append(visitor)
        await _wait_for_listener(visitor_port, visitor)
        yield manager, sessions, row.id, visitor_port, visitor_log_path, delivered
    finally:
        owned_provider = manager.relay._process
        with suppress(Exception):
            await manager.shutdown()
        if owned_provider is not None:
            await _stop(owned_provider)
        for child in reversed(children):
            await _stop(child)
        for handle in handles:
            handle.close()
        for stun_transport in stun_transports:
            stun_transport.close()
        echo_server.close()
        await echo_server.wait_closed()
        for writer in tuple(writers):
            writer.close()
            with suppress(OSError):
                await writer.wait_closed()
        engine.dispose()


@pytest.mark.asyncio
async def test_native_xtcp_loopback_direct_without_fallback(tmp_path, monkeypatch):
    async with _native_stack(tmp_path, monkeypatch, direct=True) as stack:
        manager, _, _, port, visitor_log_path, _ = stack
        reader, writer = await _roundtrip(port, timeout=15)
        try:
            logs = visitor_log_path.read_text(errors="replace")
            direct_observed = "establishing nat hole connection successful" in logs
            fallback_observed = "try to transfer connection to visitor:" in logs
            assert direct_observed, "Native loopback XTCP did not establish a direct tunnel"
            assert not fallback_observed, "Fallback was unexpectedly used in a direct-only visitor"
            # Local integration evidence cannot establish a remote peer's runtime path.
            assert manager.status()["connection_type"] == "unknown"
            writer.write(b"second-stream-payload")
            await writer.drain()
            assert await asyncio.wait_for(reader.readexactly(21), timeout=5) == b"second-stream-payload"
        finally:
            writer.close()
            with suppress(OSError):
                await writer.wait_closed()


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["disable", "delete"])
async def test_native_fallback_tcp_roundtrip_and_revocation(tmp_path, monkeypatch, operation):
    async with _native_stack(tmp_path, monkeypatch) as stack:
        manager, sessions, row_id, port, visitor_log_path, delivered = stack
        reader, writer = await _roundtrip(port)
        try:
            logs = visitor_log_path.read_text(errors="replace")
            fallback_observed = "try to transfer connection to visitor:" in logs
            direct_observed = "establishing nat hole connection successful" in logs
            assert fallback_observed, "Native visitor did not record fallback dispatch"
            assert not direct_observed, "Closed loopback STUN unexpectedly established a direct path"
            assert manager.status()["connection_type"] == "unknown"
            with sessions() as db:
                row = db.get(P2PService, row_id)
                if operation == "disable":
                    row.enabled = False
                else:
                    db.delete(row)
                db.commit()
            await manager.reconcile()
            assert not manager.status()["running"], "Revoked native provider child remained running"
            assert not manager.relay._config_path.exists(), "Revoked private native configuration remained"
            assert await asyncio.wait_for(reader.read(1), timeout=5) == b"", "Existing TCP tunnel survived revocation"
            count = len(delivered)
            with pytest.raises((asyncio.IncompleteReadError, OSError, TimeoutError)):
                await _roundtrip(port, payload=b"must-not-be-delivered", timeout=2)
            assert len(delivered) == count, "Revoked service still received visitor data"
        finally:
            writer.close()
            with suppress(OSError):
                await writer.wait_closed()


async def _eventually_roundtrip(port):
    deadline = asyncio.get_running_loop().time() + 8
    while asyncio.get_running_loop().time() < deadline:
        try:
            return await _roundtrip(port, timeout=1)
        except (asyncio.IncompleteReadError, OSError, TimeoutError):
            await asyncio.sleep(0.05)
    pytest.fail("Replacement native provider did not carry TCP data; private diagnostics withheld")


def _alive(process):
    with suppress(psutil.NoSuchProcess):
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    return False


async def _wait_for_descendants_exit(processes):
    deadline = asyncio.get_running_loop().time() + 8
    while asyncio.get_running_loop().time() < deadline:
        if not any(_alive(process) for process in processes):
            return
        await asyncio.sleep(0.05)
    pytest.fail("A native provider or guard survived abrupt backend death")


async def _spawn_backend_owner(manager, sessions, tmp_path):
    config = asdict(manager.config)
    config["state_dir"] = str(config["state_dir"])
    arguments = tmp_path / "backend-owner.json"
    _private_text(arguments, json.dumps({
        "config": config, "database_url": str(sessions.kw["bind"].url),
    }))
    script = tmp_path / "backend-owner.py"
    _private_text(script, """import asyncio
import json
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.services.p2p import P2PConfig, P2PManager

async def main():
    arguments = json.loads(Path(sys.argv[1]).read_text())
    config = arguments['config']
    config['state_dir'] = Path(config['state_dir'])
    engine = create_engine(arguments['database_url'])
    manager = P2PManager(P2PConfig(**config), sessionmaker(bind=engine))
    await manager.startup()
    if not manager.status()['running']:
        raise SystemExit(2)
    Path(sys.argv[2]).write_text('ready')
    try:
        await asyncio.Event().wait()
    finally:
        await manager.shutdown()
        engine.dispose()

asyncio.run(main())
""")
    ready = tmp_path / "backend-owner.ready"
    environment = dict(os.environ)
    api_path = str(Path(__file__).resolve().parents[1])
    environment["PYTHONPATH"] = os.pathsep.join(filter(None, [api_path, environment.get("PYTHONPATH")]))
    owner = await asyncio.create_subprocess_exec(
        sys.executable, str(script), str(arguments), str(ready), env=environment,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    deadline = asyncio.get_running_loop().time() + 8
    try:
        while asyncio.get_running_loop().time() < deadline:
            assert owner.returncode is None, "Backend owner exited before provider startup; credentials withheld"
            if ready.is_file():
                return owner
            await asyncio.sleep(0.05)
        pytest.fail("Backend owner did not start; configuration and credentials withheld")
    except BaseException:
        await _stop(owner)
        raise


@pytest.mark.asyncio
async def test_native_backend_sigkill_reaps_provider_and_restart_can_revoke(tmp_path, monkeypatch):
    async with _native_stack(tmp_path, monkeypatch) as stack:
        manager, sessions, row_id, port, _, delivered = stack
        await manager.shutdown()
        owner = await _spawn_backend_owner(manager, sessions, tmp_path)
        descendants = []
        writer = None
        replacement = P2PManager(manager.config, sessions)
        try:
            reader, writer = await _eventually_roundtrip(port)
            descendants = psutil.Process(owner.pid).children(recursive=True)
            native_count = sum(process.name() == Path(manager.config.binary).name for process in descendants)
            assert native_count == 1, "Backend did not own exactly one native frpc descendant"
            owner.kill()
            await asyncio.wait_for(owner.wait(), timeout=3)
            await _wait_for_descendants_exit(descendants)
            assert await asyncio.wait_for(reader.read(1), timeout=5) == b"", "Tunnel survived abrupt backend death"
            count = len(delivered)
            with pytest.raises((asyncio.IncompleteReadError, OSError, TimeoutError)):
                await _roundtrip(port, payload=b"must-not-reach-orphan", timeout=2)
            assert len(delivered) == count, "Orphaned native provider still forwarded data"
            writer.close()
            with suppress(OSError):
                await writer.wait_closed()
            writer = None
            await replacement.reconcile()
            replacement_reader, writer = await _eventually_roundtrip(port)
            with sessions() as db:
                db.get(P2PService, row_id).enabled = False
                db.commit()
            await replacement.reconcile()
            assert not replacement.status()["running"], "Replacement manager did not stop disabled provider"
            assert await asyncio.wait_for(replacement_reader.read(1), timeout=5) == b"", "Restarted tunnel survived disable"
            count = len(delivered)
            with pytest.raises((asyncio.IncompleteReadError, OSError, TimeoutError)):
                await _roundtrip(port, payload=b"must-not-survive-disable", timeout=2)
            assert len(delivered) == count, "Replacement manager left stale forwarding after disable"
        finally:
            if writer is not None:
                writer.close()
                with suppress(OSError):
                    await writer.wait_closed()
            await _stop(owner)
            await replacement.shutdown()
            for process in reversed(descendants):
                if _alive(process):
                    with suppress(psutil.NoSuchProcess):
                        process.kill()

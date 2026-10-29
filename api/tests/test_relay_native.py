"""Opt-in native TLS checks; no network destination or listener leaves loopback."""

import asyncio
import os
import secrets
import socket
import subprocess
from pathlib import Path

import pytest

from src.app.services.relay import FrpRelay, RelayConfig, RelayMapping, _toml_string


pytestmark = pytest.mark.skipif(
    not os.getenv("PANDAHOME_FRP_BIN_DIR"), reason="Native frp checks require PANDAHOME_FRP_BIN_DIR",
)


def unused_port():
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        return reservation.getsockname()[1]


def certificate(directory, name):
    cert, key = directory / f"{name}.crt", directory / f"{name}.key"
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
        "-keyout", str(key), "-out", str(cert), "-subj", "/CN=frps.loopback.test",
        "-addext", "subjectAltName=DNS:frps.loopback.test",
        "-addext", "basicConstraints=critical,CA:TRUE",
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    key.chmod(0o600)
    return cert, key


async def stop(process):
    if process is not None and process.returncode is None:
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), 3)
        except TimeoutError:
            process.kill()
            await asyncio.wait_for(process.wait(), 3)


@pytest.mark.asyncio
@pytest.mark.parametrize("verification", ["correct", "wrong_ca", "wrong_name"])
async def test_native_tls_pin_and_name_are_enforced_without_downgrade(tmp_path, verification):
    binaries = Path(os.environ["PANDAHOME_FRP_BIN_DIR"]).expanduser().resolve()
    cert, key = certificate(tmp_path, "server")
    wrong_cert, _ = certificate(tmp_path, "unrelated")
    control, public = unused_port(), unused_port()
    token = secrets.token_hex(24)
    server_config = tmp_path / "frps.toml"
    server_config.write_text(
        f'bindAddr = "127.0.0.1"\nbindPort = {control}\nproxyBindAddr = "127.0.0.1"\n'
        f'transport.tls.force = true\ntransport.tls.certFile = {_toml_string(str(cert))}\n'
        f'transport.tls.keyFile = {_toml_string(str(key))}\nauth.token = {_toml_string(token)}\n'
        'log.to = "console"\nlog.level = "error"\n'
    )
    server_config.chmod(0o600)

    async def echo(reader, writer):
        try:
            writer.write(await reader.read(128))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    local = await asyncio.start_server(echo, "127.0.0.1", 0)
    relay = FrpRelay(RelayConfig(
        state_dir=tmp_path, binary=str(binaries / "frpc"), server_addr="127.0.0.1", server_port=control,
        token=token, tls_trusted_ca_file=str(wrong_cert if verification == "wrong_ca" else cert),
        tls_server_name="wrong.loopback.test" if verification == "wrong_name" else "frps.loopback.test",
    ))
    server = None
    try:
        server = await asyncio.create_subprocess_exec(
            str(binaries / "frps"), "-c", str(server_config),
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        await relay.apply([RelayMapping(1, "127.0.0.1", local.sockets[0].getsockname()[1], public, "TCP")])
        registration = await relay.registration()
        if verification == "correct":
            assert registration == {1: True}
            reader, writer = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", public), 2)
            try:
                nonce = secrets.token_bytes(32)
                writer.write(nonce)
                await writer.drain()
                assert await asyncio.wait_for(reader.readexactly(len(nonce)), 2) == nonce
            finally:
                writer.close()
                await writer.wait_closed()
        else:
            assert registration == {1: False}
            # A second native retry window still cannot accept a downgraded TLS
            # connection or expose the intended business port.
            assert await relay.registration() == {1: False}
            with pytest.raises(OSError):
                await asyncio.wait_for(asyncio.open_connection("127.0.0.1", public), 1)
    finally:
        await relay.stop()
        await stop(server)
        local.close()
        await local.wait_closed()
    assert not (tmp_path / "frp/frpc.toml").exists()
    assert relay.status()["running"] is False

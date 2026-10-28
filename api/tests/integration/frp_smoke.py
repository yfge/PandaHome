"""Opt-in real frp smoke; every listener is restricted to loopback.

Install official matching frpc/frps binaries outside the checkout, then run:
PYTHONPATH=api python api/tests/integration/frp_smoke.py --bin-dir /path/to/frp

No download, public listener, cloud credentials or existing frp setup is used.
This verifies local integration, not home-network or public reachability.
"""

import argparse
import asyncio
import json
import os
import shutil
import signal
import socket
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from src.app.services.relay import FrpRelay, RelayConfig, RelayMapping, _toml_string


class UdpEcho(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, address):
        self.transport.sendto(data, address)


async def tcp_echo(reader, writer):
    try:
        writer.write(await reader.read(1024))
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


def unused_tcp_ports():
    with socket.socket() as control, socket.socket() as public:
        control.bind(("127.0.0.1", 0))
        public.bind(("127.0.0.1", 0))
        return control.getsockname()[1], public.getsockname()[1]


async def tcp_roundtrip(port, *, timeout=15):
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", port), 1)
            try:
                writer.write(b"pandahome-tcp")
                await writer.drain()
                if await asyncio.wait_for(reader.read(1024), 1) == b"pandahome-tcp":
                    return
            finally:
                writer.close()
                await writer.wait_closed()
        except (OSError, TimeoutError):
            pass
        await asyncio.sleep(0.1)
    raise AssertionError("TCP forwarding did not recover within the smoke timeout")


async def udp_roundtrip(port):
    loop = asyncio.get_running_loop()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.setblocking(False)
        for _ in range(30):
            await loop.sock_sendto(client, b"pandahome-udp", ("127.0.0.1", port))
            try:
                reply, _ = await asyncio.wait_for(loop.sock_recvfrom(client, 1024), 0.5)
                if reply == b"pandahome-udp":
                    return
            except TimeoutError:
                pass
    raise AssertionError("UDP forwarding did not recover within the smoke timeout")


async def stop_child(process):
    if process is not None and process.returncode is None:
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), 3)
        except TimeoutError:
            process.kill()
            await asyncio.wait_for(process.wait(), 3)


@asynccontextmanager
async def echo_services():
    tcp = await asyncio.start_server(tcp_echo, "127.0.0.1", 0)
    udp = None
    try:
        udp, _ = await asyncio.get_running_loop().create_datagram_endpoint(UdpEcho, local_addr=("127.0.0.1", 0))
        yield tcp.sockets[0].getsockname()[1], udp.get_extra_info("sockname")[1]
    finally:
        tcp.close()
        await tcp.wait_closed()
        if udp is not None:
            udp.close()


def report(stage, **results):
    print(json.dumps({"stage": stage, **results}), flush=True)


async def exercise_relay(frpc, frps, directory, local_tcp, local_udp):
    control_port, public_tcp = unused_tcp_ports()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as reservation:
        reservation.bind(("127.0.0.1", 0))
        public_udp = reservation.getsockname()[1]
    token = "smoke-{{literal-token}}-" + os.urandom(16).hex()
    server_config = directory / "frps.toml"
    server_config.write_text(
        f'bindAddr = "127.0.0.1"\nbindPort = {control_port}\nproxyBindAddr = "127.0.0.1"\n'
        f'transport.tls.force = true\nauth.token = {_toml_string(token)}\nlog.to = "console"\nlog.level = "error"\n'
    )
    server_config.chmod(0o600)
    relay = FrpRelay(
        RelayConfig(state_dir=directory, binary=frpc, server_addr="127.0.0.1", server_port=control_port, token=token)
    )
    mappings = [
        RelayMapping(1, "127.0.0.1", local_tcp, public_tcp, "TCP"),
        RelayMapping(2, "127.0.0.1", local_udp, public_udp, "UDP"),
    ]
    server = None

    async def launch_server():
        return await asyncio.create_subprocess_exec(
            frps, "-c", str(server_config), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )

    try:
        server = await launch_server()
        await relay.apply(mappings)
        await verify_native_config(frpc, directory / "frp" / "frpc.toml")
        await check_recovery(relay, mappings, public_tcp, public_udp, launch_server, server)
        # check_recovery stops the first server and owns its replacement.
        report(
            "complete",
            tcp=True,
            udp=True,
            unchanged_pid=True,
            native_reconnect=True,
            crash_recovery=True,
            native_registration=True,
            unrelated_port_rejected=True,
        )
    finally:
        await relay.stop()
        await stop_child(server)
    if (directory / "frp" / "frpc.toml").exists() or relay.status()["running"]:
        raise AssertionError("Relay shutdown did not remove its secret config and child")
    report("cleanup", secret_config_removed=True, process_stopped=True)


async def verify_native_config(frpc, config_path):
    process = await asyncio.create_subprocess_exec(
        frpc, "verify", "-c", str(config_path), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    try:
        if await asyncio.wait_for(process.wait(), 10) != 0:
            raise AssertionError("Native frpc rejected generated configuration")
    finally:
        await stop_child(process)


async def check_recovery(relay, mappings, public_tcp, public_udp, launch_server, first_server):
    first_pid = relay._process.pid
    await tcp_roundtrip(public_tcp)
    await udp_roundtrip(public_udp)
    if await relay.registration() != {1: True, 2: True}:
        raise AssertionError("Native frpc did not report TCP and UDP proxy acceptance")
    await relay.apply(list(reversed(mappings)))
    if relay._process.pid != first_pid:
        raise AssertionError("Unchanged mappings unexpectedly restarted frpc")
    await stop_child(first_server)
    second_server = await launch_server()
    try:
        await tcp_roundtrip(public_tcp, timeout=30)
        await udp_roundtrip(public_udp)
        if relay._process.pid != first_pid:
            raise AssertionError("Native frpc reconnect unexpectedly changed its PID")
        os.kill(first_pid, signal.SIGKILL)
        await asyncio.wait_for(relay._process.wait(), 3)
        if relay.status()["running"]:
            raise AssertionError("Crashed frpc was reported as running")
        await relay.apply(mappings)
        if relay._process.pid == first_pid:
            raise AssertionError("Reconciliation did not restart crashed frpc")
        await tcp_roundtrip(public_tcp)
        await udp_roundtrip(public_udp)
        if await relay.registration() != {1: True, 2: True}:
            raise AssertionError("Native proxy registration did not recover after frpc restart")
        await check_registration_conflict(relay, mappings)
    finally:
        await stop_child(second_server)


async def check_registration_conflict(relay, mappings):
    async def unrelated_service(reader, writer):
        writer.write(b"unrelated-public-service")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    occupied = await asyncio.start_server(unrelated_service, "127.0.0.1", 0)
    public_port = occupied.sockets[0].getsockname()[1]
    collision = RelayMapping(3, mappings[0].local_ip, mappings[0].local_port, public_port, "TCP")
    try:
        await relay.apply([*mappings, collision])
        if await relay.registration() != {1: True, 2: True, 3: False}:
            raise AssertionError("Native registration did not distinguish the occupied public port")
        reader, writer = await asyncio.open_connection("127.0.0.1", public_port)
        try:
            if await asyncio.wait_for(reader.read(1024), 1) != b"unrelated-public-service":
                raise AssertionError("Conflict smoke did not reach its unrelated public service")
        finally:
            writer.close()
            await writer.wait_closed()
    finally:
        occupied.close()
        await occupied.wait_closed()


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin-dir", type=Path, help="Directory containing matching official frpc and frps binaries")
    args = parser.parse_args()
    binaries = [
        str(args.bin_dir.expanduser().resolve() / name) if args.bin_dir else shutil.which(name)
        for name in ("frpc", "frps")
    ]
    if not all(binary and os.access(binary, os.X_OK) for binary in binaries):
        parser.error("Install matching official frpc/frps binaries or supply --bin-dir")
    with tempfile.TemporaryDirectory(prefix="pandahome-frp-smoke-") as temporary:
        async with echo_services() as (local_tcp, local_udp):
            await exercise_relay(*binaries, Path(temporary), local_tcp, local_udp)


if __name__ == "__main__":
    asyncio.run(main())

"""Fixed, dependency-free program executed on an explicitly trusted probe host.

Only JSON arrives on stdin. This module never installs, listens or changes
network configuration. The alarm bounds DNS as well as socket operations.
"""

import datetime
import hashlib
import ipaddress
import json
import platform
import re
import signal
import socket
import sys


def _global(value):
    address = ipaddress.ip_address(value)
    return address.is_global and not address.is_multicast


def probe(payload):
    host, port, nonce = payload["host"], payload["port"], payload["nonce"]
    target = f"[{host}]:{port}" if ":" in host else f"{host}:{port}"
    if (not isinstance(host, str) or not isinstance(port, int) or isinstance(port, bool)
            or not 1 <= port <= 65535 or not re.fullmatch(r"[a-f0-9]{64}", nonce)
            or target not in payload["allowed_targets"]):
        raise ValueError("Invalid probe request")
    result = {
        "version": 1, "nonce": nonce, "target": target,
        "hostname_sha256": hashlib.sha256(platform.node().encode()).hexdigest(),
        "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "success": False, "resolved_ips": [], "peer_ip": None, "peer_port": None, "error": "dns_failed",
    }
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        ips = sorted({str(ipaddress.ip_address(row[4][0])) for row in addresses})
        if not ips or len(ips) > 32 or not all(_global(value) for value in ips):
            result["error"] = "non_global_dns"
            return result
        result["resolved_ips"], result["error"] = ips, "connect_failed"
        for family, kind, protocol, _, address in addresses[:8]:
            try:
                with socket.socket(family, kind, protocol) as connection:
                    connection.settimeout(2)
                    connection.connect(address)
                    peer = connection.getpeername()
                    peer_ip = str(ipaddress.ip_address(peer[0]))
                    if peer_ip not in ips or not _global(peer_ip) or peer[1] != port:
                        result["error"] = "peer_mismatch"
                        return result
                    result.update(success=True, peer_ip=peer_ip, peer_port=peer[1], error=None)
                    return result
            except OSError:
                continue
    except (OSError, ValueError):
        pass
    return result


def main():
    signal.alarm(6)
    try:
        raw = sys.stdin.buffer.readline(4097)
        if len(raw) > 4096:
            return 2
        result = probe(json.loads(raw))
        sys.stdout.write(json.dumps(result, separators=(",", ":")) + "\n")
        sys.stdout.flush()
        return 0
    except (KeyError, TypeError, ValueError, OSError):
        return 2
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    sys.exit(main())

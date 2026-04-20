"""TCP port reachability check tool."""
from __future__ import annotations

import socket
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class TcpCheckParams:
    host: str
    port: int
    timeout: float = 5.0


@dataclass
class TcpCheckResult:
    host: str
    port: int
    reachable: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


def is_available() -> bool:
    """TCP check is always available (uses stdlib only)."""
    return True


def extract_params(data: Dict[str, Any]) -> TcpCheckParams:
    """Extract and validate TCP check parameters from a dict."""
    host = data.get("host")
    if not host:
        raise ValueError("'host' is required for tcp_check")
    port = data.get("port")
    if port is None:
        raise ValueError("'port' is required for tcp_check")
    port = int(port)
    if not (1 <= port <= 65535):
        raise ValueError(f"Invalid port number: {port}")
    timeout = float(data.get("timeout", 5.0))
    return TcpCheckParams(host=host, port=port, timeout=timeout)


def run(params: TcpCheckParams) -> TcpCheckResult:
    """Attempt a TCP connection and return the result."""
    import time

    start = time.monotonic()
    try:
        with socket.create_connection((params.host, params.port), timeout=params.timeout):
            latency_ms = (time.monotonic() - start) * 1000
            return TcpCheckResult(
                host=params.host,
                port=params.port,
                reachable=True,
                latency_ms=round(latency_ms, 3),
            )
    except OSError as exc:
        latency_ms = (time.monotonic() - start) * 1000
        return TcpCheckResult(
            host=params.host,
            port=params.port,
            reachable=False,
            latency_ms=round(latency_ms, 3),
            error=str(exc),
        )

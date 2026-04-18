"""HTTP probe tool for checking endpoint availability and response metrics."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import requests

my_tool_name = "http_probe"
MyToolName = "HttpProbe"


@dataclass
class HttpProbeParams:
    url: str
    method: str = "GET"
    timeout: float = 10.0  # increased from 5.0 - 5s was too aggressive for slow endpoints
    expected_status: int = 200
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class HttpProbeResult:
    url: str
    status_code: int | None
    latency_ms: float
    success: bool
    error: str | None = None


def is_available() -> bool:
    """Check whether requests library is available."""
    try:
        import requests  # noqa: F401
        return True
    except ImportError:
        return False


def extract_params(raw: dict[str, Any]) -> HttpProbeParams:
    """Extract and validate probe parameters from a raw dict."""
    if "url" not in raw:
        raise ValueError("'url' is required for http_probe")
    return HttpProbeParams(
        url=raw["url"],
        method=raw.get("method", "GET").upper(),
        timeout=float(raw.get("timeout", 10.0)),
        expected_status=int(raw.get("expected_status", 200)),
        headers=raw.get("headers", {}),
    )


def run(params: HttpProbeParams) -> HttpProbeResult:
    """Execute the HTTP probe and return a result."""
    start = time.perf_counter()
    try:
        response = requests.request(
            method=params.method,
            url=params.url,
            headers=params.headers,
            timeout=params.timeout,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        success = response.status_code == params.expected_status
        return HttpProbeResult(
            url=params.url,
            status_code=response.status_code,
            latency_ms=round(latency_ms, 2),
            success=success,
        )
    except requests.RequestException as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return HttpProbeResult(
            url=params.url,
            status_code=None,
            latency_ms=round(latency_ms, 2),
            success=False,
            error=str(exc),
        )

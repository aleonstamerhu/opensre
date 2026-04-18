"""DNS lookup tool for opensre."""
from __future__ import annotations

import socket
from typing import Any

from pydantic import BaseModel, Field

my_tool_name = "dns_lookup"


class DnsLookupParams(BaseModel):
    hostname: str = Field(..., description="Hostname to resolve")
    record_type: str = Field(default="A", description="DNS record type (A, AAAA, etc.)")
    timeout: float = Field(default=5.0, description="Lookup timeout in seconds")


class DnsLookupResult(BaseModel):
    hostname: str
    addresses: list[str]
    record_type: str
    success: bool
    error: str | None = None


def is_available() -> bool:
    """DNS lookup is always available via stdlib."""
    return True


def extract_params(data: dict[str, Any]) -> DnsLookupParams:
    """Extract and validate DNS lookup parameters from raw data."""
    return DnsLookupParams(
        hostname=data["hostname"],
        record_type=data.get("record_type", "A"),
        timeout=data.get("timeout", 5.0),
    )


def run(params: DnsLookupParams) -> DnsLookupResult:
    """Perform DNS lookup for the given hostname."""
    socket.setdefaulttimeout(params.timeout)
    try:
        if params.record_type == "AAAA":
            results = socket.getaddrinfo(params.hostname, None, socket.AF_INET6)
            addresses = list({r[4][0] for r in results})
        else:
            results = socket.getaddrinfo(params.hostname, None, socket.AF_INET)
            addresses = list({r[4][0] for r in results})

        return DnsLookupResult(
            hostname=params.hostname,
            addresses=addresses,
            record_type=params.record_type,
            success=True,
        )
    except socket.gaierror as exc:
        return DnsLookupResult(
            hostname=params.hostname,
            addresses=[],
            record_type=params.record_type,
            success=False,
            error=str(exc),
        )
    finally:
        socket.setdefaulttimeout(None)

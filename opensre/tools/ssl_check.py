"""SSL/TLS certificate check tool for opensre.

Verifies SSL certificate validity, expiry, and hostname matching.
"""

import ssl
import socket
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SslCheckParams:
    hostname: str
    port: int = 443
    timeout: float = 10.0
    warn_days: int = 30  # warn if cert expires within this many days


@dataclass
class SslCheckResult:
    hostname: str
    port: int
    valid: bool
    expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None
    issuer: Optional[str] = None
    subject: Optional[str] = None
    error: Optional[str] = None
    warning: bool = False


def is_available() -> bool:
    """SSL check is always available via the stdlib ssl module."""
    return True


def extract_params(data: dict) -> SslCheckParams:
    """Extract and validate SSL check parameters from a dict.

    Args:
        data: Dictionary containing tool parameters.

    Returns:
        SslCheckParams instance.

    Raises:
        ValueError: If required parameters are missing or invalid.
    """
    if "hostname" not in data or not data["hostname"]:
        raise ValueError("'hostname' is required for ssl_check")

    return SslCheckParams(
        hostname=data["hostname"],
        port=int(data.get("port", 443)),
        timeout=float(data.get("timeout", 10.0)),
        warn_days=int(data.get("warn_days", 30)),
    )


def run(params: SslCheckParams) -> SslCheckResult:
    """Perform an SSL certificate check against the given hostname.

    Args:
        params: SslCheckParams with connection details.

    Returns:
        SslCheckResult describing certificate status.
    """
    context = ssl.create_default_context()

    try:
        with socket.create_connection(
            (params.hostname, params.port), timeout=params.timeout
        ) as sock:
            with context.wrap_socket(sock, server_hostname=params.hostname) as ssock:
                cert = ssock.getpeercert()

        # Parse expiry
        not_after_str = cert.get("notAfter", "")
        expires_at = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=timezone.utc
        )
        now = datetime.now(tz=timezone.utc)
        days_remaining = (expires_at - now).days

        # Extract readable issuer / subject
        def _rdn_to_str(rdn_seq) -> str:
            return ", ".join(
                "=".join(pair) for rdn in rdn_seq for pair in rdn
            )

        issuer = _rdn_to_str(cert.get("issuer", []))
        subject = _rdn_to_str(cert.get("subject", []))

        warning = days_remaining <= params.warn_days

        return SslCheckResult(
            hostname=params.hostname,
            port=params.port,
            valid=True,
            expires_at=expires_at,
            days_remaining=days_remaining,
            issuer=issuer,
            subject=subject,
            warning=warning,
        )

    except ssl.SSLCertVerificationError as exc:
        return SslCheckResult(
            hostname=params.hostname,
            port=params.port,
            valid=False,
            error=f"Certificate verification failed: {exc}",
        )
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        return SslCheckResult(
            hostname=params.hostname,
            port=params.port,
            valid=False,
            error=f"Connection error: {exc}",
        )

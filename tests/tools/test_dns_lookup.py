"""Tests for opensre.tools.dns_lookup."""
from unittest.mock import patch

import pytest

from opensre.tools.dns_lookup import (
    DnsLookupParams,
    extract_params,
    is_available,
    run,
)


def test_is_available():
    assert is_available() is True


def test_extract_params_minimal():
    params = extract_params({"hostname": "example.com"})
    assert params.hostname == "example.com"
    assert params.record_type == "A"
    assert params.timeout == 5.0


def test_extract_params_full():
    params = extract_params({"hostname": "example.com", "record_type": "AAAA", "timeout": 2.0})
    assert params.record_type == "AAAA"
    assert params.timeout == 2.0


def test_extract_params_missing_hostname():
    with pytest.raises(Exception):
        extract_params({"record_type": "A"})


# Also verify that an empty dict raises, not just missing hostname with other keys present
def test_extract_params_empty_dict():
    with pytest.raises(Exception):
        extract_params({})


# Verify that an invalid record_type raises an exception
def test_extract_params_invalid_record_type():
    with pytest.raises(Exception):
        extract_params({"hostname": "example.com", "record_type": "INVALID"})


_FAKE_INET = [(None, None, None, None, ("93.184.216.34", 0))]
_FAKE_INET6 = [(None, None, None, None, ("2606:2800:220:1:248:1893:25c8:1946", 0, 0, 0))]


def test_run_success_a_record():
    with patch("opensre.tools.dns_lookup.socket.getaddrinfo", return_value=_FAKE_INET):
        result = run(DnsLookupParams(hostname="example.com"))
    assert result.success is True
    assert "93.184.216.34" in result.addresses
    assert result.error is None


def test_run_success_aaaa_record():
    with patch("opensre.tools.dns_lookup.socket.getaddrinfo", return_value=_FAKE_INET6):
        result = run(DnsLookupParams(hostname="example.com", record_type="AAAA"))
    assert result.success is True
    assert result.record_type == "AAAA"


def test_run_failure():
    import socket as _socket

    with patch(
        "opensre.tools.dns_lookup.socket.getaddrinfo",
        side_effect=_socket.gaierror("Name or service not known"),
    ):
        result = run(DnsLookupParams(hostname="nonexistent.invalid"))
    assert result.success is False
    assert result.addresses == []
    assert result.error is not None


def test_run_timeout_propagated():
    # Ensure that a custom timeout value is accepted without error
    with patch("opensre.tools.dns_lookup.socket.getaddrinfo", return_value=_FAKE_INET):
        result = run(DnsLookupParams(hostname="example.com", timeout=10.0))
    assert result.success is True

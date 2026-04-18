"""Tests for opensre/tools/tcp_check.py."""
from __future__ import annotations

import socket
from unittest.mock import MagicMock, patch

import pytest

from opensre.tools.tcp_check import (
    TcpCheckParams,
    extract_params,
    is_available,
    run,
)


def test_is_available():
    assert is_available() is True


def test_extract_params_minimal():
    params = extract_params({"host": "example.com", "port": 80})
    assert params.host == "example.com"
    assert params.port == 80
    assert params.timeout == 5.0


def test_extract_params_full():
    params = extract_params({"host": "10.0.0.1", "port": "443", "timeout": "2.5"})
    assert params.port == 443
    assert params.timeout == 2.5


def test_extract_params_missing_host():
    with pytest.raises(ValueError, match="'host' is required"):
        extract_params({"port": 80})


def test_extract_params_missing_port():
    with pytest.raises(ValueError, match="'port' is required"):
        extract_params({"host": "example.com"})


def test_extract_params_invalid_port():
    with pytest.raises(ValueError, match="Invalid port"):
        extract_params({"host": "example.com", "port": 99999})


def test_run_success():
    params = TcpCheckParams(host="example.com", port=80)
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=MagicMock())
    mock_cm.__exit__ = MagicMock(return_value=False)
    with patch("opensre.tools.tcp_check.socket.create_connection", return_value=mock_cm):
        result = run(params)
    assert result.reachable is True
    assert result.latency_ms is not None
    assert result.error is None


def test_run_failure():
    params = TcpCheckParams(host="192.0.2.1", port=9999, timeout=1.0)
    with patch(
        "opensre.tools.tcp_check.socket.create_connection",
        side_effect=OSError("Connection refused"),
    ):
        result = run(params)
    assert result.reachable is False
    assert "Connection refused" in result.error
    assert result.latency_ms is not None

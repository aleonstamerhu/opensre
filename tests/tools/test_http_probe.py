"""Tests for the http_probe tool."""

from unittest.mock import MagicMock, patch

import pytest

from opensre.tools.http_probe import (
    HttpProbeParams,
    extract_params,
    is_available,
    run,
)


def test_is_available():
    assert is_available() is True


def test_extract_params_minimal():
    params = extract_params({"url": "https://example.com"})
    assert params.url == "https://example.com"
    assert params.method == "GET"
    assert params.timeout == 5.0
    assert params.expected_status == 200


def test_extract_params_full():
    raw = {
        "url": "https://api.example.com/health",
        "method": "post",
        "timeout": "3",
        "expected_status": "201",
        "headers": {"Authorization": "Bearer token"},
    }
    params = extract_params(raw)
    assert params.method == "POST"
    assert params.timeout == 3.0
    assert params.expected_status == 201
    assert params.headers["Authorization"] == "Bearer token"


def test_extract_params_missing_url():
    with pytest.raises(ValueError, match="'url' is required"):
        extract_params({})


@patch("opensre.tools.http_probe.requests.request")
def test_run_success(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    params = HttpProbeParams(url="https://example.com")
    result = run(params)

    assert result.success is True
    assert result.status_code == 200
    assert result.error is None
    assert result.latency_ms >= 0


@patch("opensre.tools.http_probe.requests.request")
def test_run_unexpected_status(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_request.return_value = mock_response

    params = HttpProbeParams(url="https://example.com", expected_status=200)
    result = run(params)

    assert result.success is False
    assert result.status_code == 500


@patch("opensre.tools.http_probe.requests.request", side_effect=Exception("timeout"))
def test_run_request_exception(mock_request):
    params = HttpProbeParams(url="https://unreachable.example.com")
    result = run(params)

    assert result.success is False
    assert result.status_code is None
    assert "timeout" in result.error


@patch("opensre.tools.http_probe.requests.request")
def test_run_latency_is_positive(mock_request):
    # Sanity check: latency should always be a non-negative number on success
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_request.return_value = mock_response

    params = HttpProbeParams(url="https://example.com")
    result = run(params)

    assert isinstance(result.latency_ms, float)
    assert result.latency_ms >= 0.0

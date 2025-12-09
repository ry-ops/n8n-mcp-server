"""Tests for retry logic with exponential backoff."""

import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import httpx


@pytest.mark.asyncio
async def test_retry_on_500_error(n8n_server, mock_httpx_client):
    """Test that 500 errors are retried with exponential backoff."""
    # First two calls fail with 500, third succeeds
    mock_response_error = MagicMock()
    mock_response_error.status_code = 500
    mock_response_error.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response_error
    )

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = MagicMock()
    mock_response_success.json.return_value = {"data": [{"id": "1", "name": "Test"}]}

    mock_httpx_client.request.side_effect = [
        mock_response_error,
        mock_response_error,
        mock_response_success
    ]

    # Should succeed after retries
    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "3"}):
        result = await n8n_server._list_workflows({})

    assert result == {"data": [{"id": "1", "name": "Test"}]}
    assert mock_httpx_client.request.call_count == 3


@pytest.mark.asyncio
async def test_retry_on_502_error(n8n_server, mock_httpx_client):
    """Test that 502 (Bad Gateway) errors are retried."""
    mock_response_error = MagicMock()
    mock_response_error.status_code = 502
    mock_response_error.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Gateway", request=MagicMock(), response=mock_response_error
    )

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = MagicMock()
    mock_response_success.json.return_value = {"success": True}

    mock_httpx_client.request.side_effect = [
        mock_response_error,
        mock_response_success
    ]

    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "3"}):
        result = await n8n_server._list_workflows({})

    assert result == {"success": True}
    assert mock_httpx_client.request.call_count == 2


@pytest.mark.asyncio
async def test_retry_on_503_error(n8n_server, mock_httpx_client):
    """Test that 503 (Service Unavailable) errors are retried."""
    mock_response_error = MagicMock()
    mock_response_error.status_code = 503
    mock_response_error.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Service unavailable", request=MagicMock(), response=mock_response_error
    )

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = MagicMock()
    mock_response_success.json.return_value = {"success": True}

    mock_httpx_client.request.side_effect = [
        mock_response_error,
        mock_response_success
    ]

    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "3"}):
        result = await n8n_server._list_workflows({})

    assert result == {"success": True}
    assert mock_httpx_client.request.call_count == 2


@pytest.mark.asyncio
async def test_retry_on_504_error(n8n_server, mock_httpx_client):
    """Test that 504 (Gateway Timeout) errors are retried."""
    mock_response_error = MagicMock()
    mock_response_error.status_code = 504
    mock_response_error.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Gateway timeout", request=MagicMock(), response=mock_response_error
    )

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = MagicMock()
    mock_response_success.json.return_value = {"success": True}

    mock_httpx_client.request.side_effect = [
        mock_response_error,
        mock_response_success
    ]

    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "3"}):
        result = await n8n_server._list_workflows({})

    assert result == {"success": True}
    assert mock_httpx_client.request.call_count == 2


@pytest.mark.asyncio
async def test_retry_on_429_with_retry_after_header(n8n_server, mock_httpx_client):
    """Test that 429 (Rate Limit) respects Retry-After header."""
    mock_response_error = MagicMock()
    mock_response_error.status_code = 429
    mock_response_error.headers = {"Retry-After": "0.1"}  # Use small value for testing
    mock_response_error.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Rate limit", request=MagicMock(), response=mock_response_error
    )

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = MagicMock()
    mock_response_success.json.return_value = {"success": True}

    mock_httpx_client.request.side_effect = [
        mock_response_error,
        mock_response_success
    ]

    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "3"}):
        result = await n8n_server._list_workflows({})

    assert result == {"success": True}
    assert mock_httpx_client.request.call_count == 2


@pytest.mark.asyncio
async def test_retry_on_429_without_retry_after_header(n8n_server, mock_httpx_client):
    """Test that 429 (Rate Limit) uses exponential backoff without Retry-After."""
    mock_response_error = MagicMock()
    mock_response_error.status_code = 429
    mock_response_error.headers = {}  # No Retry-After header
    mock_response_error.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Rate limit", request=MagicMock(), response=mock_response_error
    )

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = MagicMock()
    mock_response_success.json.return_value = {"success": True}

    mock_httpx_client.request.side_effect = [
        mock_response_error,
        mock_response_success
    ]

    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "3"}):
        result = await n8n_server._list_workflows({})

    assert result == {"success": True}
    assert mock_httpx_client.request.call_count == 2


@pytest.mark.asyncio
async def test_no_retry_on_400_error(n8n_server, mock_httpx_client):
    """Test that 400 (Bad Request) errors are NOT retried."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad request", request=MagicMock(), response=mock_response
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(Exception):
        await n8n_server._list_workflows({})

    # Should only be called once (no retries)
    assert mock_httpx_client.request.call_count == 1


@pytest.mark.asyncio
async def test_no_retry_on_401_error(n8n_server, mock_httpx_client):
    """Test that 401 (Unauthorized) errors are NOT retried."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Unauthorized", request=MagicMock(), response=mock_response
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(Exception) as exc_info:
        await n8n_server._list_workflows({})

    # Should only be called once (no retries)
    assert mock_httpx_client.request.call_count == 1
    assert str(exc_info.value) == "Authentication failed. Please check your API key."


@pytest.mark.asyncio
async def test_no_retry_on_403_error(n8n_server, mock_httpx_client):
    """Test that 403 (Forbidden) errors are NOT retried."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Forbidden", request=MagicMock(), response=mock_response
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(Exception) as exc_info:
        await n8n_server._list_workflows({})

    # Should only be called once (no retries)
    assert mock_httpx_client.request.call_count == 1
    assert str(exc_info.value) == "Access denied. Insufficient permissions."


@pytest.mark.asyncio
async def test_no_retry_on_404_error(n8n_server, mock_httpx_client):
    """Test that 404 (Not Found) errors are NOT retried."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not found", request=MagicMock(), response=mock_response
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(Exception) as exc_info:
        await n8n_server._get_workflow({"workflow_id": "nonexistent"})

    # Should only be called once (no retries)
    assert mock_httpx_client.request.call_count == 1
    assert str(exc_info.value) == "Resource not found."


@pytest.mark.asyncio
async def test_retry_on_connection_error(n8n_server, mock_httpx_client):
    """Test that connection errors are retried."""
    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = MagicMock()
    mock_response_success.json.return_value = {"data": []}

    # Fail twice with connection error, then succeed
    mock_httpx_client.request.side_effect = [
        httpx.ConnectError("Connection refused"),
        httpx.ConnectError("Connection refused"),
        mock_response_success
    ]

    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "3"}):
        result = await n8n_server._list_workflows({})

    assert result == {"data": []}
    assert mock_httpx_client.request.call_count == 3


@pytest.mark.asyncio
async def test_retry_on_timeout_error(n8n_server, mock_httpx_client):
    """Test that timeout errors are retried."""
    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = MagicMock()
    mock_response_success.json.return_value = {"data": []}

    # Fail once with timeout, then succeed
    mock_httpx_client.request.side_effect = [
        httpx.TimeoutException("Request timeout"),
        mock_response_success
    ]

    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "3"}):
        result = await n8n_server._list_workflows({})

    assert result == {"data": []}
    assert mock_httpx_client.request.call_count == 2


@pytest.mark.asyncio
async def test_max_retries_exceeded(n8n_server, mock_httpx_client):
    """Test that max retries are respected."""
    mock_response_error = MagicMock()
    mock_response_error.status_code = 500
    mock_response_error.headers = {}  # Add headers attribute
    mock_response_error.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response_error
    )

    # Always fail
    mock_httpx_client.request.return_value = mock_response_error

    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "2"}):
        with pytest.raises(Exception) as exc_info:
            await n8n_server._list_workflows({})

    # Should be called 3 times total (initial + 2 retries)
    assert mock_httpx_client.request.call_count == 3
    assert "n8n server error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_configurable_max_retries_via_env(n8n_server, mock_httpx_client):
    """Test that N8N_MAX_RETRIES environment variable is respected."""
    mock_response_error = MagicMock()
    mock_response_error.status_code = 500
    mock_response_error.headers = {}  # Add headers attribute
    mock_response_error.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response_error
    )

    mock_httpx_client.request.return_value = mock_response_error

    # Set max retries to 1
    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "1"}):
        with pytest.raises(Exception):
            await n8n_server._list_workflows({})

    # Should be called 2 times total (initial + 1 retry)
    assert mock_httpx_client.request.call_count == 2


@pytest.mark.asyncio
async def test_exponential_backoff_timing(n8n_server, mock_httpx_client):
    """Test that exponential backoff timing is correct (1s, 2s, 4s)."""
    import time
    from unittest.mock import patch

    mock_response_error = MagicMock()
    mock_response_error.status_code = 500
    mock_response_error.headers = {}  # Add headers attribute
    mock_response_error.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response_error
    )

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = MagicMock()
    mock_response_success.json.return_value = {"success": True}

    # Fail 3 times, then succeed
    mock_httpx_client.request.side_effect = [
        mock_response_error,
        mock_response_error,
        mock_response_error,
        mock_response_success
    ]

    sleep_times = []

    async def mock_sleep(duration):
        sleep_times.append(duration)

    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "3"}):
        with patch("asyncio.sleep", side_effect=mock_sleep):
            result = await n8n_server._list_workflows({})

    # Should have exponential backoff: 1s, 2s, 4s
    assert len(sleep_times) == 3
    assert sleep_times[0] == 1.0  # First retry: 1s
    assert sleep_times[1] == 2.0  # Second retry: 2s
    assert sleep_times[2] == 4.0  # Third retry: 4s


@pytest.mark.asyncio
async def test_max_backoff_cap(n8n_server, mock_httpx_client):
    """Test that backoff is capped at 8 seconds."""
    import time
    from unittest.mock import patch

    mock_response_error = MagicMock()
    mock_response_error.status_code = 500
    mock_response_error.headers = {}  # Add headers attribute
    mock_response_error.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response_error
    )

    mock_httpx_client.request.return_value = mock_response_error

    sleep_times = []

    async def mock_sleep(duration):
        sleep_times.append(duration)

    # Set very high max retries to test backoff cap
    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "5"}):
        with patch("asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(Exception):
                await n8n_server._list_workflows({})

    # Should have exponential backoff but capped at 8s: 1s, 2s, 4s, 8s, 8s
    assert len(sleep_times) == 5
    assert sleep_times[0] == 1.0   # First retry: 1s
    assert sleep_times[1] == 2.0   # Second retry: 2s
    assert sleep_times[2] == 4.0   # Third retry: 4s
    assert sleep_times[3] == 8.0   # Fourth retry: 8s (capped)
    assert sleep_times[4] == 8.0   # Fifth retry: 8s (capped)


@pytest.mark.asyncio
async def test_retry_after_header_capped_at_max_delay(n8n_server, mock_httpx_client):
    """Test that Retry-After header value is capped at max_delay."""
    from unittest.mock import patch

    mock_response_error = MagicMock()
    mock_response_error.status_code = 429
    mock_response_error.headers = {"Retry-After": "100"}  # Very high value
    mock_response_error.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Rate limit", request=MagicMock(), response=mock_response_error
    )

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.raise_for_status = MagicMock()
    mock_response_success.json.return_value = {"success": True}

    mock_httpx_client.request.side_effect = [
        mock_response_error,
        mock_response_success
    ]

    sleep_times = []

    async def mock_sleep(duration):
        sleep_times.append(duration)

    with patch.dict(os.environ, {"N8N_MAX_RETRIES": "3"}):
        with patch("asyncio.sleep", side_effect=mock_sleep):
            result = await n8n_server._list_workflows({})

    # Retry-After of 100s should be capped at 8s
    assert len(sleep_times) == 1
    assert sleep_times[0] == 8.0

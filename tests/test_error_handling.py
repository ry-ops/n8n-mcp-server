"""Tests for error handling."""

import pytest
from unittest.mock import MagicMock
import httpx


@pytest.mark.asyncio
async def test_http_status_error_handling(n8n_server, mock_httpx_client):
    """Test that HTTP status errors are handled properly."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not found", request=MagicMock(), response=mock_response
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(Exception) as exc_info:
        await n8n_server._get_workflow({"workflow_id": "nonexistent"})

    assert "error" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_connection_error_handling(n8n_server, mock_httpx_client):
    """Test that connection errors are handled properly."""
    mock_httpx_client.request.side_effect = httpx.ConnectError("Connection refused")

    with pytest.raises(Exception) as exc_info:
        await n8n_server._list_workflows({})

    assert "error" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_timeout_handling(n8n_server, mock_httpx_client):
    """Test that timeouts are handled properly."""
    mock_httpx_client.request.side_effect = httpx.TimeoutException("Request timeout")

    with pytest.raises(Exception) as exc_info:
        await n8n_server._list_workflows({})

    assert "error" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_401_error_message(n8n_server, mock_httpx_client):
    """Test that 401 errors return proper authentication message."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Unauthorized", request=MagicMock(), response=mock_response
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(Exception) as exc_info:
        await n8n_server._list_workflows({})

    # Should not contain internal error details
    error_msg = str(exc_info.value)
    assert "error" in error_msg.lower()


@pytest.mark.asyncio
async def test_empty_response_handling(n8n_server, mock_httpx_client):
    """Test that empty responses (204) are handled correctly."""
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.content = b""
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._delete_workflow({"workflow_id": "1"})

    assert result == {"success": True}

"""Tests for execution operations."""

import pytest
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_list_executions(n8n_server, mock_httpx_client, sample_execution):
    """Test listing executions."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [sample_execution]}
    mock_response.content = b'{"data": []}'
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._list_executions({})

    assert "data" in result
    assert len(result["data"]) == 1


@pytest.mark.asyncio
async def test_list_executions_with_filters(n8n_server, mock_httpx_client):
    """Test listing executions with filters."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_response.content = b'{"data": []}'
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._list_executions({
        "workflow_id": "1",
        "status": "error",
        "limit": 10
    })

    call_args = mock_httpx_client.request.call_args
    params = call_args[1]["params"]
    assert params["workflowId"] == "1"
    assert params["status"] == "error"
    assert params["limit"] == 10


@pytest.mark.asyncio
async def test_get_execution(n8n_server, mock_httpx_client, sample_execution):
    """Test getting execution details."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_execution
    mock_response.content = b'{"id": "exec-1"}'
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._get_execution({"execution_id": "exec-1"})

    assert result["id"] == "exec-1"
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_delete_execution(n8n_server, mock_httpx_client):
    """Test deleting an execution."""
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.content = b""
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._delete_execution({"execution_id": "exec-1"})

    assert result["success"] is True
    call_args = mock_httpx_client.request.call_args
    assert call_args[1]["method"] == "DELETE"

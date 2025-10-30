"""Tests for workflow operations."""

import pytest
from unittest.mock import MagicMock
import httpx


@pytest.mark.asyncio
async def test_list_workflows(n8n_server, mock_httpx_client, sample_workflow):
    """Test listing workflows."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [sample_workflow]}
    mock_httpx_client.request.return_value = mock_response

    # Call the method
    result = await n8n_server._list_workflows({})

    # Assertions
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["name"] == "Test Workflow"
    mock_httpx_client.request.assert_called_once()


@pytest.mark.asyncio
async def test_list_workflows_active_filter(n8n_server, mock_httpx_client):
    """Test listing workflows with active filter."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._list_workflows({"active": True})

    # Verify params were passed correctly
    call_args = mock_httpx_client.request.call_args
    assert call_args[1]["params"]["active"] == "true"


@pytest.mark.asyncio
async def test_get_workflow(n8n_server, mock_httpx_client, sample_workflow):
    """Test getting a specific workflow."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_workflow
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._get_workflow({"workflow_id": "1"})

    assert result["id"] == "1"
    assert result["name"] == "Test Workflow"


@pytest.mark.asyncio
async def test_create_workflow(n8n_server, mock_httpx_client, sample_workflow):
    """Test creating a workflow."""
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = sample_workflow
    mock_response.content = b'{"id": "1"}'
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._create_workflow({
        "name": "Test Workflow",
        "nodes": [],
        "connections": {}
    })

    assert result["name"] == "Test Workflow"
    mock_httpx_client.request.assert_called_once()


@pytest.mark.asyncio
async def test_activate_workflow(n8n_server, mock_httpx_client):
    """Test activating a workflow."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"active": True}
    mock_response.content = b'{"active": true}'
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._activate_workflow({"workflow_id": "1"})

    # Verify PATCH request with active: True
    call_args = mock_httpx_client.request.call_args
    assert call_args[1]["method"] == "PATCH"
    assert call_args[1]["json"]["active"] is True


@pytest.mark.asyncio
async def test_deactivate_workflow(n8n_server, mock_httpx_client):
    """Test deactivating a workflow."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"active": False}
    mock_response.content = b'{"active": false}'
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._deactivate_workflow({"workflow_id": "1"})

    # Verify PATCH request with active: False
    call_args = mock_httpx_client.request.call_args
    assert call_args[1]["method"] == "PATCH"
    assert call_args[1]["json"]["active"] is False


@pytest.mark.asyncio
async def test_delete_workflow(n8n_server, mock_httpx_client):
    """Test deleting a workflow."""
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.content = b""
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._delete_workflow({"workflow_id": "1"})

    assert result["success"] is True


@pytest.mark.asyncio
async def test_update_workflow(n8n_server, mock_httpx_client, sample_workflow):
    """Test updating a workflow."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_workflow
    mock_response.content = b'{"id": "1"}'
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._update_workflow({
        "workflow_id": "1",
        "name": "Updated Workflow"
    })

    assert result["name"] == "Test Workflow"
    call_args = mock_httpx_client.request.call_args
    assert call_args[1]["method"] == "PATCH"


@pytest.mark.asyncio
async def test_execute_workflow(n8n_server, mock_httpx_client):
    """Test executing a workflow."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"executionId": "exec-1"}
    mock_response.content = b'{"executionId": "exec-1"}'
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._execute_workflow({
        "workflow_id": "1",
        "data": {"input": "test"}
    })

    assert "executionId" in result
    call_args = mock_httpx_client.request.call_args
    assert call_args[1]["method"] == "POST"

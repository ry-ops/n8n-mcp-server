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


# Enhanced filtering tests
@pytest.mark.asyncio
async def test_list_workflows_filter_by_name(n8n_server, mock_httpx_client):
    """Test filtering workflows by name (case-insensitive substring match)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "1", "name": "Email Campaign", "active": True, "tags": []},
            {"id": "2", "name": "Data Sync", "active": True, "tags": []},
            {"id": "3", "name": "Email Notification", "active": False, "tags": []},
        ]
    }
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._list_workflows({"name": "email"})

    assert len(result["data"]) == 2
    assert all("email" in w["name"].lower() for w in result["data"])
    assert result["data"][0]["name"] == "Email Campaign"
    assert result["data"][1]["name"] == "Email Notification"


@pytest.mark.asyncio
async def test_list_workflows_filter_by_tags_single(n8n_server, mock_httpx_client):
    """Test filtering workflows by single tag."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "1", "name": "Workflow 1", "active": True, "tags": ["production"]},
            {"id": "2", "name": "Workflow 2", "active": True, "tags": ["development"]},
            {"id": "3", "name": "Workflow 3", "active": True, "tags": ["production", "critical"]},
        ]
    }
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._list_workflows({"tags": "production"})

    assert len(result["data"]) == 2
    assert result["data"][0]["id"] == "1"
    assert result["data"][1]["id"] == "3"


@pytest.mark.asyncio
async def test_list_workflows_filter_by_tags_multiple(n8n_server, mock_httpx_client):
    """Test filtering workflows by multiple tags (must have all)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "1", "name": "Workflow 1", "active": True, "tags": ["production"]},
            {"id": "2", "name": "Workflow 2", "active": True, "tags": ["production", "critical"]},
            {"id": "3", "name": "Workflow 3", "active": True, "tags": ["production", "critical", "email"]},
        ]
    }
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._list_workflows({"tags": "production, critical"})

    assert len(result["data"]) == 2
    assert result["data"][0]["id"] == "2"
    assert result["data"][1]["id"] == "3"


@pytest.mark.asyncio
async def test_list_workflows_filter_by_created_after(n8n_server, mock_httpx_client):
    """Test filtering workflows by creation date."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "1", "name": "Old Workflow", "active": True, "createdAt": "2024-01-01T10:00:00.000Z"},
            {"id": "2", "name": "Recent Workflow", "active": True, "createdAt": "2024-12-01T10:00:00.000Z"},
            {"id": "3", "name": "New Workflow", "active": True, "createdAt": "2024-12-05T10:00:00.000Z"},
        ]
    }
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._list_workflows({"created_after": "2024-11-01"})

    assert len(result["data"]) == 2
    assert result["data"][0]["id"] == "2"
    assert result["data"][1]["id"] == "3"


@pytest.mark.asyncio
async def test_list_workflows_filter_by_updated_after(n8n_server, mock_httpx_client):
    """Test filtering workflows by update date."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "1", "name": "Stale Workflow", "active": True, "updatedAt": "2024-01-01T10:00:00.000Z"},
            {"id": "2", "name": "Updated Workflow", "active": True, "updatedAt": "2024-12-01T10:00:00.000Z"},
            {"id": "3", "name": "Fresh Workflow", "active": True, "updatedAt": "2024-12-07T10:00:00.000Z"},
        ]
    }
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._list_workflows({"updated_after": "2024-12-01T00:00:00Z"})

    assert len(result["data"]) == 2
    assert result["data"][0]["id"] == "2"
    assert result["data"][1]["id"] == "3"


@pytest.mark.asyncio
async def test_list_workflows_combined_filters(n8n_server, mock_httpx_client):
    """Test combining multiple filters."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "id": "1",
                "name": "Email Campaign",
                "active": True,
                "tags": ["production"],
                "createdAt": "2024-12-01T10:00:00.000Z",
                "updatedAt": "2024-12-05T10:00:00.000Z"
            },
            {
                "id": "2",
                "name": "Email Notification",
                "active": False,
                "tags": ["development"],
                "createdAt": "2024-11-01T10:00:00.000Z",
                "updatedAt": "2024-12-03T10:00:00.000Z"
            },
            {
                "id": "3",
                "name": "Email Alert",
                "active": True,
                "tags": ["production"],
                "createdAt": "2024-12-03T10:00:00.000Z",
                "updatedAt": "2024-12-06T10:00:00.000Z"
            },
        ]
    }
    mock_httpx_client.request.return_value = mock_response

    # Filter: name contains "email", tags include "production", created after Dec 1
    result = await n8n_server._list_workflows({
        "name": "email",
        "tags": "production",
        "created_after": "2024-12-01"
    })

    # Should only match workflow 1 and 3
    assert len(result["data"]) == 2
    assert result["data"][0]["id"] == "1"
    assert result["data"][1]["id"] == "3"


@pytest.mark.asyncio
async def test_list_workflows_filter_no_matches(n8n_server, mock_httpx_client):
    """Test filtering with no matches."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "1", "name": "Workflow 1", "active": True, "tags": ["production"]},
            {"id": "2", "name": "Workflow 2", "active": True, "tags": ["development"]},
        ]
    }
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._list_workflows({"name": "nonexistent"})

    assert len(result["data"]) == 0


@pytest.mark.asyncio
async def test_list_workflows_invalid_date_format(n8n_server, mock_httpx_client):
    """Test filtering with invalid date format."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ValueError, match="Invalid created_after date format"):
        await n8n_server._list_workflows({"created_after": "invalid-date"})


@pytest.mark.asyncio
async def test_parse_date_iso8601_formats(n8n_server):
    """Test parsing various ISO 8601 date formats."""
    from datetime import datetime

    # Test YYYY-MM-DD format
    date1 = n8n_server._parse_date("2024-12-08")
    assert date1 == datetime(2024, 12, 8, 0, 0, 0)

    # Test YYYY-MM-DDTHH:MM:SSZ format
    date2 = n8n_server._parse_date("2024-12-08T15:30:45Z")
    assert date2 == datetime(2024, 12, 8, 15, 30, 45)

    # Test YYYY-MM-DDTHH:MM:SS.fffZ format
    date3 = n8n_server._parse_date("2024-12-08T15:30:45.123Z")
    assert date3 == datetime(2024, 12, 8, 15, 30, 45, 123000)


@pytest.mark.asyncio
async def test_list_workflows_case_insensitive_tag_matching(n8n_server, mock_httpx_client):
    """Test that tag filtering is case-insensitive."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "1", "name": "Workflow 1", "active": True, "tags": ["Production"]},
            {"id": "2", "name": "Workflow 2", "active": True, "tags": ["PRODUCTION"]},
            {"id": "3", "name": "Workflow 3", "active": True, "tags": ["development"]},
        ]
    }
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._list_workflows({"tags": "production"})

    assert len(result["data"]) == 2
    assert result["data"][0]["id"] == "1"
    assert result["data"][1]["id"] == "2"

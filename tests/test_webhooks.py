"""Tests for webhook management operations."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def sample_webhook_workflow():
    """Sample workflow with webhook node for testing."""
    return {
        "id": "webhook-workflow-1",
        "name": "Test Webhook Workflow",
        "active": True,
        "nodes": [
            {
                "id": "webhook-node-1",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "parameters": {
                    "path": "test-webhook",
                    "httpMethod": "POST",
                    "responseMode": "lastNode",
                    "responseData": "firstEntryJson",
                    "authentication": "basicAuth",
                    "allowedOrigins": "https://example.com",
                    "responseCode": 200,
                    "responseHeaders": {},
                    "ipWhitelist": "192.168.1.0/24"
                },
                "position": [250, 300]
            },
            {
                "id": "set-node-1",
                "name": "Set",
                "type": "n8n-nodes-base.set",
                "parameters": {},
                "position": [450, 300]
            }
        ],
        "connections": {},
        "tags": ["webhook", "test"]
    }


@pytest.fixture
def sample_non_webhook_workflow():
    """Sample workflow without webhook nodes for testing."""
    return {
        "id": "regular-workflow-1",
        "name": "Regular Workflow",
        "active": True,
        "nodes": [
            {
                "id": "schedule-node-1",
                "name": "Schedule",
                "type": "n8n-nodes-base.scheduleTrigger",
                "parameters": {},
                "position": [250, 300]
            }
        ],
        "connections": {},
        "tags": ["scheduled"]
    }


@pytest.mark.asyncio
async def test_list_webhooks(n8n_server, mock_httpx_client, sample_webhook_workflow, sample_non_webhook_workflow):
    """Test listing all webhook endpoints."""
    # Setup mock responses
    workflows_list_response = MagicMock()
    workflows_list_response.status_code = 200
    workflows_list_response.json.return_value = {
        "data": [
            {"id": "webhook-workflow-1", "name": "Test Webhook Workflow", "active": True},
            {"id": "regular-workflow-1", "name": "Regular Workflow", "active": True}
        ]
    }

    workflow_detail_response_1 = MagicMock()
    workflow_detail_response_1.status_code = 200
    workflow_detail_response_1.json.return_value = sample_webhook_workflow

    workflow_detail_response_2 = MagicMock()
    workflow_detail_response_2.status_code = 200
    workflow_detail_response_2.json.return_value = sample_non_webhook_workflow

    # Set up sequential responses
    mock_httpx_client.request.side_effect = [
        workflows_list_response,
        workflow_detail_response_1,
        workflow_detail_response_2
    ]

    # Call the method
    result = await n8n_server._list_webhooks({})

    # Assertions
    assert "webhooks" in result
    assert "total_count" in result
    assert result["total_count"] == 1  # Only one webhook workflow
    assert len(result["webhooks"]) == 1

    webhook = result["webhooks"][0]
    assert webhook["workflow_id"] == "webhook-workflow-1"
    assert webhook["workflow_name"] == "Test Webhook Workflow"
    assert webhook["workflow_active"] is True
    assert webhook["node_name"] == "Webhook"
    assert webhook["webhook_path"] == "test-webhook"
    assert webhook["http_method"] == "POST"
    assert webhook["response_mode"] == "lastNode"
    assert webhook["authentication"] == "basicAuth"


@pytest.mark.asyncio
async def test_list_webhooks_active_filter(n8n_server, mock_httpx_client):
    """Test listing webhooks with active filter."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._list_webhooks({"active": True})

    # Verify params were passed correctly
    call_args = mock_httpx_client.request.call_args
    assert call_args[1]["params"]["active"] == "true"


@pytest.mark.asyncio
async def test_list_webhooks_no_webhooks_found(n8n_server, mock_httpx_client, sample_non_webhook_workflow):
    """Test listing webhooks when no webhook workflows exist."""
    workflows_list_response = MagicMock()
    workflows_list_response.status_code = 200
    workflows_list_response.json.return_value = {
        "data": [{"id": "regular-workflow-1", "name": "Regular Workflow", "active": True}]
    }

    workflow_detail_response = MagicMock()
    workflow_detail_response.status_code = 200
    workflow_detail_response.json.return_value = sample_non_webhook_workflow

    mock_httpx_client.request.side_effect = [workflows_list_response, workflow_detail_response]

    result = await n8n_server._list_webhooks({})

    assert result["total_count"] == 0
    assert len(result["webhooks"]) == 0


@pytest.mark.asyncio
async def test_get_webhook(n8n_server, mock_httpx_client, sample_webhook_workflow):
    """Test getting detailed webhook information."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_webhook_workflow
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._get_webhook({"workflow_id": "webhook-workflow-1"})

    # Assertions
    assert result["workflow_id"] == "webhook-workflow-1"
    assert result["workflow_name"] == "Test Webhook Workflow"
    assert result["workflow_active"] is True
    assert result["total_webhook_nodes"] == 1

    webhook_node = result["webhook_nodes"][0]
    assert webhook_node["node_name"] == "Webhook"
    assert webhook_node["node_id"] == "webhook-node-1"
    assert webhook_node["webhook_path"] == "test-webhook"
    assert webhook_node["http_method"] == "POST"
    assert webhook_node["response_mode"] == "lastNode"
    assert webhook_node["response_data"] == "firstEntryJson"
    assert webhook_node["authentication"] == "basicAuth"
    assert webhook_node["allowed_origins"] == "https://example.com"
    assert webhook_node["response_code"] == 200
    assert webhook_node["ip_whitelist"] == "192.168.1.0/24"


@pytest.mark.asyncio
async def test_get_webhook_no_webhook_nodes(n8n_server, mock_httpx_client, sample_non_webhook_workflow):
    """Test getting webhook info from workflow without webhook nodes."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_non_webhook_workflow
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ValueError, match="No webhook nodes found"):
        await n8n_server._get_webhook({"workflow_id": "regular-workflow-1"})


@pytest.mark.asyncio
async def test_get_webhook_validates_id(n8n_server):
    """Test that get_webhook validates workflow ID."""
    with pytest.raises(ValueError, match="invalid characters|invalid path"):
        await n8n_server._get_webhook({"workflow_id": "../../../etc/passwd"})


@pytest.mark.asyncio
async def test_test_webhook(n8n_server, mock_httpx_client, sample_webhook_workflow):
    """Test webhook execution."""
    # Mock workflow details response
    workflow_response = MagicMock()
    workflow_response.status_code = 200
    workflow_response.json.return_value = sample_webhook_workflow

    # Mock execution response
    execution_response = MagicMock()
    execution_response.status_code = 200
    execution_response.json.return_value = {
        "executionId": "exec-123",
        "status": "success"
    }
    execution_response.content = b'{"executionId": "exec-123"}'

    # Set up sequential responses
    mock_httpx_client.request.side_effect = [workflow_response, execution_response]

    result = await n8n_server._test_webhook({
        "workflow_id": "webhook-workflow-1",
        "data": {"test": "data"}
    })

    # Assertions
    assert result["workflow_id"] == "webhook-workflow-1"
    assert result["workflow_name"] == "Test Webhook Workflow"
    assert result["test_result"] == "success"
    assert "execution" in result
    assert result["execution"]["executionId"] == "exec-123"


@pytest.mark.asyncio
async def test_test_webhook_without_data(n8n_server, mock_httpx_client, sample_webhook_workflow):
    """Test webhook execution without test data."""
    workflow_response = MagicMock()
    workflow_response.status_code = 200
    workflow_response.json.return_value = sample_webhook_workflow

    execution_response = MagicMock()
    execution_response.status_code = 200
    execution_response.json.return_value = {"executionId": "exec-124"}
    execution_response.content = b'{"executionId": "exec-124"}'

    mock_httpx_client.request.side_effect = [workflow_response, execution_response]

    result = await n8n_server._test_webhook({"workflow_id": "webhook-workflow-1"})

    assert result["test_result"] == "success"
    # Verify empty data was passed
    call_args = list(mock_httpx_client.request.call_args_list)[1]
    assert call_args[1]["json"] == {}


@pytest.mark.asyncio
async def test_test_webhook_non_webhook_workflow(n8n_server, mock_httpx_client, sample_non_webhook_workflow):
    """Test that testing a non-webhook workflow raises error."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_non_webhook_workflow
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ValueError, match="does not contain any webhook nodes"):
        await n8n_server._test_webhook({"workflow_id": "regular-workflow-1"})


@pytest.mark.asyncio
async def test_test_webhook_validates_id(n8n_server):
    """Test that test_webhook validates workflow ID."""
    with pytest.raises(ValueError, match="invalid characters|invalid path"):
        await n8n_server._test_webhook({"workflow_id": "../admin"})


@pytest.mark.asyncio
async def test_list_webhooks_multiple_webhooks_in_workflow(n8n_server, mock_httpx_client):
    """Test workflow with multiple webhook nodes."""
    multi_webhook_workflow = {
        "id": "multi-webhook-1",
        "name": "Multi Webhook Workflow",
        "active": True,
        "nodes": [
            {
                "id": "webhook-1",
                "name": "Webhook 1",
                "type": "n8n-nodes-base.webhook",
                "parameters": {"path": "webhook-1", "httpMethod": "GET"}
            },
            {
                "id": "webhook-2",
                "name": "Webhook 2",
                "type": "n8n-nodes-base.webhook",
                "parameters": {"path": "webhook-2", "httpMethod": "POST"}
            }
        ],
        "connections": {}
    }

    workflows_list_response = MagicMock()
    workflows_list_response.status_code = 200
    workflows_list_response.json.return_value = {
        "data": [{"id": "multi-webhook-1", "name": "Multi Webhook Workflow", "active": True}]
    }

    workflow_detail_response = MagicMock()
    workflow_detail_response.status_code = 200
    workflow_detail_response.json.return_value = multi_webhook_workflow

    mock_httpx_client.request.side_effect = [workflows_list_response, workflow_detail_response]

    result = await n8n_server._list_webhooks({})

    assert result["total_count"] == 2
    assert len(result["webhooks"]) == 2
    assert result["webhooks"][0]["webhook_path"] == "webhook-1"
    assert result["webhooks"][1]["webhook_path"] == "webhook-2"


@pytest.mark.asyncio
async def test_get_webhook_multiple_nodes(n8n_server, mock_httpx_client):
    """Test getting webhook with multiple webhook nodes."""
    multi_webhook_workflow = {
        "id": "multi-webhook-1",
        "name": "Multi Webhook Workflow",
        "active": True,
        "nodes": [
            {
                "id": "webhook-1",
                "name": "Webhook 1",
                "type": "n8n-nodes-base.webhook",
                "parameters": {"path": "webhook-1", "httpMethod": "GET"}
            },
            {
                "id": "webhook-2",
                "name": "Webhook 2",
                "type": "n8n-nodes-base.webhook",
                "parameters": {"path": "webhook-2", "httpMethod": "POST"}
            }
        ],
        "connections": {}
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = multi_webhook_workflow
    mock_httpx_client.request.return_value = mock_response

    result = await n8n_server._get_webhook({"workflow_id": "multi-webhook-1"})

    assert result["total_webhook_nodes"] == 2
    assert len(result["webhook_nodes"]) == 2

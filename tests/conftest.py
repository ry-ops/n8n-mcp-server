"""Pytest configuration and fixtures."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from n8n_mcp_server import N8nMCPServer


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    return mock_client


@pytest.fixture
def n8n_server(mock_httpx_client):
    """Create N8nMCPServer instance with mocked client."""
    server = N8nMCPServer(
        n8n_url="http://localhost:5678",
        api_key="fake-test-key-not-real-n8n-12345"  # Not a real API key - for testing only
    )
    server.client = mock_httpx_client
    return server


@pytest.fixture
def sample_workflow():
    """Sample workflow data for testing."""
    return {
        "id": "1",
        "name": "Test Workflow",
        "active": True,
        "nodes": [],
        "connections": {},
        "tags": ["test"]
    }


@pytest.fixture
def sample_execution():
    """Sample execution data for testing."""
    return {
        "id": "exec-1",
        "workflowId": "1",
        "status": "success",
        "startedAt": "2025-10-05T10:00:00.000Z",
        "finishedAt": "2025-10-05T10:00:05.000Z"
    }

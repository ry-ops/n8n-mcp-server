"""
Comprehensive tests for execution operations.
Tests list_executions, get_execution, and delete_execution functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
import httpx


class TestListExecutions:
    """Test suite for listing executions."""

    @pytest.mark.asyncio
    async def test_list_executions_basic(self, n8n_server, mock_httpx_client, sample_execution):
        """Test listing executions without filters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [sample_execution]}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({})

        assert "data" in result
        assert len(result["data"]) == 1
        assert result["data"][0]["id"] == "exec-1"
        assert result["data"][0]["status"] == "success"
        mock_httpx_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_executions_with_workflow_filter(self, n8n_server, mock_httpx_client):
        """Test listing executions filtered by workflow ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({"workflow_id": "1"})

        call_args = mock_httpx_client.request.call_args
        params = call_args[1]["params"]
        assert params["workflowId"] == "1"
        assert "data" in result

    @pytest.mark.asyncio
    async def test_list_executions_with_status_filter(self, n8n_server, mock_httpx_client):
        """Test listing executions filtered by status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({"status": "error"})

        call_args = mock_httpx_client.request.call_args
        params = call_args[1]["params"]
        assert params["status"] == "error"

    @pytest.mark.asyncio
    async def test_list_executions_with_limit(self, n8n_server, mock_httpx_client):
        """Test listing executions with limit parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({"limit": 10})

        call_args = mock_httpx_client.request.call_args
        params = call_args[1]["params"]
        assert params["limit"] == 10

    @pytest.mark.asyncio
    async def test_list_executions_with_all_filters(self, n8n_server, mock_httpx_client):
        """Test listing executions with all filters combined."""
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
    async def test_list_executions_success_status(self, n8n_server, mock_httpx_client, sample_execution):
        """Test listing executions with success status filter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [sample_execution]}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({"status": "success"})

        call_args = mock_httpx_client.request.call_args
        params = call_args[1]["params"]
        assert params["status"] == "success"
        assert result["data"][0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_list_executions_running_status(self, n8n_server, mock_httpx_client):
        """Test listing executions with running status filter."""
        running_execution = {
            "id": "exec-2",
            "workflowId": "1",
            "status": "running",
            "startedAt": "2025-10-05T10:00:00.000Z"
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [running_execution]}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({"status": "running"})

        call_args = mock_httpx_client.request.call_args
        params = call_args[1]["params"]
        assert params["status"] == "running"

    @pytest.mark.asyncio
    async def test_list_executions_waiting_status(self, n8n_server, mock_httpx_client):
        """Test listing executions with waiting status filter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({"status": "waiting"})

        call_args = mock_httpx_client.request.call_args
        params = call_args[1]["params"]
        assert params["status"] == "waiting"

    @pytest.mark.asyncio
    async def test_list_executions_empty_result(self, n8n_server, mock_httpx_client):
        """Test listing executions when no results are returned."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({})

        assert "data" in result
        assert len(result["data"]) == 0

    @pytest.mark.asyncio
    async def test_list_executions_multiple_results(self, n8n_server, mock_httpx_client):
        """Test listing executions with multiple results."""
        executions = [
            {
                "id": "exec-1",
                "workflowId": "1",
                "status": "success",
                "startedAt": "2025-10-05T10:00:00.000Z",
                "finishedAt": "2025-10-05T10:00:05.000Z"
            },
            {
                "id": "exec-2",
                "workflowId": "1",
                "status": "error",
                "startedAt": "2025-10-05T10:05:00.000Z",
                "finishedAt": "2025-10-05T10:05:02.000Z"
            },
            {
                "id": "exec-3",
                "workflowId": "2",
                "status": "success",
                "startedAt": "2025-10-05T10:10:00.000Z",
                "finishedAt": "2025-10-05T10:10:10.000Z"
            }
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": executions}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({})

        assert "data" in result
        assert len(result["data"]) == 3


class TestGetExecution:
    """Test suite for getting execution details."""

    @pytest.mark.asyncio
    async def test_get_execution_basic(self, n8n_server, mock_httpx_client, sample_execution):
        """Test getting execution details with valid ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_execution
        mock_response.content = b'{"id": "exec-1"}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._get_execution({"execution_id": "exec-1"})

        assert result["id"] == "exec-1"
        assert result["status"] == "success"
        assert result["workflowId"] == "1"
        mock_httpx_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_execution_with_data(self, n8n_server, mock_httpx_client):
        """Test getting execution with full execution data."""
        execution_with_data = {
            "id": "exec-1",
            "workflowId": "1",
            "status": "success",
            "startedAt": "2025-10-05T10:00:00.000Z",
            "finishedAt": "2025-10-05T10:00:05.000Z",
            "data": {
                "resultData": {
                    "runData": {
                        "Start": [
                            {
                                "startTime": 1696502400000,
                                "executionTime": 5000,
                                "data": {"main": [[{"json": {"result": "success"}}]]}
                            }
                        ]
                    }
                }
            }
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = execution_with_data
        mock_response.content = b'{"id": "exec-1"}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._get_execution({"execution_id": "exec-1"})

        assert result["id"] == "exec-1"
        assert "data" in result
        assert "resultData" in result["data"]

    @pytest.mark.asyncio
    async def test_get_execution_error_status(self, n8n_server, mock_httpx_client):
        """Test getting execution with error status."""
        error_execution = {
            "id": "exec-2",
            "workflowId": "1",
            "status": "error",
            "startedAt": "2025-10-05T10:00:00.000Z",
            "finishedAt": "2025-10-05T10:00:01.000Z",
            "data": {
                "resultData": {
                    "error": {
                        "message": "Node execution failed"
                    }
                }
            }
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = error_execution
        mock_response.content = b'{"id": "exec-2"}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._get_execution({"execution_id": "exec-2"})

        assert result["id"] == "exec-2"
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_get_execution_alphanumeric_id(self, n8n_server, mock_httpx_client, sample_execution):
        """Test getting execution with alphanumeric ID."""
        sample_execution["id"] = "exec-abc-123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_execution
        mock_response.content = b'{"id": "exec-abc-123"}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._get_execution({"execution_id": "exec-abc-123"})

        assert result["id"] == "exec-abc-123"

    @pytest.mark.asyncio
    async def test_get_execution_with_hyphen(self, n8n_server, mock_httpx_client, sample_execution):
        """Test getting execution with hyphenated ID."""
        sample_execution["id"] = "exec-test-123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_execution
        mock_response.content = b'{"id": "exec-test-123"}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._get_execution({"execution_id": "exec-test-123"})

        assert result["id"] == "exec-test-123"
        call_args = mock_httpx_client.request.call_args
        assert "/executions/exec-test-123" in call_args[1]["url"]

    @pytest.mark.asyncio
    async def test_get_execution_with_underscore(self, n8n_server, mock_httpx_client, sample_execution):
        """Test getting execution with underscore in ID."""
        sample_execution["id"] = "exec_test_123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_execution
        mock_response.content = b'{"id": "exec_test_123"}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._get_execution({"execution_id": "exec_test_123"})

        assert result["id"] == "exec_test_123"


class TestDeleteExecution:
    """Test suite for deleting executions."""

    @pytest.mark.asyncio
    async def test_delete_execution_basic(self, n8n_server, mock_httpx_client):
        """Test deleting an execution successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._delete_execution({"execution_id": "exec-1"})

        assert result["success"] is True
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "DELETE"
        assert "/executions/exec-1" in call_args[1]["url"]
        mock_httpx_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_execution_alphanumeric_id(self, n8n_server, mock_httpx_client):
        """Test deleting execution with alphanumeric ID."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._delete_execution({"execution_id": "exec-abc-123"})

        assert result["success"] is True
        call_args = mock_httpx_client.request.call_args
        assert "/executions/exec-abc-123" in call_args[1]["url"]

    @pytest.mark.asyncio
    async def test_delete_execution_numeric_id(self, n8n_server, mock_httpx_client):
        """Test deleting execution with numeric ID."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._delete_execution({"execution_id": "12345"})

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_execution_uses_delete_method(self, n8n_server, mock_httpx_client):
        """Test that delete execution uses DELETE HTTP method."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_httpx_client.request.return_value = mock_response

        await n8n_server._delete_execution({"execution_id": "exec-1"})

        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["method"] == "DELETE"

    @pytest.mark.asyncio
    async def test_delete_execution_correct_endpoint(self, n8n_server, mock_httpx_client):
        """Test that delete execution uses correct endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_httpx_client.request.return_value = mock_response

        await n8n_server._delete_execution({"execution_id": "exec-1"})

        call_args = mock_httpx_client.request.call_args
        url = call_args[1]["url"]
        assert url.endswith("/api/v1/executions/exec-1")


class TestExecutionValidation:
    """Test suite for execution ID validation."""

    @pytest.mark.asyncio
    async def test_get_execution_empty_id_rejected(self, n8n_server):
        """Test that empty execution ID is rejected."""
        with pytest.raises(ValueError, match="is required|cannot be empty"):
            await n8n_server._get_execution({"execution_id": ""})

    @pytest.mark.asyncio
    async def test_get_execution_none_id_rejected(self, n8n_server):
        """Test that None execution ID is rejected."""
        with pytest.raises(ValueError, match="is required"):
            await n8n_server._get_execution({"execution_id": None})

    @pytest.mark.asyncio
    async def test_get_execution_whitespace_id_rejected(self, n8n_server):
        """Test that whitespace-only execution ID is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await n8n_server._get_execution({"execution_id": "   "})

    @pytest.mark.asyncio
    async def test_get_execution_path_traversal_blocked(self, n8n_server):
        """Test that path traversal in execution ID is blocked."""
        malicious_ids = [
            "../workflows/1/delete",
            "../../admin",
            "../../../root",
            "exec/../other"
        ]

        for malicious_id in malicious_ids:
            with pytest.raises(ValueError, match="invalid characters|invalid path"):
                await n8n_server._get_execution({"execution_id": malicious_id})

    @pytest.mark.asyncio
    async def test_get_execution_slash_rejected(self, n8n_server):
        """Test that forward slash in execution ID is rejected."""
        with pytest.raises(ValueError, match="invalid characters|invalid path"):
            await n8n_server._get_execution({"execution_id": "exec/123"})

    @pytest.mark.asyncio
    async def test_get_execution_backslash_rejected(self, n8n_server):
        """Test that backslash in execution ID is rejected."""
        with pytest.raises(ValueError, match="invalid characters"):
            await n8n_server._get_execution({"execution_id": "exec\\123"})

    @pytest.mark.asyncio
    async def test_get_execution_special_chars_rejected(self, n8n_server):
        """Test that special characters in execution ID are rejected."""
        invalid_ids = [
            "exec;DROP TABLE",
            "exec|rm -rf",
            "<script>alert('xss')</script>",
            "exec with spaces",
            "exec@123",
            "exec#123",
            "exec$123",
            "exec%123"
        ]

        for invalid_id in invalid_ids:
            with pytest.raises(ValueError, match="invalid characters"):
                await n8n_server._get_execution({"execution_id": invalid_id})

    @pytest.mark.asyncio
    async def test_get_execution_too_long_rejected(self, n8n_server):
        """Test that overly long execution ID is rejected."""
        too_long = "a" * 101

        with pytest.raises(ValueError, match="too long"):
            await n8n_server._get_execution({"execution_id": too_long})

    @pytest.mark.asyncio
    async def test_delete_execution_empty_id_rejected(self, n8n_server):
        """Test that empty execution ID is rejected for delete."""
        with pytest.raises(ValueError, match="is required|cannot be empty"):
            await n8n_server._delete_execution({"execution_id": ""})

    @pytest.mark.asyncio
    async def test_delete_execution_path_traversal_blocked(self, n8n_server):
        """Test that path traversal in execution ID is blocked for delete."""
        with pytest.raises(ValueError, match="invalid characters|invalid path"):
            await n8n_server._delete_execution({"execution_id": "../admin"})


class TestExecutionErrorHandling:
    """Test suite for execution error handling."""

    @pytest.mark.asyncio
    async def test_get_execution_not_found(self, n8n_server):
        """Test getting non-existent execution."""
        async with n8n_server:
            with patch.object(n8n_server.client, 'request') as mock_request:
                mock_response = MagicMock()
                mock_response.status_code = 404
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Not Found",
                    request=MagicMock(),
                    response=mock_response
                )
                mock_request.return_value = mock_response

                with pytest.raises(Exception) as exc_info:
                    await n8n_server._get_execution({"execution_id": "nonexistent"})

                assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_execution_not_found(self, n8n_server):
        """Test deleting non-existent execution."""
        async with n8n_server:
            with patch.object(n8n_server.client, 'request') as mock_request:
                mock_response = MagicMock()
                mock_response.status_code = 404
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Not Found",
                    request=MagicMock(),
                    response=mock_response
                )
                mock_request.return_value = mock_response

                with pytest.raises(Exception) as exc_info:
                    await n8n_server._delete_execution({"execution_id": "nonexistent"})

                assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_list_executions_server_error(self, n8n_server):
        """Test listing executions when server returns error."""
        async with n8n_server:
            with patch.object(n8n_server.client, 'request') as mock_request:
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Internal Server Error",
                    request=MagicMock(),
                    response=mock_response
                )
                mock_request.return_value = mock_response

                with pytest.raises(Exception) as exc_info:
                    await n8n_server._list_executions({})

                assert "server error" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_execution_unauthorized(self, n8n_server):
        """Test getting execution with invalid credentials."""
        async with n8n_server:
            with patch.object(n8n_server.client, 'request') as mock_request:
                mock_response = MagicMock()
                mock_response.status_code = 401
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Unauthorized",
                    request=MagicMock(),
                    response=mock_response
                )
                mock_request.return_value = mock_response

                with pytest.raises(Exception) as exc_info:
                    await n8n_server._get_execution({"execution_id": "exec-1"})

                error_message = str(exc_info.value)
                assert "authentication" in error_message.lower() or "api key" in error_message.lower()

    @pytest.mark.asyncio
    async def test_delete_execution_forbidden(self, n8n_server):
        """Test deleting execution with insufficient permissions."""
        async with n8n_server:
            with patch.object(n8n_server.client, 'request') as mock_request:
                mock_response = MagicMock()
                mock_response.status_code = 403
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Forbidden",
                    request=MagicMock(),
                    response=mock_response
                )
                mock_request.return_value = mock_response

                with pytest.raises(Exception) as exc_info:
                    await n8n_server._delete_execution({"execution_id": "exec-1"})

                assert "access denied" in str(exc_info.value).lower() or "permission" in str(exc_info.value).lower()


class TestExecutionEdgeCases:
    """Test suite for execution edge cases."""

    @pytest.mark.asyncio
    async def test_list_executions_large_limit(self, n8n_server, mock_httpx_client):
        """Test listing executions with large limit value."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({"limit": 1000})

        call_args = mock_httpx_client.request.call_args
        params = call_args[1]["params"]
        assert params["limit"] == 1000

    @pytest.mark.asyncio
    async def test_list_executions_zero_limit(self, n8n_server, mock_httpx_client):
        """Test listing executions with zero limit."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({"limit": 0})

        call_args = mock_httpx_client.request.call_args
        params = call_args[1]["params"]
        assert params["limit"] == 0

    @pytest.mark.asyncio
    async def test_get_execution_max_length_id(self, n8n_server, mock_httpx_client, sample_execution):
        """Test getting execution with maximum allowed ID length."""
        max_length_id = "a" * 100
        sample_execution["id"] = max_length_id
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_execution
        mock_response.content = b'{"id": "a..."}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._get_execution({"execution_id": max_length_id})

        assert result["id"] == max_length_id

    @pytest.mark.asyncio
    async def test_list_executions_combined_filters_multiple_workflows(self, n8n_server, mock_httpx_client):
        """Test complex filtering scenario."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.content = b'{"data": []}'
        mock_httpx_client.request.return_value = mock_response

        result = await n8n_server._list_executions({
            "workflow_id": "workflow-abc-123",
            "status": "success",
            "limit": 50
        })

        call_args = mock_httpx_client.request.call_args
        params = call_args[1]["params"]
        assert params["workflowId"] == "workflow-abc-123"
        assert params["status"] == "success"
        assert params["limit"] == 50
        assert "data" in result

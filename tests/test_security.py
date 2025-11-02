"""
Security-focused test cases for n8n-mcp-server.
Tests input validation, error sanitization, and other security measures.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from n8n_mcp_server import N8nMCPServer
import httpx


@pytest.fixture
def n8n_server():
    """Create a test N8nMCPServer instance."""
    return N8nMCPServer(
        n8n_url="http://test.example.com",
        api_key="test_key_12345"
    )


class TestInputValidation:
    """Test suite for input validation security fixes (CVE-PATH-001)."""

    @pytest.mark.asyncio
    async def test_path_traversal_blocked_workflow(self, n8n_server):
        """Test that path traversal attempts in workflow_id are blocked."""
        malicious_ids = [
            "../../../etc/passwd",
            "../../admin/users",
            "id/../../../secrets",
            "id/../../config",
        ]

        for malicious_id in malicious_ids:
            with pytest.raises(ValueError, match="invalid characters|invalid path"):
                await n8n_server._get_workflow({"workflow_id": malicious_id})

    @pytest.mark.asyncio
    async def test_path_traversal_blocked_execution(self, n8n_server):
        """Test that path traversal attempts in execution_id are blocked."""
        malicious_ids = [
            "../workflows/1/delete",
            "../../admin",
            "../../../root"
        ]

        for malicious_id in malicious_ids:
            with pytest.raises(ValueError, match="invalid characters|invalid path"):
                await n8n_server._get_execution({"execution_id": malicious_id})

    @pytest.mark.asyncio
    async def test_empty_id_rejected(self, n8n_server):
        """Test that empty IDs are rejected."""
        empty_values = ["", "   ", None]

        for empty_value in empty_values:
            with pytest.raises(ValueError, match="is required|cannot be empty"):
                await n8n_server._get_workflow({"workflow_id": empty_value})

    @pytest.mark.asyncio
    async def test_invalid_characters_rejected(self, n8n_server):
        """Test that IDs with invalid characters are rejected."""
        invalid_ids = [
            "id with spaces",
            "id/with/slashes",
            "id\\with\\backslashes",
            "<script>alert('xss')</script>",
            "id;DROP TABLE workflows;",
            "id|rm -rf /",
        ]

        for invalid_id in invalid_ids:
            with pytest.raises(ValueError, match="invalid characters|invalid path"):
                await n8n_server._get_workflow({"workflow_id": invalid_id})

    @pytest.mark.asyncio
    async def test_id_length_limit_enforced(self, n8n_server):
        """Test that overly long IDs are rejected."""
        too_long = "a" * 101  # Max is 100

        with pytest.raises(ValueError, match="too long"):
            await n8n_server._get_workflow({"workflow_id": too_long})

    @pytest.mark.asyncio
    async def test_valid_ids_accepted(self, n8n_server):
        """Test that valid IDs are accepted."""
        valid_ids = [
            "workflow-123",
            "test_workflow_1",
            "ABC-123-XYZ",
            "workflow123",
            "a" * 100  # Exactly 100 chars
        ]

        for valid_id in valid_ids:
            # Should not raise ValueError
            validated = n8n_server._validate_id(valid_id, "Test ID")
            assert validated == valid_id


class TestErrorSanitization:
    """Test suite for error sanitization (CVE-INFO-001)."""

    @pytest.mark.asyncio
    async def test_401_error_sanitized(self, n8n_server):
        """Test that 401 errors return sanitized message."""
        # Initialize client in async context
        async with n8n_server:
            with patch.object(n8n_server.client, 'request') as mock_request:
                mock_response = MagicMock()
                mock_response.status_code = 401
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Unauthorized: Invalid API key at /home/user/config.json",
                    request=MagicMock(),
                    response=mock_response
                )
                mock_request.return_value = mock_response

                with pytest.raises(Exception) as exc_info:
                    await n8n_server._make_request("/workflows")

                # Should NOT contain internal file paths
                error_message = str(exc_info.value)
                assert "/home/user" not in error_message
                assert "config.json" not in error_message
                # Should contain user-friendly message
                assert "Authentication failed" in error_message or "API key" in error_message

    @pytest.mark.asyncio
    async def test_500_error_sanitized(self, n8n_server):
        """Test that 500 errors return sanitized message."""
        async with n8n_server:
            with patch.object(n8n_server.client, 'request') as mock_request:
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Internal Server Error: Database connection failed at /var/lib/n8n/db.sqlite",
                    request=MagicMock(),
                    response=mock_response
                )
                mock_request.return_value = mock_response

                with pytest.raises(Exception) as exc_info:
                    await n8n_server._make_request("/workflows")

                error_message = str(exc_info.value)
                # Should NOT contain internal paths
                assert "/var/lib" not in error_message
                assert "db.sqlite" not in error_message
                # Should contain user-friendly message
                assert "server error" in error_message.lower()

    @pytest.mark.asyncio
    async def test_connection_error_sanitized(self, n8n_server):
        """Test that connection errors return sanitized message."""
        async with n8n_server:
            with patch.object(n8n_server.client, 'request') as mock_request:
                mock_request.side_effect = httpx.RequestError(
                    "Connection failed: Network unreachable at 192.168.1.100:5678",
                    request=MagicMock()
                )

                with pytest.raises(Exception) as exc_info:
                    await n8n_server._make_request("/workflows")

                error_message = str(exc_info.value)
                # Should NOT contain internal IP addresses
                assert "192.168.1.100" not in error_message
                # Should contain user-friendly message
                assert "Unable to connect" in error_message or "N8N_URL" in error_message


class TestDependencySecurity:
    """Test suite for dependency security (CVE-2025-53365, CVE-2025-53366)."""

    def test_mcp_version_sufficient(self):
        """Test that MCP version is >= 1.9.4 to fix known CVEs."""
        from packaging import version
        import importlib.metadata

        # Get MCP version from package metadata
        mcp_version_str = importlib.metadata.version("mcp")
        mcp_version = version.parse(mcp_version_str)
        required_version = version.parse("1.9.4")

        assert mcp_version >= required_version, \
            f"MCP version {mcp_version} is below required {required_version} (CVE-2025-53365, CVE-2025-53366)"


class TestValidationAppliedToAllMethods:
    """Test that validation is applied to all 8 affected methods."""

    @pytest.mark.asyncio
    async def test_get_workflow_validates(self, n8n_server):
        """Test _get_workflow validates input."""
        with pytest.raises(ValueError):
            await n8n_server._get_workflow({"workflow_id": "../admin"})

    @pytest.mark.asyncio
    async def test_update_workflow_validates(self, n8n_server):
        """Test _update_workflow validates input."""
        with pytest.raises(ValueError):
            await n8n_server._update_workflow({
                "workflow_id": "../admin",
                "name": "test",
                "nodes": [],
                "connections": {}
            })

    @pytest.mark.asyncio
    async def test_delete_workflow_validates(self, n8n_server):
        """Test _delete_workflow validates input."""
        with pytest.raises(ValueError):
            await n8n_server._delete_workflow({"workflow_id": "../admin"})

    @pytest.mark.asyncio
    async def test_activate_workflow_validates(self, n8n_server):
        """Test _activate_workflow validates input."""
        with pytest.raises(ValueError):
            await n8n_server._activate_workflow({"workflow_id": "../admin"})

    @pytest.mark.asyncio
    async def test_deactivate_workflow_validates(self, n8n_server):
        """Test _deactivate_workflow validates input."""
        with pytest.raises(ValueError):
            await n8n_server._deactivate_workflow({"workflow_id": "../admin"})

    @pytest.mark.asyncio
    async def test_execute_workflow_validates(self, n8n_server):
        """Test _execute_workflow validates input."""
        with pytest.raises(ValueError):
            await n8n_server._execute_workflow({"workflow_id": "../admin"})

    @pytest.mark.asyncio
    async def test_get_execution_validates(self, n8n_server):
        """Test _get_execution validates input."""
        with pytest.raises(ValueError):
            await n8n_server._get_execution({"execution_id": "../admin"})

    @pytest.mark.asyncio
    async def test_delete_execution_validates(self, n8n_server):
        """Test _delete_execution validates input."""
        with pytest.raises(ValueError):
            await n8n_server._delete_execution({"execution_id": "../admin"})

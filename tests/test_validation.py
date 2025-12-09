"""Tests for response validation."""

import pytest
from n8n_mcp_server.models import (
    Workflow,
    Execution,
    Credential,
    Tag,
    validate_response,
    validate_workflow_response,
    validate_execution_response,
    validate_credential_response,
    validate_tag_response,
)


class TestWorkflowValidation:
    """Test workflow validation."""

    def test_valid_workflow(self):
        """Test validation with valid workflow data."""
        data = {
            "id": "1",
            "name": "Test Workflow",
            "active": True,
            "nodes": [],
            "connections": {},
            "tags": []
        }

        result = validate_workflow_response(data)
        assert result["id"] == "1"
        assert result["name"] == "Test Workflow"
        assert result["active"] is True

    def test_workflow_with_missing_optional_fields(self):
        """Test validation with minimal workflow data."""
        data = {
            "name": "Minimal Workflow"
        }

        result = validate_workflow_response(data)
        assert result["name"] == "Minimal Workflow"
        assert result["active"] is False  # Default value
        assert result["nodes"] == []
        assert result["connections"] == {}

    def test_workflow_with_extra_fields(self):
        """Test validation allows extra fields."""
        data = {
            "id": "1",
            "name": "Test Workflow",
            "active": True,
            "nodes": [],
            "connections": {},
            "extraField": "should be kept",
            "anotherExtra": 123
        }

        result = validate_workflow_response(data)
        assert result["name"] == "Test Workflow"
        assert "extraField" in result
        assert result["extraField"] == "should be kept"

    def test_workflow_list_response(self):
        """Test validation of list response."""
        data = {
            "data": [
                {"id": "1", "name": "Workflow 1", "active": True},
                {"id": "2", "name": "Workflow 2", "active": False}
            ]
        }

        result = validate_workflow_response(data)
        assert "data" in result
        assert len(result["data"]) == 2
        assert result["data"][0]["name"] == "Workflow 1"
        assert result["data"][1]["name"] == "Workflow 2"

    def test_workflow_with_complex_nodes(self):
        """Test validation with complex node data."""
        data = {
            "id": "1",
            "name": "Complex Workflow",
            "nodes": [
                {
                    "id": "node-1",
                    "name": "HTTP Request",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {
                        "url": "https://api.example.com",
                        "method": "GET"
                    }
                }
            ]
        }

        result = validate_workflow_response(data)
        assert result["name"] == "Complex Workflow"
        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["type"] == "n8n-nodes-base.httpRequest"

    def test_workflow_validation_graceful_failure(self):
        """Test that invalid data is returned sanitized."""
        data = {
            "name": 12345  # Invalid type - should be string
        }

        # Should not crash, but return sanitized data
        result = validate_workflow_response(data)
        assert isinstance(result, dict)
        assert "name" in result


class TestExecutionValidation:
    """Test execution validation."""

    def test_valid_execution(self):
        """Test validation with valid execution data."""
        data = {
            "id": "exec-1",
            "workflowId": "1",
            "status": "success",
            "startedAt": "2025-10-05T10:00:00.000Z",
            "finishedAt": "2025-10-05T10:00:05.000Z"
        }

        result = validate_execution_response(data)
        assert result["id"] == "exec-1"
        assert result["status"] == "success"

    def test_execution_with_minimal_data(self):
        """Test validation with minimal execution data."""
        data = {}

        result = validate_execution_response(data)
        assert isinstance(result, dict)

    def test_execution_list_response(self):
        """Test validation of execution list."""
        data = {
            "data": [
                {"id": "exec-1", "status": "success"},
                {"id": "exec-2", "status": "error"}
            ]
        }

        result = validate_execution_response(data)
        assert "data" in result
        assert len(result["data"]) == 2

    def test_execution_with_workflow_data(self):
        """Test execution with nested workflow data."""
        data = {
            "id": "exec-1",
            "workflowId": "1",
            "status": "running",
            "workflowData": {
                "id": "1",
                "name": "Test Workflow",
                "nodes": []
            }
        }

        result = validate_execution_response(data)
        assert result["id"] == "exec-1"
        assert "workflowData" in result


class TestCredentialValidation:
    """Test credential validation."""

    def test_valid_credential(self):
        """Test validation with valid credential data."""
        data = {
            "id": "cred-1",
            "name": "API Credentials",
            "type": "httpBasicAuth"
        }

        result = validate_credential_response(data)
        assert result["id"] == "cred-1"
        assert result["name"] == "API Credentials"
        assert result["type"] == "httpBasicAuth"

    def test_credential_list_response(self):
        """Test validation of credential list."""
        data = {
            "data": [
                {"id": "cred-1", "name": "Cred 1", "type": "oauth2"},
                {"id": "cred-2", "name": "Cred 2", "type": "apiKey"}
            ]
        }

        result = validate_credential_response(data)
        assert "data" in result
        assert len(result["data"]) == 2


class TestTagValidation:
    """Test tag validation."""

    def test_valid_tag(self):
        """Test validation with valid tag data."""
        data = {
            "id": "tag-1",
            "name": "production"
        }

        result = validate_tag_response(data)
        assert result["id"] == "tag-1"
        assert result["name"] == "production"

    def test_tag_minimal_data(self):
        """Test tag with minimal data."""
        data = {
            "name": "test"
        }

        result = validate_tag_response(data)
        assert result["name"] == "test"

    def test_tag_list_response(self):
        """Test validation of tag list."""
        data = {
            "data": [
                {"id": "tag-1", "name": "production"},
                {"id": "tag-2", "name": "development"}
            ]
        }

        result = validate_tag_response(data)
        assert "data" in result
        assert len(result["data"]) == 2


class TestValidationErrorHandling:
    """Test validation error handling."""

    def test_none_data(self):
        """Test handling of None data."""
        result = validate_response(None, Workflow, "test_operation")
        assert result == {}

    def test_invalid_data_type(self):
        """Test handling of invalid data types."""
        result = validate_workflow_response("not a dict")
        assert isinstance(result, (dict, str))

    def test_list_with_mixed_valid_invalid(self):
        """Test list with some invalid items."""
        data = {
            "data": [
                {"id": "1", "name": "Valid Workflow"},
                {"name": 12345},  # Invalid name type
                {"id": "3", "name": "Another Valid"}
            ]
        }

        result = validate_workflow_response(data)
        assert "data" in result
        # All items should be present, even if some validation failed
        assert len(result["data"]) == 3

    def test_deeply_nested_invalid_data(self):
        """Test handling of deeply nested invalid structures."""
        data = {
            "id": "1",
            "name": "Test",
            "nodes": [
                {
                    "name": "Node 1",
                    "type": "test",
                    "deeply": {
                        "nested": {
                            "structure": {
                                "with": {
                                    "unknown": "fields"
                                }
                            }
                        }
                    }
                }
            ]
        }

        result = validate_workflow_response(data)
        # Should handle gracefully
        assert result["name"] == "Test"
        assert len(result["nodes"]) == 1

    def test_empty_list_response(self):
        """Test empty list response."""
        data = {"data": []}

        result = validate_workflow_response(data)
        assert "data" in result
        assert result["data"] == []

    def test_response_with_cursor(self):
        """Test list response with pagination cursor."""
        data = {
            "data": [
                {"id": "1", "name": "Workflow 1"}
            ],
            "nextCursor": "cursor-123"
        }

        result = validate_workflow_response(data)
        assert "data" in result
        assert "nextCursor" in result
        assert result["nextCursor"] == "cursor-123"


class TestModels:
    """Test Pydantic models directly."""

    def test_workflow_model_creation(self):
        """Test creating a Workflow model."""
        workflow = Workflow(
            id="1",
            name="Test Workflow",
            active=True,
            nodes=[],
            connections={}
        )

        assert workflow.id == "1"
        assert workflow.name == "Test Workflow"
        assert workflow.active is True

    def test_execution_model_creation(self):
        """Test creating an Execution model."""
        execution = Execution(
            id="exec-1",
            workflowId="1",
            status="success"
        )

        assert execution.id == "exec-1"
        assert execution.workflowId == "1"
        assert execution.status == "success"

    def test_credential_model_creation(self):
        """Test creating a Credential model."""
        credential = Credential(
            id="cred-1",
            name="Test Cred",
            type="oauth2"
        )

        assert credential.id == "cred-1"
        assert credential.name == "Test Cred"
        assert credential.type == "oauth2"

    def test_tag_model_creation(self):
        """Test creating a Tag model."""
        tag = Tag(name="production")

        assert tag.name == "production"

    def test_model_to_dict(self):
        """Test converting model to dictionary."""
        workflow = Workflow(
            id="1",
            name="Test",
            active=True
        )

        data = workflow.model_dump()
        assert isinstance(data, dict)
        assert data["id"] == "1"
        assert data["name"] == "Test"

"""Response validation models for n8n API."""

import logging
from typing import Any, Dict, List, Optional, TypeVar, Union
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class Tag(BaseModel):
    """n8n tag model."""

    model_config = ConfigDict(extra='allow')

    id: Optional[str] = None
    name: str
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class WorkflowSettings(BaseModel):
    """Workflow settings model."""

    model_config = ConfigDict(extra='allow')

    saveDataErrorExecution: Optional[str] = None
    saveDataSuccessExecution: Optional[str] = None
    saveManualExecutions: Optional[bool] = None
    callerPolicy: Optional[str] = None
    errorWorkflow: Optional[str] = None
    timezone: Optional[str] = None


class Node(BaseModel):
    """Workflow node model."""

    model_config = ConfigDict(extra='allow')

    id: Optional[str] = None
    name: str
    type: str
    typeVersion: Optional[Union[int, float]] = None
    position: Optional[List[Union[int, float]]] = None
    parameters: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None


class Workflow(BaseModel):
    """n8n workflow model."""

    model_config = ConfigDict(extra='allow')

    id: Optional[str] = None
    name: str
    active: Optional[bool] = False
    nodes: Optional[List[Union[Node, Dict[str, Any]]]] = Field(default_factory=list)
    connections: Optional[Dict[str, Any]] = Field(default_factory=dict)
    settings: Optional[Union[WorkflowSettings, Dict[str, Any]]] = None
    staticData: Optional[Dict[str, Any]] = None
    tags: Optional[List[Union[Tag, str, Dict[str, Any]]]] = Field(default_factory=list)
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    versionId: Optional[str] = None

    @field_validator('nodes', mode='before')
    @classmethod
    def validate_nodes(cls, v):
        """Allow nodes to be dicts or Node objects."""
        if v is None:
            return []
        return v

    @field_validator('tags', mode='before')
    @classmethod
    def validate_tags(cls, v):
        """Allow tags to be strings, dicts, or Tag objects."""
        if v is None:
            return []
        return v


class ExecutionData(BaseModel):
    """Execution data model."""

    model_config = ConfigDict(extra='allow')

    startData: Optional[Dict[str, Any]] = None
    resultData: Optional[Dict[str, Any]] = None
    executionData: Optional[Dict[str, Any]] = None


class Execution(BaseModel):
    """n8n execution model."""

    model_config = ConfigDict(extra='allow')

    id: Optional[str] = None
    workflowId: Optional[str] = None
    workflowData: Optional[Union[Workflow, Dict[str, Any]]] = None
    mode: Optional[str] = None
    status: Optional[str] = None
    startedAt: Optional[str] = None
    stoppedAt: Optional[str] = None
    finishedAt: Optional[str] = None
    retryOf: Optional[str] = None
    retrySuccessId: Optional[str] = None
    data: Optional[Union[ExecutionData, Dict[str, Any]]] = None
    waitTill: Optional[str] = None


class Credential(BaseModel):
    """n8n credential model."""

    model_config = ConfigDict(extra='allow')

    id: Optional[str] = None
    name: str
    type: str
    data: Optional[Dict[str, Any]] = None
    nodesAccess: Optional[List[Dict[str, Any]]] = None
    sharedWith: Optional[List[Dict[str, Any]]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class ListResponse(BaseModel):
    """Generic list response wrapper."""

    model_config = ConfigDict(extra='allow')

    data: List[Any] = Field(default_factory=list)
    nextCursor: Optional[str] = None


def validate_response(
    data: Any,
    model: type[T],
    operation: str = "unknown"
) -> Union[T, Dict[str, Any]]:
    """
    Validate API response against a Pydantic model.

    Args:
        data: Raw response data from API
        model: Pydantic model class to validate against
        operation: Name of the operation for logging

    Returns:
        Validated model instance or sanitized dict if validation fails
    """
    if data is None:
        logger.warning(f"Received None response for {operation}")
        return {}

    try:
        # If it's a list response wrapper
        if isinstance(data, dict) and 'data' in data:
            validated = ListResponse.model_validate(data)
            # Try to validate each item in the list
            if validated.data:
                validated_items = []
                for item in validated.data:
                    try:
                        validated_item = model.model_validate(item)
                        validated_items.append(validated_item.model_dump())
                    except Exception as e:
                        logger.warning(
                            f"Failed to validate list item in {operation}: {str(e)}. "
                            f"Using raw data."
                        )
                        # Keep the original item if validation fails
                        validated_items.append(item)

                result = validated.model_dump()
                result['data'] = validated_items
                return result
            return validated.model_dump()

        # Single item validation
        validated = model.model_validate(data)
        return validated.model_dump()

    except Exception as e:
        # Log warning but don't crash - return sanitized data
        logger.warning(
            f"Response validation failed for {operation}: {str(e)}. "
            f"Returning data without validation."
        )

        # Return sanitized version - ensure it's JSON serializable
        if isinstance(data, dict):
            return _sanitize_dict(data)
        elif isinstance(data, list):
            return [_sanitize_dict(item) if isinstance(item, dict) else item for item in data]
        else:
            return data


def _sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a dictionary to ensure it's JSON serializable.

    Args:
        data: Dictionary to sanitize

    Returns:
        Sanitized dictionary
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, dict):
            sanitized[key] = _sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                _sanitize_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, (str, int, float, bool, type(None))):
            sanitized[key] = value
        else:
            # Convert unknown types to string
            sanitized[key] = str(value)

    return sanitized


def validate_workflow_response(data: Any, operation: str = "workflow") -> Dict[str, Any]:
    """Validate workflow response."""
    return validate_response(data, Workflow, operation)


def validate_execution_response(data: Any, operation: str = "execution") -> Dict[str, Any]:
    """Validate execution response."""
    return validate_response(data, Execution, operation)


def validate_credential_response(data: Any, operation: str = "credential") -> Dict[str, Any]:
    """Validate credential response."""
    return validate_response(data, Credential, operation)


def validate_tag_response(data: Any, operation: str = "tag") -> Dict[str, Any]:
    """Validate tag response."""
    return validate_response(data, Tag, operation)

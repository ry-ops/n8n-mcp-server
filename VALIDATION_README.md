# Response Validation

This document describes the response validation feature added to n8n-mcp-server.

## Overview

The n8n-mcp-server now includes robust response validation using Pydantic models. This ensures API responses are properly structured while gracefully handling unexpected formats.

## Features

- **Type-safe models**: Pydantic models for Workflow, Execution, Credential, and Tag
- **Graceful degradation**: Invalid responses are sanitized and returned rather than crashing
- **Logging**: Warnings are logged for validation failures
- **Extra fields**: Unknown fields are preserved (not stripped)
- **List support**: Handles both single items and paginated list responses

## Models

### Workflow
Represents an n8n workflow with nodes, connections, settings, and tags.

```python
from n8n_mcp_server.models import Workflow

workflow = Workflow(
    id="1",
    name="My Workflow",
    active=True,
    nodes=[],
    connections={}
)
```

### Execution
Represents a workflow execution with status, timestamps, and result data.

```python
from n8n_mcp_server.models import Execution

execution = Execution(
    id="exec-1",
    workflowId="1",
    status="success",
    startedAt="2025-10-05T10:00:00.000Z"
)
```

### Credential
Represents n8n credentials with type and access control.

```python
from n8n_mcp_server.models import Credential

credential = Credential(
    id="cred-1",
    name="API Key",
    type="apiKey"
)
```

### Tag
Represents workflow tags.

```python
from n8n_mcp_server.models import Tag

tag = Tag(
    id="tag-1",
    name="production"
)
```

## Validation Functions

### validate_workflow_response
Validates workflow API responses.

```python
from n8n_mcp_server.models import validate_workflow_response

# Single workflow
data = {"id": "1", "name": "Test", "active": True}
validated = validate_workflow_response(data, "get_workflow")

# List of workflows
data = {
    "data": [
        {"id": "1", "name": "Workflow 1"},
        {"id": "2", "name": "Workflow 2"}
    ]
}
validated = validate_workflow_response(data, "list_workflows")
```

### validate_execution_response
Validates execution API responses.

```python
from n8n_mcp_server.models import validate_execution_response

data = {
    "id": "exec-1",
    "workflowId": "1",
    "status": "success"
}
validated = validate_execution_response(data, "get_execution")
```

### validate_credential_response
Validates credential API responses.

```python
from n8n_mcp_server.models import validate_credential_response

data = {
    "id": "cred-1",
    "name": "My Credentials",
    "type": "oauth2"
}
validated = validate_credential_response(data, "list_credentials")
```

### validate_tag_response
Validates tag API responses.

```python
from n8n_mcp_server.models import validate_tag_response

data = {"id": "tag-1", "name": "production"}
validated = validate_tag_response(data, "list_tags")
```

## Error Handling

The validation layer is designed to be resilient:

1. **Missing fields**: Optional fields use defaults (e.g., `active=False`)
2. **Extra fields**: Unknown fields are preserved using `extra='allow'`
3. **Invalid types**: Validation failures are logged but don't crash
4. **Mixed validity**: In lists, valid items are validated while invalid items are sanitized

### Example: Invalid Data Handling

```python
# Invalid name type (should be string, not int)
data = {"name": 12345}
result = validate_workflow_response(data, "create_workflow")
# Result: Logs warning but returns sanitized dict

# Mixed valid/invalid in list
data = {
    "data": [
        {"id": "1", "name": "Valid"},
        {"name": 12345},  # Invalid
        {"id": "3", "name": "Also Valid"}
    ]
}
result = validate_workflow_response(data, "list_workflows")
# Result: All 3 items present, valid ones validated, invalid one sanitized
```

## Logging

Validation failures generate warning logs:

```
WARNING - Response validation failed for get_workflow: 1 validation error for Workflow
name
  Input should be a valid string [type=string_type, input_value=12345, input_type=int]
Returning data without validation.
```

This helps with debugging while allowing the application to continue.

## Integration

All API response handlers in the main server automatically use validation:

```python
async def _list_workflows(self, args: dict) -> Any:
    """List workflows."""
    params = {}
    if args.get("active") is not None:
        params["active"] = str(args["active"]).lower()

    result = await self._make_request("/workflows", params=params)
    return validate_workflow_response(result, "list_workflows")
```

## Testing

Comprehensive tests are included in `tests/test_validation.py`:

- Valid data validation
- Missing optional fields
- Extra fields preservation
- List responses
- Invalid data handling
- Edge cases (None, empty lists, pagination)
- Direct model creation

Run tests:

```bash
pytest tests/test_validation.py -v
```

Or run the standalone test:

```bash
python3 test_models_only.py
```

## Benefits

1. **Type Safety**: Catch API schema changes early
2. **Robustness**: Graceful handling of unexpected responses
3. **Debugging**: Clear warnings for validation failures
4. **Forward Compatibility**: Extra fields preserved for future API versions
5. **Documentation**: Models serve as API documentation

## Dependencies

- `pydantic>=2.0.0` - Added to project dependencies

## Files Added

- `src/n8n_mcp_server/models.py` - Validation models and functions
- `tests/test_validation.py` - Comprehensive validation tests
- `VALIDATION_README.md` - This documentation

## Files Modified

- `pyproject.toml` - Added pydantic dependency
- `src/n8n_mcp_server/__init__.py` - Integrated validation in all response handlers

## Migration Notes

This change is backward compatible. Existing code continues to work, but now with added validation and safety.

No changes are required for users of the MCP server - validation happens transparently.

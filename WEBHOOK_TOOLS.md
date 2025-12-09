# Webhook Management Tools

This document describes the new webhook management tools added to n8n-mcp-server.

## Overview

Three new tools have been added to manage webhook endpoints in n8n workflows:

1. **list_webhooks** - List all webhook endpoints across workflows
2. **get_webhook** - Get detailed webhook configuration by workflow ID
3. **test_webhook** - Test a webhook endpoint by executing its workflow

## Implementation Details

### Architecture

n8n doesn't have dedicated webhook management API endpoints. Instead, webhooks are managed as nodes within workflows. The implementation:

- Scans workflows to identify webhook nodes (type: `n8n-nodes-base.webhook`)
- Extracts webhook configuration from node parameters
- Provides a unified interface for webhook management

### Tool Descriptions

#### 1. list_webhooks

Lists all webhook endpoints across all workflows.

**Input Schema:**
```json
{
  "active": boolean (optional) - Filter by active workflow status
}
```

**Returns:**
```json
{
  "webhooks": [
    {
      "workflow_id": "string",
      "workflow_name": "string",
      "workflow_active": boolean,
      "node_name": "string",
      "node_id": "string",
      "webhook_path": "string",
      "http_method": "string",
      "response_mode": "string",
      "authentication": "string"
    }
  ],
  "total_count": number
}
```

**Features:**
- Filters workflows by active status
- Scans all workflows to find webhook nodes
- Handles multiple webhook nodes per workflow
- Continues processing even if individual workflows fail

#### 2. get_webhook

Gets detailed webhook information for a specific workflow.

**Input Schema:**
```json
{
  "workflow_id": "string" (required) - The workflow ID
}
```

**Returns:**
```json
{
  "workflow_id": "string",
  "workflow_name": "string",
  "workflow_active": boolean,
  "webhook_nodes": [
    {
      "node_name": "string",
      "node_id": "string",
      "webhook_path": "string",
      "http_method": "string",
      "response_mode": "string",
      "response_data": "string",
      "authentication": "string",
      "allowed_origins": "string",
      "response_code": number,
      "response_headers": object,
      "ip_whitelist": "string" (optional)
    }
  ],
  "total_webhook_nodes": number
}
```

**Features:**
- Validates workflow ID using existing `_validate_id` method
- Returns comprehensive webhook configuration
- Includes optional security settings (IP whitelist)
- Raises error if workflow contains no webhook nodes

#### 3. test_webhook

Tests a webhook endpoint by executing its workflow.

**Input Schema:**
```json
{
  "workflow_id": "string" (required) - The workflow ID
  "data": object (optional) - Test data to send
}
```

**Returns:**
```json
{
  "workflow_id": "string",
  "workflow_name": "string",
  "test_result": "success",
  "execution": object,
  "message": "string"
}
```

**Features:**
- Validates workflow contains webhook nodes before execution
- Executes workflow with optional test data
- Returns execution results for verification
- Raises error if workflow is not a webhook workflow

## Security

All webhook tools implement security best practices:

### Input Validation

- **Workflow ID validation**: Uses existing `_validate_id` method
- **Path traversal protection**: Blocks patterns like `../`, `./`, `\\`
- **Character validation**: Only allows alphanumeric, hyphens, and underscores
- **Length limits**: Maximum 100 characters for IDs
- **Empty value rejection**: Prevents empty or whitespace-only IDs

### Error Handling

- Consistent error messages across all tools
- Graceful handling of missing webhook nodes
- Continues processing in `list_webhooks` if individual workflows fail
- Logs warnings for failed workflow processing

### Security Tests

Added comprehensive security tests in `/tmp/n8n-mcp-server-webhook/tests/test_security.py`:
- `test_get_webhook_validates` - Validates input sanitization
- `test_test_webhook_validates` - Validates input sanitization

## Testing

Created comprehensive test suite in `/tmp/n8n-mcp-server-webhook/tests/test_webhooks.py`:

### Test Coverage (12 tests)

1. **test_list_webhooks** - Lists webhooks successfully
2. **test_list_webhooks_active_filter** - Filters by active status
3. **test_list_webhooks_no_webhooks_found** - Handles no webhooks case
4. **test_get_webhook** - Gets detailed webhook info
5. **test_get_webhook_no_webhook_nodes** - Handles missing webhook nodes
6. **test_get_webhook_validates_id** - Validates ID input
7. **test_test_webhook** - Tests webhook execution
8. **test_test_webhook_without_data** - Tests without data
9. **test_test_webhook_non_webhook_workflow** - Validates workflow type
10. **test_test_webhook_validates_id** - Validates ID input
11. **test_list_webhooks_multiple_webhooks_in_workflow** - Handles multiple webhooks
12. **test_get_webhook_multiple_nodes** - Handles multiple nodes

### Test Results

All tests pass:
```
============================== 50 passed in 0.32s ==============================
Coverage: 65%
```

## Usage Examples

### List all webhook endpoints

```python
# List all webhooks
await server._list_webhooks({})

# List only active webhooks
await server._list_webhooks({"active": True})
```

### Get webhook details

```python
# Get webhook configuration
await server._get_webhook({"workflow_id": "webhook-workflow-1"})
```

### Test a webhook

```python
# Test without data
await server._test_webhook({"workflow_id": "webhook-workflow-1"})

# Test with data
await server._test_webhook({
    "workflow_id": "webhook-workflow-1",
    "data": {"test_key": "test_value"}
})
```

## Implementation Notes

### Webhook Node Detection

Webhooks are identified by node type:
```python
node.get("type") == "n8n-nodes-base.webhook"
```

### Parameter Extraction

Webhook configuration is stored in node parameters:
```python
parameters = node.get("parameters", {})
webhook_path = parameters.get("path", "")
http_method = parameters.get("httpMethod", "GET")
```

### Error Resilience

The `list_webhooks` tool continues processing even if individual workflows fail:
```python
try:
    workflow_details = await self._make_request(f"/workflows/{workflow_id}")
    # Process webhook nodes...
except Exception as e:
    logger.warning(f"Error processing workflow {workflow_id}: {str(e)}")
    continue
```

## Files Modified

1. `/tmp/n8n-mcp-server-webhook/src/n8n_mcp_server/__init__.py`
   - Added 3 new tool definitions in `list_tools()`
   - Added 3 new tool handlers in `call_tool()`
   - Added 3 new implementation methods:
     - `_list_webhooks()`
     - `_get_webhook()`
     - `_test_webhook()`

2. `/tmp/n8n-mcp-server-webhook/tests/test_webhooks.py` (new file)
   - Comprehensive test suite with 12 tests
   - Fixtures for webhook and non-webhook workflows
   - Tests for validation, error handling, and edge cases

3. `/tmp/n8n-mcp-server-webhook/tests/test_security.py`
   - Added 2 new security validation tests
   - Ensures webhook tools follow security best practices

## Future Enhancements

Potential improvements:

1. **Webhook URL Construction**: Return full webhook URLs based on n8n instance URL
2. **Webhook Statistics**: Track webhook execution counts and success rates
3. **Webhook Filtering**: Filter by HTTP method, authentication type, etc.
4. **Bulk Operations**: Activate/deactivate multiple webhook workflows
5. **Webhook Templates**: Create webhook workflows from templates

## References

Research conducted on n8n webhook functionality:
- n8n webhook nodes are part of workflows, not separate API entities
- Webhooks are registered when workflows are activated
- Test and production webhook URLs are available
- Webhook configuration includes authentication, CORS, IP whitelisting

### Documentation Sources

- [n8n Webhook Node Documentation](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/)
- [n8n API Reference](https://docs.n8n.io/api/api-reference/)
- [n8n Public REST API](https://docs.n8n.io/api/)

# Retry Logic Quick Start Guide

## Installation

```bash
cd /tmp/n8n-mcp-server-retry
pip install -e ".[dev]"
```

## Basic Usage

### Default Configuration (Recommended)

No configuration needed! Retry logic is automatically enabled with sensible defaults:

```bash
# Default settings:
# - Max retries: 3
# - Backoff: 1s, 2s, 4s, 8s (exponential, capped at 8s)
# - Retry on: 429, 500, 502, 503, 504, connection errors
# - No retry on: 400, 401, 403, 404

python -m n8n_mcp_server
```

### Custom Retry Count

```bash
# Increase for unreliable networks
export N8N_MAX_RETRIES=5
python -m n8n_mcp_server

# Decrease for fast-fail scenarios
export N8N_MAX_RETRIES=1
python -m n8n_mcp_server

# Disable retries completely
export N8N_MAX_RETRIES=0
python -m n8n_mcp_server
```

## What Gets Retried?

### ✅ Retryable (Automatic Retry)
- **HTTP 429** (Rate Limit) - Respects `Retry-After` header
- **HTTP 500** (Internal Server Error)
- **HTTP 502** (Bad Gateway)
- **HTTP 503** (Service Unavailable)
- **HTTP 504** (Gateway Timeout)
- **Connection Errors** (network issues, timeouts)

### ❌ Non-Retryable (Fail Immediately)
- **HTTP 400** (Bad Request) - Invalid input
- **HTTP 401** (Unauthorized) - Bad API key
- **HTTP 403** (Forbidden) - No permissions
- **HTTP 404** (Not Found) - Resource doesn't exist

## Retry Timing

### Exponential Backoff
```
Attempt 1: Immediate
Attempt 2: Wait 1s
Attempt 3: Wait 2s
Attempt 4: Wait 4s
Attempt 5: Wait 8s (max)
Attempt 6+: Wait 8s (capped)
```

### Rate Limit (429) with Retry-After Header
```
Server says: "Retry-After: 5"
→ Wait exactly 5 seconds (respects server request)

Server says: "Retry-After: 100"
→ Wait 8 seconds (capped at maximum)
```

## Environment Variables

```bash
# .env file or export
N8N_URL=https://n8n.example.com
N8N_API_KEY=your_api_key_here
N8N_MAX_RETRIES=3           # Optional, defaults to 3
N8N_TIMEOUT=30              # Request timeout (works with retries)
N8N_VERIFY_SSL=true
LOG_LEVEL=INFO              # Set to DEBUG to see retry attempts
```

## Logging

### View Retry Attempts
```bash
export LOG_LEVEL=INFO
python -m n8n_mcp_server
```

Example log output:
```
INFO - Retrying after HTTP 500, waiting 1.0s (attempt 1/4)
INFO - Retrying after HTTP 500, waiting 2.0s (attempt 2/4)
INFO - Rate limited (429), respecting Retry-After: 5.0s (attempt 3/4)
```

## Testing

### Run Retry Tests
```bash
# All retry-specific tests
pytest tests/test_retry_logic.py -v

# All tests (including retry)
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src/n8n_mcp_server --cov-report=html
```

## Common Scenarios

### Scenario 1: Temporary Network Issues
```python
# Your code
workflows = await server._list_workflows({})

# What happens internally:
# Attempt 1: Connection error → Wait 1s
# Attempt 2: Connection error → Wait 2s
# Attempt 3: Success! ✓
# Your code receives: workflows data
```

### Scenario 2: Server Under Load
```python
# Your code
result = await server._execute_workflow({"workflow_id": "123"})

# What happens internally:
# Attempt 1: HTTP 503 → Wait 1s
# Attempt 2: HTTP 503 → Wait 2s
# Attempt 3: HTTP 503 → Wait 4s
# Attempt 4: HTTP 200 ✓
# Your code receives: execution result
```

### Scenario 3: Rate Limited
```python
# Your code
for i in range(100):
    workflow = await server._get_workflow({"workflow_id": str(i)})

# What happens internally:
# Requests 1-50: Success
# Request 51: HTTP 429 (Retry-After: 3) → Wait 3s → Success
# Requests 52-100: Success
# Your code: Just works!
```

### Scenario 4: Invalid API Key (No Retry)
```python
# Your code
workflows = await server._list_workflows({})

# What happens internally:
# Attempt 1: HTTP 401 → Fail immediately ✗
# Your code receives: Exception("Authentication failed. Please check your API key.")
```

## Performance Considerations

### Total Time Estimates
With default 3 retries:
- **All succeed**: No overhead
- **1 failure**: +1s
- **2 failures**: +3s (1+2)
- **3 failures**: +7s (1+2+4)
- **All fail**: +7s total

With 5 retries:
- **All fail**: +15s total (1+2+4+8)

### Recommendations
- **Default (3)**: Good for most use cases
- **Lower (1-2)**: Fast-fail critical paths
- **Higher (5-10)**: Batch jobs, unreliable networks
- **Zero (0)**: Testing, debugging

## Troubleshooting

### Too Many Retries
```bash
# Check logs for patterns
export LOG_LEVEL=DEBUG

# Reduce retry count
export N8N_MAX_RETRIES=1
```

### Not Enough Retries
```bash
# Increase retry count
export N8N_MAX_RETRIES=5

# Check if error is retryable
# 400, 401, 403, 404 = NOT retried (by design)
```

### Slow Performance
```bash
# Retries add delay on failures
# Check if n8n server is healthy
# Consider reducing max retries for faster failure
export N8N_MAX_RETRIES=1
```

## Best Practices

1. **Use defaults** for production (3 retries)
2. **Enable INFO logging** to monitor retry frequency
3. **Set appropriate timeouts** (`N8N_TIMEOUT`)
4. **Monitor logs** for excessive retries (service health issue)
5. **Test with retries disabled** (`N8N_MAX_RETRIES=0`) during development

## Examples

### Example 1: Development Setup
```bash
# .env
N8N_URL=http://localhost:5678
N8N_API_KEY=test_key_123
N8N_MAX_RETRIES=1  # Fast-fail during development
LOG_LEVEL=DEBUG
```

### Example 2: Production Setup
```bash
# .env
N8N_URL=https://n8n.company.com
N8N_API_KEY=${N8N_API_KEY}  # From secrets manager
N8N_MAX_RETRIES=3           # Default, good for production
N8N_TIMEOUT=60              # Higher timeout for complex workflows
LOG_LEVEL=INFO
```

### Example 3: Batch Processing
```bash
# .env
N8N_URL=https://n8n.company.com
N8N_API_KEY=${N8N_API_KEY}
N8N_MAX_RETRIES=5           # More retries for batch jobs
N8N_TIMEOUT=120             # Higher timeout
LOG_LEVEL=INFO
```

## Summary

✅ Retry logic is **automatic** and **transparent**
✅ **Zero code changes** required
✅ **Configurable** via environment variable
✅ **Smart** rate limit handling
✅ **Production-ready** with comprehensive tests

Questions? Check `RETRY_IMPLEMENTATION.md` for technical details.

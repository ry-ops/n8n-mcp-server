# Retry Logic Implementation Summary

## Overview

This document summarizes the retry logic with exponential backoff added to the n8n-mcp-server.

## Implementation Location

Repository: https://github.com/ry-ops/n8n-mcp-server
Local clone: /tmp/n8n-mcp-server-retry

## Changes Made

### 1. Core Retry Decorator (`src/n8n_mcp_server/__init__.py`)

Added `async_retry_with_backoff()` decorator with the following features:

#### Retry Strategy
- **Exponential backoff**: 1s, 2s, 4s, 8s (max)
- **Default max retries**: 3 (configurable via `N8N_MAX_RETRIES` env var)
- **Retry on**:
  - Connection errors (ConnectError, TimeoutException, RequestError)
  - HTTP 429 (Rate Limit)
  - HTTP 500 (Internal Server Error)
  - HTTP 502 (Bad Gateway)
  - HTTP 503 (Service Unavailable)
  - HTTP 504 (Gateway Timeout)

- **Do NOT retry on**:
  - HTTP 400 (Bad Request)
  - HTTP 401 (Unauthorized)
  - HTTP 403 (Forbidden)
  - HTTP 404 (Not Found)

#### Rate Limit Handling
- Respects `Retry-After` header when present (HTTP 429)
- Falls back to exponential backoff if header is missing or invalid
- Caps retry delay at 8 seconds maximum

#### Configuration
- `N8N_MAX_RETRIES`: Environment variable to configure max retry attempts (default: 3)
- All retry settings configurable via decorator parameters

### 2. Updated `_make_request` Method

- Applied `@async_retry_with_backoff()` decorator
- Re-raises retryable errors for decorator to handle
- Converts errors to user-friendly messages after retries exhausted
- Maintains backward compatibility with existing error handling

### 3. Environment Configuration (`.env.example`)

Added new configuration section:

```bash
# Retry Configuration
# Maximum number of retry attempts for failed requests
# Default: 3
# Retries apply to: connection errors, 429 (rate limit), 500, 502, 503, 504
# Does NOT retry: 400, 401, 403, 404 (client errors)
# Backoff strategy: exponential (1s, 2s, 4s, 8s max)
N8N_MAX_RETRIES=3
```

### 4. Comprehensive Test Suite (`tests/test_retry_logic.py`)

Added 17 tests covering:

1. **Retry on server errors** (500, 502, 503, 504)
2. **Retry on rate limits** (429 with and without Retry-After header)
3. **No retry on client errors** (400, 401, 403, 404)
4. **Retry on connection/timeout errors**
5. **Max retries enforcement**
6. **Configurable retry count via environment variable**
7. **Exponential backoff timing verification**
8. **Backoff cap at 8 seconds**
9. **Retry-After header value capping**

## Test Results

All 53 tests pass (36 existing + 17 new):

```
============================= 53 passed in 38.49s ==============================
Name                             Stmts   Miss  Cover   Missing
--------------------------------------------------------------
src/n8n_mcp_server/__init__.py     271     97    64%
```

## Key Features

### 1. Transparent Retry Logic
- Automatic retries without code changes in calling code
- Maintains existing error messages and behavior
- No breaking changes to API

### 2. Smart Rate Limit Handling
- Honors server-specified `Retry-After` header
- Prevents aggressive retries during rate limiting
- Caps delays to prevent excessive wait times

### 3. Exponential Backoff
- Progressive delay: 1s → 2s → 4s → 8s (max)
- Prevents overwhelming failing services
- Reduces load during service degradation

### 4. Configurable Behavior
- `N8N_MAX_RETRIES` environment variable
- Decorator parameters for fine-tuning
- Respects existing timeout settings

### 5. Comprehensive Logging
- Logs each retry attempt with timing
- Differentiates between retry types (rate limit, server error, connection)
- Helps with debugging and monitoring

## Usage Examples

### Basic Usage (Default 3 Retries)

```python
# No code changes needed - decorator handles everything
server = N8nMCPServer(n8n_url="https://n8n.example.com", api_key="key")
workflows = await server._list_workflows({})
```

### Custom Retry Count

```bash
# Set via environment variable
export N8N_MAX_RETRIES=5
```

### Retry Behavior Demonstration

```python
# Connection temporarily down
# Attempt 1: Connection error → Wait 1s → Retry
# Attempt 2: Connection error → Wait 2s → Retry
# Attempt 3: Connection error → Wait 4s → Retry
# Attempt 4: Success! ✓

# Rate limited (429) with Retry-After: 3
# Attempt 1: HTTP 429 → Wait 3s (from header) → Retry
# Attempt 2: Success! ✓

# Client error (404)
# Attempt 1: HTTP 404 → Fail immediately (no retry) ✗
```

## Error Handling

### Retryable Errors
After all retries exhausted, converts to user-friendly messages:
- 429 → "Rate limit exceeded. Please try again later."
- 500 → "n8n server error. Please check your n8n instance."
- 502 → "n8n bad gateway error."
- 503 → "n8n service unavailable."
- 504 → "n8n gateway timeout."
- Connection errors → "Unable to connect to n8n. Please check your N8N_URL."

### Non-Retryable Errors
Fail immediately with appropriate messages:
- 400 → "An error occurred while communicating with n8n."
- 401 → "Authentication failed. Please check your API key."
- 403 → "Access denied. Insufficient permissions."
- 404 → "Resource not found."

## Performance Impact

### Benefits
- **Improved reliability**: Automatic recovery from transient failures
- **Better user experience**: Fewer failed requests
- **Reduced manual intervention**: No need to manually retry

### Overhead
- **Minimal when successful**: No overhead for successful requests
- **Additional delay on failures**: Exponential backoff adds wait time
- **Configurable**: Can disable by setting `N8N_MAX_RETRIES=0`

## Best Practices

1. **Use default settings** (3 retries) for most scenarios
2. **Increase retries** for unreliable networks or batch operations
3. **Monitor logs** for excessive retries (indicates service issues)
4. **Set timeouts appropriately** to work with retry delays
5. **Consider total time**: 3 retries = ~15s total (1+2+4+8)

## Files Modified

1. `/tmp/n8n-mcp-server-retry/src/n8n_mcp_server/__init__.py` - Core implementation
2. `/tmp/n8n-mcp-server-retry/.env.example` - Configuration documentation
3. `/tmp/n8n-mcp-server-retry/tests/test_retry_logic.py` - Comprehensive tests (NEW)

## Backward Compatibility

✅ Fully backward compatible:
- Existing code works without changes
- Default behavior unchanged for successful requests
- Error messages remain consistent
- No breaking API changes

## Future Enhancements

Potential improvements for consideration:
1. Configurable backoff strategy (linear, exponential, fibonacci)
2. Circuit breaker pattern for repeated failures
3. Retry metrics/statistics collection
4. Per-endpoint retry configuration
5. Jitter addition to prevent thundering herd

## Conclusion

The retry logic implementation provides robust, automatic error recovery with minimal overhead and maximum configurability. All tests pass, and the implementation is production-ready.

"""n8n MCP Server - Python Implementation"""

import asyncio
import json
import logging
import os
import re
import signal
import sys
import time
from datetime import datetime
from typing import Any, Optional, Callable
from functools import wraps

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Retry configuration
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404}
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 1.0  # 1 second
MAX_BACKOFF = 8.0  # 8 seconds max


def async_retry_with_backoff(
    max_retries: Optional[int] = None,
    base_delay: float = DEFAULT_BACKOFF_BASE,
    max_delay: float = MAX_BACKOFF,
):
    """
    Decorator for async functions to retry with exponential backoff.

    Retries on:
    - Connection errors (ConnectError, TimeoutException, etc.)
    - HTTP 429 (rate limit), 500, 502, 503, 504

    Does NOT retry on:
    - HTTP 400, 401, 403, 404 (client errors)

    Args:
        max_retries: Maximum number of retries (defaults to env N8N_MAX_RETRIES or 3)
        base_delay: Base delay for exponential backoff (default: 1 second)
        max_delay: Maximum delay between retries (default: 8 seconds)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get max_retries from env or use default
            retries = max_retries
            if retries is None:
                retries = int(os.getenv("N8N_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))

            last_exception = None

            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)

                except httpx.HTTPStatusError as e:
                    last_exception = e
                    status_code = e.response.status_code

                    # Don't retry on client errors (400, 401, 403, 404)
                    if status_code in NON_RETRYABLE_STATUS_CODES:
                        logger.debug(f"Non-retryable status {status_code}, not retrying")
                        raise

                    # Retry on specific server errors and rate limits
                    if status_code in RETRYABLE_STATUS_CODES:
                        if attempt < retries:
                            # Check for Retry-After header (rate limiting)
                            retry_after = e.response.headers.get("Retry-After")
                            if retry_after:
                                try:
                                    delay = float(retry_after)
                                    # Cap the delay at max_delay
                                    delay = min(delay, max_delay)
                                    logger.info(
                                        f"Rate limited (429), respecting Retry-After: {delay}s "
                                        f"(attempt {attempt + 1}/{retries + 1})"
                                    )
                                except ValueError:
                                    # If Retry-After is not a number, use exponential backoff
                                    delay = min(base_delay * (2 ** attempt), max_delay)
                                    logger.info(
                                        f"Rate limited (429), using backoff: {delay}s "
                                        f"(attempt {attempt + 1}/{retries + 1})"
                                    )
                            else:
                                # Exponential backoff: 1s, 2s, 4s, 8s
                                delay = min(base_delay * (2 ** attempt), max_delay)
                                logger.info(
                                    f"Retrying after HTTP {status_code}, "
                                    f"waiting {delay}s (attempt {attempt + 1}/{retries + 1})"
                                )

                            await asyncio.sleep(delay)
                            continue
                        else:
                            # Max retries exceeded for retryable status - convert to user-friendly message
                            error_messages = {
                                429: "Rate limit exceeded. Please try again later.",
                                500: "n8n server error. Please check your n8n instance.",
                                502: "n8n bad gateway error.",
                                503: "n8n service unavailable.",
                                504: "n8n gateway timeout.",
                            }
                            user_message = error_messages.get(
                                status_code,
                                "An error occurred while communicating with n8n."
                            )
                            raise Exception(user_message)

                    # For other HTTP errors, don't retry
                    raise

                except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
                    last_exception = e

                    # Retry on connection/network errors
                    if attempt < retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.info(
                            f"Connection error ({type(e).__name__}), "
                            f"retrying in {delay}s (attempt {attempt + 1}/{retries + 1})"
                        )
                        await asyncio.sleep(delay)
                        continue

                    # Max retries exceeded - convert to user-friendly message
                    raise Exception("Unable to connect to n8n. Please check your N8N_URL.")

            # Should not reach here, but handle it just in case
            if last_exception:
                # Convert final HTTPStatusError to user-friendly message
                if isinstance(last_exception, httpx.HTTPStatusError):
                    status_code = last_exception.response.status_code
                    error_messages = {
                        429: "Rate limit exceeded. Please try again later.",
                        500: "n8n server error. Please check your n8n instance.",
                        502: "n8n bad gateway error.",
                        503: "n8n service unavailable.",
                        504: "n8n gateway timeout.",
                    }
                    user_message = error_messages.get(
                        status_code,
                        "An error occurred while communicating with n8n."
                    )
                    raise Exception(user_message)
                raise last_exception

        return wrapper
    return decorator


class N8nMCPServer:
    """MCP Server for n8n API integration."""

    def __init__(self, n8n_url: str, api_key: str, timeout: float = 30.0, verify_ssl: bool = True):
        from urllib.parse import urlparse

        # Validate and check HTTPS
        parsed_url = urlparse(n8n_url)
        if parsed_url.scheme == 'http' and 'localhost' not in parsed_url.netloc and '127.0.0.1' not in parsed_url.netloc:
            logger.warning(
                "WARNING: Using unencrypted HTTP connection to n8n. "
                "Your API key will be transmitted in plaintext. "
                "Consider using HTTPS for security."
            )

        self.n8n_url = n8n_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.server = Server("n8n-mcp-server")
        self.client: Optional[httpx.AsyncClient] = None
        self._api_key = api_key

        if not verify_ssl:
            logger.warning(
                "SSL certificate verification is DISABLED. "
                "This should only be used in development environments!"
            )

        logger.info(f"HTTP timeout configured: {timeout}s")
        self._setup_handlers()

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                timeout=self.timeout,
                connect=10.0,
                read=self.timeout,
                write=10.0,
                pool=5.0
            ),
            headers={
                "X-N8N-API-KEY": self._api_key,
                "Content-Type": "application/json",
            },
            verify=self.verify_ssl,
            follow_redirects=False,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
            )
        )
        logger.info("n8n MCP Server initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
            logger.info("n8n MCP Server client closed")
        return False

    def _validate_id(self, id_value: Any, id_name: str = "ID") -> str:
        """
        Validate that an ID is safe to use in URLs.

        Args:
            id_value: The ID to validate
            id_name: Name of the ID for error messages

        Returns:
            The validated ID as a string

        Raises:
            ValueError: If the ID is invalid
        """
        if not id_value:
            raise ValueError(f"{id_name} is required")

        # Convert to string
        id_str = str(id_value).strip()

        # Check for empty after stripping
        if not id_str:
            raise ValueError(f"{id_name} cannot be empty")

        # Validate format - n8n IDs are typically numeric or alphanumeric
        # Allow: numbers, letters, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', id_str):
            raise ValueError(
                f"{id_name} contains invalid characters. "
                f"Only alphanumeric, hyphens, and underscores are allowed."
            )

        # Check length (n8n IDs shouldn't be extremely long)
        if len(id_str) > 100:
            raise ValueError(f"{id_name} is too long (max 100 characters)")

        # Prevent path traversal attempts
        if '..' in id_str or '/' in id_str or '\\' in id_str:
            raise ValueError(f"{id_name} contains invalid path characters")

        return id_str

    @async_retry_with_backoff()
    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Any:
        """Make a request to the n8n API with automatic retry logic."""
        url = f"{self.n8n_url}/api/v1{endpoint}"

        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=data,
                params=params,
            )
            response.raise_for_status()

            # Some endpoints return empty responses
            if response.status_code == 204 or not response.content:
                return {"success": True}

            return response.json()

        except httpx.HTTPStatusError as e:
            # Log full error internally for debugging
            logger.error(f"n8n API error: {method} {endpoint} - {e.response.status_code} - {str(e)}")

            status_code = e.response.status_code

            # For retryable errors, re-raise the original HTTPStatusError
            # so the decorator can handle retries
            if status_code in RETRYABLE_STATUS_CODES:
                raise

            # For non-retryable errors, convert to user-friendly message
            error_messages = {
                401: "Authentication failed. Please check your API key.",
                403: "Access denied. Insufficient permissions.",
                404: "Resource not found.",
            }
            user_message = error_messages.get(
                status_code,
                "An error occurred while communicating with n8n."
            )
            raise Exception(user_message)

        except httpx.RequestError as e:
            # Log full error internally
            logger.error(f"Request error: {method} {endpoint} - {str(e)}")
            # For connection/network errors, re-raise so decorator can retry
            # The decorator will convert to a user-friendly message after retries are exhausted
            raise

    def _setup_handlers(self):
        """Set up MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="list_workflows",
                    description=(
                        "List all workflows in n8n with enhanced filtering options. "
                        "Returns workflow names, IDs, active status, tags, and timestamps."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "active": {
                                "type": "boolean",
                                "description": "Filter by active status (optional)",
                            },
                            "name": {
                                "type": "string",
                                "description": "Filter by workflow name (case-insensitive substring match, optional)",
                            },
                            "tags": {
                                "type": "string",
                                "description": "Filter by tag names (comma-separated, workflow must have all specified tags, optional)",
                            },
                            "created_after": {
                                "type": "string",
                                "description": "Filter workflows created after this date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ, optional)",
                            },
                            "updated_after": {
                                "type": "string",
                                "description": "Filter workflows updated after this date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ, optional)",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_workflow",
                    description=(
                        "Get detailed information about a specific workflow including its nodes and connections."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "The workflow ID",
                            }
                        },
                        "required": ["workflow_id"],
                    },
                ),
                Tool(
                    name="create_workflow",
                    description="Create a new workflow in n8n.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the workflow",
                            },
                            "nodes": {
                                "type": "array",
                                "description": "Array of workflow nodes",
                            },
                            "connections": {
                                "type": "object",
                                "description": "Connections between nodes",
                            },
                            "active": {
                                "type": "boolean",
                                "description": "Whether the workflow should be active",
                                "default": False,
                            },
                            "settings": {
                                "type": "object",
                                "description": "Workflow settings",
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Workflow tags",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="update_workflow",
                    description="Update an existing workflow.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "The workflow ID to update",
                            },
                            "name": {
                                "type": "string",
                                "description": "New name for the workflow",
                            },
                            "nodes": {
                                "type": "array",
                                "description": "Updated workflow nodes",
                            },
                            "connections": {
                                "type": "object",
                                "description": "Updated connections between nodes",
                            },
                            "active": {
                                "type": "boolean",
                                "description": "Whether the workflow should be active",
                            },
                            "settings": {
                                "type": "object",
                                "description": "Updated workflow settings",
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Updated workflow tags",
                            },
                        },
                        "required": ["workflow_id"],
                    },
                ),
                Tool(
                    name="delete_workflow",
                    description="Delete a workflow from n8n.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "The workflow ID to delete",
                            }
                        },
                        "required": ["workflow_id"],
                    },
                ),
                Tool(
                    name="activate_workflow",
                    description="Activate a workflow to start it running.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "The workflow ID to activate",
                            }
                        },
                        "required": ["workflow_id"],
                    },
                ),
                Tool(
                    name="deactivate_workflow",
                    description="Deactivate a workflow to stop it from running.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "The workflow ID to deactivate",
                            }
                        },
                        "required": ["workflow_id"],
                    },
                ),
                Tool(
                    name="execute_workflow",
                    description="Execute a workflow manually with optional input data.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "The workflow ID to execute",
                            },
                            "data": {
                                "type": "object",
                                "description": "Input data for the workflow execution",
                            },
                        },
                        "required": ["workflow_id"],
                    },
                ),
                Tool(
                    name="list_executions",
                    description="List workflow executions with optional filtering.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "Filter by workflow ID (optional)",
                            },
                            "status": {
                                "type": "string",
                                "description": "Filter by status: success, error, waiting, running (optional)",
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of executions to return (default: 20)",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_execution",
                    description="Get detailed information about a specific execution.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "execution_id": {
                                "type": "string",
                                "description": "The execution ID",
                            }
                        },
                        "required": ["execution_id"],
                    },
                ),
                Tool(
                    name="delete_execution",
                    description="Delete an execution from n8n.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "execution_id": {
                                "type": "string",
                                "description": "The execution ID to delete",
                            }
                        },
                        "required": ["execution_id"],
                    },
                ),
                Tool(
                    name="list_credentials",
                    description="List all credentials in n8n.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "description": "Filter by credential type (optional)",
                            }
                        },
                    },
                ),
                Tool(
                    name="list_tags",
                    description="List all tags used in workflows.",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="list_webhooks",
                    description=(
                        "List all webhook endpoints across workflows. Returns workflows containing webhook nodes "
                        "with their URLs, HTTP methods, and active status."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "active": {
                                "type": "boolean",
                                "description": "Filter by active workflow status (optional)",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_webhook",
                    description=(
                        "Get detailed information about a webhook by workflow ID. "
                        "Returns webhook configuration including URL paths, HTTP methods, authentication, and response settings."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "The workflow ID containing the webhook",
                            }
                        },
                        "required": ["workflow_id"],
                    },
                ),
                Tool(
                    name="test_webhook",
                    description=(
                        "Test a webhook endpoint by executing its workflow with test data. "
                        "Returns the execution result to verify webhook functionality."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "The workflow ID containing the webhook to test",
                            },
                            "data": {
                                "type": "object",
                                "description": "Test data to send to the webhook (optional)",
                            },
                        },
                        "required": ["workflow_id"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "list_workflows":
                    result = await self._list_workflows(arguments)
                elif name == "get_workflow":
                    result = await self._get_workflow(arguments)
                elif name == "create_workflow":
                    result = await self._create_workflow(arguments)
                elif name == "update_workflow":
                    result = await self._update_workflow(arguments)
                elif name == "delete_workflow":
                    result = await self._delete_workflow(arguments)
                elif name == "activate_workflow":
                    result = await self._activate_workflow(arguments)
                elif name == "deactivate_workflow":
                    result = await self._deactivate_workflow(arguments)
                elif name == "execute_workflow":
                    result = await self._execute_workflow(arguments)
                elif name == "list_executions":
                    result = await self._list_executions(arguments)
                elif name == "get_execution":
                    result = await self._get_execution(arguments)
                elif name == "delete_execution":
                    result = await self._delete_execution(arguments)
                elif name == "list_credentials":
                    result = await self._list_credentials(arguments)
                elif name == "list_tags":
                    result = await self._list_tags(arguments)
                elif name == "list_webhooks":
                    result = await self._list_webhooks(arguments)
                elif name == "get_webhook":
                    result = await self._get_webhook(arguments)
                elif name == "test_webhook":
                    result = await self._test_webhook(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Tool implementations
    async def _list_workflows(self, args: dict) -> Any:
        """List workflows with enhanced filtering.

        Supports filtering by:
        - active: boolean (API-level filter)
        - name: substring match (client-side filter)
        - tags: comma-separated tag names (client-side filter)
        - created_after: ISO 8601 date (client-side filter)
        - updated_after: ISO 8601 date (client-side filter)
        """
        # API-level filtering (supported by n8n API)
        params = {}
        if args.get("active") is not None:
            params["active"] = str(args["active"]).lower()

        # Get workflows from API
        response = await self._make_request("/workflows", params=params)

        # Client-side filtering for enhanced options
        workflows = response.get("data", [])

        # Filter by name (case-insensitive substring match)
        if args.get("name"):
            name_filter = args["name"].lower()
            workflows = [
                w for w in workflows
                if name_filter in w.get("name", "").lower()
            ]

        # Filter by tags (comma-separated, must have all specified tags)
        if args.get("tags"):
            required_tags = [tag.strip().lower() for tag in args["tags"].split(",")]
            workflows = [
                w for w in workflows
                if all(
                    any(tag.lower() == req_tag for tag in w.get("tags", []))
                    for req_tag in required_tags
                )
            ]

        # Filter by created_after date
        if args.get("created_after"):
            try:
                created_after = self._parse_date(args["created_after"])
                workflows = [
                    w for w in workflows
                    if w.get("createdAt") and self._parse_date(w["createdAt"]) >= created_after
                ]
            except ValueError as e:
                raise ValueError(f"Invalid created_after date format: {str(e)}")

        # Filter by updated_after date
        if args.get("updated_after"):
            try:
                updated_after = self._parse_date(args["updated_after"])
                workflows = [
                    w for w in workflows
                    if w.get("updatedAt") and self._parse_date(w["updatedAt"]) >= updated_after
                ]
            except ValueError as e:
                raise ValueError(f"Invalid updated_after date format: {str(e)}")

        # Return filtered results in the same format as the API
        return {"data": workflows}

    def _parse_date(self, date_str: str) -> datetime:
        """Parse ISO 8601 date string to datetime object.

        Supports formats:
        - YYYY-MM-DD
        - YYYY-MM-DDTHH:MM:SSZ
        - YYYY-MM-DDTHH:MM:SS.fffZ
        """
        # Try full ISO 8601 format with timezone
        for fmt in [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d"
        ]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(
            f"Date must be in ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ): {date_str}"
        )

    async def _get_workflow(self, args: dict) -> Any:
        """Get workflow details."""
        workflow_id = self._validate_id(args.get('workflow_id'), "Workflow ID")
        return await self._make_request(f"/workflows/{workflow_id}")

    async def _create_workflow(self, args: dict) -> Any:
        """Create workflow."""
        data = {
            "name": args["name"],
            "nodes": args.get("nodes", []),
            "connections": args.get("connections", {}),
            "active": args.get("active", False),
            "settings": args.get("settings", {}),
        }

        if "tags" in args:
            data["tags"] = args["tags"]

        return await self._make_request("/workflows", method="POST", data=data)

    async def _update_workflow(self, args: dict) -> Any:
        """Update workflow."""
        workflow_id = self._validate_id(args.get("workflow_id"), "Workflow ID")
        # Create a copy of args and remove workflow_id
        data = {k: v for k, v in args.items() if k != "workflow_id" and v is not None}

        return await self._make_request(
            f"/workflows/{workflow_id}", method="PATCH", data=data
        )

    async def _delete_workflow(self, args: dict) -> Any:
        """Delete workflow."""
        workflow_id = self._validate_id(args.get('workflow_id'), "Workflow ID")
        return await self._make_request(
            f"/workflows/{workflow_id}", method="DELETE"
        )

    async def _activate_workflow(self, args: dict) -> Any:
        """Activate workflow."""
        workflow_id = self._validate_id(args.get('workflow_id'), "Workflow ID")
        return await self._make_request(
            f"/workflows/{workflow_id}",
            method="PATCH",
            data={"active": True},
        )

    async def _deactivate_workflow(self, args: dict) -> Any:
        """Deactivate workflow."""
        workflow_id = self._validate_id(args.get('workflow_id'), "Workflow ID")
        return await self._make_request(
            f"/workflows/{workflow_id}",
            method="PATCH",
            data={"active": False},
        )

    async def _execute_workflow(self, args: dict) -> Any:
        """Execute workflow."""
        workflow_id = self._validate_id(args.get('workflow_id'), "Workflow ID")
        data = {}
        if args.get("data"):
            data = args["data"]

        return await self._make_request(
            f"/workflows/{workflow_id}/execute", method="POST", data=data
        )

    async def _list_executions(self, args: dict) -> Any:
        """List executions."""
        params = {}
        if args.get("workflow_id"):
            params["workflowId"] = args["workflow_id"]
        if args.get("status"):
            params["status"] = args["status"]
        if args.get("limit"):
            params["limit"] = args["limit"]

        return await self._make_request("/executions", params=params)

    async def _get_execution(self, args: dict) -> Any:
        """Get execution details."""
        execution_id = self._validate_id(args.get('execution_id'), "Execution ID")
        return await self._make_request(f"/executions/{execution_id}")

    async def _delete_execution(self, args: dict) -> Any:
        """Delete execution."""
        execution_id = self._validate_id(args.get('execution_id'), "Execution ID")
        return await self._make_request(
            f"/executions/{execution_id}", method="DELETE"
        )

    async def _list_credentials(self, args: dict) -> Any:
        """List credentials."""
        params = {}
        if args.get("type"):
            params["type"] = args["type"]

        return await self._make_request("/credentials", params=params)

    async def _list_tags(self, args: dict) -> Any:
        """List tags."""
        return await self._make_request("/tags")

    async def _list_webhooks(self, args: dict) -> Any:
        """
        List all webhook endpoints across workflows.

        This scans all workflows and extracts webhook node information.
        """
        # Get all workflows with optional active filter
        params = {}
        if args.get("active") is not None:
            params["active"] = str(args["active"]).lower()

        workflows_response = await self._make_request("/workflows", params=params)

        # Extract workflows data (handle both direct array and {data: array} formats)
        workflows = workflows_response
        if isinstance(workflows_response, dict) and "data" in workflows_response:
            workflows = workflows_response["data"]

        # Extract webhook information from each workflow
        webhook_list = []
        for workflow in workflows:
            workflow_id = workflow.get("id")
            workflow_name = workflow.get("name")
            is_active = workflow.get("active", False)

            # Get full workflow details to access nodes
            try:
                workflow_details = await self._make_request(f"/workflows/{workflow_id}")
                nodes = workflow_details.get("nodes", [])

                # Find webhook nodes
                for node in nodes:
                    node_type = node.get("type", "")
                    if node_type == "n8n-nodes-base.webhook":
                        webhook_info = {
                            "workflow_id": workflow_id,
                            "workflow_name": workflow_name,
                            "workflow_active": is_active,
                            "node_name": node.get("name"),
                            "node_id": node.get("id"),
                            "webhook_path": node.get("parameters", {}).get("path", ""),
                            "http_method": node.get("parameters", {}).get("httpMethod", "GET"),
                            "response_mode": node.get("parameters", {}).get("responseMode", "onReceived"),
                            "authentication": node.get("parameters", {}).get("authentication", "none"),
                        }
                        webhook_list.append(webhook_info)
            except Exception as e:
                # Log error but continue processing other workflows
                logger.warning(f"Error processing workflow {workflow_id}: {str(e)}")
                continue

        return {
            "webhooks": webhook_list,
            "total_count": len(webhook_list)
        }

    async def _get_webhook(self, args: dict) -> Any:
        """
        Get detailed webhook information for a specific workflow.

        Returns webhook nodes and their configuration.
        """
        workflow_id = self._validate_id(args.get('workflow_id'), "Workflow ID")

        # Get workflow details
        workflow = await self._make_request(f"/workflows/{workflow_id}")

        nodes = workflow.get("nodes", [])
        webhook_nodes = []

        # Find all webhook nodes in the workflow
        for node in nodes:
            node_type = node.get("type", "")
            if node_type == "n8n-nodes-base.webhook":
                parameters = node.get("parameters", {})
                webhook_config = {
                    "node_name": node.get("name"),
                    "node_id": node.get("id"),
                    "webhook_path": parameters.get("path", ""),
                    "http_method": parameters.get("httpMethod", "GET"),
                    "response_mode": parameters.get("responseMode", "onReceived"),
                    "response_data": parameters.get("responseData", "firstEntryJson"),
                    "authentication": parameters.get("authentication", "none"),
                    "allowed_origins": parameters.get("allowedOrigins", "*"),
                    "response_code": parameters.get("responseCode", 200),
                    "response_headers": parameters.get("responseHeaders", {}),
                }

                # Add IP whitelist if configured
                if parameters.get("ipWhitelist"):
                    webhook_config["ip_whitelist"] = parameters.get("ipWhitelist")

                webhook_nodes.append(webhook_config)

        if not webhook_nodes:
            raise ValueError(f"No webhook nodes found in workflow {workflow_id}")

        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.get("name"),
            "workflow_active": workflow.get("active", False),
            "webhook_nodes": webhook_nodes,
            "total_webhook_nodes": len(webhook_nodes)
        }

    async def _test_webhook(self, args: dict) -> Any:
        """
        Test a webhook by executing its workflow.

        This validates that the webhook workflow can execute successfully.
        """
        workflow_id = self._validate_id(args.get('workflow_id'), "Workflow ID")

        # First verify the workflow contains webhook nodes
        workflow = await self._make_request(f"/workflows/{workflow_id}")
        nodes = workflow.get("nodes", [])

        has_webhook = any(
            node.get("type") == "n8n-nodes-base.webhook"
            for node in nodes
        )

        if not has_webhook:
            raise ValueError(
                f"Workflow {workflow_id} does not contain any webhook nodes. "
                "Cannot test a non-webhook workflow."
            )

        # Execute the workflow with test data
        data = args.get("data", {})

        execution_result = await self._make_request(
            f"/workflows/{workflow_id}/execute",
            method="POST",
            data=data
        )

        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.get("name"),
            "test_result": "success",
            "execution": execution_result,
            "message": "Webhook workflow executed successfully"
        }

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def async_main():
    """Async main function with proper resource cleanup."""
    # Configure logging level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.getLogger().setLevel(getattr(logging, log_level, logging.INFO))

    logger.info("Starting n8n MCP Server")

    n8n_url = os.getenv("N8N_URL", "http://localhost:5678")
    api_key = os.getenv("N8N_API_KEY")

    # Configure timeout
    try:
        timeout = float(os.getenv("N8N_TIMEOUT", "30"))
    except ValueError:
        logger.warning("Invalid N8N_TIMEOUT value, using default 30s")
        timeout = 30.0

    # Configure SSL verification
    verify_ssl = os.getenv("N8N_VERIFY_SSL", "true").lower() != "false"

    if not api_key:
        logger.error("N8N_API_KEY environment variable is not set")
        raise ValueError("N8N_API_KEY environment variable is required")

    # Use async context manager for proper cleanup
    async with N8nMCPServer(n8n_url, api_key, timeout=timeout, verify_ssl=verify_ssl) as server:
        # Setup graceful shutdown
        shutdown_event = asyncio.Event()

        def signal_handler(signum, frame):
            """Handle shutdown signals."""
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            shutdown_event.set()

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Run server with shutdown handling
            server_task = asyncio.create_task(server.run())
            shutdown_task = asyncio.create_task(shutdown_event.wait())

            # Wait for either server to finish or shutdown signal
            done, pending = await asyncio.wait(
                [server_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            logger.info("n8n MCP Server stopped")

        except Exception as e:
            logger.exception("Server error")
            raise


def main():
    """Main entry point."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()

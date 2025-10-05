"""n8n MCP Server - Python Implementation"""

import asyncio
import json
import os
from typing import Any, Optional

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


class N8nMCPServer:
    """MCP Server for n8n API integration."""

    def __init__(self, n8n_url: str, api_key: str):
        self.n8n_url = n8n_url.rstrip("/")
        self.api_key = api_key
        self.server = Server("n8n-mcp-server")
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "X-N8N-API-KEY": self.api_key,
                "Content-Type": "application/json",
            },
        )
        self._setup_handlers()

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Any:
        """Make a request to the n8n API."""
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

        except httpx.HTTPError as e:
            raise Exception(f"n8n API error: {str(e)}")

    def _setup_handlers(self):
        """Set up MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="list_workflows",
                    description=(
                        "List all workflows in n8n. Returns workflow names, IDs, active status, and tags."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "active": {
                                "type": "boolean",
                                "description": "Filter by active status (optional)",
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
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Tool implementations
    async def _list_workflows(self, args: dict) -> Any:
        """List workflows."""
        params = {}
        if args.get("active") is not None:
            params["active"] = str(args["active"]).lower()

        return await self._make_request("/workflows", params=params)

    async def _get_workflow(self, args: dict) -> Any:
        """Get workflow details."""
        return await self._make_request(f"/workflows/{args['workflow_id']}")

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
        workflow_id = args.pop("workflow_id")
        data = {k: v for k, v in args.items() if v is not None}

        return await self._make_request(
            f"/workflows/{workflow_id}", method="PATCH", data=data
        )

    async def _delete_workflow(self, args: dict) -> Any:
        """Delete workflow."""
        return await self._make_request(
            f"/workflows/{args['workflow_id']}", method="DELETE"
        )

    async def _activate_workflow(self, args: dict) -> Any:
        """Activate workflow."""
        return await self._make_request(
            f"/workflows/{args['workflow_id']}",
            method="PATCH",
            data={"active": True},
        )

    async def _deactivate_workflow(self, args: dict) -> Any:
        """Deactivate workflow."""
        return await self._make_request(
            f"/workflows/{args['workflow_id']}",
            method="PATCH",
            data={"active": False},
        )

    async def _execute_workflow(self, args: dict) -> Any:
        """Execute workflow."""
        data = {}
        if args.get("data"):
            data = args["data"]

        return await self._make_request(
            f"/workflows/{args['workflow_id']}/execute", method="POST", data=data
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
        return await self._make_request(f"/executions/{args['execution_id']}")

    async def _delete_execution(self, args: dict) -> Any:
        """Delete execution."""
        return await self._make_request(
            f"/executions/{args['execution_id']}", method="DELETE"
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

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

    async def cleanup(self):
        """Cleanup resources."""
        await self.client.aclose()


def main():
    """Main entry point."""
    n8n_url = os.getenv("N8N_URL", "http://localhost:5678")
    api_key = os.getenv("N8N_API_KEY")

    if not api_key:
        raise ValueError("N8N_API_KEY environment variable is required")

    server = N8nMCPServer(n8n_url, api_key)

    try:
        asyncio.run(server.run())
    finally:
        asyncio.run(server.cleanup())


if __name__ == "__main__":
    main()

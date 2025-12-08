"""A2A (Agent-to-Agent) HTTP Server Wrapper for n8n MCP Server."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import httpx
from mcp.types import CallToolResult, TextContent

logger = logging.getLogger(__name__)


class A2AServer:
    """
    HTTP server wrapper providing A2A protocol endpoints for the n8n MCP Server.

    This enables agent-to-agent communication via HTTP instead of stdio transport.
    """

    def __init__(self, n8n_url: str, api_key: str, timeout: float = 30.0, verify_ssl: bool = True):
        """Initialize A2A server."""
        from . import N8nMCPServer

        self.mcp_server = N8nMCPServer(n8n_url, api_key, timeout, verify_ssl)
        self.n8n_url = n8n_url
        self.api_key = api_key

    async def __aenter__(self):
        """Async context manager entry."""
        await self.mcp_server.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        return await self.mcp_server.__aexit__(exc_type, exc_val, exc_tb)

    async def get_agent_card(self) -> dict:
        """
        Get the agent card for A2A discovery.

        Returns:
            dict: Agent card with capabilities and skills
        """
        agent_card_path = Path(__file__).parent.parent.parent / "agent-card.json"

        if agent_card_path.exists():
            with open(agent_card_path, 'r') as f:
                return json.load(f)

        # Fallback: generate basic agent card from available tools
        return {
            "name": "n8n-mcp-server",
            "version": "1.0.0",
            "description": "Model Context Protocol server for n8n API integration",
            "protocols": {
                "mcp": {"version": "1.0", "supported": True},
                "a2a": {"version": "1.0", "supported": True}
            }
        }

    async def get_capabilities(self) -> dict:
        """
        Get server capabilities for A2A protocol.

        Returns:
            dict: Server capabilities including available skills
        """
        # Get tools from MCP server
        tools = []

        # Access the tools handler
        list_tools_handler = None
        for handler in self.mcp_server.server._tool_list_handlers:
            list_tools_handler = handler
            break

        if list_tools_handler:
            tools = await list_tools_handler()

        skills = []
        for tool in tools:
            skill = {
                "id": tool.name,
                "name": tool.name.replace('_', ' ').title(),
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            skills.append(skill)

        return {
            "capabilities": {
                "streaming": False,
                "async_execution": True,
                "batch_operations": True
            },
            "skills": skills,
            "authentication": {
                "required": True,
                "methods": ["api_key"]
            }
        }

    async def execute_skill(self, skill_id: str, parameters: dict) -> dict:
        """
        Execute a skill (tool) via A2A protocol.

        Args:
            skill_id: The skill/tool ID to execute
            parameters: Parameters for the skill execution

        Returns:
            dict: Execution result
        """
        try:
            # Get the call_tool handler
            call_tool_handler = None
            for handler in self.mcp_server.server._tool_call_handlers:
                call_tool_handler = handler
                break

            if not call_tool_handler:
                return {
                    "success": False,
                    "error": "Tool execution handler not found"
                }

            # Execute the tool
            result = await call_tool_handler(skill_id, parameters)

            # Extract text content from result
            if isinstance(result, list) and len(result) > 0:
                content = result[0]
                if isinstance(content, TextContent):
                    try:
                        # Try to parse as JSON
                        data = json.loads(content.text)
                        return {
                            "success": True,
                            "result": data
                        }
                    except json.JSONDecodeError:
                        # Return as plain text
                        return {
                            "success": True,
                            "result": content.text
                        }

            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            logger.exception(f"Error executing skill {skill_id}")
            return {
                "success": False,
                "error": str(e)
            }

    async def batch_execute(self, requests: list[dict]) -> list[dict]:
        """
        Execute multiple skills in batch.

        Args:
            requests: List of skill execution requests

        Returns:
            list: List of execution results
        """
        results = []

        for request in requests:
            skill_id = request.get('skill_id')
            parameters = request.get('parameters', {})

            if not skill_id:
                results.append({
                    "success": False,
                    "error": "Missing skill_id"
                })
                continue

            result = await self.execute_skill(skill_id, parameters)
            results.append(result)

        return results


async def create_fastapi_app():
    """
    Create a FastAPI application for A2A HTTP endpoints.

    This function is optional and requires FastAPI to be installed.
    Run with: uvicorn n8n_mcp_server.a2a_server:app --host 0.0.0.0 --port 8000

    Returns:
        FastAPI: Configured FastAPI application
    """
    try:
        from fastapi import FastAPI, HTTPException, Header, Request
        from fastapi.responses import JSONResponse
    except ImportError:
        raise ImportError(
            "FastAPI is required for HTTP server mode. "
            "Install with: pip install fastapi uvicorn"
        )

    app = FastAPI(
        title="n8n MCP Server - A2A Protocol",
        description="Agent-to-Agent HTTP endpoints for n8n MCP Server",
        version="1.0.0"
    )

    # Global server instance
    server: Optional[A2AServer] = None

    @app.on_event("startup")
    async def startup():
        """Initialize server on startup."""
        nonlocal server

        n8n_url = os.getenv("N8N_URL", "http://localhost:5678")
        api_key = os.getenv("N8N_API_KEY")

        if not api_key:
            raise ValueError("N8N_API_KEY environment variable is required")

        timeout = float(os.getenv("N8N_TIMEOUT", "30"))
        verify_ssl = os.getenv("N8N_VERIFY_SSL", "true").lower() != "false"

        server = A2AServer(n8n_url, api_key, timeout, verify_ssl)
        await server.__aenter__()

        logger.info("A2A Server started")

    @app.on_event("shutdown")
    async def shutdown():
        """Cleanup on shutdown."""
        nonlocal server
        if server:
            await server.__aexit__(None, None, None)
            logger.info("A2A Server stopped")

    def verify_api_key(x_n8n_api_key: Optional[str] = Header(None)):
        """Verify API key from request header."""
        expected_key = os.getenv("N8N_API_KEY")

        if not x_n8n_api_key or x_n8n_api_key != expected_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )

    @app.get("/.well-known/agent-card.json")
    async def get_agent_card():
        """A2A Discovery endpoint - returns agent card."""
        if not server:
            raise HTTPException(status_code=503, detail="Server not initialized")

        return await server.get_agent_card()

    @app.get("/a2a/capabilities")
    async def get_capabilities(x_n8n_api_key: Optional[str] = Header(None)):
        """Get server capabilities."""
        verify_api_key(x_n8n_api_key)

        if not server:
            raise HTTPException(status_code=503, detail="Server not initialized")

        return await server.get_capabilities()

    @app.post("/a2a/execute")
    async def execute_skill(
        request: Request,
        x_n8n_api_key: Optional[str] = Header(None)
    ):
        """Execute a skill."""
        verify_api_key(x_n8n_api_key)

        if not server:
            raise HTTPException(status_code=503, detail="Server not initialized")

        body = await request.json()
        skill_id = body.get('skill_id')
        parameters = body.get('parameters', {})

        if not skill_id:
            raise HTTPException(status_code=400, detail="Missing skill_id")

        result = await server.execute_skill(skill_id, parameters)

        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Execution failed')
            )

        return result

    @app.post("/a2a/batch")
    async def batch_execute(
        request: Request,
        x_n8n_api_key: Optional[str] = Header(None)
    ):
        """Execute multiple skills in batch."""
        verify_api_key(x_n8n_api_key)

        if not server:
            raise HTTPException(status_code=503, detail="Server not initialized")

        body = await request.json()
        requests = body.get('requests', [])

        if not requests:
            raise HTTPException(status_code=400, detail="Missing requests array")

        results = await server.batch_execute(requests)

        return {
            "success": True,
            "results": results
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "server": "n8n-mcp-server-a2a",
            "version": "1.0.0"
        }

    return app


# Create app instance for uvicorn
app = None
try:
    app = asyncio.run(create_fastapi_app())
except Exception as e:
    logger.warning(f"Could not create FastAPI app: {e}")
    logger.info("A2A HTTP mode requires FastAPI. Install with: pip install fastapi uvicorn")

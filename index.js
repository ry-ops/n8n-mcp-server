#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

// Configuration from environment variables
const N8N_URL = process.env.N8N_URL || 'http://localhost:5678';
const N8N_API_KEY = process.env.N8N_API_KEY;

if (!N8N_API_KEY) {
  console.error('Error: N8N_API_KEY environment variable is required');
  process.exit(1);
}

// Create axios instance with default config
const n8nApi = axios.create({
  baseURL: `${N8N_URL}/api/v1`,
  headers: {
    'X-N8N-API-KEY': N8N_API_KEY,
    'Content-Type': 'application/json',
  },
});

// Create MCP server
const server = new Server(
  {
    name: 'n8n-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'list_workflows',
        description: 'List all workflows in n8n. Returns workflow names, IDs, active status, and tags.',
        inputSchema: {
          type: 'object',
          properties: {
            active: {
              type: 'boolean',
              description: 'Filter by active status (optional)',
            },
          },
        },
      },
      {
        name: 'get_workflow',
        description: 'Get detailed information about a specific workflow including its nodes and connections.',
        inputSchema: {
          type: 'object',
          properties: {
            workflowId: {
              type: 'string',
              description: 'The ID of the workflow to retrieve',
            },
          },
          required: ['workflowId'],
        },
      },
      {
        name: 'execute_workflow',
        description: 'Execute a workflow by ID. Can optionally provide input data.',
        inputSchema: {
          type: 'object',
          properties: {
            workflowId: {
              type: 'string',
              description: 'The ID of the workflow to execute',
            },
            data: {
              type: 'object',
              description: 'Optional input data to pass to the workflow',
            },
          },
          required: ['workflowId'],
        },
      },
      {
        name: 'activate_workflow',
        description: 'Activate a workflow to enable automatic execution.',
        inputSchema: {
          type: 'object',
          properties: {
            workflowId: {
              type: 'string',
              description: 'The ID of the workflow to activate',
            },
          },
          required: ['workflowId'],
        },
      },
      {
        name: 'deactivate_workflow',
        description: 'Deactivate a workflow to disable automatic execution.',
        inputSchema: {
          type: 'object',
          properties: {
            workflowId: {
              type: 'string',
              description: 'The ID of the workflow to deactivate',
            },
          },
          required: ['workflowId'],
        },
      },
      {
        name: 'list_executions',
        description: 'List recent workflow executions with their status and details.',
        inputSchema: {
          type: 'object',
          properties: {
            workflowId: {
              type: 'string',
              description: 'Filter executions by workflow ID (optional)',
            },
            status: {
              type: 'string',
              enum: ['success', 'error', 'waiting', 'running'],
              description: 'Filter by execution status (optional)',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of executions to return (default: 20)',
              default: 20,
            },
          },
        },
      },
      {
        name: 'get_execution',
        description: 'Get detailed information about a specific workflow execution including its data.',
        inputSchema: {
          type: 'object',
          properties: {
            executionId: {
              type: 'string',
              description: 'The ID of the execution to retrieve',
            },
          },
          required: ['executionId'],
        },
      },
      {
        name: 'create_workflow',
        description: 'Create a new workflow in n8n.',
        inputSchema: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: 'Name of the workflow',
            },
            nodes: {
              type: 'array',
              description: 'Array of workflow nodes',
            },
            connections: {
              type: 'object',
              description: 'Connections between nodes',
            },
            active: {
              type: 'boolean',
              description: 'Whether the workflow should be active',
              default: false,
            },
            settings: {
              type: 'object',
              description: 'Workflow settings (optional)',
            },
          },
          required: ['name', 'nodes', 'connections'],
        },
      },
      {
        name: 'update_workflow',
        description: 'Update an existing workflow.',
        inputSchema: {
          type: 'object',
          properties: {
            workflowId: {
              type: 'string',
              description: 'The ID of the workflow to update',
            },
            name: {
              type: 'string',
              description: 'New name for the workflow (optional)',
            },
            nodes: {
              type: 'array',
              description: 'Updated array of workflow nodes (optional)',
            },
            connections: {
              type: 'object',
              description: 'Updated connections between nodes (optional)',
            },
            active: {
              type: 'boolean',
              description: 'Whether the workflow should be active (optional)',
            },
          },
          required: ['workflowId'],
        },
      },
      {
        name: 'delete_workflow',
        description: 'Delete a workflow from n8n.',
        inputSchema: {
          type: 'object',
          properties: {
            workflowId: {
              type: 'string',
              description: 'The ID of the workflow to delete',
            },
          },
          required: ['workflowId'],
        },
      },
    ],
  };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const { name, arguments: args } = request.params;

    switch (name) {
      case 'list_workflows': {
        const params = {};
        if (args.active !== undefined) {
          params.active = args.active;
        }
        const response = await n8nApi.get('/workflows', { params });
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
      }

      case 'get_workflow': {
        const response = await n8nApi.get(`/workflows/${args.workflowId}`);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
      }

      case 'execute_workflow': {
        const response = await n8nApi.post(`/workflows/${args.workflowId}/execute`, {
          data: args.data || {},
        });
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
      }

      case 'activate_workflow': {
        const workflow = await n8nApi.get(`/workflows/${args.workflowId}`);
        const response = await n8nApi.patch(`/workflows/${args.workflowId}`, {
          ...workflow.data,
          active: true,
        });
        return {
          content: [
            {
              type: 'text',
              text: `Workflow ${args.workflowId} activated successfully`,
            },
          ],
        };
      }

      case 'deactivate_workflow': {
        const workflow = await n8nApi.get(`/workflows/${args.workflowId}`);
        const response = await n8nApi.patch(`/workflows/${args.workflowId}`, {
          ...workflow.data,
          active: false,
        });
        return {
          content: [
            {
              type: 'text',
              text: `Workflow ${args.workflowId} deactivated successfully`,
            },
          ],
        };
      }

      case 'list_executions': {
        const params = { limit: args.limit || 20 };
        if (args.workflowId) {
          params.workflowId = args.workflowId;
        }
        if (args.status) {
          params.status = args.status;
        }
        const response = await n8nApi.get('/executions', { params });
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
      }

      case 'get_execution': {
        const response = await n8nApi.get(`/executions/${args.executionId}`);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
      }

      case 'create_workflow': {
        const workflowData = {
          name: args.name,
          nodes: args.nodes,
          connections: args.connections,
          active: args.active || false,
          settings: args.settings || {},
        };
        const response = await n8nApi.post('/workflows', workflowData);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
      }

      case 'update_workflow': {
        const workflow = await n8nApi.get(`/workflows/${args.workflowId}`);
        const updateData = { ...workflow.data };
        
        if (args.name) updateData.name = args.name;
        if (args.nodes) updateData.nodes = args.nodes;
        if (args.connections) updateData.connections = args.connections;
        if (args.active !== undefined) updateData.active = args.active;
        
        const response = await n8nApi.patch(`/workflows/${args.workflowId}`, updateData);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
      }

      case 'delete_workflow': {
        await n8nApi.delete(`/workflows/${args.workflowId}`);
        return {
          content: [
            {
              type: 'text',
              text: `Workflow ${args.workflowId} deleted successfully`,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    if (error.response) {
      return {
        content: [
          {
            type: 'text',
            text: `API Error: ${error.response.status} - ${JSON.stringify(error.response.data)}`,
          },
        ],
        isError: true,
      };
    }
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('n8n MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});

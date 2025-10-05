# n8n MCP Server

A Model Context Protocol (MCP) server that provides Claude Desktop with access to your self-hosted n8n instance. Control workflows, monitor executions, and manage automation directly through Claude.

## Features

- **Workflow Management**: List, create, update, and delete workflows
- **Workflow Execution**: Execute workflows manually with optional input data
- **Workflow Control**: Activate and deactivate workflows
- **Execution Monitoring**: View execution history and details
- **Full API Access**: Comprehensive integration with n8n's REST API

## Prerequisites

- Node.js 18 or higher
- A self-hosted n8n instance (version 1.0+)
- Claude Desktop application
- n8n API key

## Getting Your n8n API Key

1. Open your n8n instance
2. Go to **Settings** → **API**
3. Click **Create API Key**
4. Copy the generated API key (you won't be able to see it again!)

## Installation

1. **Clone or download this directory** to your local machine

2. **Install dependencies:**
   ```bash
   cd n8n-mcp-server
   npm install
   ```

3. **Create environment configuration:**
   ```bash
   cp .env.example .env
   ```

4. **Edit `.env` file** with your n8n details:
   ```
   N8N_URL=http://localhost:5678
   N8N_API_KEY=your_actual_api_key_here
   ```

   If your n8n instance is running on a different host or port, update the URL accordingly.

## Configuration for Claude Desktop

Add this server to your Claude Desktop configuration file:

### macOS
Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
Edit: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration Content

```json
{
  "mcpServers": {
    "n8n": {
      "command": "node",
      "args": ["/absolute/path/to/n8n-mcp-server/index.js"],
      "env": {
        "N8N_URL": "http://localhost:5678",
        "N8N_API_KEY": "your_actual_api_key_here"
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/n8n-mcp-server/index.js` with the actual full path to the index.js file.

## Usage

Once configured, restart Claude Desktop. You can now interact with your n8n instance through natural conversation:

### Example Commands

**List all workflows:**
```
Show me all my n8n workflows
```

**Get workflow details:**
```
Get details for workflow ID abc123
```

**Execute a workflow:**
```
Execute workflow xyz789
```

**Execute with custom data:**
```
Execute workflow abc123 with this data: {"email": "user@example.com", "name": "John"}
```

**Activate/Deactivate workflows:**
```
Activate workflow abc123
```

**View executions:**
```
Show me the last 10 workflow executions
```

**Filter executions:**
```
Show me failed executions for workflow abc123
```

**Create a workflow:**
```
Create a new workflow that sends an email when a webhook is triggered
```

## Available Tools

The MCP server exposes these tools to Claude:

- `list_workflows` - List all workflows with optional filtering
- `get_workflow` - Get detailed workflow information
- `execute_workflow` - Execute a workflow manually
- `activate_workflow` - Activate a workflow
- `deactivate_workflow` - Deactivate a workflow
- `list_executions` - List workflow executions
- `get_execution` - Get detailed execution information
- `create_workflow` - Create a new workflow
- `update_workflow` - Update an existing workflow
- `delete_workflow` - Delete a workflow

## Troubleshooting

### Server not appearing in Claude Desktop

1. Check that the path in `claude_desktop_config.json` is absolute and correct
2. Verify that Node.js is in your system PATH
3. Restart Claude Desktop completely (quit and reopen)
4. Check Claude Desktop logs for errors

### API Connection Issues

1. Verify your n8n instance is running and accessible
2. Test the API key with a curl command:
   ```bash
   curl -H "X-N8N-API-KEY: your_api_key" http://localhost:5678/api/v1/workflows
   ```
3. Check that your N8N_URL doesn't have a trailing slash
4. Ensure your n8n instance has the API enabled

### Permission Errors

Make sure the n8n API key has sufficient permissions to perform the operations you're trying to execute.

## Security Notes

- **Never commit your `.env` file** or share your API key
- The API key provides full access to your n8n instance
- Consider using network restrictions if exposing n8n beyond localhost
- Regularly rotate your API keys

## Development

To test the server independently:
```bash
npm start
```

The server communicates via stdio and expects MCP protocol messages.

## API Documentation

For more information about the n8n API, see: https://docs.n8n.io/api/

## License

MIT

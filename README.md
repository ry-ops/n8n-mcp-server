<img src="https://github.com/ry-ops/n8n-mcp-server/blob/main/n8n-mcp-server.png" width="100%">

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-latest-green.svg)](https://github.com/astral-sh/uv)
[![MCP](https://img.shields.io/badge/MCP-1.0-purple.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

# n8n MCP Server

A Model Context Protocol (MCP) server that provides seamless integration with the n8n API. Manage your n8n workflows, executions, and credentials through natural language using Claude AI.

Built with Python and managed with `uv` for blazing-fast dependency management.

## Features

### 🔄 Workflow Management
- List all workflows with filtering
- Get detailed workflow information
- Create new workflows
- Update existing workflows
- Delete workflows
- Activate/deactivate workflows
- Execute workflows manually

### 📊 Execution Management
- List workflow executions
- Filter executions by workflow or status
- Get detailed execution information
- Delete executions

### 🔐 Credentials & Tags
- List all credentials
- Filter credentials by type
- List all workflow tags

## Installation

### Prerequisites
- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) installed
- A self-hosted n8n instance (v1.0+)
- n8n API key

### Quick Start with uv

1. **Clone or create the project:**
```bash
mkdir n8n-mcp-server
cd n8n-mcp-server
```

2. **Install with uv:**
```bash
uv pip install -e .
```

Or install from the directory:
```bash
uv pip install n8n-mcp-server
```

### Alternative: Using pip

```bash
pip install -e .
```

## Configuration

### Getting Your n8n API Key

1. Open your n8n instance (e.g., http://localhost:5678)
2. Go to **Settings** > **API**
3. Click **Create API Key**
4. Give it a name and copy the key (**you won't see it again!**)

### Environment Variables

Set the following environment variables:

```bash
export N8N_URL="http://localhost:5678"
export N8N_API_KEY="your_api_key_here"
```

Or create a `.env` file (see `.env.example`).

### Claude Desktop Configuration

Add to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

#### Using uv (recommended):

```json
{
  "mcpServers": {
    "n8n": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/n8n-mcp-server",
        "run",
        "n8n-mcp-server"
      ],
      "env": {
        "N8N_URL": "http://localhost:5678",
        "N8N_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### Using Python directly:

```json
{
  "mcpServers": {
    "n8n": {
      "command": "python",
      "args": ["-m", "n8n_mcp_server"],
      "env": {
        "N8N_URL": "http://localhost:5678",
        "N8N_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Available Tools

The server provides 13 powerful tools for managing n8n:

### Workflow Operations
- `list_workflows` - List all workflows with optional filtering
- `get_workflow` - Get detailed workflow information
- `create_workflow` - Create a new workflow
- `update_workflow` - Update an existing workflow
- `delete_workflow` - Delete a workflow
- `activate_workflow` - Activate a workflow to start it running
- `deactivate_workflow` - Deactivate a workflow to stop it
- `execute_workflow` - Execute a workflow manually with optional data

### Execution Operations
- `list_executions` - List workflow executions with filtering
- `get_execution` - Get detailed execution information
- `delete_execution` - Delete an execution

### Other Operations
- `list_credentials` - List all credentials
- `list_tags` - List all workflow tags

For detailed documentation on each tool, see [EXAMPLES.md](EXAMPLES.md).

## Usage Examples

### Example 1: List Active Workflows

**Ask Claude:**
> "Show me all my active workflows"

Claude will use `list_workflows` with `active: true` filter.

### Example 2: Execute a Workflow

**Ask Claude:**
> "Execute the email campaign workflow"

Claude will find the workflow and use `execute_workflow`.

### Example 3: Check Failed Executions

**Ask Claude:**
> "Show me the last 10 failed executions"

Claude will use `list_executions` with `status: error` and `limit: 10`.

### Example 4: Activate Multiple Workflows

**Ask Claude:**
> "Activate all workflows tagged with 'production'"

Claude will list workflows with that tag and activate each one.

For more examples, see [EXAMPLES.md](EXAMPLES.md).

## Development

### Using uv for Development

```bash
# Install in development mode with dev dependencies
uv pip install -e ".[dev]"

# Run the server directly
uv run n8n-mcp-server

# Run tests (when implemented)
uv run pytest

# Format code with ruff
uv run ruff format src/

# Lint code
uv run ruff check src/
```

### Project Structure

```
n8n-mcp-server/
├── src/
│   └── n8n_mcp_server/
│       └── __init__.py       # Main server implementation
├── tests/                     # Tests (to be implemented)
├── pyproject.toml            # Project configuration (uv-compatible)
├── README.md                 # This file
├── QUICKSTART.md            # Quick start guide
├── EXAMPLES.md              # Usage examples
└── .env.example             # Environment template
```

## API Permissions

Your n8n API key has full access to your n8n instance. Make sure to:
- Store it securely
- Never commit it to version control
- Regenerate it if compromised
- Use environment variables only

## Troubleshooting

### Common Issues

1. **"N8N_API_KEY environment variable is required"**
   - Make sure you've set the environment variable
   - Check your Claude Desktop config has the correct API key

2. **"n8n API error: 401"**
   - Your API key is invalid or expired
   - Regenerate the API key in n8n settings

3. **"Connection refused"**
   - Make sure your n8n instance is running
   - Check the N8N_URL is correct
   - If using Docker, ensure ports are exposed

4. **"uv command not found"**
   - Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Or use the Python direct method instead

## Why uv?

This project uses [uv](https://github.com/astral-sh/uv) because it's:
- ⚡ **10-100x faster** than pip
- 🔒 **More reliable** with better dependency resolution
- 🎯 **Simpler** - one tool for everything
- 🐍 **Modern** - built in Rust, designed for Python

## Security Notes

- **Never commit your API key** to version control
- Store API keys securely using environment variables
- Your API key has full access to n8n - treat it like a password
- Regenerate keys regularly as a security best practice
- Use `.gitignore` to exclude `.env` files

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- [n8n API Documentation](https://docs.n8n.io/api/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [uv - Python Package Manager](https://github.com/astral-sh/uv)
- [Claude Desktop](https://claude.ai/download)

## Support

For issues related to:
- **This MCP server**: Open an issue on GitHub
- **n8n API**: Check [n8n Documentation](https://docs.n8n.io/)
- **MCP Protocol**: Check [MCP Documentation](https://modelcontextprotocol.io/)
- **uv**: Check [uv Documentation](https://github.com/astral-sh/uv)

# n8n MCP Server - Quick Start Guide (Python + uv)

Get your n8n workflows talking to Claude AI in 5 minutes!

## Step 1: Install uv (if you haven't already)

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

## Step 2: Get Your n8n API Key

1. Open your n8n instance (e.g., http://localhost:5678)
2. Go to **Settings** (gear icon in bottom left)
3. Click **API** in the sidebar
4. Click **Create API Key**
5. Give it a name like "Claude MCP Server"
6. **Copy the key** (you won't see it again!)

## Step 3: Find Your n8n URL

Your n8n URL is where you access n8n in your browser, typically:
- Local: `http://localhost:5678`
- Self-hosted: `https://n8n.yourdomain.com`
- Docker: Check your docker-compose port mapping

## Step 4: Install the Server

```bash
cd n8n-mcp-server

# Install with uv (recommended - super fast!)
uv pip install -e .

# Or install with regular pip
pip install -e .
```

## Step 5: Configure Claude Desktop

### macOS
Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
Edit: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration with uv (recommended):

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

### Alternative - Using Python directly:

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

**Important:** Replace `/absolute/path/to/n8n-mcp-server` with the actual full path!

### Finding the absolute path:

**macOS/Linux:**
```bash
cd n8n-mcp-server
pwd
```

**Windows (PowerShell):**
```powershell
cd n8n-mcp-server
(Get-Location).Path
```

## Step 6: Restart Claude Desktop

Completely quit and restart Claude Desktop for the changes to take effect.

## Step 7: Test It!

Open Claude and try:

> "Show me all my n8n workflows"

or

> "What's the status of my last workflow execution?"

## Testing Locally (Optional)

You can test the server locally before adding it to Claude:

```bash
# Set environment variables
export N8N_URL="http://localhost:5678"
export N8N_API_KEY="your_api_key_here"

# Run the server
uv run n8n-mcp-server
```

## Common First Tasks

### View Your Workflows
> "List all my workflows"

### Check Active Workflows
> "Show me all active workflows"

### Execute a Workflow
> "Execute the email campaign workflow"

### Check Recent Executions
> "Show me the last 5 workflow executions"

### Debug a Failed Workflow
> "Why did workflow abc123 fail?"

### Activate a Workflow
> "Activate the daily backup workflow"

## Troubleshooting

### "uv: command not found"
- Install uv using the command in Step 1
- Or use the Python direct method instead

### "No module named 'n8n_mcp_server'"
- Make sure you ran `uv pip install -e .` in the project directory
- Check that you're using the correct Python environment

### "N8N_API_KEY environment variable is required"
- Check your API key is correctly pasted in the config file
- Make sure there are no extra spaces or quotes
- The key should look like a long random string

### "Server not found" or tools don't appear
- Make sure the path in config is absolute
- For uv: verify `--directory` path is correct
- Restart Claude Desktop completely

### "n8n API error: 401 Unauthorized"
- Your API key is invalid or expired
- Regenerate the API key in n8n Settings > API
- Make sure you copied the entire key

### "n8n API error: Connection refused"
- Make sure n8n is running
- Check your N8N_URL is correct
- If using Docker, ensure ports are exposed

### "n8n API error: 404"
- Your n8n version might not support the API
- Update to n8n v1.0 or later
- Check the API is enabled in n8n settings

## n8n API Requirements

This MCP server requires:
- **n8n version 1.0 or later** (for API support)
- **API access enabled** (should be enabled by default)
- **Valid API key** with necessary permissions

## Security Reminder

🔒 **Never share or commit your API key!** It has full access to your n8n instance.

## Next Steps

Once everything works, explore:
- Managing workflows through natural language
- Monitoring execution history
- Debugging failed workflows
- Activating/deactivating workflows in bulk
- Creating automated workflow management routines

Check out [EXAMPLES.md](EXAMPLES.md) for practical usage examples!

Happy automating! 🔄🚀

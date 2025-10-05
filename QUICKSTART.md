# Quick Start Guide

## 1. Get Your n8n API Key

1. Open your n8n instance (http://localhost:5678)
2. Go to Settings → API
3. Click "Create API Key"
4. Copy the key immediately (you can't see it again!)

## 2. Install the MCP Server

```bash
cd n8n-mcp-server
npm install
```

## 3. Configure

Create a `.env` file:
```bash
cp .env.example .env
```

Edit `.env`:
```
N8N_URL=http://localhost:5678
N8N_API_KEY=your_copied_api_key_here
```

## 4. Add to Claude Desktop

Find the full path to your index.js:
```bash
pwd
# Copy this path and add /index.js
```

Edit Claude config:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this (replace YOUR_FULL_PATH and YOUR_API_KEY):
```json
{
  "mcpServers": {
    "n8n": {
      "command": "node",
      "args": ["/YOUR_FULL_PATH/n8n-mcp-server/index.js"],
      "env": {
        "N8N_URL": "http://localhost:5678",
        "N8N_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

## 5. Restart Claude Desktop

Completely quit and restart the Claude Desktop app.

## 6. Test It!

In Claude Desktop, try:
- "List my n8n workflows"
- "Show me recent workflow executions"

## Troubleshooting

**Can't see the n8n server in Claude?**
- Check the path is absolute (starts with `/` on Mac/Linux or `C:\` on Windows)
- Make sure you completely quit and restarted Claude Desktop
- Verify Node.js is installed: `node --version`

**API errors?**
- Test your API key:
  ```bash
  curl -H "X-N8N-API-KEY: your_key" http://localhost:5678/api/v1/workflows
  ```
- Make sure n8n is running
- Check the N8N_URL is correct (no trailing slash!)

Need more help? See the full README.md

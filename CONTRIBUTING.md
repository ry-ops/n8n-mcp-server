# Contributing to n8n MCP Server (Python)

Thank you for your interest in contributing! This document provides guidelines for contributing to the Python version of the n8n MCP Server.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/n8n-mcp-server.git`
3. Install dependencies: `uv pip install -e ".[dev]"`
4. Create a branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Prerequisites
- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) installed (recommended)
- A self-hosted n8n instance for testing (v1.0+)
- n8n API key for testing

### Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your n8n credentials to `.env`:
   ```
   N8N_URL=http://localhost:5678
   N8N_API_KEY=your_test_api_key
   ```

### Installing Dependencies

```bash
# With uv (recommended - super fast!)
uv pip install -e ".[dev]"

# Or with regular pip
pip install -e ".[dev]"
```

### Running the Server

```bash
# Set environment variables
export N8N_URL="http://localhost:5678"
export N8N_API_KEY="your_api_key"

# Run with uv
uv run n8n-mcp-server

# Or run directly with Python
python -m n8n_mcp_server
```

## Project Structure

```
n8n-mcp-server/
├── src/
│   └── n8n_mcp_server/
│       └── __init__.py        # Main server implementation
├── tests/                     # Tests (to be implemented)
├── pyproject.toml            # Project configuration
├── README.md                 # Main documentation
├── QUICKSTART.md            # Quick start guide
├── EXAMPLES.md              # Usage examples
└── CONTRIBUTING.md          # This file
```

## Code Style

We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting.

### Format Code

```bash
uv run ruff format src/
```

### Lint Code

```bash
uv run ruff check src/
```

### Python Style Guidelines

- Follow PEP 8
- Use type hints for function signatures
- Use docstrings for public functions and classes
- Keep functions focused and single-purpose
- Use descriptive variable names

Example:

```python
async def execute_workflow(self, args: dict[str, Any]) -> dict[str, Any]:
    """
    Execute an n8n workflow with optional input data.
    
    Args:
        args: Dictionary containing workflow_id and optional data
        
    Returns:
        Dictionary containing the execution result
        
    Raises:
        ValueError: If workflow_id is missing
        Exception: If the n8n API request fails
    """
    # Implementation here
    pass
```

## Adding New Tools

To add a new tool to the MCP server:

1. **Add the tool definition in `list_tools()` handler:**

```python
Tool(
    name="your_tool_name",
    description="Clear description of what the tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Description of param1",
            },
            # ... more parameters
        },
        "required": ["param1"],
    },
)
```

2. **Add the tool handler in `call_tool()` function:**

```python
elif name == "your_tool_name":
    result = await self._your_tool_name(arguments)
```

3. **Implement the tool method:**

```python
async def _your_tool_name(self, args: dict[str, Any]) -> Any:
    """Tool description."""
    # Make API call
    return await self._make_request(
        "/your/endpoint",
        method="GET",  # or POST, PUT, PATCH, DELETE
    )
```

4. **Update README.md** with documentation for your new tool

5. **Add examples** to EXAMPLES.md

6. **Test thoroughly** before submitting

## Testing

Currently, this project uses manual testing. We welcome contributions for automated tests!

### Manual Testing Checklist

For new tools, verify:
- ✅ Tool appears in Claude's tool list
- ✅ Tool executes without errors
- ✅ Required parameters are enforced
- ✅ Optional parameters work correctly
- ✅ Error messages are clear and helpful
- ✅ Response format is consistent
- ✅ Documentation is accurate

### Future: Automated Tests

We plan to add `pytest` tests. Structure:

```python
import pytest
from n8n_mcp_server import N8nMCPServer

@pytest.mark.asyncio
async def test_list_workflows():
    """Test listing workflows."""
    server = N8nMCPServer(
        n8n_url="http://localhost:5678",
        api_key="test_key"
    )
    # Test implementation
    pass
```

## n8n API Guidelines

When adding new n8n API endpoints:

1. **Consult the official docs:** https://docs.n8n.io/api/
2. **Use proper HTTP methods:**
   - GET for reading data
   - POST for creating resources or executing
   - PATCH for updating
   - DELETE for deleting

3. **Handle pagination** if the endpoint supports it
4. **Include proper error handling**
5. **Test with a real n8n instance**

## Type Hints

Use Python type hints for better code quality:

```python
from typing import Any, Optional

async def _make_request(
    self,
    endpoint: str,
    method: str = "GET",
    data: Optional[dict[str, Any]] = None,
    params: Optional[dict[str, Any]] = None,
) -> Any:
    """Make a request to the n8n API."""
    pass
```

## Async/Await

This project uses async/await for all API calls:

```python
import asyncio
import httpx

async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

## Documentation

When adding features:

1. **Update README.md** with:
   - Tool description
   - Parameters table
   - Usage examples
   - Any special considerations

2. **Update QUICKSTART.md** if it affects setup

3. **Add examples** to EXAMPLES.md

4. **Add docstrings** to functions:
   ```python
   def function_name(param: str) -> dict:
       """
       Brief description.
       
       Args:
           param: Description of parameter
           
       Returns:
           Description of return value
           
       Raises:
           ExceptionType: When this exception is raised
       """
       pass
   ```

## Commit Messages

Use clear, descriptive commit messages:

```
✅ Good:
- "Add support for n8n credentials management"
- "Fix workflow execution parameter validation"
- "Update README with bulk operations examples"

❌ Avoid:
- "fix bug"
- "update"
- "changes"
```

Format: `<type>: <description>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks
- `style`: Code style changes

## Pull Request Process

1. **Update documentation** for any changed functionality
2. **Format and lint** your code:
   ```bash
   uv run ruff format src/
   uv run ruff check src/ --fix
   ```
3. **Test your changes** with a real n8n instance
4. **Create a clear PR description**:
   - What does this PR do?
   - Why is this change needed?
   - How was it tested?
   - Any breaking changes?

5. Wait for review and address feedback

## Feature Requests

Have an idea? Great! Here's how to suggest it:

1. **Check existing issues** to avoid duplicates
2. **Open a new issue** with:
   - Clear description of the feature
   - Use case / why it's needed
   - Example of how it would work
   - Any relevant n8n API documentation

## Bug Reports

Found a bug? Help us fix it:

1. **Check existing issues** first
2. **Create a detailed bug report**:
   - What happened?
   - What did you expect?
   - Steps to reproduce
   - Error messages / logs
   - Your environment (OS, Python version, n8n version)

**Security issues:** Email directly instead of creating a public issue.

## Areas for Contribution

Looking for ideas? Here are areas that need help:

### High Priority
- [ ] Add automated tests (pytest)
- [ ] Implement webhook management tools
- [ ] Add workflow template management
- [ ] Better error messages
- [ ] Rate limiting handling

### Nice to Have
- [ ] Support for workflow exports/imports
- [ ] Execution retry mechanism
- [ ] Workflow statistics and analytics
- [ ] Bulk workflow operations
- [ ] Workflow search and filtering improvements

### Documentation
- [ ] More usage examples
- [ ] Video tutorials
- [ ] Common workflow guides
- [ ] Troubleshooting guide
- [ ] API reference docs

## Dependencies

We minimize dependencies to keep the project lean:
- `mcp` - Model Context Protocol SDK
- `httpx` - Modern HTTP client with async support

Dev dependencies:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `ruff` - Fast Python linter and formatter

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on the best solution, not winning arguments
- Assume good intentions

## Questions?

- Open an issue for technical questions
- Check existing documentation first
- Be specific about what you need help with

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to make this project better! 🔄🎉

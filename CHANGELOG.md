# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-05

### Added
- Initial release of n8n MCP Server (Python version)
- Built with Python 3.10+ and async/await
- Managed with uv for fast dependency management
- Workflow management tools (list, get, create, update, delete)
- Workflow activation and deactivation
- Manual workflow execution with optional data
- Execution management (list, get, delete)
- Credential listing
- Tag listing
- Comprehensive documentation (README, QUICKSTART, EXAMPLES, CONTRIBUTING)
- Full type hints for better IDE support
- Error handling for all API operations
- Support for filtering and pagination
- httpx async client for reliable HTTP requests

### Features by Category

#### Workflow Management
- List all workflows with optional active filter
- Get detailed workflow information including nodes and connections
- Create new workflows with nodes, connections, and settings
- Update existing workflows
- Delete workflows
- Activate workflows to start them running
- Deactivate workflows to stop them
- Execute workflows manually with optional input data

#### Execution Management
- List workflow executions with filtering by workflow and status
- Get detailed execution information including node outputs
- Delete executions
- Support for pagination and limits

#### Credentials & Tags
- List all credentials with optional type filtering
- List all workflow tags

### Technical Details
- Built with Python 3.10+
- Uses MCP SDK (Python) v1.1.2+
- httpx for async HTTP requests
- Full async/await support
- Type hints throughout
- uv-compatible pyproject.toml
- ruff for linting and formatting
- Comprehensive error handling
- JSON response formatting

### Development Features
- uv support for fast package management
- Editable install with `uv pip install -e .`
- Dev dependencies for testing and linting
- ruff configuration for code quality
- pytest-ready structure (tests to be implemented)

## [Unreleased]

### Planned Features
- Automated tests with pytest
- Webhook management
- Workflow template management
- Workflow export/import
- Execution retry mechanism
- Workflow statistics and analytics
- Bulk workflow operations
- Better error messages
- Rate limit handling
- Workflow search improvements

### Improvements
- Add mypy for static type checking
- Add more comprehensive tests
- Improve error messages
- Add request retry logic
- Add response validation
- Workflow caching for performance

---

## Version History

### Format
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes

---

## n8n API Compatibility

This MCP server is compatible with:
- **n8n v1.0+** (requires API support)
- All n8n API endpoints used are stable

---

## Migration from Node.js Version

This is a complete rewrite in Python. Key differences:
- Uses Python's async/await instead of TypeScript/Node.js
- Managed with uv instead of npm
- Uses httpx instead of axios
- Uses MCP Python SDK instead of TypeScript SDK
- Same functionality, different implementation

*Note: This is version 1.0.0 - the initial Python release.*

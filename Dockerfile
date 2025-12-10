# n8n MCP Server Dockerfile
# Multi-arch: amd64 + arm64
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install dependencies
RUN uv venv && uv pip install -e .

# Create non-root user
RUN useradd -m -u 1000 n8n && \
    chown -R n8n:n8n /app

USER n8n

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Labels
LABEL org.opencontainers.image.title="n8n MCP Server"
LABEL org.opencontainers.image.description="MCP server for n8n workflow automation"
LABEL org.opencontainers.image.source="https://github.com/ry-ops/n8n-mcp-server"
LABEL org.opencontainers.image.vendor="ry-ops"

# Default command
CMD ["python", "-m", "n8n_mcp_server"]

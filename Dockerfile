# Use a multi-stage build or a single image with both runtimes
FROM python:3.11-slim-bookworm

# Install Node.js (needed for WEALTH CLI logic)
RUN apt-get update && apt-get install -y curl git && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy package.json and install Node dependencies
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Copy pyproject.toml and install Python dependencies
COPY pyproject.toml ./
COPY uv.lock ./
RUN uv sync --no-dev

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port (if using SSE transport, default is stdio)
EXPOSE 8000

# Default command: Run the FastMCP server
# Use --transport sse if deploying to cloud, or keep default for stdio
ENTRYPOINT ["python", "server.py"]

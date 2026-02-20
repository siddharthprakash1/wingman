# Dockerfile for Wingman AI Assistant
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -e .[all]

# Copy application code
COPY src/ ./src/
COPY .env.example ./.env.example

# Create workspace directory
RUN mkdir -p /root/.wingman/workspace

# Expose ports
EXPOSE 18789

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:18789/health || exit 1

# Default command
CMD ["python", "-m", "src.cli.app", "gateway"]

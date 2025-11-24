# Multi-stage Dockerfile for Python Cloud Server
# Stage 1: Build stage - build wheel using uv
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY .here .here
COPY config.prod.json config.json
COPY python_cloud_server/ ./python_cloud_server/

# Build the wheel
RUN uv build --wheel

# Stage 2: Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 cloudserver && \
    mkdir -p /app/certs /app/logs && \
    chown -R cloudserver:cloudserver /app

# Install uv in runtime stage
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the built wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install the wheel
RUN uv pip install --system --no-cache /tmp/*.whl && \
    rm /tmp/*.whl

# Copy runtime files (.here is needed for pyhere to find project root)
COPY --chown=cloudserver:cloudserver .here .here
COPY --chown=cloudserver:cloudserver config.prod.json config.json

# Switch to non-root user
USER cloudserver

# Expose HTTPS port
EXPOSE 8443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('https://localhost:8443/api/metrics', context=__import__('ssl')._create_unverified_context()).read()" || exit 1

# Default command: generate certificates if missing, then start server
CMD ["sh", "-c", "if [ ! -f certs/cert.pem ] || [ ! -f certs/key.pem ]; then echo 'Generating self-signed certificates...'; generate-certificate; fi && python-cloud-server"]

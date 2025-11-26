# Multi-stage Dockerfile for Python Cloud Server
# Stage 1: Build stage - build wheel using uv
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY python_cloud_server/ ./python_cloud_server/
COPY .here .here
COPY config.prod.json config.json
COPY pyproject.toml LICENSE README.md ./

# Build the wheel
RUN uv build --wheel

# Stage 2: Runtime stage
FROM python:3.12-slim

# Build arguments for environment-specific config
ARG ENV=dev
ARG PORT=8443

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 cloudserver && \
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

# Conditionally copy the appropriate config file based on ENV
COPY --chown=cloudserver:cloudserver config.json /tmp/config.dev.json
COPY --chown=cloudserver:cloudserver config.prod.json /tmp/config.prod.json
RUN if [ "$ENV" = "prod" ]; then cp /tmp/config.prod.json /app/config.json; else cp /tmp/config.dev.json /app/config.json; fi && \
    chown cloudserver:cloudserver /app/config.json

# Create startup script
RUN echo '#!/bin/sh\n\
    if [ ! -f certs/cert.pem ] || [ ! -f certs/key.pem ]; then\n\
    echo "Generating self-signed certificates..."\n\
    generate-certificate\n\
    fi\n\
    exec python-cloud-server' > /app/start.sh && \
    chmod +x /app/start.sh && \
    chown cloudserver:cloudserver /app/start.sh

# Switch to non-root user
USER cloudserver

# Expose HTTPS port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('https://localhost:$PORT/api/metrics', context=__import__('ssl')._create_unverified_context()).read()" || exit 1

# Default command: generate certificates if missing, then start server
CMD ["/app/start.sh"]

# Multi-stage Dockerfile for Python Cloud Server
# Stage 1: Build stage - install dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY .here .here
COPY config.json ./
COPY python_cloud_server/ ./python_cloud_server/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Stage 2: Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 cloudserver && \
    mkdir -p /app/certs /app/logs && \
    chown -R cloudserver:cloudserver /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY --chown=cloudserver:cloudserver .here .here
COPY --chown=cloudserver:cloudserver config.json ./
COPY --chown=cloudserver:cloudserver python_cloud_server/ ./python_cloud_server/

# Switch to non-root user
USER cloudserver

# Expose HTTPS port
EXPOSE 8443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('https://localhost:8443/api/metrics', context=__import__('ssl')._create_unverified_context()).read()" || exit 1

# Default command: generate certificates if missing, then start server
CMD sh -c "if [ ! -f certs/cert.pem ] || [ ! -f certs/key.pem ]; then echo 'Generating self-signed certificates...'; generate-certificate; fi && python-cloud-server"

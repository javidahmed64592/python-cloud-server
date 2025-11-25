[![python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=ffd343)](https://docs.python.org/3.12/)
[![CI](https://img.shields.io/github/actions/workflow/status/javidahmed64592/python-cloud-server/ci.yml?branch=main&style=flat-square&label=CI&logo=github)](https://github.com/javidahmed64592/python-cloud-server/actions)
[![License](https://img.shields.io/github/license/javidahmed64592/python-cloud-server?style=flat-square)](https://github.com/javidahmed64592/python-cloud-server/blob/main/LICENSE)

<!-- omit from toc -->
# Python Cloud Server

A secure FastAPI-based cloud storage server with HTTPS support, API key authentication, rate limiting, and comprehensive testing.
Built for local development with production-ready security patterns and designed for future extensibility with file upload/download, caching, and observability features.

<!-- omit from toc -->
## Table of Contents
- [Features](#features)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [First-Time Setup](#first-time-setup)
  - [Running the Server](#running-the-server)
- [Docker Deployment](#docker-deployment)
- [Metrics \& Monitoring](#metrics--monitoring)
- [API Documentation](#api-documentation)
- [Security](#security)
- [License](#license)

## Features

✨ **Core Capabilities**
- **FastAPI Framework**: Modern, high-performance web framework with automatic OpenAPI documentation
- **HTTPS Support**: Self-signed SSL certificates for secure local development
- **API Key Authentication**: SHA-256 hashed authentication tokens with header-based verification

🔒 **Security**
- Cryptographically secure token generation using `secrets` module
- SHA-256 token hashing for safe storage
- Certificate generation with RSA-4096 keys
- Authentication middleware for all protected endpoints
- Rate limiting to prevent abuse and DoS attacks
- Security headers (HSTS, CSP, X-Frame-Options, etc.) on all responses
- Request/response logging for security monitoring and debugging
- Environment-based configuration for sensitive data

📊 **Monitoring & Observability**
- Prometheus metrics endpoint (`/metrics`) with standard HTTP metrics
- Custom authentication and rate limiting metrics
- Docker Compose setup with Grafana dashboards for visualization
- Pre-configured dashboards for authentication and performance monitoring
- Request/response logging with rotating file handlers

## Quick Start

### Prerequisites
- Python 3.12 or higher
- `uv` package manager ([installation instructions](https://docs.astral.sh/uv/))

### Installation

```sh
# Clone the repository
git clone https://github.com/javidahmed64592/python-cloud-server.git
cd python-cloud-server

# Install dependencies
uv sync
```

### Configuration

The server uses a `config.json` file for configuration:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8443
  },
  "security": {
    "hsts_max_age": 31536000,
    "content_security_policy": "default-src 'self'"
  },
  "rate_limit": {
    "enabled": true,
    "rate_limit": "100/minute",
    "storage_uri": ""
  },
  "certificate": {
    "directory": "certs",
    "ssl_keyfile": "key.pem",
    "ssl_certfile": "cert.pem",
    "days_valid": 365
  }
}
```

### First-Time Setup

1. **Generate SSL Certificate**:
   ```sh
   uv run generate-certificate
   ```
   This creates a self-signed certificate in the `certs/` directory, valid for 365 days.

2. **Generate API Authentication Token**:
   ```sh
   uv run generate-new-token
   ```
   This generates a secure token, hashes it, and stores the hash in `.env`. **Save the displayed token** - you'll need it to authenticate API requests.

### Running the Server

```sh
uv run python-cloud-server
```

The server will start on `https://localhost:8443` with the API mounted at `https://localhost:8443/api`.

**Testing the API**:
```sh
# Replace YOUR_TOKEN with the token from step 2
curl -k -H "X-API-Key: YOUR_TOKEN" https://localhost:8443/api/health
```

Expected response:
```json
{
  "code": 200,
  "message": "Server is healthy",
  "timestamp": "2025-11-22T12:00:00.000000Z"
}
```

## Docker Deployment

🐳 **Run with Docker Compose** (includes Prometheus + Grafana):

```sh
# 1. Generate API key (automatically creates .env file)
uv run generate-new-token

# 2. Start all services (FastAPI, Prometheus, Grafana)
docker compose up -d

# 3. Access services:
# - API Server: https://localhost:8443/api
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

**What's included:**
- FastAPI server with auto-generated SSL certificates
- Prometheus for metrics collection
- Grafana with pre-configured dashboards:
  - Authentication metrics (success/failure rates, reasons)
  - Rate limiting violations by endpoint
  - HTTP performance metrics (latency percentiles, request rates)

For detailed Docker deployment instructions, see [`docs/DOCKER_DEPLOYMENT.md`](docs/DOCKER_DEPLOYMENT.md).

## Metrics & Monitoring

The server exposes Prometheus-compatible metrics at `/api/metrics`:

**Available Metrics:**
- `auth_success_total` - Successful authentication attempts
- `auth_failure_total{reason}` - Failed authentications (by reason: missing, invalid, error)
- `rate_limit_exceeded_total{endpoint}` - Rate limit violations per endpoint
- `http_requests_total` - Total HTTP requests (method, handler, status)
- `http_request_duration_seconds` - Request latency histogram

**Access Metrics:**
```sh
curl -k https://localhost:8443/api/metrics
```

**Visualization:**
Use the Docker Compose setup to access pre-built Grafana dashboards at `http://localhost:3000`.

## API Documentation

Interactive API documentation is available when the server is running:

- **Swagger UI**: https://localhost:8443/api/docs
- **ReDoc**: https://localhost:8443/api/redoc

For server-specific endpoint information, see [`docs/API.md`](docs/API.md).

## Security

⚠️ **Important Security Notes**:

- **Self-signed certificates**: The generated certificates are for **local development only**. For production, use certificates from a trusted Certificate Authority.
- **API key storage**: Tokens are hashed using SHA-256 before storage. Never commit `.env` files or expose tokens.
- **HTTPS only**: The server enforces HTTPS connections for all API endpoints.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

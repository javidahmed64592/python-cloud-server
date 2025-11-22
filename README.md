[![python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=ffd343)](https://docs.python.org/3.12/)
[![CI](https://img.shields.io/github/actions/workflow/status/javidahmed64592/python-cloud-server/ci.yml?branch=main&style=flat-square&label=CI&logo=github)](https://github.com/javidahmed64592/python-cloud-server/actions)
[![License](https://img.shields.io/github/license/javidahmed64592/python-cloud-server?style=flat-square)](https://github.com/javidahmed64592/python-cloud-server/blob/main/LICENSE)

<!-- omit from toc -->
# Python Cloud Server

A secure FastAPI-based cloud storage server with HTTPS support, API key authentication, and comprehensive testing.
Built for local development with production-ready patterns and designed for future extensibility with file upload/download, caching, and observability features.

<!-- omit from toc -->
## Table of Contents
- [Features](#features)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [First-Time Setup](#first-time-setup)
  - [Running the Server](#running-the-server)
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
- Environment-based configuration for sensitive data

🏗️ **Architecture**
- Clean separation of concerns (models, config, authentication, certificates)
- Factory pattern for application creation (supports hot-reload)
- Pydantic models for configuration and response validation
- Structured logging with Python's logging module
- Type-safe codebase with full mypy compliance

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
    "host": "localhost",
    "port": 8443
  },
  "certificate": {
    "directory": "certs",
    "ssl_keyfile": "key.pem",
    "ssl_certfile": "cert.pem",
    "days_valid": 365
  },
  "rate_limit": {
    "enabled": true,
    "rate_limit": "100/minute",
    "storage_uri": ""
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

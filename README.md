[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=ffd343)](https://docs.python.org/3.13/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![CI](https://img.shields.io/github/actions/workflow/status/javidahmed64592/python-cloud-server/ci.yml?branch=main&style=flat-square&label=CI&logo=github)](https://github.com/javidahmed64592/python-cloud-server/actions/workflows/ci.yml)
[![Build](https://img.shields.io/github/actions/workflow/status/javidahmed64592/python-cloud-server/build.yml?branch=main&style=flat-square&label=Build&logo=github)](https://github.com/javidahmed64592/python-cloud-server/actions/workflows/build.yml)
[![Docker](https://img.shields.io/github/actions/workflow/status/javidahmed64592/python-cloud-server/docker.yml?branch=main&style=flat-square&label=Docker&logo=github)](https://github.com/javidahmed64592/python-cloud-server/actions/workflows/docker.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<!-- omit from toc -->
# Python Cloud Server

A production-ready FastAPI cloud server which uses [python-template-server](https://github.com/javidahmed64592/python-template-server).

<!-- omit from toc -->
## Table of Contents
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Generate Certificates and API Token](#generate-certificates-and-api-token)
  - [Run the Server](#run-the-server)
- [Docker Deployment](#docker-deployment)
- [Documentation](#documentation)
- [License](#license)

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

Install `uv`:

```sh
# Linux/Mac
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Installation

```sh
# Clone the repository
git clone https://github.com/javidahmed64592/python-cloud-server.git
cd python-cloud-server

# Install dependencies
uv sync --extra dev
```

### Generate Certificates and API Token

```sh
# Generate self-signed SSL certificate (saves to certs/ directory)
uv run generate-certificate

# Generate API authentication token (saves hash to .env)
uv run generate-new-token
# ⚠️ Save the displayed token - you'll need it for API requests!
```

### Run the Server

```sh
# Start the server
uv run python-cloud-server

# Server runs at https://localhost:443/api
# Swagger UI: https://localhost:443/api/docs
# Redoc: https://localhost:443/api/redoc
# Metrics: curl -k https://localhost:443/api/metrics
# Health check: curl -k https://localhost:443/api/health
# Login (requires authentication): curl -k -H "X-API-Key: your-token-here" https://localhost:443/api/login
```

## Docker Deployment

```sh
# Start all services (FastAPI + Prometheus + Grafana)
docker compose up -d

# View logs
docker compose logs -f python-cloud-server

# Access services:
# - API: https://localhost:443/api
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

## Documentation

- **[API Documentation](./docs/API.md)**: Endpoints, authentication, metrics
- **[Software Maintenance Guide](./docs/SMG.md)**: Development setup, configuration
- **[Docker Deployment Guide](./docs/DOCKER_DEPLOYMENT.md)**: Container orchestration
- **[Workflows](./docs/WORKFLOWS.md)**: CI/CD pipeline details

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

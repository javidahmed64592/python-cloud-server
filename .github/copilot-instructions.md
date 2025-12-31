# Python Cloud Server - AI Agent Instructions

## Project Overview

Production-ready FastAPI cloud server built on [python-template-server](https://github.com/javidahmed64592/python-template-server).
Extends `TemplateServer` to create a cloud-based application server with authentication, rate limiting, security headers, and observability.

## Architecture & Key Components

### Application Factory Pattern

- Entry: `main.py:run()` → instantiates `CloudServer` (subclass of `TemplateServer`) → calls `.run()`
- `CloudServer.__init__()` initializes with `config.json` and package name `python_cloud_server`
- Inherits all middleware, rate limiting and auth from `TemplateServer`
- Currently extends base `setup_routes()` without adding custom endpoints (future expansion point)

### Configuration System

- Config: `configuration/config.json` loaded via inherited `TemplateServer.load_config()`
- Model: `CloudServerConfig` (extends `TemplateServerConfig` in `models.py`)
- Validation: `CloudServer.validate_config()` uses `CloudServerConfig.model_validate()`
- Logging configured by template server with rotating file handler
- Environment variables: `.env`

### Base Infrastructure (from python-template-server)

- **Authentication**: API key via `X-API-Key` header, SHA-256 hashed token verification
- **Rate Limiting**: Configurable slowapi integration (100/minute default)
- **Security Headers**: HSTS, CSP, X-Frame-Options middleware
- **SSL/TLS**: Self-signed certificate generation and HTTPS support

## Developer Workflows

### Essential Commands

```bash
# Setup (first time)
uv sync --extra dev              # Install all dependencies
uv run generate-certificate      # Create self-signed SSL certs (certs/)
uv run generate-new-token        # Generate API key, save hash to .env

# Development
uv run python-cloud-server       # Start server (https://localhost:443/api)
uv run -m pytest                 # Run tests with coverage (80% minimum)
uv run -m mypy .                 # Type checking
uv run -m ruff check .           # Linting

# Docker Development
docker compose up --build -d     # Build + start all services
docker compose logs -f python-cloud-server  # View server logs
docker compose down              # Stop and remove containers
```

### Docker Multi-Stage Build

- **Stage 1 (builder)**: Uses `uv` to build wheel
- **Stage 2 (runtime)**: Installs wheel, copies runtime files from site-packages to /app
- **Startup Script**: `/app/start.sh` generates token/certs if missing, copies monitoring configs to shared volume
- **Config**: Uses `config.json` for all environments
- **Port**: 443 (HTTPS)
- **Health Check**: Curls `/api/health` (no auth required)

## Project-Specific Conventions

### Code Organization

```
python_cloud_server/
├── main.py           # Entry point with run() function
├── models.py         # CloudServerConfig model
└── server.py         # CloudServer class
```

### API Design

- **Prefix**: All routes under `/api`
- **Authentication**: Inherited from TemplateServer, applied via `Security(self._verify_api_key)`
- **Unauthenticated Endpoints**: `/api/health`
- **Current Endpoints**: Only base endpoints from TemplateServer (health, login)
- **Future Extension**: Add custom routes in `CloudServer.setup_routes()`

### CI/CD Validation

All PRs must pass:

**CI Workflow:**

1. `validate-pyproject` - pyproject.toml schema validation
2. `ruff` - linting (120 char line length)
3. `mypy` - type coverage
4. `pytest` - 80% minimum coverage
5. `bandit` - security scanning
6. `pip-audit` - dependency CVE audit
7. `version-check` - pyproject.toml vs uv.lock consistency

**Build Workflow:**

1. `build_wheel` - Build wheel with uv, upload artifact
2. `verify_structure` - Install wheel, verify package structure (python_cloud_server/, configuration/)

**Docker Workflow:**

1. `build` - Build/start services, health check, cleanup

## Quick Reference

### Key Files

- `python_cloud_server/server.py` - CloudServer class extending TemplateServer
- `python_cloud_server/main.py` - Application entry point
- `python_cloud_server/models.py` - CloudServerConfig model
- `configuration/config.json` - Server configuration
- `docker-compose.yml` - Container stack
- `Dockerfile` - Multi-stage build with wheel installation

### Environment Variables

- `API_TOKEN_HASH` - SHA-256 hash of API token (only var required)
- `PORT` - Server port (default 443)

### Configuration Files

- `configuration/config.json` - Configuration (used for all environments)
- `.env` - API token hash (auto-created by generate-new-token)
- **Docker**: Startup script uses `config.json` for all environments

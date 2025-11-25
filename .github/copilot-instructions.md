# Python Cloud Server - AI Agent Instructions

## Project Overview

FastAPI-based secure HTTPS server with production-grade security patterns. Currently implements authentication, rate limiting, and observability foundations. File upload/download features are planned but **not yet implemented**.

## Architecture & Key Components

### Application Factory Pattern

- Entry: `main.py:run()` → loads config → instantiates `CloudServer` → calls `.run()`
- `CloudServer.__init__()` sets up middleware, rate limiting, metrics, and routes in specific order
- **Critical**: Middleware order matters - request logging → security headers → rate limiting

### Configuration System

- `config.json` (dev) / `config.prod.json` (prod) loaded via `config.py:load_config()`
- Validated using Pydantic models in `models.py` (AppConfigModel hierarchy)
- Logging configured automatically on `config.py` import with rotating file handler
- Environment variables stored in `.env` (API_TOKEN_HASH only, never commit)

### Authentication Architecture

- **Token Generation**: `uv run generate-new-token` creates secure token + SHA-256 hash
- **Hash Storage**: Only hash stored in `.env` (API_TOKEN_HASH), raw token shown once
- **Verification Flow**: Request → `_verify_api_key()` dependency → `verify_token()` → hash comparison
- **Metrics**: Success/failure counters with labeled reasons (missing/invalid/error)
- Header: `X-API-Key` (defined in `constants.API_KEY_HEADER_NAME`)

### Rate Limiting

- Uses `slowapi` with configurable storage (in-memory/Redis/Memcached)
- Applied via `_limit_route()` wrapper when `config.rate_limit.enabled=true`
- Custom exception handler increments `rate_limit_exceeded_counter` per endpoint
- Format: `"100/minute"` (supports /second, /minute, /hour)

### Observability Stack

- **Prometheus**: `/metrics` endpoint always exposed (no auth), custom auth/rate-limit metrics
- **Grafana**: Pre-configured dashboards in `grafana/dashboards/*.json`
- **Logging**: Dual output (console + rotating file), 10MB per file, 5 backups in `logs/`
- **Request Tracking**: `RequestLoggingMiddleware` logs all requests with client IP

## Developer Workflows

### Essential Commands

```powershell
# Setup (first time)
uv sync                          # Install dependencies
uv run generate-certificate      # Create self-signed SSL certs (certs/ dir)
uv run generate-new-token        # Generate API key, save hash to .env

# Development
uv run python-cloud-server       # Start server (https://localhost:8443/api)
uv run -m pytest                 # Run tests with coverage
uv run -m mypy .                 # Type checking
uv run -m ruff check .           # Linting

# Docker Development
docker compose up --build -d     # Build + start all services
docker compose logs -f python-cloud-server  # View logs
docker compose down              # Stop and remove containers
```

### Testing Patterns

- **Fixtures**: All tests use `conftest.py` fixtures, auto-mock `pyhere.here()` to tmp_path
- **Config Mocking**: Use `mock_app_config` fixture for consistent test config
- **Integration Tests**: Test via FastAPI TestClient with auth headers
- **Coverage Target**: 99% (currently achieved)
- **Pattern**: Unit tests per module (test\_\*.py) + integration tests (test_cloud_server.py)

### Docker Multi-Stage Build

- **Stage 1 (builder)**: Uses `uv` to build wheel, copies prod config
- **Stage 2 (runtime)**: Installs wheel, switches to non-root user, auto-generates certs on startup
- **Build Args**: `ENV=prod` (chooses config), `PORT=443` (exposes port)
- **Health Check**: Curls `/api/metrics` with unverified SSL context

## Project-Specific Conventions

### Code Organization

- **Handlers**: Separate modules for auth (`authentication_handler.py`), certs (`certificate_handler.py`)
- **Middleware**: Dedicated package `middleware/` with base classes extending `BaseHTTPMiddleware`
- **Constants**: All magic strings/numbers in `constants.py` (ports, file names, log config)
- **Models**: Pydantic models for config + API responses, use `@property` for derived values

### Security Patterns

- **Never log secrets**: Print tokens via `print()`, not `logger` (see `generate_new_token()`)
- **Path validation**: Use Pydantic validators, Path objects for cert paths
- **Security headers**: HSTS, CSP, X-Frame-Options via `SecurityHeadersMiddleware`
- **Cert generation**: RSA-4096, SHA-256, 365-day validity, SANs for localhost

### API Design

- **Prefix**: All routes under `/api` (API_PREFIX constant)
- **Authentication**: Applied via `dependencies=[Security(self._verify_api_key)]` in route registration
- **Response Models**: All endpoints return `BaseResponse` subclasses with code/message/timestamp
- **Metrics Endpoint**: `/metrics` excluded from authentication (Prometheus scraping)

### Logging Format

- Format: `[DD/MM/YYYY | HH:MM:SS] (LEVEL) module: message`
- Client IPs logged in requests: `"Request: GET /api/health from 192.168.1.1"`
- Auth failures: `"Invalid API key attempt!"`

## Development Constraints

### What's NOT Implemented Yet

- File upload/download endpoints
- Database/metadata storage (planned: SQLite/PostgreSQL)
- CORS configuration
- API key rotation/expiry
- Multi-user auth (JWT/OAuth2)

### Testing Requirements

- Mock `pyhere.here()` for all file path tests (see `conftest.py`)
- Use `mock_app_config` fixture for CloudServer instantiation
- Test async endpoints with `@pytest.mark.asyncio`
- Mock `uvicorn.run` when testing `CloudServer.run()`

### CI/CD Validation

All PRs must pass:

1. `validate-pyproject` - pyproject.toml schema validation
2. `ruff` - linting (120 char line length, strict rules in pyproject.toml)
3. `mypy` - 100% type coverage (strict mode)
4. `pytest` - 99% code coverage, HTML report uploaded
5. `version-check` - pyproject.toml vs uv.lock version consistency

## Quick Reference

### Key Files

- `cloud_server.py` - Main application class, middleware/route setup
- `authentication_handler.py` - Token generation, hashing, verification
- `config.py` - Config loading, logging setup (executed on import)
- `models.py` - All Pydantic models (config + responses)
- `constants.py` - Project constants, logging config
- `docker-compose.yml` - FastAPI + Prometheus + Grafana stack

### Environment Variables

- `API_TOKEN_HASH` - SHA-256 hash of API token (only var required)

### Configuration Files

- `config.json` - Development config (default)
- `config.prod.json` - Production config (used in Docker with ENV=prod)
- `.env` - API token hash (auto-created by generate-new-token)

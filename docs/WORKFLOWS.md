# GitHub Workflows

This document details the CI/CD workflows to build and release the Python Cloud Server application.
They run automated code quality checks to ensure code remains robust, maintainable, and testable.

## CI Workflow

The CI workflow runs on pushes and pull requests to the `main` branch.
It consists of the following jobs:

### validate-pyproject
- **Runner**: Ubuntu Latest
- **Steps**:
  - Checkout code
  - Install uv with caching
  - Set up Python from `.python-version`
  - Install dependencies with `uv sync --extra dev`
  - Validate `pyproject.toml` using `uv run validate-pyproject pyproject.toml`

### ruff
- **Runner**: Ubuntu Latest
- **Steps**:
  - Checkout code
  - Run Ruff linter using `chartboost/ruff-action@v1`

### mypy
- **Runner**: Ubuntu Latest
- **Steps**:
  - Checkout code
  - Install uv with caching
  - Set up Python from `.python-version`
  - Install dependencies with `uv sync --extra dev`
  - Run mypy type checking with `uv run -m mypy .`

### test
- **Runner**: Ubuntu Latest
- **Steps**:
  - Checkout code
  - Install uv with caching
  - Set up Python from `.python-version`
  - Install dependencies with `uv sync --extra dev`
  - Run pytest with coverage report using `uv run -m pytest --cov-report html`
  - Upload coverage report as artifact

## Docker Workflow

The Docker workflow runs on pushes and pull requests to the `main` branch.
It consists of the following jobs:

### docker-development
- **Runner**: Ubuntu Latest
- **Steps**:
  - Checkout code
  - Install uv with caching and set up Python from `.python-version`
  - Create directories with proper permissions
  - Build and start services with docker compose
  - Show server logs
  - **Health check** using reusable composite action `.github/actions/docker-check-containers` that checks Python Cloud Server, Prometheus, and Grafana
  - Stop services

### docker-production
- **Runner**: Ubuntu Latest
- **Steps**:
  - Checkout code
  - Install uv with caching and set up Python from `.python-version`
  - Create directories with proper permissions
  - Build production image with `ENV=prod` and `PORT=443` build arguments
  - Start services with docker compose using production environment variables
  - Show server logs
  - **Health check** using reusable composite action `.github/actions/docker-check-containers` that checks Python Cloud Server, Prometheus, and Grafana
  - Stop services

### docker-check-containers (Composite Action)
- **Location**: `.github/actions/docker-check-containers/action.yml`
- **Purpose**: Centralized health check logic for Docker containers
- **Inputs**:
  - `port` (required): Port to check for Python Cloud Server health endpoint
  - `num-retries` (optional, default: 5): Number of retries for health checks
  - `timeout-seconds` (optional, default: 5): Timeout between retries
- **Checks**:
  - Python Cloud Server: Curls `https://localhost:{port}/api/health` (no authentication required)
  - Prometheus: Curls `http://localhost:9090`
  - Grafana: Curls `http://localhost:3000`

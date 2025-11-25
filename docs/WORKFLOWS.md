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

The CI workflow runs on pushes and pull requests to the `main` branch.
It consists of the following jobs:

### docker-compose-dev
- **Runner**: Ubuntu Latest
- **Steps**:
  - Checkout code
  - Install uv with caching
  - Set up Python from `.python-version`
  - Install dependencies with `uv sync`
  - Generate API token hash
  - Create directories with proper permissions
  - Build and start services with docker-compose
  - Check if services are running
  - Show server logs
  - Health check
  - Stop services

### docker-compose-prod
- **Runner**: Ubuntu Latest
- **Steps**:
  - Checkout code
  - Install uv with caching
  - Set up Python from `.python-version`
  - Install dependencies with `uv sync`
  - Generate API token hash
  - Create directories with proper permissions
  - Build production image
  - Run production container
  - Show server logs
  - Health check
  - Stop container

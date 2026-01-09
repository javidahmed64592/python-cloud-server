<!-- omit from toc -->
# Software Maintenance Guide

This document outlines how to configure and setup a development environment to work on the Python Cloud Server application.

<!-- omit from toc -->
## Table of Contents
- [Backend (Python)](#backend-python)
  - [Directory Structure](#directory-structure)
  - [Installing Dependencies](#installing-dependencies)
  - [Setting Up Authentication](#setting-up-authentication)
  - [Running the Backend](#running-the-backend)
  - [Testing, Linting, and Type Checking](#testing-linting-and-type-checking)

## Backend (Python)

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=ffd343)](https://docs.python.org/3.13/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=flat-square)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square)](https://github.com/astral-sh/ruff)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

### Directory Structure

```
python_cloud_server/
├── main.py           # Application entry point
├── metadata.py       # Metadata manager
├── models.py         # Pydantic models (config + API responses)
└── server.py         # Cloud server class
```

### Installing Dependencies

This repository is managed using the `uv` Python project manager: https://docs.astral.sh/uv/

Install the required dependencies:

```sh
uv sync
```

To include development dependencies:

```sh
uv sync --extra dev
```

After installing dev dependencies, set up pre-commit hooks:

```sh
uv run pre-commit install
```

### Setting Up Authentication

Before running the server, you need to generate an API authentication token.

```sh
uv run generate-new-token
```

This command:
- Creates a cryptographically secure token using Python's `secrets` module
- Hashes the token with SHA-256 for safe storage
- Stores the hash in `.env` file
- Displays the plain token (save it securely - it won't be shown again)

### Running the Backend

Start the FastAPI server:

```sh
uv run python-cloud-server
```

The backend will be available at `https://localhost:443/api` by default.

**Available Endpoints:**
- Health Check: `https://localhost:443/api/health`
- Login: `https://localhost:443/api/login` (requires authentication)

**Testing the API:**
```sh
# Health check (no auth required)
curl -k https://localhost:443/api/health

# Login endpoint (requires authentication)
curl -k -H "X-API-Key: your-token-here" https://localhost:443/api/login
```

### Testing, Linting, and Type Checking

- **Run all pre-commit checks:** `uv run pre-commit run --all-files`
- **Lint code:** `uv run ruff check .`
- **Format code:** `uv run ruff format .`
- **Type check:** `uv run mypy .`
- **Run tests:** `uv run pytest`
- **Security scan:** `uv run bandit -r python_cloud_server/`
- **Audit dependencies:** `uv run pip-audit`

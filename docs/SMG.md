<!-- omit from toc -->
# Software Maintenance Guide

This document outlines how to configure and setup a development environment to work on the Python Cloud Server application.

<!-- omit from toc -->
## Table of Contents
- [Backend (Python)](#backend-python)
  - [Directory Structure](#directory-structure)
  - [Installing Dependencies](#installing-dependencies)
  - [Running the Backend](#running-the-backend)
  - [Testing, Linting, and Type Checking](#testing-linting-and-type-checking)

## Backend (Python)

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=ffd343)](https://docs.python.org/3.12/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=flat-square)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square)](https://github.com/astral-sh/ruff)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

### Directory Structure

```
cyber_query_ai/
├── authentication_handler.py      # Authentication
├── certificate_handler.py         # Certificate generator
├── cloud_server.py                # FastAPI endpoints
├── config.py                      # Configuration management
├── constants.py                   # Server constants
├── main.py                        # Application entry point
└── models.py                      # Pydantic models
```

### Installing Dependencies

This repository is managed using the `uv` Python project manager: https://docs.astral.sh/uv/

To install `uv`:

```sh
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" # Windows
```

Install the required dependencies:

```sh
uv sync
```

To include development dependencies:

```sh
uv sync --extra dev
```

### Running the Backend

Start the FastAPI server:

```sh
uv run python-cloud-server
```

The backend will be available at `http://localhost:8443/api` by default.

### Testing, Linting, and Type Checking

- **Run tests:** `uv run pytest`
- **Lint code:** `uv run ruff check .`
- **Format code:** `uv run ruff format .`
- **Type check:** `uv run mypy .`

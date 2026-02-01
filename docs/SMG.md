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
- [Frontend (TypeScript)](#frontend-typescript)
  - [Directory Structure](#directory-structure-1)
  - [Installing Dependencies](#installing-dependencies-1)
  - [Running the Frontend](#running-the-frontend)
  - [Testing, Linting, and Type Checking](#testing-linting-and-type-checking-1)
- [Creating a New Release Version](#creating-a-new-release-version)
  - [Steps to Update Version](#steps-to-update-version)

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

## Frontend (TypeScript)

[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![ESLint](https://img.shields.io/badge/ESLint-9-4B32C3?style=flat-square&logo=eslint&logoColor=white)](https://eslint.org/)
[![Prettier](https://img.shields.io/badge/Prettier-3-F7B93E?style=flat-square&logo=prettier&logoColor=black)](https://prettier.io/)

### Directory Structure

```
python-cloud-server-frontend/
├── src/
│   ├── app/
│   │   ├── login/                # Login page for API key authentication
│   │   ├── globals.css           # UI style configuration
│   │   ├── layout.tsx            # Root layout with AuthProvider and navigation
│   │   ├── not-found.tsx         # Not found page
│   │   └── page.tsx              # Homepage
│   ├── components/
│   │   ├── Footer.tsx            # App footer with version info
│   │   ├── HealthIndicator.tsx   # Server health status indicator
│   │   └── Navigation.tsx        # Main navigation bar with logout
│   ├── contexts/
│   │   └── AuthContext.tsx       # Authentication context and route protection
│   ├── lib/
│   │   ├── api.ts                # API client with authentication interceptors
│   │   ├── auth.ts               # localStorage API key management
│   │   └── types.ts              # TypeScript type definitions (matches backend models)
├── jest.config.js                # Jest configuration for testing
├── jest.setup.js                 # Jest setup for mocking and environment
├── next.config.ts                # Next.js configuration
├── package.json                  # Dependencies and scripts
└── postcss.config.mjs            # Tailwind CSS configuration
```

### Installing Dependencies

Install the required dependencies:

```bash
npm install
```

### Running the Frontend

**Prerequisites:**
Ensure the backend server is running (see [Running the Backend](#running-the-backend))

**Start the development server:**
```bash
cd python-cloud-server-frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`.

**Authentication in Development:**
- The development server proxies `/api` requests to the HTTPS backend (`https://localhost:443`)
- On first visit, you'll be redirected to `/login/`
- Enter the API token generated via `uv run generate-new-token`
- The token is stored in localStorage and included in all API requests via the `X-API-KEY` header

**Building for Production:**
```bash
npm run build        # Standard Next.js build
```

### Testing, Linting, and Type Checking

- **Run tests:** `npm run test`
- **Run all quality checks:** `npm run quality`
- **Fix all quality issues:** `npm run quality:fix`
- **Type check:** `npm run type-check`
- **Lint code:** `npm run lint`
- **Fix lint issues:** `npm run lint:fix`
- **Check formatting:** `npm run format`
- **Format code:** `npm run format:fix`

## Creating a New Release Version

When preparing a new release, you must update version numbers across multiple files to maintain consistency. The CI pipeline enforces version alignment between backend and frontend.

### Steps to Update Version

1. **Update `pyproject.toml`** (backend version):
   ```toml
   [project]
   name = "python-cloud-server"
   version = "X.Y.Z"  # Update this line
   ```

2. **Update `python-cloud-server-frontend/package.json`** (frontend version):
   ```json
   {
     "name": "python-cloud-server-frontend",
     "version": "X.Y.Z"  // Update this line to match backend
   }
   ```

3. **Synchronize `uv.lock`** (from project root):
   ```sh
   uv lock
   ```

4. **Synchronize `package-lock.json`** (from `python-cloud-server-frontend` directory):
   ```sh
   cd python-cloud-server-frontend
   npm install --package-lock-only
   ```

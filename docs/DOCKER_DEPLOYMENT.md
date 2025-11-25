<!-- omit from toc -->
# Docker Deployment Guide

This guide provides comprehensive instructions for deploying the Python Cloud Server using Docker and Docker Compose, including metrics visualization with Prometheus and Grafana.

<!-- omit from toc -->
## Table of Contents
- [Prerequisites](#prerequisites)
  - [Check Prerequisites](#check-prerequisites)
- [Quick Start](#quick-start)
  - [1. Generate API Key](#1-generate-api-key)
  - [2. Start Services](#2-start-services)
- [Configuration](#configuration)
  - [Docker Compose Services](#docker-compose-services)
  - [Environment Variables](#environment-variables)
  - [Server Configuration](#server-configuration)
- [Building and Running](#building-and-running)
  - [Development Mode](#development-mode)
  - [Managing Containers](#managing-containers)
- [Accessing Services](#accessing-services)
  - [Python Cloud Server](#python-cloud-server)
  - [Prometheus](#prometheus)
  - [Grafana](#grafana)
- [Metrics Visualization](#metrics-visualization)
  - [Available Metrics](#available-metrics)
    - [Authentication Metrics](#authentication-metrics)
    - [Rate Limiting Metrics](#rate-limiting-metrics)
    - [HTTP Metrics (provided by prometheus-fastapi-instrumentator)](#http-metrics-provided-by-prometheus-fastapi-instrumentator)
  - [Custom Dashboard Setup](#custom-dashboard-setup)
  - [View Container Logs](#view-container-logs)

## Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **API Key**: Generate using `generate-new-token` command (see below)

### Check Prerequisites

```bash
docker --version
docker-compose --version
```

## Quick Start

### 1. Generate API Key

Before starting the containers, you need to generate an API key:

```bash
# Install the package locally (if not already installed)
uv sync

# Generate a new API token (automatically creates/updates .env file)
uv run generate-new-token
```

This will:
- Generate a cryptographically secure **raw token** (displayed once - keep this secret!)
- Hash the token using SHA-256
- Automatically save the hash to `.env` as `API_TOKEN_HASH`

**Important**:
- Save the displayed raw token - you'll need it for API requests
- The `.env` file is automatically created/updated by the command

### 2. Start Services

```bash
# Start all services (FastAPI server, Prometheus, Grafana)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Configuration

### Docker Compose Services

The `docker-compose.yml` defines three services:

1. **python-cloud-server** (Port 8443)
   - FastAPI application with HTTPS
   - Auto-generates self-signed certificates on first run
   - Exposes `/api/metrics` endpoint for Prometheus

2. **prometheus** (Port 9090)
   - Metrics collection and storage
   - Scrapes `/api/metrics` endpoint every 15 seconds
   - Persistent storage via Docker volume

3. **grafana** (Port 3000)
   - Metrics visualization dashboards
   - Pre-configured Prometheus datasource
   - Custom dashboards for authentication and rate limiting
   - Default credentials: `admin/admin`

### Environment Variables

Configure the FastAPI server using environment variables in `docker-compose.yml`:

```yaml
environment:
  - API_TOKEN_HASH=${API_TOKEN_HASH}
```

### Server Configuration

Modify `config.json` to customize:

- **Host and Port**: Change server binding address
- **Security Headers**: Configure HSTS and CSP policies
- **Rate Limiting**: Adjust rate limit rules
- **Certificates**: Set certificate validity period

## Building and Running

### Development Mode

```bash
# Stop containers if required
docker-compose down

# Build and start in background
docker-compose up --build -d
```

### Managing Containers

```bash
# View running containers
docker-compose ps

# Stop services
docker-compose stop

# Start stopped services
docker-compose start

# Restart services
docker-compose restart python-cloud-server

# Remove containers and volumes
docker-compose down -v
```

## Accessing Services

### Python Cloud Server

**Base URL**: `https://localhost:8443`

**API Endpoints**:
- Health Check: `GET /api/health` (requires authentication)
- Metrics: `GET /api/metrics` (no authentication required)

**Example Request**:
```bash
# Using curl (with self-signed cert)
curl -k -H "X-API-Key: YOUR_RAW_TOKEN" https://localhost:8443/api/health
```

### Prometheus

**URL**: `http://localhost:9090`

**Features**:
- Query metrics directly
- View scrape targets and status
- Create custom queries

### Grafana

**URL**: `http://localhost:3000`

**Default Credentials**:
- Username: `admin`
- Password: `admin` (change on first login)

**Pre-installed Dashboards**:
1. **Authentication Metrics** (`/d/auth-metrics`)
   - Success/failure rates
   - Total authentication attempts
   - Failure reasons breakdown
   - Success rate percentage

2. **Rate Limiting & Performance** (`/d/rate-limit-metrics`)
   - Rate limit violations by endpoint
   - HTTP request rates
   - Request duration percentiles
   - Total violations gauge

## Metrics Visualization

### Available Metrics

#### Authentication Metrics
- `auth_success_total`: Successful authentication attempts
- `auth_failure_total{reason}`: Failed attempts by reason (missing, invalid, error)

#### Rate Limiting Metrics
- `rate_limit_exceeded_total{endpoint}`: Rate limit violations per endpoint

#### HTTP Metrics (provided by prometheus-fastapi-instrumentator)
- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request latency histogram
- `http_requests_in_progress`: Current in-flight requests

### Custom Dashboard Setup

1. **Access Grafana**: Navigate to `http://localhost:3000`
2. **Login**: Use `admin/admin`
3. **Navigate**: Go to Dashboards → Browse → Python Cloud Server folder
4. **View**: Select either dashboard to visualize metrics

### View Container Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f python-cloud-server

# Last 100 lines
docker-compose logs --tail=100 prometheus
```

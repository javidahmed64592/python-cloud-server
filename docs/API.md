<!-- omit from toc -->
# API

This document summarizes the backend API provided by the Python Cloud Server application.
All endpoints are mounted under the `/api` prefix.

<!-- omit from toc -->
## Table of Contents
- [Authentication](#authentication)
- [Security Headers](#security-headers)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [GET /api/health](#get-apihealth)
- [Request and Response Models (Pydantic)](#request-and-response-models-pydantic)

## Authentication

All API endpoints require authentication via an API key passed in the `X-API-Key` header.

**Request Header**:
```
X-API-Key: your-api-token-here
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid API key

## Security Headers

All API responses include security headers to protect against common web vulnerabilities:

**Headers Included**:
- `Strict-Transport-Security`: Forces HTTPS connections (HSTS)
- `X-Content-Type-Options`: Prevents MIME-type sniffing
- `X-Frame-Options`: Prevents clickjacking attacks
- `Content-Security-Policy`: Controls which resources can be loaded
- `X-XSS-Protection`: Enables browser XSS filtering
- `Referrer-Policy`: Controls referrer information sent with requests

**Configuration** (`config.json`):
```json
{
  "security": {
    "hsts_max_age": 31536000,
    "content_security_policy": "default-src 'self'"
  }
}
```

- `hsts_max_age`: Duration in seconds that browsers should remember to only access the site via HTTPS (default: 1 year)
- `content_security_policy`: CSP directive controlling resource loading (default: only allow resources from same origin)
## Rate Limiting

API endpoints are rate-limited to prevent abuse. When the rate limit is exceeded, the server responds with:

**Response**:
- Status Code: `429 Too Many Requests`
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

Default rate limit: **100 requests per minute** per IP address.

Rate limits can be configured in `config.json`.

## Endpoints

### GET /api/health

**Purpose**: Simple health check of the server.

**Authentication**: Required (X-API-Key header)

**Rate Limiting**: Subject to rate limits (default: 100/minute)

**Request**: None

**Response Model**: `GetHealthResponse`
- `code` (int): HTTP status code
- `message` (string): Status message
- `timestamp` (string): ISO 8601 timestamp

**Example Request**:
```bash
curl -k -H "X-API-Key: your-token" https://localhost:8443/api/health
```

**Example Response** (200 OK):
```json
{
  "code": 200,
  "message": "Server is healthy",
  "timestamp": "2025-11-22T12:00:00.000000Z"
}
```

## Request and Response Models (Pydantic)

The primary Pydantic models are defined in `python_cloud_server/models.py`:
- GetHealthResponse: { code: int, message: str, timestamp: str }

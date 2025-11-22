<!-- omit from toc -->
# API

This document summarizes the backend API provided by the Python Cloud Server application.
All endpoints are mounted under the `/api` prefix.

<!-- omit from toc -->
## Table of Contents
- [Endpoints](#endpoints)
  - [GET /api/health](#get-apihealth)
- [Request and Response Models (Pydantic)](#request-and-response-models-pydantic)

## Endpoints

### GET /api/health

- Purpose: Simple health check of the server.
- Request: none
- Response model: `GetHealthResponse`
    - code: int
    - message: string
    - timestamp: ISO 8601 string

Example response:
{
    "code": 200,
    "message": "Server is healthy",
    "timestamp": "2025-11-22T12:00:00Z"
}

## Request and Response Models (Pydantic)

The primary Pydantic models are defined in `python_cloud_server/models.py`:
- GetHealthResponse: { code: int, message: str, timestamp: str }

<!-- omit from toc -->
# API

This document summarizes the API endpoints specific to the Python Cloud Server.

## Base Server Infrastructure

The Python Cloud Server is built from [python-template-server](https://github.com/javidahmed64592/python-template-server), which provides production-ready infrastructure including:

- **API Key Authentication**: All authenticated endpoints require the `X-API-KEY` header with a SHA-256 hashed token
- **Rate Limiting**: Configurable request throttling (default: 10 requests/minute per IP)
- **Security Headers**: Automatic HSTS, CSP, and X-Frame-Options enforcement
- **Request Logging**: Comprehensive logging of all requests/responses with client IP tracking
- **Prometheus Metrics**: Built-in metrics for monitoring authentication, rate limiting, and HTTP performance
- **Health Checks**: Standard `/api/health` endpoint for availability monitoring
- **HTTPS Support**: Built-in SSL certificate generation and management

For detailed information about these features, authentication token generation, server middleware, and base configuration, see the [python-template-server README](https://github.com/javidahmed64592/python-template-server/blob/main/README.md).

<!-- omit from toc -->
## Table of Contents
- [Base Server Infrastructure](#base-server-infrastructure)

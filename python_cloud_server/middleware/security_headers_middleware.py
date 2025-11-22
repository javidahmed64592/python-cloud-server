"""Middleware to add security headers to all responses."""

from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    def __init__(self, app: FastAPI, hsts_max_age: int, csp: str) -> None:
        """Initialize the SecurityHeadersMiddleware."""
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.csp = csp

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = self.csp
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

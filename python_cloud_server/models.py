"""Pydantic models for the server."""

from datetime import datetime
from enum import IntEnum
from pathlib import Path

from pydantic import BaseModel, Field

from python_cloud_server.constants import API_PREFIX


# Application Configuration Models
class ServerConfigModel(BaseModel):
    """Server configuration model."""

    host: str = Field(default="localhost", description="Server hostname or IP address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port number")

    @property
    def address(self) -> str:
        """Get the server address in host:port format."""
        return f"{self.host}:{self.port}"

    @property
    def url(self) -> str:
        """Get the server URL."""
        return f"https://{self.address}"

    @property
    def full_url(self) -> str:
        """Get the full server URL including API prefix."""
        return f"{self.url}{API_PREFIX}"


class CertificateConfigModel(BaseModel):
    """Certificate configuration model."""

    directory: str = Field(default="certs", description="Directory where SSL certificate and key files are stored")
    ssl_keyfile: str = Field(default="key.pem", description="Filename of the SSL key file")
    ssl_certfile: str = Field(default="cert.pem", description="Filename of the SSL certificate file")
    days_valid: int = Field(default=365, ge=1, description="Number of days the certificate is valid")

    @property
    def ssl_key_file_path(self) -> Path:
        """Get the full path to the SSL key file."""
        return Path(self.directory) / self.ssl_keyfile

    @property
    def ssl_cert_file_path(self) -> Path:
        """Get the full path to the SSL certificate file."""
        return Path(self.directory) / self.ssl_certfile


class RateLimitConfigModel(BaseModel):
    """Rate limit configuration model."""

    enabled: bool = Field(default=True, description="Whether rate limiting is enabled")
    rate_limit: str = Field(default="100/minute", description="Rate limit for API endpoints (format: count/period)")
    storage_uri: str = Field(default="", description="Storage URI for rate limit data (empty string for in-memory)")


class AppConfigModel(BaseModel):
    """Application configuration model."""

    server: ServerConfigModel = Field(default_factory=ServerConfigModel)
    certificate: CertificateConfigModel = Field(default_factory=CertificateConfigModel)
    rate_limit: RateLimitConfigModel = Field(default_factory=RateLimitConfigModel)


# API Response Models
class ResponseCode(IntEnum):
    """HTTP response codes for API endpoints."""

    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class BaseResponse(BaseModel):
    """Base response model for all API endpoints."""

    code: ResponseCode = Field(..., description="Response code indicating the result status")
    message: str = Field(..., description="Human-readable message describing the response")
    timestamp: str = Field(..., description="Timestamp of the response in ISO 8601 format")

    @staticmethod
    def current_timestamp() -> str:
        """Get the current timestamp in ISO 8601 format."""
        return datetime.now().isoformat() + "Z"


class GetHealthResponse(BaseResponse):
    """Response model for the health endpoint."""

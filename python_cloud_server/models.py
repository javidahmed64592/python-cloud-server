"""Pydantic models for the server."""

from enum import IntEnum

from pydantic import BaseModel, Field


# Application Configuration Models
class ServerConfigModel(BaseModel):
    """Server configuration model."""

    host: str
    port: int


class CertificateConfigModel(BaseModel):
    """Certificate configuration model."""

    ssl_keyfile: str
    ssl_certfile: str
    days_valid: int = 365


class AppConfigModel(BaseModel):
    """Application configuration model."""

    server: ServerConfigModel
    certificate: CertificateConfigModel


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


class GetHealthResponse(BaseResponse):
    """Response model for the health endpoint."""

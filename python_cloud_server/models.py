"""Pydantic models for the server."""

from pydantic import BaseModel


class ServerModel(BaseModel):
    """Server configuration model."""

    host: str
    port: int


class CertificateModel(BaseModel):
    """Certificate configuration model."""

    ssl_keyfile: str
    ssl_certfile: str
    days_valid: int = 365


class ConfigModel(BaseModel):
    """Configuration model for the server."""

    server: ServerModel
    certificate: CertificateModel

"""Pydantic models for the server."""

from pydantic import BaseModel


class ConfigModel(BaseModel):
    """Configuration model for the server."""

    ssl_keyfile: str
    ssl_certfile: str
    days_valid: int = 365

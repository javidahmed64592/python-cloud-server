"""Pydantic models for the server."""

from python_template_server.models import TemplateServerConfig


# Cloud Server Configuration Models
class CloudServerConfig(TemplateServerConfig):
    """Configuration model for the Cloud Server."""

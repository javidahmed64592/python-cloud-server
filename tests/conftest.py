"""Pytest fixtures for the application's unit tests."""

import pytest

from python_cloud_server.models import (
    AppConfigModel,
    CertificateConfigModel,
    ServerConfigModel,
)


# Application Configuration Models
@pytest.fixture
def mock_server_config_dict() -> dict:
    """Provide a mock server configuration dictionary."""
    return {"host": "localhost", "port": 8080}


@pytest.fixture
def mock_certificate_config_dict() -> dict:
    """Provide a mock certificate configuration dictionary."""
    return {
        "directory": "/path/to/certs",
        "ssl_keyfile": "key.pem",
        "ssl_certfile": "cert.pem",
        "days_valid": 365,
    }


@pytest.fixture
def mock_server_config(mock_server_config_dict: dict) -> ServerConfigModel:
    """Provide a mock ServerConfigModel instance."""
    return ServerConfigModel(**mock_server_config_dict)


@pytest.fixture
def mock_certificate_config(mock_certificate_config_dict: dict) -> CertificateConfigModel:
    """Provide a mock CertificateConfigModel instance."""
    return CertificateConfigModel(**mock_certificate_config_dict)


@pytest.fixture
def mock_app_config(
    mock_server_config: ServerConfigModel,
    mock_certificate_config: CertificateConfigModel,
) -> AppConfigModel:
    """Provide a mock AppConfigModel instance."""
    return AppConfigModel(server=mock_server_config, certificate=mock_certificate_config)

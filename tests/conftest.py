"""Pytest fixtures for the application's unit tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, mock_open, patch

import pytest

from python_cloud_server.models import (
    AppConfigModel,
    CertificateConfigModel,
    RateLimitConfigModel,
    ServerConfigModel,
)


# General fixtures
@pytest.fixture(autouse=True)
def mock_here(tmp_path: str) -> Generator[MagicMock, None, None]:
    """Mock the here() function to return a temporary directory."""
    with patch("pyhere.here") as mock_here:
        mock_here.return_value = tmp_path
        yield mock_here


@pytest.fixture
def mock_exists() -> Generator[MagicMock, None, None]:
    """Mock the Path.exists() method."""
    with patch("pathlib.Path.exists") as mock_exists:
        yield mock_exists


@pytest.fixture
def mock_mkdir() -> Generator[MagicMock, None, None]:
    """Mock Path.mkdir method."""
    with patch("pathlib.Path.mkdir") as mock_mkdir:
        yield mock_mkdir


@pytest.fixture
def mock_open_file() -> Generator[MagicMock, None, None]:
    """Mock the Path.open() method."""
    with patch("pathlib.Path.open", mock_open()) as mock_file:
        yield mock_file


@pytest.fixture
def mock_touch() -> Generator[MagicMock, None, None]:
    """Mock the Path.touch() method."""
    with patch("pathlib.Path.touch") as mock_touch:
        yield mock_touch


@pytest.fixture
def mock_sys_exit() -> Generator[MagicMock, None, None]:
    """Mock sys.exit to raise SystemExit."""
    with patch("sys.exit") as mock_exit:
        mock_exit.side_effect = SystemExit
        yield mock_exit


@pytest.fixture
def mock_set_key() -> Generator[MagicMock, None, None]:
    """Mock the set_key function."""
    with patch("dotenv.set_key") as mock_set_key:
        yield mock_set_key


@pytest.fixture
def mock_os_getenv() -> Generator[MagicMock, None, None]:
    """Mock the os.getenv function."""
    with patch("os.getenv") as mock_getenv:
        yield mock_getenv


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
def mock_rate_limit_config_dict() -> dict:
    """Provide a mock rate limit configuration dictionary."""
    return {
        "enabled": False,
        "rate_limit": "200/minute",
        "storage_uri": "memory://",
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
def mock_rate_limit_config(mock_rate_limit_config_dict: dict) -> RateLimitConfigModel:
    """Provide a mock RateLimitConfigModel instance."""
    return RateLimitConfigModel(**mock_rate_limit_config_dict)


@pytest.fixture
def mock_app_config(
    mock_server_config: ServerConfigModel,
    mock_certificate_config: CertificateConfigModel,
    mock_rate_limit_config: RateLimitConfigModel,
) -> AppConfigModel:
    """Provide a mock AppConfigModel instance."""
    return AppConfigModel(
        server=mock_server_config, certificate=mock_certificate_config, rate_limit=mock_rate_limit_config
    )

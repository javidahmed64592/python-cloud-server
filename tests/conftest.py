"""Pytest fixtures for the application's unit tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, mock_open, patch

import pytest
from prometheus_client import REGISTRY

from python_cloud_server.models import CloudServerConfig


# General fixtures
@pytest.fixture(autouse=True)
def mock_here(tmp_path: str) -> Generator[MagicMock]:
    """Mock the here() function to return a temporary directory."""
    with patch("pyhere.here") as mock_here:
        mock_here.return_value = tmp_path
        yield mock_here


@pytest.fixture
def mock_exists() -> Generator[MagicMock]:
    """Mock the Path.exists() method."""
    with patch("pathlib.Path.exists") as mock_exists:
        yield mock_exists


@pytest.fixture
def mock_mkdir() -> Generator[MagicMock]:
    """Mock Path.mkdir method."""
    with patch("pathlib.Path.mkdir") as mock_mkdir:
        yield mock_mkdir


@pytest.fixture
def mock_open_file() -> Generator[MagicMock]:
    """Mock the Path.open() method."""
    with patch("pathlib.Path.open", mock_open()) as mock_file:
        yield mock_file


@pytest.fixture
def mock_touch() -> Generator[MagicMock]:
    """Mock the Path.touch() method."""
    with patch("pathlib.Path.touch") as mock_touch:
        yield mock_touch


@pytest.fixture
def mock_sys_exit() -> Generator[MagicMock]:
    """Mock sys.exit to raise SystemExit."""
    with patch("sys.exit") as mock_exit:
        mock_exit.side_effect = SystemExit
        yield mock_exit


@pytest.fixture
def mock_set_key() -> Generator[MagicMock]:
    """Mock the set_key function."""
    with patch("dotenv.set_key") as mock_set_key:
        yield mock_set_key


@pytest.fixture
def mock_os_getenv() -> Generator[MagicMock]:
    """Mock the os.getenv function."""
    with patch("os.getenv") as mock_getenv:
        yield mock_getenv


@pytest.fixture(autouse=True)
def clear_prometheus_registry() -> Generator[None]:
    """Clear Prometheus registry before each test to avoid duplicate metric errors."""
    # Clear all collectors from the registry
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)
    yield
    # Clear again after the test
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)


# Cloud Server Configuration Models
@pytest.fixture
def mock_cloud_server_config() -> CloudServerConfig:
    """Provide a mock CloudServerConfig instance."""
    return CloudServerConfig.model_validate({})

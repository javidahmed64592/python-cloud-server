"""Unit tests for the python_cloud_server.main module."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from python_cloud_server.main import run
from python_cloud_server.models import CloudServerConfig

TEST_PORT = 443


@pytest.fixture
def mock_load_config(mock_app_config: CloudServerConfig) -> Generator[MagicMock, None, None]:
    """Mock the load_config function."""
    with patch("python_cloud_server.main.load_config") as mock_config:
        mock_config.return_value = mock_app_config
        yield mock_config


@pytest.fixture
def mock_cloud_server_class() -> Generator[MagicMock, None, None]:
    """Mock CloudServer class."""
    with patch("python_cloud_server.main.CloudServer") as mock_server:
        yield mock_server


class TestRun:
    """Unit tests for the run function."""

    def test_run(self, mock_load_config: MagicMock, mock_cloud_server_class: MagicMock) -> None:
        """Test successful server run."""
        run()

        mock_load_config.assert_called_once()
        mock_cloud_server_class.return_value.run.assert_called_once()

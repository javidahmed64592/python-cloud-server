"""Unit tests for the python_cloud_server.main module."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from python_cloud_server.main import run
from python_cloud_server.models import CloudServerConfig


@pytest.fixture
def mock_server_class(mock_cloud_server_config: CloudServerConfig) -> Generator[MagicMock]:
    """Mock CloudServer class."""
    with patch("python_cloud_server.main.CloudServer") as mock_server:
        mock_server.load_config.return_value = mock_cloud_server_config
        yield mock_server


class TestRun:
    """Unit tests for the run function."""

    def test_run(self, mock_server_class: MagicMock) -> None:
        """Test successful server run."""
        run()

        mock_server_class.return_value.run.assert_called_once()

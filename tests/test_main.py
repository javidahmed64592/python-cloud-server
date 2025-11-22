"""Unit tests for the python_cloud_server.main module."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from python_cloud_server.main import run

TEST_PORT = 8443


@pytest.fixture
def mock_load_config() -> Generator[MagicMock, None, None]:
    """Mock the load_config function."""
    with patch("python_cloud_server.main.load_config") as mock_config:
        yield mock_config


@pytest.fixture
def mock_uvicorn_run() -> Generator[MagicMock, None, None]:
    """Mock uvicorn.run."""
    with patch("python_cloud_server.main.uvicorn.run") as mock_run:
        yield mock_run


class TestRun:
    """Unit tests for the run function."""

    def test_run_success(
        self,
        mock_load_config: MagicMock,
        mock_uvicorn_run: MagicMock,
    ) -> None:
        """Test successful server run."""
        mock_config = MagicMock()
        mock_config.certificate.ssl_cert_file_path.exists.return_value = True
        mock_config.certificate.ssl_key_file_path.exists.return_value = True
        mock_config.server.host = "localhost"
        mock_config.server.port = TEST_PORT
        mock_load_config.return_value = mock_config

        run()

        mock_uvicorn_run.assert_called_once()
        call_kwargs = mock_uvicorn_run.call_args.kwargs
        assert call_kwargs["host"] == "localhost"
        assert call_kwargs["port"] == TEST_PORT
        assert call_kwargs["factory"] is True
        assert call_kwargs["reload"] is True

    def test_run_missing_cert_file(
        self,
        mock_load_config: MagicMock,
        mock_uvicorn_run: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Test run exits when certificate file is missing."""
        mock_config = MagicMock()
        mock_config.certificate.ssl_cert_file_path.exists.return_value = False
        mock_config.certificate.ssl_key_file_path.exists.return_value = True
        mock_load_config.return_value = mock_config

        with pytest.raises(SystemExit):
            run()

        mock_sys_exit.assert_called_once_with(1)
        mock_uvicorn_run.assert_not_called()

    def test_run_missing_key_file(
        self,
        mock_load_config: MagicMock,
        mock_uvicorn_run: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Test run exits when key file is missing."""
        mock_config = MagicMock()
        mock_config.certificate.ssl_cert_file_path.exists.return_value = True
        mock_config.certificate.ssl_key_file_path.exists.return_value = False
        mock_load_config.return_value = mock_config

        with pytest.raises(SystemExit):
            run()

        mock_sys_exit.assert_called_once_with(1)
        mock_uvicorn_run.assert_not_called()

    def test_run_os_error(
        self,
        mock_load_config: MagicMock,
        mock_uvicorn_run: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Test run handles OSError from uvicorn."""
        mock_config = MagicMock()
        mock_config.certificate.ssl_cert_file_path.exists.return_value = True
        mock_config.certificate.ssl_key_file_path.exists.return_value = True
        mock_load_config.return_value = mock_config
        mock_uvicorn_run.side_effect = OSError("Port already in use")

        with pytest.raises(SystemExit):
            run()

        mock_sys_exit.assert_called_once_with(1)

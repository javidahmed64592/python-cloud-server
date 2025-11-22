"""Unit tests for the python_cloud_server.config module."""

from unittest.mock import MagicMock, call

from python_cloud_server.config import load_config
from python_cloud_server.models import AppConfigModel


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_success(
        self,
        mock_exists: MagicMock,
        mock_open_file: MagicMock,
        mock_sys_exit: MagicMock,
        mock_app_config: AppConfigModel,
    ) -> None:
        """Test successful loading of config."""
        mock_exists.return_value = True
        mock_open_file.return_value.read.return_value = str(mock_app_config.model_dump()).replace("'", '"')

        config = load_config()

        assert isinstance(config, AppConfigModel)
        assert config == mock_app_config
        mock_sys_exit.assert_not_called()

    def test_load_config_file_not_found(
        self,
        mock_exists: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Test loading config when the file does not exist."""
        mock_exists.return_value = False

        load_config()

        mock_sys_exit.assert_called_once_with(1)

    def test_load_config_invalid_json(
        self,
        mock_exists: MagicMock,
        mock_open_file: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Test loading config with invalid JSON content."""
        mock_exists.return_value = True
        mock_open_file.return_value.read.return_value = "invalid json"

        load_config()

        mock_sys_exit.assert_has_calls(
            [call(1), call(1)]
        )  # Called twice: once for JSON error, once for exit (only in test environment)

    def test_load_config_os_error(
        self,
        mock_exists: MagicMock,
        mock_open_file: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Test loading config that raises an OSError."""
        mock_exists.return_value = True
        mock_open_file.side_effect = OSError("File read error")

        load_config()

        mock_sys_exit.assert_has_calls(
            [call(1), call(1)]
        )  # Called twice: once for OSError, once for exit (only in test environment)

    def test_load_config_validation_error(
        self,
        mock_exists: MagicMock,
        mock_open_file: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Test loading config that fails validation."""
        mock_exists.return_value = True
        mock_open_file.return_value.read.return_value = '{"server": {"host": "localhost"}}'  # Incomplete config

        load_config()

        mock_sys_exit.assert_called_once_with(1)

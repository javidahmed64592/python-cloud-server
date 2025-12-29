"""Unit tests for the python_cloud_server.server module."""

from collections.abc import Generator
from importlib.metadata import PackageMetadata
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Security
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader

from python_cloud_server.metadata import MetadataManager
from python_cloud_server.models import CloudServerConfig
from python_cloud_server.server import CloudServer


@pytest.fixture(autouse=True)
def mock_package_metadata() -> Generator[MagicMock]:
    """Mock importlib.metadata.metadata to return a mock PackageMetadata."""
    with patch("python_template_server.template_server.metadata") as mock_metadata:
        mock_pkg_metadata = MagicMock(spec=PackageMetadata)
        metadata_dict = {
            "Name": "python-cloud-server",
            "Version": "0.1.0",
            "Summary": "A lightweight FastAPI cloud server.",
        }
        mock_pkg_metadata.__getitem__.side_effect = lambda key: metadata_dict[key]
        mock_metadata.return_value = mock_pkg_metadata
        yield mock_metadata


@pytest.fixture
def mock_server(
    mock_cloud_server_config: CloudServerConfig, mock_metadata_manager: MetadataManager
) -> Generator[CloudServer]:
    """Provide a CloudServer instance for testing."""

    async def fake_verify_api_key(
        api_key: str | None = Security(APIKeyHeader(name="X-API-Key", auto_error=False)),
    ) -> None:
        """Fake verify API key that accepts the security header and always succeeds in tests."""
        return

    with (
        patch.object(CloudServer, "_verify_api_key", new=fake_verify_api_key),
        patch("python_cloud_server.server.CloudServerConfig.save_to_file"),
        patch("python_cloud_server.server.MetadataManager", return_value=mock_metadata_manager),
    ):
        server = CloudServer(mock_cloud_server_config)
        yield server


class TestCloudServer:
    """Unit tests for the CloudServer class."""

    def test_init(self, mock_server: CloudServer) -> None:
        """Test CloudServer initialization."""
        assert isinstance(mock_server.config, CloudServerConfig)

    def test_storage_directory_properties(self, mock_server: CloudServer) -> None:
        """Test storage directory property methods."""
        server_dir = Path(mock_server.config.storage_config.server_directory)
        storage_dir = server_dir / mock_server.config.storage_config.storage_directory
        metadata_file = server_dir / mock_server.config.storage_config.metadata_filename

        assert mock_server.server_directory == server_dir
        assert mock_server.storage_directory == storage_dir
        assert mock_server.metadata_filepath == metadata_file

    def test_storage_initialization(self, mock_server: CloudServer) -> None:
        """Test that storage directories are created during initialization."""
        # Verify storage directory exists
        assert mock_server.storage_directory.exists()

        # Verify metadata file parent directory exists
        assert mock_server.metadata_filepath.parent.exists()

    def test_server_directory_not_exists(self, mock_cloud_server_config: CloudServerConfig) -> None:
        """Test that SystemExit is raised if server directory doesn't exist."""
        # Set server directory to a non-existent path
        mock_cloud_server_config.storage_config.server_directory = "/nonexistent/path"

        async def fake_verify_api_key(
            api_key: str | None = Security(APIKeyHeader(name="X-API-Key", auto_error=False)),
        ) -> None:
            return

        with (
            patch.object(CloudServer, "_verify_api_key", new=fake_verify_api_key),
            patch("python_cloud_server.server.CloudServerConfig.save_to_file"),
            pytest.raises(SystemExit),
        ):
            CloudServer(mock_cloud_server_config)

    def test_metadata_manager_initialization(self, mock_server: CloudServer) -> None:
        """Test that metadata manager is initialized."""
        assert isinstance(mock_server.metadata_manager, MetadataManager)
        assert mock_server.metadata_manager.metadata_filepath == mock_server.metadata_filepath

    def test_validate_config(self, mock_server: CloudServer, mock_cloud_server_config: CloudServerConfig) -> None:
        """Test configuration validation."""
        config_dict = mock_cloud_server_config.model_dump()
        validated_config = mock_server.validate_config(config_dict)
        assert validated_config == mock_cloud_server_config

    def test_validate_config_invalid_returns_default(self, mock_server: CloudServer) -> None:
        """Test invalid configuration returns default configuration."""
        invalid_config = {"model": None}
        validated_config = mock_server.validate_config(invalid_config)
        assert isinstance(validated_config, CloudServerConfig)


class TestCloudServerRoutes:
    """Integration tests for the routes in CloudServer."""

    def test_setup_routes(self, mock_server: CloudServer) -> None:
        """Test that routes are set up correctly."""
        api_routes = [route for route in mock_server.app.routes if isinstance(route, APIRoute)]
        routes = [route.path for route in api_routes]
        expected_endpoints = [
            "/health",
            "/metrics",
            "/login",
            "/files/{filepath:path}",
        ]
        for endpoint in expected_endpoints:
            assert endpoint in routes, f"Expected endpoint {endpoint} not found in routes"

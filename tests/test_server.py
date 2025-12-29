"""Unit tests for the python_cloud_server.server module."""

import asyncio
from collections.abc import Generator
from importlib.metadata import PackageMetadata
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, Security
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader
from fastapi.testclient import TestClient
from python_template_server.models import ResponseCode

from python_cloud_server.metadata import MetadataManager
from python_cloud_server.models import CloudServerConfig, FileMetadata
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


class TestGetFileEndpoint:
    """Integration and unit tests for the GET /files/{filepath} endpoint."""

    def test_get_file(self, mock_server: CloudServer, mock_file_metadata: FileMetadata) -> None:
        """Test get_file successfully retrieves a file."""
        request = MagicMock(spec=Request)

        # Ensure metadata exists
        assert mock_server.metadata_manager.get_file_entry(mock_file_metadata.filepath) is not None

        response = asyncio.run(mock_server.get_file(request, mock_file_metadata.filepath))

        assert isinstance(response, FileResponse)
        assert response.path == mock_server.storage_directory / mock_file_metadata.filepath
        assert response.media_type == mock_file_metadata.mime_type
        assert response.filename == Path(mock_file_metadata.filepath).name

    def test_get_file_not_found_in_metadata(self, mock_server: CloudServer) -> None:
        """Test get_file raises 404 when file not in metadata."""
        request = MagicMock(spec=Request)
        filepath = "nonexistent/file.txt"

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(mock_server.get_file(request, filepath))

        assert exc_info.value.status_code == ResponseCode.NOT_FOUND
        assert f"File not found in metadata: {filepath}" in str(exc_info.value.detail)

    def test_get_file_not_found_on_disk(self, mock_server: CloudServer, mock_file_metadata: FileMetadata) -> None:
        """Test get_file raises 404 when file in metadata but not on disk."""
        request = MagicMock(spec=Request)

        # Ensure file is in metadata but not on disk
        file_path = mock_server.storage_directory / mock_file_metadata.filepath
        if file_path.exists():
            file_path.unlink()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(mock_server.get_file(request, mock_file_metadata.filepath))

        assert exc_info.value.status_code == ResponseCode.NOT_FOUND
        assert f"File not found on disk: {mock_file_metadata.filepath}" in str(exc_info.value.detail)

    def test_get_file_endpoint(self, mock_server: CloudServer, mock_file_metadata: FileMetadata) -> None:
        """Test GET /files/{filepath} endpoint returns file successfully."""
        app = mock_server.app
        client = TestClient(app)

        response = client.get(f"/files/{mock_file_metadata.filepath}")
        assert response.status_code == ResponseCode.OK
        assert response.content == b"test content"

    def test_get_file_endpoint_not_found(self, mock_server: CloudServer) -> None:
        """Test GET /files/{filepath} endpoint returns 404 for nonexistent file."""
        app = mock_server.app
        client = TestClient(app)

        filepath = "nonexistent/file.txt"
        response = client.get(f"/files/{filepath}")
        assert response.status_code == ResponseCode.NOT_FOUND

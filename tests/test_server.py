"""Unit tests for the python_cloud_server.server module."""

import asyncio
from collections.abc import Generator
from importlib.metadata import PackageMetadata
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, Security, UploadFile
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader
from fastapi.testclient import TestClient
from python_template_server.constants import BYTES_TO_MB
from python_template_server.models import ResponseCode

from python_cloud_server.metadata import MetadataManager
from python_cloud_server.models import CloudServerConfig, DeleteFileResponse, FileMetadata, PostFileResponse
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


def _mock_file_factory(filename: str, content: bytes, content_type: str) -> UploadFile:
    """Helper to create a mock UploadFile."""
    file = MagicMock(spec=UploadFile)
    file.filename = filename
    file.content_type = content_type
    bytes_io = BytesIO(content)

    async def mock_read(size: int = -1) -> bytes:
        return bytes_io.read(size)

    file.read = mock_read
    return file


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


class TestPostFileEndpoint:
    """Integration and unit tests for the POST /files/{filepath} endpoint."""

    MOCK_FILENAME = "test_upload.txt"
    MOCK_FILEPATH = f"uploads/{MOCK_FILENAME}"
    MOCK_CONTENT = b"test file content"
    MOCK_CONTENT_TYPE = "text/plain"

    def test_post_file(self, mock_server: CloudServer) -> None:
        """Test post_file successfully uploads a file."""
        request = MagicMock(spec=Request)
        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)

        response = asyncio.run(mock_server.post_file(request, self.MOCK_FILEPATH, mock_file))

        assert isinstance(response, PostFileResponse)
        assert response.code == ResponseCode.OK
        assert response.filepath == self.MOCK_FILEPATH
        assert response.size == len(self.MOCK_CONTENT)
        assert response.message == "File uploaded successfully"

        # Verify file exists on disk
        full_path = mock_server.storage_directory / self.MOCK_FILEPATH
        assert full_path.exists()
        assert full_path.read_bytes() == self.MOCK_CONTENT

        # Verify metadata exists
        metadata = mock_server.metadata_manager.get_file_entry(self.MOCK_FILEPATH)
        assert metadata is not None
        assert metadata.filepath == self.MOCK_FILEPATH
        assert metadata.size == len(self.MOCK_CONTENT)
        assert metadata.mime_type == self.MOCK_CONTENT_TYPE

    def test_post_file_duplicate(self, mock_server: CloudServer) -> None:
        """Test post_file returns conflict when file already exists."""
        request = MagicMock(spec=Request)
        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)

        response1 = asyncio.run(mock_server.post_file(request, self.MOCK_FILEPATH, mock_file))
        assert response1.code == ResponseCode.OK

        # Try to upload again
        response2 = asyncio.run(mock_server.post_file(request, self.MOCK_FILEPATH, mock_file))
        assert isinstance(response2, PostFileResponse)
        assert response2.code == ResponseCode.CONFLICT
        assert response2.message == f"File already exists: {self.MOCK_FILEPATH}"
        assert response2.filepath == self.MOCK_FILEPATH
        assert response2.size == 0

    def test_post_file_guess_mime_type(self, mock_server: CloudServer) -> None:
        """Test post_file guesses MIME type when not provided."""
        request = MagicMock(spec=Request)
        filepath = "uploads/image.png"
        mock_file = _mock_file_factory("image.png", b"\x89PNG\r\n\x1a\n", "application/octet-stream")

        response = asyncio.run(mock_server.post_file(request, filepath, mock_file))

        assert response.code == ResponseCode.OK
        metadata = mock_server.metadata_manager.get_file_entry(filepath)
        assert metadata is not None
        assert metadata.mime_type == "image/png"

    def test_post_file_exceeds_size_limit(self, mock_server: CloudServer) -> None:
        """Test post_file returns error when file exceeds size limit."""
        request = MagicMock(spec=Request)
        max_size = mock_server.config.storage_config.max_file_size_mb * BYTES_TO_MB
        large_content = b"X" * (max_size + 1000)
        mock_file = _mock_file_factory(self.MOCK_FILENAME, large_content, "application/octet-stream")

        response = asyncio.run(mock_server.post_file(request, self.MOCK_FILEPATH, mock_file))

        assert isinstance(response, PostFileResponse)
        assert response.code in (ResponseCode.BAD_REQUEST, ResponseCode.INTERNAL_SERVER_ERROR)
        assert response.message in [
            f"File size exceeds maximum limit: {self.MOCK_FILEPATH} ({len(large_content)} bytes)",
            f"Failed to save file: {self.MOCK_FILEPATH}",
        ]

        # Verify no metadata entry
        assert mock_server.metadata_manager.get_file_entry(self.MOCK_FILEPATH) is None

    def test_post_file_metadata_error_cleanup(self, mock_server: CloudServer) -> None:
        """Test post_file cleans up file when metadata save fails."""
        request = MagicMock(spec=Request)
        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)

        # Patch add_file_entry to raise an exception
        with patch.object(mock_server.metadata_manager, "add_file_entry", side_effect=Exception("Metadata error")):
            response = asyncio.run(mock_server.post_file(request, self.MOCK_FILEPATH, mock_file))

        assert isinstance(response, PostFileResponse)
        assert response.code == ResponseCode.INTERNAL_SERVER_ERROR
        assert response.message == f"Failed to save metadata for file: {self.MOCK_FILEPATH}"

        # Verify file was cleaned up
        full_path = mock_server.storage_directory / self.MOCK_FILEPATH
        assert not full_path.exists()

    def test_post_file_endpoint(self, mock_server: CloudServer) -> None:
        """Test POST /files/{filepath} endpoint via TestClient."""
        app = mock_server.app
        client = TestClient(app)

        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)

        response = client.post(
            f"/files/{self.MOCK_FILEPATH}",
            files={"file": (mock_file.filename, BytesIO(self.MOCK_CONTENT), mock_file.content_type)},
        )

        assert response.status_code == ResponseCode.OK
        data = response.json()
        assert data["filepath"] == self.MOCK_FILEPATH
        assert data["size"] == len(self.MOCK_CONTENT)

        # Verify file exists
        full_path = mock_server.storage_directory / self.MOCK_FILEPATH
        assert full_path.exists()

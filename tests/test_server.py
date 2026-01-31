"""Unit tests for the python_cloud_server.server module."""

import asyncio
from collections.abc import Generator
from importlib.metadata import PackageMetadata
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request, Security, UploadFile
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader
from fastapi.testclient import TestClient
from python_template_server.constants import BYTES_TO_MB
from python_template_server.models import ResponseCode

from python_cloud_server.metadata import MetadataManager
from python_cloud_server.models import (
    CloudServerConfig,
    DeleteFileResponse,
    FileMetadata,
    GetFilesRequest,
    GetFilesResponse,
    PatchFileRequest,
    PatchFileResponse,
    PostFileResponse,
)
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
    mock_cloud_server_config: CloudServerConfig, mock_metadata_manager: MetadataManager, mock_server_root_path: Path
) -> Generator[CloudServer]:
    """Provide a CloudServer instance for testing."""

    async def fake_verify_api_key(
        api_key: str | None = Security(APIKeyHeader(name="X-API-Key", auto_error=False)),
    ) -> None:
        """Fake verify API key that accepts the security header and always succeeds in tests."""
        return

    storage_path = mock_server_root_path / "storage"

    with (
        patch.object(CloudServer, "_verify_api_key", new=fake_verify_api_key),
        patch.object(CloudServer, "server_directory", property(lambda self: mock_server_root_path)),
        patch.object(CloudServer, "storage_directory", property(lambda self: storage_path)),
        patch.object(CloudServer, "metadata_filepath", property(lambda self: mock_server_root_path / "metadata.json")),
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
        assert mock_server.storage_directory.exists()
        assert mock_server.metadata_filepath.parent.exists()

    def test_server_directory_properties(self, mock_server: CloudServer) -> None:
        """Test server directory property methods."""
        assert mock_server.storage_directory == mock_server.server_directory / "storage"
        assert mock_server.metadata_filepath == mock_server.server_directory / "metadata.json"

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

    def test_setup_routes(self, mock_server: CloudServer) -> None:
        """Test that routes are set up correctly."""
        api_routes = [route for route in mock_server.app.routes if isinstance(route, APIRoute)]
        routes = [route.path for route in api_routes]
        expected_endpoints = [
            "/health",
            "/login",
            "/files",
            "/files/{filepath:path}",
        ]
        for endpoint in expected_endpoints:
            assert endpoint in routes, f"Expected endpoint {endpoint} not found in routes"


class TestGetFilesEndpoint:
    """Integration and unit tests for the GET /files endpoint."""

    @pytest.fixture
    def mock_request_object(self) -> Request:
        """Provide a mock Request object."""
        return MagicMock(spec=Request)

    def test_get_files(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test get_files successfully retrieves files."""
        files_request = GetFilesRequest(tag=None, offset=0, limit=100)
        mock_request_object.json = AsyncMock(return_value=files_request.model_dump())

        response = asyncio.run(mock_server.get_files(mock_request_object))

        assert isinstance(response, GetFilesResponse)
        assert response.message == "Retrieved 1 files successfully."
        assert len(response.files) == 1

    def test_get_files_with_tag_filter(
        self,
        mock_server: CloudServer,
        mock_file_metadata: FileMetadata,
        mock_request_object: Request,
    ) -> None:
        """Test get_files filters by tag."""
        files_request = GetFilesRequest(tag="test", offset=0, limit=100)
        mock_request_object.json = AsyncMock(return_value=files_request.model_dump())

        response = asyncio.run(mock_server.get_files(mock_request_object))

        assert isinstance(response, GetFilesResponse)
        assert len(response.files) == 1
        assert response.files[0].filepath == mock_file_metadata.filepath

    def test_get_files_with_nonexistent_tag(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test get_files returns empty list for nonexistent tag."""
        files_request = GetFilesRequest(tag="nonexistent", offset=0, limit=100)
        mock_request_object.json = AsyncMock(return_value=files_request.model_dump())

        response = asyncio.run(mock_server.get_files(mock_request_object))

        assert isinstance(response, GetFilesResponse)
        assert len(response.files) == 0

    def test_get_files_pagination(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test get_files pagination."""
        limit = 10
        files_request = GetFilesRequest(tag=None, offset=0, limit=limit)
        mock_request_object.json = AsyncMock(return_value=files_request.model_dump())

        response = asyncio.run(mock_server.get_files(mock_request_object))

        assert isinstance(response, GetFilesResponse)
        assert len(response.files) <= limit

    def test_get_files_endpoint(self, mock_server: CloudServer) -> None:
        """Test GET /files endpoint returns files successfully."""
        app = mock_server.app
        client = TestClient(app)

        response = client.request(
            "GET",
            "/files",
            json={"tag": None, "offset": 0, "limit": 100},
        )
        assert response.status_code == ResponseCode.OK
        data = response.json()
        assert data["message"] == "Retrieved 1 files successfully."
        assert len(data["files"]) == 1


class TestGetFileEndpoint:
    """Integration and unit tests for the GET /files/{filepath} endpoint."""

    @pytest.fixture
    def mock_request_object(self) -> Request:
        """Provide a mock Request object."""
        return MagicMock(spec=Request)

    @pytest.fixture
    def mock_file_response(self, mock_server: CloudServer, mock_file_metadata: FileMetadata) -> Generator[MagicMock]:
        """Mock FastAPI FileResponse for file serving."""
        mock_response = MagicMock()
        mock_response.path = mock_server.storage_directory / mock_file_metadata.filepath
        mock_response.media_type = mock_file_metadata.mime_type
        mock_response.filename = Path(mock_file_metadata.filepath).name
        mock_response.content = b"test content"
        with patch("python_cloud_server.server.FileResponse", return_value=mock_response):
            yield mock_response

    def test_get_file(
        self,
        mock_server: CloudServer,
        mock_file_metadata: FileMetadata,
        mock_file_response: MagicMock,
        mock_request_object: Request,
    ) -> None:
        """Test get_file successfully retrieves a file."""
        response = asyncio.run(mock_server.get_file(mock_request_object, mock_file_metadata.filepath))

        assert response == mock_file_response
        assert mock_file_response.path == mock_server.storage_directory / mock_file_metadata.filepath
        assert mock_file_response.media_type == mock_file_metadata.mime_type
        assert mock_file_response.filename == Path(mock_file_metadata.filepath).name

    def test_get_file_not_found_in_metadata(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test get_file raises 404 when file not in metadata."""
        filepath = "nonexistent/file.txt"

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(mock_server.get_file(mock_request_object, filepath))

        assert exc_info.value.status_code == ResponseCode.NOT_FOUND
        assert f"File not found in metadata: {filepath}" in str(exc_info.value.detail)

    def test_get_file_not_found_on_disk(
        self,
        mock_server: CloudServer,
        mock_file_metadata: FileMetadata,
        mock_request_object: Request,
    ) -> None:
        """Test get_file raises 404 when file in metadata but not on disk."""
        filepath = mock_file_metadata.filepath
        (mock_server.storage_directory / filepath).unlink(missing_ok=True)

        with pytest.raises(HTTPException, match=rf"File not found on disk: {filepath}") as exc_info:
            asyncio.run(mock_server.get_file(mock_request_object, filepath))

        assert exc_info.value.status_code == ResponseCode.NOT_FOUND

    def test_get_file_endpoint(self, mock_server: CloudServer, mock_file_metadata: FileMetadata) -> None:
        """Test GET /files/{filepath} endpoint returns file successfully."""
        app = mock_server.app
        client = TestClient(app)

        response = client.get(f"/files/{mock_file_metadata.filepath}")
        assert response.status_code == ResponseCode.OK
        assert response.content == b"test content"


class TestPostFileEndpoint:
    """Integration and unit tests for the POST /files/{filepath} endpoint."""

    MOCK_FILENAME = "test_upload.txt"
    MOCK_FILEPATH = f"uploads/{MOCK_FILENAME}"
    MOCK_CONTENT = b"test file content"
    MOCK_CONTENT_TYPE = "text/plain"

    @pytest.fixture
    def mock_request_object(self) -> Request:
        """Provide a mock Request object."""
        return MagicMock(spec=Request)

    def test_post_file(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test post_file successfully uploads a file."""
        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)

        response = asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        assert isinstance(response, PostFileResponse)
        assert response.filepath == self.MOCK_FILEPATH
        assert response.size == len(self.MOCK_CONTENT)
        assert response.message == f"File uploaded successfully: {self.MOCK_FILEPATH} ({len(self.MOCK_CONTENT)} bytes)"

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

    def test_post_file_duplicate(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test post_file returns conflict when file already exists."""
        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)

        asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        # Try to upload again
        with pytest.raises(HTTPException, match=rf"File already exists: {self.MOCK_FILEPATH}") as exc_info:
            asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        assert exc_info.value.status_code == ResponseCode.CONFLICT

    def test_post_file_guess_mime_type(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test post_file guesses MIME type when not provided."""
        filepath = "uploads/image.png"
        mock_file = _mock_file_factory("image.png", b"\x89PNG\r\n\x1a\n", "application/octet-stream")

        asyncio.run(mock_server.post_file(mock_request_object, filepath, mock_file))

        metadata = mock_server.metadata_manager.get_file_entry(filepath)
        assert metadata is not None
        assert metadata.mime_type == "image/png"

    def test_post_file_exceeds_size_limit(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test post_file returns error when file exceeds size limit."""
        max_size = mock_server.config.storage_config.max_file_size_mb * BYTES_TO_MB
        large_content = b"X" * (max_size + 1000)
        mock_file = _mock_file_factory(self.MOCK_FILENAME, large_content, "application/octet-stream")

        with pytest.raises(HTTPException, match=rf"Failed to save file: {self.MOCK_FILEPATH}") as exc_info:
            asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        assert exc_info.value.status_code == ResponseCode.INTERNAL_SERVER_ERROR

        # Verify no metadata entry
        assert mock_server.metadata_manager.get_file_entry(self.MOCK_FILEPATH) is None

    def test_post_file_metadata_error_cleanup(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test post_file cleans up file when metadata save fails."""
        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)

        # Patch add_file_entry to raise an exception
        with (
            patch.object(mock_server.metadata_manager, "add_file_entries", side_effect=Exception("Metadata error")),
            pytest.raises(HTTPException, match=rf"Failed to save metadata for file: {self.MOCK_FILEPATH}") as exc_info,
        ):
            asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        assert exc_info.value.status_code == ResponseCode.INTERNAL_SERVER_ERROR

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


class TestPatchFileEndpoint:
    """Integration and unit tests for the PATCH /files/{filepath} endpoint."""

    MOCK_FILENAME = "test_patch.txt"
    MOCK_FILEPATH = f"uploads/{MOCK_FILENAME}"
    MOCK_CONTENT = b"patch me"
    MOCK_CONTENT_TYPE = "text/plain"

    @pytest.fixture
    def mock_request_object(self) -> Request:
        """Provide a mock Request object."""
        return MagicMock(spec=Request)

    def test_patch_file_add_tags(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test patch_file successfully adds tags."""
        patch_request = PatchFileRequest(add_tags=["new_tag"], remove_tags=[])
        mock_request_object.json = AsyncMock(return_value=patch_request.model_dump())

        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)
        asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        response = asyncio.run(mock_server.patch_file(mock_request_object, self.MOCK_FILEPATH))

        assert isinstance(response, PatchFileResponse)
        assert response.filepath == self.MOCK_FILEPATH
        assert "new_tag" in response.tags

    def test_patch_file_remove_tags(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test patch_file successfully removes tags."""
        patch_request = PatchFileRequest(add_tags=[], remove_tags=["test"])
        mock_request_object.json = AsyncMock(return_value=patch_request.model_dump())

        response = asyncio.run(mock_server.patch_file(mock_request_object, "test/test.txt"))

        assert isinstance(response, PatchFileResponse)
        assert "test" not in response.tags

    def test_patch_file_move_file(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test patch_file successfully moves/renames file."""
        new_filepath = "uploads/moved.txt"
        patch_request = PatchFileRequest(new_filepath=new_filepath, add_tags=[], remove_tags=[])
        mock_request_object.json = AsyncMock(return_value=patch_request.model_dump())

        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)
        asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        response = asyncio.run(mock_server.patch_file(mock_request_object, self.MOCK_FILEPATH))

        assert isinstance(response, PatchFileResponse)
        assert response.filepath == new_filepath

        old_path = mock_server.storage_directory / self.MOCK_FILEPATH
        new_path = mock_server.storage_directory / new_filepath
        assert not old_path.exists()
        assert new_path.exists()

    def test_patch_file_not_found(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test patch_file returns error when file doesn't exist."""
        patch_request = PatchFileRequest(add_tags=["tag"], remove_tags=[])
        mock_request_object.json = AsyncMock(return_value=patch_request.model_dump())
        filepath = "nonexistent/file.txt"

        with pytest.raises(HTTPException, match=rf"File not found in metadata: {filepath}") as exc_info:
            asyncio.run(mock_server.patch_file(mock_request_object, filepath))

        assert exc_info.value.status_code == ResponseCode.NOT_FOUND

    def test_patch_file_destination_exists(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test patch_file returns conflict when destination exists."""
        new_filepath = "test/test.txt"
        patch_request = PatchFileRequest(new_filepath=new_filepath, add_tags=[], remove_tags=[])

        mock_request_object.json = AsyncMock(return_value=patch_request.model_dump())

        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)
        asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        with pytest.raises(HTTPException, match=rf"Destination file already exists: {new_filepath}") as exc_info:
            asyncio.run(mock_server.patch_file(mock_request_object, self.MOCK_FILEPATH))

        assert exc_info.value.status_code == ResponseCode.CONFLICT

    def test_patch_file_tag_limit_exceeded(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test patch_file returns error when tag limit exceeded."""
        # Add more tags than allowed
        max_tags = mock_server.config.storage_config.max_tags_per_file
        add_tags = [f"tag{i}" for i in range(max_tags)]
        patch_request = PatchFileRequest(add_tags=add_tags, remove_tags=[])
        mock_request_object.json = AsyncMock(return_value=patch_request.model_dump())

        with pytest.raises(
            HTTPException, match=rf"Number of tags exceeds maximum: {len(add_tags) + 1} > {max_tags}"
        ) as exc_info:
            asyncio.run(mock_server.patch_file(mock_request_object, "test/test.txt"))

        assert exc_info.value.status_code == ResponseCode.BAD_REQUEST

    def test_patch_file_tag_too_long(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test patch_file skips tags that are too long."""
        max_length = mock_server.config.storage_config.max_tag_length
        long_tag = "a" * (max_length + 1)
        patch_request = PatchFileRequest(add_tags=[long_tag, "valid_tag"], remove_tags=[])
        mock_request_object.json = AsyncMock(return_value=patch_request.model_dump())

        response = asyncio.run(mock_server.patch_file(mock_request_object, "test/test.txt"))

        assert isinstance(response, PatchFileResponse)
        assert "valid_tag" in response.tags
        assert long_tag not in response.tags

    def test_patch_file_move_error(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
        mock_rename_file: MagicMock,
    ) -> None:
        """Test patch_file returns error when file move fails."""
        new_filepath = "uploads/moved.txt"
        patch_request = PatchFileRequest(new_filepath=new_filepath, add_tags=[], remove_tags=[])
        mock_request_object.json = AsyncMock(return_value=patch_request.model_dump())

        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)
        asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        mock_rename_file.side_effect = Exception("Rename failed")
        with pytest.raises(
            HTTPException, match=rf"Failed to move file from {self.MOCK_FILEPATH} to {new_filepath}"
        ) as exc_info:
            asyncio.run(mock_server.patch_file(mock_request_object, self.MOCK_FILEPATH))

        assert exc_info.value.status_code == ResponseCode.INTERNAL_SERVER_ERROR

    def test_patch_file_metadata_update_failure_rollback(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test patch_file rolls back file move when metadata update fails."""
        new_filepath = "uploads/moved.txt"
        patch_request = PatchFileRequest(new_filepath=new_filepath, add_tags=[], remove_tags=[])
        mock_request_object.json = AsyncMock(return_value=patch_request.model_dump())

        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)
        asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        with (
            patch.object(
                mock_server.metadata_manager, "update_file_entry", side_effect=Exception("Metadata update failed")
            ),
            pytest.raises(
                HTTPException, match=rf"Failed to update metadata for file: {self.MOCK_FILEPATH}"
            ) as exc_info,
        ):
            asyncio.run(mock_server.patch_file(mock_request_object, self.MOCK_FILEPATH))

        assert exc_info.value.status_code == ResponseCode.INTERNAL_SERVER_ERROR

        old_path = mock_server.storage_directory / self.MOCK_FILEPATH
        new_path = mock_server.storage_directory / new_filepath
        assert old_path.exists()
        assert not new_path.exists()

        metadata = mock_server.metadata_manager.get_file_entry(self.MOCK_FILEPATH)
        assert metadata is not None
        assert metadata.filepath == self.MOCK_FILEPATH

    def test_patch_file_endpoint(self, mock_server: CloudServer) -> None:
        """Test PATCH /files/{filepath} endpoint via TestClient."""
        app = mock_server.app
        client = TestClient(app)

        # First upload a file
        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)
        client.post(
            f"/files/{self.MOCK_FILEPATH}",
            files={"file": (mock_file.filename, BytesIO(self.MOCK_CONTENT), mock_file.content_type)},
        )

        # Patch the file
        patch_data = {"add_tags": ["new_tag"], "remove_tags": []}
        response = client.patch(f"/files/{self.MOCK_FILEPATH}", json=patch_data)

        assert response.status_code == ResponseCode.OK
        data = response.json()

        assert data["filepath"] == self.MOCK_FILEPATH
        assert "new_tag" in data["tags"]


class TestDeleteFileEndpoint:
    """Integration and unit tests for the DELETE /files/{filepath} endpoint."""

    MOCK_FILENAME = "test_delete.txt"
    MOCK_FILEPATH = f"uploads/{MOCK_FILENAME}"
    MOCK_CONTENT = b"delete me"
    MOCK_CONTENT_TYPE = "text/plain"

    @pytest.fixture
    def mock_request_object(self) -> Request:
        """Provide a mock Request object."""
        return MagicMock(spec=Request)

    def test_delete_file_success(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test delete_file successfully deletes a file."""
        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)
        asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        full_path = mock_server.storage_directory / self.MOCK_FILEPATH
        assert full_path.exists()
        assert mock_server.metadata_manager.get_file_entry(self.MOCK_FILEPATH) is not None

        response = asyncio.run(mock_server.delete_file(mock_request_object, self.MOCK_FILEPATH))

        assert isinstance(response, DeleteFileResponse)
        assert response.filepath == self.MOCK_FILEPATH
        assert response.message == f"File deleted successfully: {self.MOCK_FILEPATH}"

        assert not full_path.exists()
        assert mock_server.metadata_manager.get_file_entry(self.MOCK_FILEPATH) is None

    def test_delete_file_not_found(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test delete_file returns error when file doesn't exist."""
        filepath = "nonexistent/file.txt"

        with pytest.raises(HTTPException, match=rf"File not found in metadata: {filepath}") as exc_info:
            asyncio.run(mock_server.delete_file(mock_request_object, filepath))

        assert exc_info.value.status_code == ResponseCode.NOT_FOUND

    def test_delete_file_metadata_error(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test delete_file returns error when metadata deletion fails."""
        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)
        asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        with (
            patch.object(
                mock_server.metadata_manager, "delete_file_entries", side_effect=Exception("Metadata deletion error")
            ),
            pytest.raises(
                HTTPException, match=rf"Failed to delete metadata for file: {self.MOCK_FILEPATH}"
            ) as exc_info,
        ):
            asyncio.run(mock_server.delete_file(mock_request_object, self.MOCK_FILEPATH))

        assert exc_info.value.status_code == ResponseCode.INTERNAL_SERVER_ERROR

    def test_delete_file_disk_error(
        self,
        mock_server: CloudServer,
        mock_request_object: Request,
    ) -> None:
        """Test delete_file returns error when file deletion from disk fails."""
        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)
        asyncio.run(mock_server.post_file(mock_request_object, self.MOCK_FILEPATH, mock_file))

        with (
            patch.object(Path, "unlink", side_effect=Exception("Disk error")),
            pytest.raises(HTTPException, match=rf"Failed to delete file from disk: {self.MOCK_FILEPATH}") as exc_info,
        ):
            asyncio.run(mock_server.delete_file(mock_request_object, self.MOCK_FILEPATH))

        assert exc_info.value.status_code == ResponseCode.INTERNAL_SERVER_ERROR

        full_path = mock_server.storage_directory / self.MOCK_FILEPATH
        assert full_path.exists()
        assert mock_server.metadata_manager.get_file_entry(self.MOCK_FILEPATH) is not None

    def test_delete_file_endpoint(
        self,
        mock_server: CloudServer,
    ) -> None:
        """Test DELETE /files/{filepath} endpoint via TestClient."""
        app = mock_server.app
        client = TestClient(app)

        mock_file = _mock_file_factory(self.MOCK_FILENAME, self.MOCK_CONTENT, self.MOCK_CONTENT_TYPE)

        # First upload a file
        client.post(
            f"/files/{self.MOCK_FILEPATH}",
            files={"file": (mock_file.filename, BytesIO(self.MOCK_CONTENT), mock_file.content_type)},
        )

        # Verify file exists
        full_path = mock_server.storage_directory / self.MOCK_FILEPATH
        assert full_path.exists()

        # Delete the file
        response = client.delete(f"/files/{self.MOCK_FILEPATH}")

        assert response.status_code == ResponseCode.OK
        data = response.json()
        assert data["filepath"] == self.MOCK_FILEPATH

        # Verify file deleted
        assert not full_path.exists()

"""Unit tests for the python_cloud_server.models module."""

from python_cloud_server.models import (
    CloudServerConfig,
    DeleteFileResponse,
    FileMetadata,
    GetFilesRequest,
    GetFilesResponse,
    PatchFileRequest,
    PatchFileResponse,
    PostFileResponse,
    StorageConfig,
)


# Cloud Server Configuration Models
class TestStorageConfig:
    """Unit tests for the StorageConfig class."""

    def test_model_dump(self, mock_storage_config: StorageConfig, mock_storage_config_dict: dict) -> None:
        """Test the model_dump method."""
        assert mock_storage_config.model_dump() == mock_storage_config_dict


class TestCloudServerConfig:
    """Unit tests for the CloudServerConfig class."""

    def test_model_dump(self, mock_cloud_server_config: CloudServerConfig, mock_storage_config: StorageConfig) -> None:
        """Test the model_dump method."""
        assert mock_cloud_server_config.storage_config.model_dump() == mock_storage_config.model_dump()


# File Metadata Model
class TestFileMetadata:
    """Unit tests for the FileMetadata class."""

    def test_model_dump(self, mock_file_metadata: FileMetadata, mock_file_metadata_dict: dict) -> None:
        """Test the model_dump method."""
        dumped = mock_file_metadata.model_dump()
        expected = mock_file_metadata_dict.copy()
        expected["uploaded_at"] = mock_file_metadata.uploaded_at
        expected["updated_at"] = mock_file_metadata.updated_at
        assert dumped == expected


# API Response Models
class TestGetFilesResponse:
    """Unit tests for the GetFilesResponse class."""

    def test_model_dump(self) -> None:
        """Test the model_dump method."""
        data = {
            "code": 200,
            "message": "Files retrieved successfully",
            "timestamp": "2025-01-01T12:00:00Z",
            "files": [],
            "total": 0,
        }
        response = GetFilesResponse.model_validate(data)
        assert response.model_dump() == data


class TestPostFileResponse:
    """Unit tests for the PostFileResponse class."""

    def test_model_dump(self) -> None:
        """Test the model_dump method."""
        data = {
            "code": 201,
            "message": "File uploaded successfully",
            "timestamp": "2025-01-01T12:00:00Z",
            "filepath": "animals/cat.png",
            "size": 2048,
        }
        response = PostFileResponse.model_validate(data)
        assert response.model_dump() == data


class TestPatchFileResponse:
    """Unit tests for the PatchFileResponse class."""

    def test_model_dump(self) -> None:
        """Test the model_dump method."""
        data = {
            "code": 200,
            "message": "File metadata updated successfully",
            "timestamp": "2025-01-01T12:00:00Z",
            "success": True,
            "filepath": "uploads/renamed.png",
            "tags": ["new", "tag"],
        }
        response = PatchFileResponse.model_validate(data)
        assert response.model_dump() == data


class TestDeleteFileResponse:
    """Unit tests for the DeleteFileResponse class."""

    def test_model_dump(self) -> None:
        """Test the model_dump method."""
        data = {
            "code": 200,
            "message": "File deleted successfully",
            "timestamp": "2025-01-01T12:00:00Z",
            "success": True,
            "filepath": "uploads/file_to_delete.png",
        }
        response = DeleteFileResponse.model_validate(data)
        assert response.model_dump() == data


# API Request Models
class TestGetFilesRequest:
    """Unit tests for the GetFilesRequest class."""

    def test_model_dump(self) -> None:
        """Test the model_dump method."""
        data = {
            "tag": "example",
            "offset": 10,
            "limit": 50,
        }
        request = GetFilesRequest.model_validate(data)
        assert request.model_dump() == data


class TestPatchFileRequest:
    """Unit tests for the PatchFileRequest class."""

    def test_model_dump(self) -> None:
        """Test the model_dump method."""
        data = {
            "new_filepath": "uploads/updated_file.png",
            "add_tags": ["updated", "file"],
            "remove_tags": ["old"],
        }
        request = PatchFileRequest.model_validate(data)
        assert request.model_dump() == data

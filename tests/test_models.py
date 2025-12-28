"""Unit tests for the python_cloud_server.models module."""

from python_cloud_server.models import CloudServerConfig, FileMetadata, StorageConfig


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
        assert mock_file_metadata.model_dump() == mock_file_metadata_dict

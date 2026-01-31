"""Pytest fixtures for the application's unit tests."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from python_cloud_server.metadata import MetadataManager
from python_cloud_server.models import CloudServerConfig, FileMetadata, StorageConfig


# General fixtures
@pytest.fixture
def mock_open_file() -> Generator[MagicMock]:
    """Mock the Path.open() method."""
    with patch("pathlib.Path.open", mock_open()) as mock_file:
        yield mock_file


@pytest.fixture
def mock_replace_file() -> Generator[MagicMock]:
    """Mock the Path.replace() method."""
    with patch("pathlib.Path.replace") as mock_replace:
        yield mock_replace


@pytest.fixture
def mock_rename_file() -> Generator[MagicMock]:
    """Mock the Path.rename() method."""
    with patch("pathlib.Path.rename") as mock_rename:
        yield mock_rename


# Cloud Server Configuration Models
@pytest.fixture
def mock_storage_config_dict() -> dict:
    """Provide a mock storage configuration dictionary."""
    return {
        "capacity_gb": 20,
        "upload_chunk_size_kb": 8,
        "max_file_size_mb": 100,
        "max_tags_per_file": 10,
        "max_tag_length": 50,
    }


@pytest.fixture
def mock_storage_config(mock_storage_config_dict: dict) -> StorageConfig:
    """Provide a mock StorageConfig instance."""
    return StorageConfig.model_validate(mock_storage_config_dict)


@pytest.fixture
def mock_cloud_server_config(mock_storage_config: StorageConfig) -> CloudServerConfig:
    """Provide a mock CloudServerConfig instance with temporary storage."""
    return CloudServerConfig(storage_config=mock_storage_config)


# File Metadata Model
@pytest.fixture
def mock_file_metadata_dict() -> dict:
    """Provide a mock file metadata dictionary."""
    return {
        "filepath": "test/test.txt",
        "mime_type": "text/plain",
        "size": 1234,
        "tags": ["test"],
    }


@pytest.fixture
def mock_file_metadata(mock_file_metadata_dict: dict) -> FileMetadata:
    """Provide a mock FileMetadata instance."""
    return FileMetadata.new_current_instance(
        filepath=mock_file_metadata_dict["filepath"],
        mime_type=mock_file_metadata_dict["mime_type"],
        size=mock_file_metadata_dict["size"],
        tags=mock_file_metadata_dict["tags"],
    )


# Server fixtures
@pytest.fixture
def mock_server_root_path(tmp_path: Path) -> Path:
    """Create a temporary server root path."""
    server_root = tmp_path / "server"
    server_root.mkdir(parents=True, exist_ok=True)
    return server_root


@pytest.fixture
def mock_metadata_manager(mock_server_root_path: Path, mock_file_metadata: FileMetadata) -> MetadataManager:
    """Create a metadata manager."""
    file_path = mock_server_root_path / "storage" / mock_file_metadata.filepath
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("test content")

    metadata_filepath = mock_server_root_path / "metadata.json"
    metadata_manager = MetadataManager(metadata_filepath)
    metadata_manager.add_file_entries([mock_file_metadata])
    return metadata_manager

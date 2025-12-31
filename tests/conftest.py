"""Pytest fixtures for the application's unit tests."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from python_cloud_server.metadata import MetadataManager
from python_cloud_server.models import CloudServerConfig, FileMetadata, StorageConfig


# General fixtures
@pytest.fixture(autouse=True)
def mock_here(tmp_path: str) -> Generator[MagicMock]:
    """Mock the here() function to return a temporary directory."""
    with patch("pyhere.here") as mock_here:
        mock_here.return_value = tmp_path
        yield mock_here


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


# Cloud Server Configuration Models
@pytest.fixture
def mock_storage_config_dict(tmp_path: Path) -> dict:
    """Provide a mock storage configuration dictionary."""
    return {
        "server_directory": str(tmp_path),
        "storage_directory": "files",
        "metadata_filename": "metadata.json",
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
def mock_metadata_manager(mock_file_metadata: FileMetadata, mock_storage_config: StorageConfig) -> MetadataManager:
    """Create a metadata manager with a temporary file path.

    Uses tmp_path which is provided by pytest and is automatically cleaned up.
    """
    metadata_filepath = Path(mock_storage_config.server_directory) / mock_storage_config.metadata_filename
    metadata_manager = MetadataManager(metadata_filepath)
    file_path = (
        Path(mock_storage_config.server_directory) / mock_storage_config.storage_directory / mock_file_metadata.filepath
    )
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("test content")
    metadata_manager.add_file_entry(mock_file_metadata)
    return metadata_manager

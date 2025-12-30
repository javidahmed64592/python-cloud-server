"""Unit tests for the metadata manager."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from python_cloud_server.metadata import MetadataManager
from python_cloud_server.models import FileMetadata


class TestMetadataManager:
    """Unit tests for the MetadataManager class."""

    def test_mock_metadata_manager_initialization(self, mock_metadata_manager: MetadataManager) -> None:
        """Test that metadata manager initializes correctly."""
        assert mock_metadata_manager.metadata_filepath.exists()

    def test_file_count_property(self, mock_metadata_manager: MetadataManager) -> None:
        """Test the file_count property."""
        assert mock_metadata_manager.file_count == 1

    def test_save_metadata_atomic(
        self, mock_metadata_manager: MetadataManager, mock_file_metadata: FileMetadata
    ) -> None:
        """Test saving metadata to disk atomically."""
        mock_metadata_manager._save_metadata_atomic()

        assert mock_metadata_manager.metadata_filepath.exists()
        with mock_metadata_manager.metadata_filepath.open("r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert mock_file_metadata.filepath in saved_data
        assert saved_data[mock_file_metadata.filepath] == mock_file_metadata.model_dump(mode="json")
        assert not mock_metadata_manager.metadata_filepath.with_suffix(".tmp").exists()

    def test_save_metadata_atomic_exception(
        self, mock_metadata_manager: MetadataManager, mock_replace_file: MagicMock
    ) -> None:
        """Test that temporary file is cleaned up on exception during save."""
        mock_replace_file.side_effect = PermissionError("Mocked permission error")

        with pytest.raises(PermissionError, match="Mocked permission error"):
            mock_metadata_manager._save_metadata_atomic()

        assert not mock_metadata_manager.metadata_filepath.with_suffix(".tmp").exists()

    def test_load_metadata(self, mock_metadata_manager: MetadataManager, mock_file_metadata: FileMetadata) -> None:
        """Test loading metadata from disk."""
        # First, save the current metadata to disk
        mock_metadata_manager._save_metadata_atomic()

        # Create a new manager to load from disk
        new_manager = MetadataManager(mock_metadata_manager.metadata_filepath)
        assert new_manager.file_count == 1
        loaded_metadata = new_manager._metadata[mock_file_metadata.filepath]
        assert loaded_metadata == mock_file_metadata

    def test_load_metadata_file_not_exists(self, tmp_path: Path) -> None:
        """Test loading metadata when the file does not exist."""
        metadata_filepath = tmp_path / "nonexistent_metadata.json"
        manager = MetadataManager(metadata_filepath)

        assert manager.file_count == 0
        assert metadata_filepath.exists()

    def test_load_metadata_file_exception(
        self, mock_metadata_manager: MetadataManager, mock_open_file: MagicMock
    ) -> None:
        """Test that exception during load is raised."""
        mock_open_file.side_effect = PermissionError("Mocked permission error")

        with pytest.raises(PermissionError, match="Mocked permission error"):
            mock_metadata_manager._load_metadata()

    def test_file_exists(self, mock_metadata_manager: MetadataManager, mock_file_metadata: FileMetadata) -> None:
        """Test checking if a file exists in metadata."""
        assert mock_metadata_manager._file_exists(mock_file_metadata.filepath) is True
        assert mock_metadata_manager._file_exists("nonexistent/file.txt") is False

    def test_get_file_entry(self, mock_metadata_manager: MetadataManager, mock_file_metadata: FileMetadata) -> None:
        """Test retrieving a file entry from metadata."""
        entry = mock_metadata_manager.get_file_entry(mock_file_metadata.filepath)
        assert entry == mock_file_metadata

        nonexistent_entry = mock_metadata_manager.get_file_entry("nonexistent/file.txt")
        assert nonexistent_entry is None

    def test_add_file_entry(self, mock_metadata_manager: MetadataManager, mock_file_metadata: FileMetadata) -> None:
        """Test adding a new file entry to metadata."""
        new_file_metadata = mock_file_metadata.model_copy()
        new_file_metadata.filepath = "new/file.txt"

        initial_file_count = mock_metadata_manager.file_count
        mock_metadata_manager.add_file_entry(new_file_metadata)
        assert mock_metadata_manager.file_count == initial_file_count + 1
        retrieved_entry = mock_metadata_manager.get_file_entry(new_file_metadata.filepath)
        assert retrieved_entry == new_file_metadata

    def test_add_file_entry_existing_file(
        self, mock_metadata_manager: MetadataManager, mock_file_metadata: FileMetadata
    ) -> None:
        """Test that adding an existing file entry raises ValueError."""
        with pytest.raises(ValueError, match=f"File {mock_file_metadata.filepath} already exists!"):
            mock_metadata_manager.add_file_entry(mock_file_metadata)

    def test_delete_file_entry(self, mock_metadata_manager: MetadataManager, mock_file_metadata: FileMetadata) -> None:
        """Test deleting a file entry from metadata."""
        initial_file_count = mock_metadata_manager.file_count
        mock_metadata_manager.delete_file_entry(mock_file_metadata.filepath)
        assert mock_metadata_manager.file_count == initial_file_count - 1
        assert mock_metadata_manager.get_file_entry(mock_file_metadata.filepath) is None

    def test_delete_file_entry_nonexistent_file(self, mock_metadata_manager: MetadataManager) -> None:
        """Test that deleting a non-existent file entry raises KeyError."""
        nonexistent_file = "nonexistent/file.txt"
        with pytest.raises(KeyError, match=f"File {nonexistent_file} not found!"):
            mock_metadata_manager.delete_file_entry(nonexistent_file)

    def test_update_file_entry(self, mock_metadata_manager: MetadataManager, mock_file_metadata: FileMetadata) -> None:
        """Test updating a file entry in metadata."""
        updates = {"tags": ["updated", "tags"]}
        mock_metadata_manager.update_file_entry(mock_file_metadata.filepath, updates)

        updated_entry = mock_metadata_manager.get_file_entry(mock_file_metadata.filepath)
        assert updated_entry is not None
        assert updated_entry.tags == updates["tags"]
        assert updated_entry.updated_at != mock_file_metadata.updated_at

    def test_update_file_entry_filepath_change(
        self, mock_metadata_manager: MetadataManager, mock_file_metadata: FileMetadata
    ) -> None:
        """Test updating the filepath of a file entry."""
        new_filepath = "new/path.txt"
        initial_file_count = mock_metadata_manager.file_count

        mock_metadata_manager.update_file_entry(mock_file_metadata.filepath, {"filepath": new_filepath})

        assert mock_metadata_manager.file_count == initial_file_count
        assert mock_metadata_manager.get_file_entry(mock_file_metadata.filepath) is None

        updated_entry = mock_metadata_manager.get_file_entry(new_filepath)
        assert updated_entry is not None
        assert updated_entry.filepath == new_filepath
        assert updated_entry.mime_type == mock_file_metadata.mime_type
        assert updated_entry.size == mock_file_metadata.size
        assert updated_entry.tags == mock_file_metadata.tags
        assert updated_entry.uploaded_at == mock_file_metadata.uploaded_at
        assert updated_entry.updated_at != mock_file_metadata.updated_at

    def test_update_file_entry_nonexistent_file(self, mock_metadata_manager: MetadataManager) -> None:
        """Test that updating a non-existent file entry raises KeyError."""
        nonexistent_file = "nonexistent/file.txt"
        with pytest.raises(KeyError, match=f"File {nonexistent_file} not found!"):
            mock_metadata_manager.update_file_entry(nonexistent_file, {})

    def test_list_files(self, mock_metadata_manager: MetadataManager, mock_file_metadata: FileMetadata) -> None:
        """Test listing all file entries in metadata."""
        files = mock_metadata_manager.list_files()
        assert len(files) == 1
        assert files[0] == mock_file_metadata

    def test_list_files_with_tag(
        self, mock_metadata_manager: MetadataManager, mock_file_metadata: FileMetadata
    ) -> None:
        """Test listing file entries filtered by tag."""
        files_with_tag = mock_metadata_manager.list_files(tag="test")
        assert len(files_with_tag) == 1
        assert files_with_tag[0] == mock_file_metadata

        files_without_tag = mock_metadata_manager.list_files(tag="nonexistent")
        assert len(files_without_tag) == 0

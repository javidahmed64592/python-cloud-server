"""Metadata management for cloud server file storage."""

import json
import logging
import threading
from pathlib import Path

from python_cloud_server.models import FileMetadata

logger = logging.getLogger(__name__)


class MetadataManager:
    """Thread-safe manager for file metadata with atomic operations."""

    def __init__(self, metadata_filepath: Path) -> None:
        """Initialize the metadata manager.

        :param Path metadata_filepath: Path to the metadata.json file
        """
        self.metadata_filepath = metadata_filepath
        logger.info("Initializing MetadataManager with file: %s", self.metadata_filepath)
        self.metadata_filepath.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._metadata: dict[str, FileMetadata] = {}
        self._load_metadata()

    @property
    def file_count(self) -> int:
        """Get the total number of files in the metadata.

        :return int: Number of files
        """
        return len(self._metadata)

    def _save_metadata_atomic(self) -> None:
        """Save metadata to disk atomically using temporary file + rename.

        This ensures the metadata file is never left in a corrupted state.
        """
        temp_filepath = self.metadata_filepath.with_suffix(".tmp")

        try:
            with temp_filepath.open("w", encoding="utf-8") as f:
                json.dump(
                    {k: v.model_dump(mode="json") for k, v in self._metadata.items()}, f, ensure_ascii=False, indent=2
                )
            temp_filepath.replace(self.metadata_filepath)
            logger.info("Saved metadata for %d files", self.file_count)

        except Exception:
            logger.exception("Failed to save metadata!")
            if temp_filepath.exists():
                temp_filepath.unlink()
            raise

    def _load_metadata(self) -> None:
        """Load metadata from disk into memory."""
        with self._lock:
            if not self.metadata_filepath.exists():
                logger.info("Metadata file does not exist, initializing empty metadata.")
                self._metadata = {}
                self._save_metadata_atomic()
                return

            try:
                with self.metadata_filepath.open(encoding="utf-8") as f:
                    data = json.load(f)
                self._metadata = {k: FileMetadata.model_validate(v) for k, v in data.items()}
                logger.info("Loaded metadata for %d files", self.file_count)
            except Exception:
                logger.exception("Failed to load metadata!")
                raise

    def file_exists(self, filepath: str) -> bool:
        """Check if a file exists in the metadata.

        :param str filepath: The file path to check
        :return bool: True if the file exists, False otherwise
        """
        return filepath in self._metadata

    def list_files(self, tag: str | None = None) -> list[FileMetadata]:
        """List files with optional tag filtering and pagination.

        :param str | None tag: Optional tag to filter by
        :return list[FileMetadata]: List of file metadata objects
        """
        with self._lock:
            files = [
                FileMetadata.model_validate(data) for data in self._metadata.values() if tag is None or tag in data.tags
            ]

            files.sort(key=lambda f: f.uploaded_at, reverse=True)
            return files

    def get_file_entry(self, filepath: str) -> FileMetadata | None:
        """Get a file entry from the metadata.

        :param str filepath: The file path to retrieve
        :return FileMetadata | None: The file metadata or None if not found
        """
        with self._lock:
            if (data := self._metadata.get(filepath)) is None:
                return None
            return FileMetadata.model_validate(data)

    def add_file_entries(self, file_metadata_list: list[FileMetadata]) -> None:
        """Add new file entries to the metadata.

        :param list[FileMetadata] file_metadata_list: List of file metadata to add
        """
        _changes_applied = False
        with self._lock:
            for file_metadata in file_metadata_list:
                if not self.file_exists(file_metadata.filepath):
                    self._metadata[file_metadata.filepath] = file_metadata
                    _changes_applied = True
            if _changes_applied:
                self._save_metadata_atomic()

    def delete_file_entries(self, filepaths: list[str]) -> None:
        """Delete file entries from the metadata.

        :param list[str] filepaths: The file paths to delete
        """
        _changes_applied = False
        with self._lock:
            for filepath in filepaths:
                if self.file_exists(filepath):
                    del self._metadata[filepath]
                    _changes_applied = True

            if _changes_applied:
                self._save_metadata_atomic()

    def update_file_entry(self, filepath: str, updates: dict) -> None:
        """Update a file entry in the metadata.

        :param str filepath: The file path to update
        :param dict updates: Dictionary of fields to update
        :raise KeyError: If filepath does not exist
        """
        with self._lock:
            if not self.file_exists(filepath):
                msg = f"File {filepath} not found!"
                logger.error(msg)
                raise KeyError(msg)

            metadata_dict = self._metadata[filepath].model_dump()
            metadata_dict.update(updates)
            self._metadata[filepath] = FileMetadata.model_validate(metadata_dict)
            self._metadata[filepath].updated_at = FileMetadata.current_timestamp()

            if (new_filepath := updates.get("filepath")) and new_filepath != filepath:
                self._metadata[new_filepath] = self._metadata.pop(filepath)
                logger.info("Filepath updated from %s to %s", filepath, new_filepath)

            self._save_metadata_atomic()
            logger.info("Updated file entry: %s", filepath)

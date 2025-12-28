"""Metadata management for cloud server file storage."""

import json
import logging
import threading
from datetime import UTC, datetime
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
        logger.info("Initializing MetadataManager with file: %s", metadata_filepath)

        self._lock = threading.RLock()
        self._metadata: dict[str, dict] = {}
        self._load_metadata()

    @property
    def file_count(self) -> int:
        """Get the total number of files in the metadata.

        :return int: Number of files
        """
        return len(self._metadata)

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
                    self._metadata = json.load(f)
                logger.info("Loaded metadata for %d files", self.file_count)
            except json.JSONDecodeError:
                logger.exception("Failed to parse metadata file!")
                raise
            except Exception:
                logger.exception("Failed to load metadata!")
                raise

    def _save_metadata_atomic(self) -> None:
        """Save metadata to disk atomically using temporary file + rename.

        This ensures the metadata file is never left in a corrupted state.
        """
        temp_filepath = self.metadata_filepath.with_suffix(".tmp")

        try:
            with temp_filepath.open("w", encoding="utf-8") as f:
                json.dump(self._metadata, f, ensure_ascii=False, indent=2)

            temp_filepath.replace(self.metadata_filepath)
            logger.info("Saved metadata for %d files", self.file_count)

        except Exception:
            logger.exception("Failed to save metadata!")
            if temp_filepath.exists():
                temp_filepath.unlink()
            raise

    def _file_exists(self, file_id: str) -> bool:
        """Check if a file exists in the metadata.

        :param str file_id: The file ID to check
        :return bool: True if the file exists, False otherwise
        """
        return file_id in self._metadata

    def get_file_entry(self, file_id: str) -> FileMetadata | None:
        """Get a file entry from the metadata.

        :param str file_id: The file ID to retrieve
        :return FileMetadata | None: The file metadata or None if not found
        """
        with self._lock:
            if (data := self._metadata.get(file_id)) is None:
                return None
            return FileMetadata.model_validate(data)

    def add_file_entry(self, file_metadata: FileMetadata) -> None:
        """Add a new file entry to the metadata.

        :param FileMetadata file_metadata: The file metadata to add
        :raise ValueError: If file_id already exists
        """
        with self._lock:
            if self._file_exists(file_metadata.file_id):
                msg = f"File ID {file_metadata.file_id} already exists!"
                logger.error(msg)
                raise ValueError(msg)

            self._metadata[file_metadata.file_id] = file_metadata.model_dump(mode="json")
            self._save_metadata_atomic()
            logger.info("Added file entry: %s", file_metadata.file_id)

    def delete_file_entry(self, file_id: str) -> None:
        """Delete a file entry from the metadata.

        :param str file_id: The file ID to delete
        :raise KeyError: If file_id does not exist
        """
        with self._lock:
            if not self._file_exists(file_id):
                msg = f"File ID {file_id} not found!"
                logger.error(msg)
                raise KeyError(msg)

            del self._metadata[file_id]
            self._save_metadata_atomic()
            logger.info("Deleted file entry: %s", file_id)

    def update_file_entry(self, file_id: str, updates: dict) -> None:
        """Update a file entry in the metadata.

        :param str file_id: The file ID to update
        :param dict updates: Dictionary of fields to update
        :raise KeyError: If file_id does not exist
        """
        with self._lock:
            if not self._file_exists(file_id):
                msg = f"File ID {file_id} not found!"
                logger.error(msg)
                raise KeyError(msg)

            self._metadata[file_id].update(updates)
            # Update the timestamp
            self._metadata[file_id]["updated_at"] = datetime.now(UTC).isoformat()
            self._save_metadata_atomic()
            logger.info("Updated file entry: %s", file_id)

    def list_files(
        self,
        tag: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[FileMetadata]:
        """List files with optional tag filtering and pagination.

        :param str | None tag: Optional tag to filter by
        :param int offset: Number of results to skip
        :param int limit: Maximum number of results to return
        :return list[FileMetadata]: List of file metadata objects
        """
        with self._lock:
            files = []
            for data in self._metadata.values():
                # Apply tag filter if specified
                if tag is not None:
                    file_tags = data.get("tags", [])
                    if tag not in file_tags:
                        continue

                files.append(FileMetadata.model_validate(data))

            # Sort by uploaded_at descending (newest first)
            files.sort(key=lambda f: f.uploaded_at, reverse=True)

            # Apply pagination
            return files[offset : offset + limit]

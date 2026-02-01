"""Pydantic models for the server."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from python_template_server.models import BaseResponse, TemplateServerConfig


# Cloud Server Configuration Models
class StorageConfig(BaseModel):
    """Configuration model for the cloud storage."""

    capacity_gb: int = Field(default=20, description="Total storage capacity in GB.")
    upload_chunk_size_kb: int = Field(default=8, description="Chunk size for file uploads in KB.")
    max_file_size_mb: int = Field(default=100, description="Maximum file size in MB.")
    max_tags_per_file: int = Field(default=10, description="Maximum number of tags per file.")
    max_tag_length: int = Field(default=50, description="Maximum length of a tag.")


class CloudServerConfig(TemplateServerConfig):
    """Configuration model for the Cloud Server."""

    storage_config: StorageConfig = Field(default_factory=StorageConfig, description="Storage configuration.")


# File Metadata Model
class FileMetadata(BaseModel):
    """Model for file metadata stored in the index."""

    filepath: str = Field(description="Relative file path (e.g., 'animals/cat.png').")
    mime_type: str = Field(description="MIME type of the file.")
    size: int = Field(description="File size in bytes.")
    tags: list[str] = Field(default_factory=list, description="Tags associated with the file.")
    uploaded_at: str = Field(description="Timestamp when the file was uploaded (ISO 8601 format + Z).")
    updated_at: str = Field(description="Timestamp when the file was last updated (ISO 8601 format + Z).")

    @staticmethod
    def current_timestamp() -> str:
        """Get the current timestamp in ISO 8601 format with 'Z' suffix.

        :return str: Current timestamp
        """
        return datetime.now().isoformat() + "Z"

    @classmethod
    def new_current_instance(cls, filepath: str, mime_type: str, size: int, tags: list[str]) -> FileMetadata:
        """Create a new FileMetadata instance with the current timestamp.

        :param filepath: Relative file path
        :param mime_type: MIME type of the file
        :param size: File size in bytes
        :param tags: Tags associated with the file
        :return FileMetadata: New instance with current timestamps
        """
        now_iso = cls.current_timestamp()
        return cls(
            filepath=filepath,
            mime_type=mime_type,
            size=size,
            tags=tags,
            uploaded_at=now_iso,
            updated_at=now_iso,
        )


# API Response Models
class GetFilesResponse(BaseResponse):
    """Response model for list files endpoint."""

    files: list[FileMetadata] = Field(description="List of file metadata.")


class PostFileResponse(BaseResponse):
    """Response model for post file endpoint."""

    filepath: str = Field(description="File path where the file was stored.")
    size: int = Field(description="File size in bytes.")


class PatchFileResponse(BaseResponse):
    """Response model for patch file endpoint."""

    filepath: str = Field(description="New file path if updated.")
    tags: list[str] = Field(description="Updated list of tags for the file.")


class DeleteFileResponse(BaseResponse):
    """Response model for delete file endpoint."""

    filepath: str = Field(description="File path that was deleted.")


# API Request Models
class GetFilesRequest(BaseModel):
    """Request model for listing files."""

    tag: str | None = Field(default=None, description="Optional tag filter.")


class PatchFileRequest(BaseModel):
    """Request model for patching file metadata."""

    new_filepath: str | None = Field(default=None, description="New file path if renaming the file.")
    add_tags: list[str] = Field(default_factory=list, description="Tags to add.")
    remove_tags: list[str] = Field(default_factory=list, description="Tags to remove.")

"""Pydantic models for the server."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from python_template_server.models import BaseResponse, TemplateServerConfig


# Cloud Server Configuration Models
class StorageConfig(BaseModel):
    """Configuration model for the cloud storage."""

    server_directory: str = Field(default="/srv/cloud_server", description="Directory of the cloud server.")
    storage_directory: str = Field(default="files", description="Directory to store files.")
    metadata_filename: str = Field(default="metadata.json", description="Filename for storing metadata.")
    capacity_gb: int = Field(default=20, description="Total storage capacity in GB.")
    upload_chunk_size_kb: int = Field(default=8, description="Chunk size for file uploads in KB.")
    max_file_size_mb: int = Field(default=100, description="Maximum file size in MB.")
    allowed_mime_types: list[str] = Field(default_factory=list, description="Allowed MIME types (empty = all).")
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
    def new_current_instance(cls, **data: dict) -> FileMetadata:
        """Create a new FileMetadata instance with the current timestamp.

        :param data: Fields for the FileMetadata
        :return FileMetadata: New instance with current timestamps
        """
        now_iso = cls.current_timestamp()
        return cls(
            **data,
            uploaded_at=now_iso,
            updated_at=now_iso,
        )


# API Response Models
class GetFilesResponse(BaseResponse):
    """Response model for list files endpoint."""

    files: list[FileMetadata] = Field(description="List of file metadata.")
    total: int = Field(description="Total number of files matching the filter.")


class PostFileResponse(BaseResponse):
    """Response model for post file endpoint."""

    filepath: str = Field(description="File path where the file was stored.")
    size: int = Field(description="File size in bytes.")


class PatchFileResponse(BaseResponse):
    """Response model for patch file endpoint."""

    success: bool = Field(description="Indicates if the tag update was successful.")
    filepath: str = Field(description="New file path if updated.")
    tags: list[str] = Field(description="Updated list of tags for the file.")


class DeleteFileResponse(BaseResponse):
    """Response model for delete file endpoint."""

    success: bool = Field(description="Indicates if the deletion was successful.")
    filepath: str = Field(description="File path that was deleted.")


# API Request Models
class GetFilesRequest(BaseModel):
    """Request model for listing files."""

    tag: str | None = Field(default=None, description="Optional tag filter.")
    offset: int = Field(default=0, ge=0, description="Pagination offset.")
    limit: int = Field(default=100, ge=1, le=1000, description="Pagination limit (max 1000).")


class PatchFileRequest(BaseModel):
    """Request model for patching file metadata."""

    new_filepath: str | None = Field(default=None, description="New file path if renaming the file.")
    add_tags: list[str] = Field(default_factory=list, description="Tags to add.")
    remove_tags: list[str] = Field(default_factory=list, description="Tags to remove.")

"""Pydantic models for the server."""

from datetime import datetime

from pydantic import BaseModel, Field
from python_template_server.models import BaseResponse, TemplateServerConfig


# Cloud Server Configuration Models
class StorageConfig(BaseModel):
    """Configuration model for the cloud storage."""

    server_directory: str = Field(default="/srv/cloud_server", description="Directory of the cloud server.")
    storage_directory: str = Field(default="files", description="Directory to store files.")
    metadata_filename: str = Field(default="metadata.json", description="Filename for storing metadata.")
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

    file_id: str = Field(description="Unique identifier for the file.")
    filename: str = Field(description="Original filename.")
    mime_type: str = Field(description="MIME type of the file.")
    size: int = Field(description="File size in bytes.")
    tags: list[str] = Field(default_factory=list, description="Tags associated with the file.")
    uploaded_at: datetime = Field(description="Timestamp when the file was uploaded.")
    updated_at: datetime = Field(description="Timestamp when the file was last updated.")


# API Response Models
class GetFileResponse(BaseResponse):
    """Response model for get file endpoint."""

    file_bytes: bytes  # TODO: Update as required


class PostFileResponse(BaseResponse):
    """Response model for post file endpoint."""

    file_id: str


class DeleteFileResponse(BaseResponse):
    """Response model for delete file endpoint."""

    success: bool


# API Request Models
class GetFileRequest(BaseModel):
    """Request model for get file endpoint."""

    file_id: str


class PostFileRequest(BaseModel):
    """Request model for post file endpoint."""

    file_bytes: bytes  # TODO: Multipart upload


class DeleteFileRequest(BaseModel):
    """Request model for delete file endpoint."""

    file_id: str

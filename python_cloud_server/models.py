"""Pydantic models for the server."""

from pydantic import BaseModel, Field
from python_template_server.models import BaseResponse, TemplateServerConfig


# Cloud Server Configuration Models
class StorageConfig(BaseModel):
    """Configuration model for the cloud storage."""

    storage_directory: str = Field(default="storage", description="Directory to store files.")


class CloudServerConfig(TemplateServerConfig):
    """Configuration model for the Cloud Server."""

    storage_config: StorageConfig = Field(default_factory=StorageConfig, description="Storage configuration.")


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

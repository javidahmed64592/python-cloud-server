"""Cloud server module."""

import logging
import mimetypes
from pathlib import Path

from fastapi import HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from python_template_server.constants import CONFIG_DIR
from python_template_server.models import ResponseCode
from python_template_server.template_server import TemplateServer

from python_cloud_server.metadata import MetadataManager
from python_cloud_server.models import (
    CloudServerConfig,
    DeleteFileResponse,
    FileMetadata,
    PostFileResponse,
)

logger = logging.getLogger(__name__)


class CloudServer(TemplateServer):
    """FastAPI cloud server."""

    def __init__(self, config: CloudServerConfig | None = None) -> None:
        """Initialize the TemplateServer.

        :param CloudServerConfig | None config: Optional pre-loaded configuration
        """
        self.config: CloudServerConfig
        super().__init__(
            package_name="python_cloud_server",
            config_filepath=CONFIG_DIR / "cloud_server_config.json",
            config=config,
        )
        self.config.save_to_file(self.config_filepath)

        # Initialize storage directories
        self._initialize_storage()

        # Initialize metadata manager
        self.metadata_manager = MetadataManager(self.metadata_filepath)

    @property
    def server_directory(self) -> Path:
        """Get the server directory path."""
        return Path(self.config.storage_config.server_directory)

    @property
    def storage_directory(self) -> Path:
        """Get the storage directory path."""
        return self.server_directory / self.config.storage_config.storage_directory

    @property
    def metadata_filepath(self) -> Path:
        """Get the metadata file path."""
        return self.server_directory / self.config.storage_config.metadata_filename

    def _initialize_storage(self) -> None:
        """Initialize storage directories and verify configuration."""
        # Verify server directory exists (should be mounted volume in Docker)
        if not self.server_directory.exists():
            logger.error("Server directory does not exist: %s", self.server_directory)
            raise SystemExit(1)

        # Create storage directory for files if it doesn't exist
        self.storage_directory.mkdir(parents=True, exist_ok=True)
        logger.info("Storage directory ready: %s", self.storage_directory)

    def validate_config(self, config_data: dict) -> CloudServerConfig:
        """Validate configuration data against the TemplateServerConfig model.

        :param dict config_data: The configuration data to validate
        :return TemplateServerConfig: The validated configuration model
        :raise ValidationError: If the configuration data is invalid
        """
        return CloudServerConfig.model_validate(config_data)  # type: ignore[no-any-return]

    def setup_routes(self) -> None:
        """Set up API routes."""
        super().setup_routes()
        self.add_authenticated_route(
            endpoint="/files/{filepath:path}",
            handler_function=self.get_file,
            response_model=None,
            methods=["GET"],
        )
        self.add_authenticated_route(
            endpoint="/files/{filepath:path}",
            handler_function=self.post_file,
            response_model=PostFileResponse,
            methods=["POST"],
        )
        self.add_authenticated_route(
            endpoint="/files/{filepath:path}",
            handler_function=self.delete_file,
            response_model=DeleteFileResponse,
            methods=["DELETE"],
        )

    async def get_file(self, request: Request, filepath: str) -> FileResponse:
        """Handle get file requests - download a file.

        :param Request request: The request object
        :param str filepath: The file path to retrieve (e.g., 'animals/cat.png')
        :return FileResponse: Server response
        :raise HTTPException: If file not found
        """
        logger.info("Received get file request for: %s", filepath)

        # Get file metadata
        file_metadata = self.metadata_manager.get_file_entry(filepath)
        if not file_metadata:
            msg = f"File not found in metadata: {filepath}"
            logger.error(msg)
            raise HTTPException(status_code=ResponseCode.NOT_FOUND, detail=msg)

        # Construct absolute file path
        if not (full_path := self.storage_directory / filepath).exists():
            msg = f"File not found on disk: {filepath}"
            logger.error(msg)
            raise HTTPException(status_code=ResponseCode.NOT_FOUND, detail=msg)

        return FileResponse(
            path=full_path,
            media_type=file_metadata.mime_type,
            filename=full_path.name,
        )

    async def post_file(self, request: Request, filepath: str, file: UploadFile) -> PostFileResponse:
        """Handle post file requests - upload a file.

        :param Request request: The request object
        :param str filepath: The destination path for the file (e.g., 'animals/cat.png')
        :param UploadFile file: The uploaded file
        :return PostFileResponse: Server response
        """
        # Get MIME type
        mime_type = file.content_type or "application/octet-stream"
        if not mime_type or mime_type == "application/octet-stream":
            # Try to guess from filename
            guessed_type, _ = mimetypes.guess_type(filepath)
            if guessed_type:
                mime_type = guessed_type

        # Construct absolute file path and ensure parent directories exist
        file_path = self.storage_directory / filepath
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file already exists
        if self.metadata_manager._file_exists(filepath):
            return PostFileResponse(
                code=ResponseCode.CONFLICT,
                message=f"File {filepath} already exists",
                timestamp=PostFileResponse.current_timestamp(),
                filepath=filepath,
                size=0,
            )

        file_size = 0

        try:
            with file_path.open("wb") as f:
                while chunk := await file.read(8192):  # Read in 8KB chunks
                    file_size += len(chunk)
                    # Check file size limit
                    if file_size > self.config.storage_config.max_file_size_mb * 1024 * 1024:
                        # Clean up partial file
                        file_path.unlink(missing_ok=True)
                        return PostFileResponse(
                            code=ResponseCode.BAD_REQUEST,
                            message="File size exceeds maximum limit",
                            timestamp=PostFileResponse.current_timestamp(),
                            filepath=filepath,
                            size=file_size,
                        )
                    f.write(chunk)
        except Exception:
            # Clean up on error
            file_path.unlink(missing_ok=True)
            logger.exception("Failed to save file!")
            return PostFileResponse(
                code=ResponseCode.INTERNAL_SERVER_ERROR,
                message="Failed to save file",
                timestamp=PostFileResponse.current_timestamp(),
                filepath=filepath,
                size=file_size,
            )

        # Create metadata entry
        file_metadata = FileMetadata.new_current_instance(
            filepath=filepath,
            mime_type=mime_type,
            size=file_size,
            tags=[],
        )

        try:
            self.metadata_manager.add_file_entry(file_metadata)
        except Exception:
            file_path.unlink(missing_ok=True)
            logger.exception("Failed to save metadata!")
            return PostFileResponse(
                code=ResponseCode.INTERNAL_SERVER_ERROR,
                message="Failed to save metadata",
                timestamp=PostFileResponse.current_timestamp(),
                filepath=filepath,
                size=file_size,
            )

        logger.info("Uploaded file: %s (%d bytes)", filepath, file_size)
        return PostFileResponse(
            code=ResponseCode.OK,
            message="File uploaded successfully",
            timestamp=PostFileResponse.current_timestamp(),
            filepath=filepath,
            size=file_size,
        )

    async def delete_file(self, request: Request, filepath: str) -> DeleteFileResponse:
        """Handle delete file requests.

        :param Request request: The request object
        :param str filepath: The file path to delete (e.g., 'animals/cat.png')
        :return DeleteFileResponse: Server response
        """
        # Check if file exists in metadata
        if not self.metadata_manager._file_exists(filepath):
            return DeleteFileResponse(
                code=ResponseCode.NOT_FOUND,
                message="File not found",
                timestamp=DeleteFileResponse.current_timestamp(),
                success=False,
                filepath=filepath,
            )

        # Delete physical file
        file_path = self.storage_directory / filepath
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info("Deleted file from disk: %s", filepath)
            else:
                logger.warning("File not found on disk but exists in metadata: %s", filepath)
        except Exception:
            logger.exception("Failed to delete file from disk: %s", filepath)
            return DeleteFileResponse(
                code=ResponseCode.INTERNAL_SERVER_ERROR,
                message="Failed to delete file from disk",
                timestamp=DeleteFileResponse.current_timestamp(),
                success=False,
                filepath=filepath,
            )

        # Delete metadata entry
        try:
            self.metadata_manager.delete_file_entry(filepath)
            logger.info("Deleted metadata for file: %s", filepath)
        except Exception:
            logger.exception("Failed to delete metadata!")
            return DeleteFileResponse(
                code=ResponseCode.INTERNAL_SERVER_ERROR,
                message="Failed to delete metadata",
                timestamp=DeleteFileResponse.current_timestamp(),
                success=False,
                filepath=filepath,
            )

        return DeleteFileResponse(
            code=ResponseCode.OK,
            message="File deleted successfully",
            timestamp=DeleteFileResponse.current_timestamp(),
            success=True,
            filepath=filepath,
        )

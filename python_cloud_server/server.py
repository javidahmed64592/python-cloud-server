"""Cloud server module."""

import logging
import mimetypes
from pathlib import Path

from fastapi import HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from python_template_server.constants import BYTES_TO_MB, CONFIG_DIR
from python_template_server.models import ResponseCode
from python_template_server.template_server import TemplateServer

from python_cloud_server.metadata import MetadataManager
from python_cloud_server.models import (
    CloudServerConfig,
    DeleteFileResponse,
    FileMetadata,
    GetFilesRequest,
    GetFilesResponse,
    PatchFileRequest,
    PatchFileResponse,
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
            endpoint="/files",
            handler_function=self.get_files,
            response_model=GetFilesResponse,
            methods=["GET"],
        )
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
            handler_function=self.patch_file,
            response_model=PatchFileResponse,
            methods=["PATCH"],
        )
        self.add_authenticated_route(
            endpoint="/files/{filepath:path}",
            handler_function=self.delete_file,
            response_model=DeleteFileResponse,
            methods=["DELETE"],
        )

    async def get_files(
        self,
        request: Request,
    ) -> GetFilesResponse:
        """Handle list files requests.

        :param Request request: The request object
        :return GetFilesResponse: Server response with file list
        """
        files_request = GetFilesRequest.model_validate(await request.json())
        logger.info(
            "Received list files request: tag=%s, offset=%d, limit=%d",
            files_request.tag,
            files_request.offset,
            files_request.limit,
        )

        # Get filtered and paginated file list
        files = self.metadata_manager.list_files(
            tag=files_request.tag, offset=files_request.offset, limit=files_request.limit
        )

        # Get total count
        if files_request.tag:
            total = sum(1 for entry in self.metadata_manager._metadata.values() if files_request.tag in entry.tags)
        else:
            total = self.metadata_manager.file_count

        logger.info("Returning %d files (total: %d)", len(files), total)
        return GetFilesResponse(
            code=ResponseCode.OK,
            message="Files retrieved successfully",
            timestamp=GetFilesResponse.current_timestamp(),
            files=files,
            total=total,
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
        logger.info("Received post file request for: %s", filepath)

        # Check if file already exists
        if self.metadata_manager._file_exists(filepath):
            msg = f"File already exists: {filepath}"
            logger.error(msg)
            return PostFileResponse(
                code=ResponseCode.CONFLICT,
                message=msg,
                timestamp=PostFileResponse.current_timestamp(),
                filepath=filepath,
                size=0,
            )

        # Get MIME type
        mime_type = file.content_type or "application/octet-stream"
        if mime_type == "application/octet-stream":
            guessed_type, _ = mimetypes.guess_type(filepath)
            if guessed_type:
                mime_type = guessed_type

        # Construct absolute file path and ensure parent directories exist
        full_path = self.storage_directory / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        file_size = 0

        try:
            with full_path.open("wb") as f:
                while chunk := await file.read(self.config.storage_config.upload_chunk_size_kb * 1024):
                    file_size += len(chunk)
                    if file_size > self.config.storage_config.max_file_size_mb * BYTES_TO_MB:
                        full_path.unlink(missing_ok=True)
                        msg = f"File size exceeds maximum limit: {filepath} ({file_size} bytes)"
                        logger.error(msg)
                        return PostFileResponse(
                            code=ResponseCode.BAD_REQUEST,
                            message=msg,
                            timestamp=PostFileResponse.current_timestamp(),
                            filepath=filepath,
                            size=file_size,
                        )
                    f.write(chunk)
        except Exception:
            full_path.unlink(missing_ok=True)
            msg = f"Failed to save file: {filepath}"
            logger.exception(msg)
            return PostFileResponse(
                code=ResponseCode.INTERNAL_SERVER_ERROR,
                message=msg,
                timestamp=PostFileResponse.current_timestamp(),
                filepath=filepath,
                size=file_size,
            )

        try:
            # Create metadata entry
            file_metadata = FileMetadata.new_current_instance(
                filepath=filepath,
                mime_type=mime_type,
                size=file_size,
                tags=[],
            )
            self.metadata_manager.add_file_entry(file_metadata)
        except Exception:
            full_path.unlink(missing_ok=True)
            msg = f"Failed to save metadata for file: {filepath}"
            logger.exception(msg)
            return PostFileResponse(
                code=ResponseCode.INTERNAL_SERVER_ERROR,
                message=msg,
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

    async def patch_file(self, request: Request, filepath: str) -> PatchFileResponse:
        """Handle patch file requests - update file metadata and/or move file.

        :param Request request: The request object
        :param str filepath: The file path to update (e.g., 'animals/cat.png')
        :return PatchFileResponse: Server response
        """
        patch_request = PatchFileRequest.model_validate(await request.json())
        logger.info("Received patch file request for: %s", filepath)

        # Check if file exists
        if not self.metadata_manager._file_exists(filepath) or not (
            current_metadata := self.metadata_manager.get_file_entry(filepath)
        ):
            msg = f"File not found in metadata: {filepath}"
            logger.error(msg)
            return PatchFileResponse(
                code=ResponseCode.NOT_FOUND,
                message=msg,
                timestamp=PatchFileResponse.current_timestamp(),
                success=False,
                filepath=filepath,
                tags=[],
            )

        # Calculate new tags
        current_tags = set(current_metadata.tags)
        new_tags = current_tags.copy()

        # Add tags
        for tag in patch_request.add_tags:
            # Validate tag
            if len(tag) > self.config.storage_config.max_tag_length:
                msg = f"Skipping tag which exceeds maximum length: {tag}"
                logger.warning(msg)
                continue
            new_tags.add(tag)

        # Remove tags
        for tag in patch_request.remove_tags:
            new_tags.discard(tag)

        # Check max tags limit
        if len(new_tags) > self.config.storage_config.max_tags_per_file:
            msg = f"Number of tags exceeds maximum: {len(new_tags)} > {self.config.storage_config.max_tags_per_file}"
            logger.error(msg)
            return PatchFileResponse(
                code=ResponseCode.BAD_REQUEST,
                message=msg,
                timestamp=PatchFileResponse.current_timestamp(),
                success=False,
                filepath=filepath,
                tags=list(current_tags),
            )

        # Handle file moving/renaming if new_filepath is specified
        final_filepath = filepath
        if patch_request.new_filepath:
            new_filepath = patch_request.new_filepath

            # Check if destination already exists
            if self.metadata_manager._file_exists(new_filepath):
                msg = f"Destination file already exists: {new_filepath}"
                logger.error(msg)
                return PatchFileResponse(
                    code=ResponseCode.CONFLICT,
                    message=msg,
                    timestamp=PatchFileResponse.current_timestamp(),
                    success=False,
                    filepath=filepath,
                    tags=list(current_tags),
                )

            # Move the physical file
            old_path = self.storage_directory / filepath
            new_path = self.storage_directory / new_filepath

            try:
                # Create parent directories for new path
                new_path.parent.mkdir(parents=True, exist_ok=True)

                # Move the file
                old_path.rename(new_path)
                logger.info("Moved file from %s to %s", filepath, new_filepath)

                final_filepath = new_filepath

            except Exception:
                msg = f"Failed to move file from {filepath} to {new_filepath}"
                logger.exception(msg)
                return PatchFileResponse(
                    code=ResponseCode.INTERNAL_SERVER_ERROR,
                    message=msg,
                    timestamp=PatchFileResponse.current_timestamp(),
                    success=False,
                    filepath=filepath,
                    tags=list(current_tags),
                )

        # Update metadata once at the end with all changes
        try:
            # Prepare updates dictionary
            updates: dict = {"tags": list(new_tags)}

            # Include filepath change if it occurred
            if final_filepath != filepath:
                updates["filepath"] = final_filepath

            self.metadata_manager.update_file_entry(filepath=filepath, updates=updates)

        except Exception:
            # If metadata update fails and we moved the file, try to move it back
            if final_filepath != filepath:
                try:
                    new_path.rename(old_path)
                    logger.warning("Rolled back file move due to metadata update failure")
                except Exception:
                    logger.exception("Failed to rollback file move")

            msg = f"Failed to update metadata for file: {filepath}"
            logger.exception(msg)
            return PatchFileResponse(
                code=ResponseCode.INTERNAL_SERVER_ERROR,
                message=msg,
                timestamp=PatchFileResponse.current_timestamp(),
                success=False,
                filepath=filepath,
                tags=list(current_tags),
            )

        logger.info("Updated file: %s (tags: %s)", final_filepath, list(new_tags))
        return PatchFileResponse(
            code=ResponseCode.OK,
            message="File updated successfully",
            timestamp=PatchFileResponse.current_timestamp(),
            success=True,
            filepath=final_filepath,
            tags=list(new_tags),
        )

    async def delete_file(self, request: Request, filepath: str) -> DeleteFileResponse:
        """Handle delete file requests.

        :param Request request: The request object
        :param str filepath: The file path to delete (e.g., 'animals/cat.png')
        :return DeleteFileResponse: Server response
        """
        logger.info("Received delete file request for: %s", filepath)

        # Check if file exists in metadata
        if not self.metadata_manager._file_exists(filepath):
            msg = f"File not found in metadata: {filepath}"
            logger.error(msg)
            return DeleteFileResponse(
                code=ResponseCode.NOT_FOUND,
                message=msg,
                timestamp=DeleteFileResponse.current_timestamp(),
                success=False,
                filepath=filepath,
            )

        # Construct absolute file path and delete physical file
        full_path = self.storage_directory / filepath

        try:
            if full_path.exists():
                full_path.unlink()
                logger.info("Deleted file from disk: %s", filepath)
            else:
                logger.warning("File not found on disk but exists in metadata: %s", filepath)
        except Exception:
            msg = f"Failed to delete file from disk: {filepath}"
            logger.exception(msg)
            return DeleteFileResponse(
                code=ResponseCode.INTERNAL_SERVER_ERROR,
                message=msg,
                timestamp=DeleteFileResponse.current_timestamp(),
                success=False,
                filepath=filepath,
            )

        # Delete metadata entry
        try:
            self.metadata_manager.delete_file_entry(filepath)
        except Exception:
            msg = f"Failed to delete metadata for file: {filepath}"
            logger.exception(msg)
            return DeleteFileResponse(
                code=ResponseCode.INTERNAL_SERVER_ERROR,
                message=msg,
                timestamp=DeleteFileResponse.current_timestamp(),
                success=False,
                filepath=filepath,
            )

        logger.info("Deleted file: %s", filepath)
        return DeleteFileResponse(
            code=ResponseCode.OK,
            message="File deleted successfully",
            timestamp=DeleteFileResponse.current_timestamp(),
            success=True,
            filepath=filepath,
        )

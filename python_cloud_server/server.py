"""Cloud server module."""

import logging
import mimetypes
from pathlib import Path

from fastapi import HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from python_template_server.constants import BYTES_TO_MB, ROOT_DIR
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
        super().__init__(package_name="python_cloud_server", config=config)

        self._initialize_storage()
        self._initialize_metadata()

    @property
    def server_directory(self) -> Path:
        """Get the server directory path."""
        return Path(ROOT_DIR) / "server"

    @property
    def storage_directory(self) -> Path:
        """Get the storage directory path."""
        return self.server_directory / "storage"

    @property
    def metadata_filepath(self) -> Path:
        """Get the metadata file path."""
        return self.server_directory / "metadata.json"

    def _initialize_storage(self) -> None:
        """Initialize storage directories and verify configuration."""
        if not self.server_directory.exists():
            logger.error("Server directory does not exist: %s", self.server_directory)
            raise SystemExit(1)

        self.storage_directory.mkdir(parents=True, exist_ok=True)
        logger.info("Storage directory ready: %s", self.storage_directory)

    def _initialize_metadata(self) -> None:
        """Initialize metadata manager."""
        self.metadata_manager = MetadataManager(self.metadata_filepath)
        with self.metadata_manager._lock:
            # Add existing files on disk to metadata if missing
            filepaths_to_add: list[FileMetadata] = []
            for file_path in self.storage_directory.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.storage_directory).as_posix()
                    if not self.metadata_manager.file_exists(relative_path):
                        size = file_path.stat().st_size
                        mime_type, _ = mimetypes.guess_type(str(file_path))
                        if mime_type is None:
                            mime_type = "application/octet-stream"
                        file_metadata = FileMetadata.new_current_instance(
                            filepath=relative_path,
                            mime_type=mime_type,
                            size=size,
                            tags=[],
                        )
                        filepaths_to_add.append(file_metadata)

            if filepaths_to_add:
                logger.info("Syncing %d files from storage", len(filepaths_to_add))
                self.metadata_manager.add_file_entries(filepaths_to_add)

            # Remove metadata entries for files that no longer exist on disk
            filepaths_to_remove: list[str] = []
            for filepath in list(self.metadata_manager._metadata.keys()):
                full_path = self.storage_directory / filepath
                if not full_path.exists():
                    filepaths_to_remove.append(filepath)

            if filepaths_to_remove:
                logger.info("Removing %d stale metadata entries", len(filepaths_to_remove))
                self.metadata_manager.delete_file_entries(filepaths_to_remove)

        logger.info("Metadata manager initialized with %d files", self.metadata_manager.file_count)

    def validate_config(self, config_data: dict) -> CloudServerConfig:
        """Validate configuration data against the TemplateServerConfig model.

        :param dict config_data: The configuration data to validate
        :return TemplateServerConfig: The validated configuration model
        :raise ValidationError: If the configuration data is invalid
        """
        return CloudServerConfig.model_validate(config_data)  # type: ignore[no-any-return]

    def setup_routes(self) -> None:
        """Set up API routes."""
        self.add_authenticated_route(
            endpoint="/files",
            handler_function=self.get_files,
            response_model=GetFilesResponse,
            methods=["GET"],
            limited=True,
        )
        self.add_authenticated_route(
            endpoint="/files/{filepath:path}",
            handler_function=self.get_file,
            response_model=None,
            methods=["GET"],
            limited=True,
        )
        self.add_authenticated_route(
            endpoint="/files/{filepath:path}",
            handler_function=self.post_file,
            response_model=PostFileResponse,
            methods=["POST"],
            limited=True,
        )
        self.add_authenticated_route(
            endpoint="/files/{filepath:path}",
            handler_function=self.patch_file,
            response_model=PatchFileResponse,
            methods=["PATCH"],
            limited=True,
        )
        self.add_authenticated_route(
            endpoint="/files/{filepath:path}",
            handler_function=self.delete_file,
            response_model=DeleteFileResponse,
            methods=["DELETE"],
            limited=True,
        )

    async def get_files(self, request: Request) -> GetFilesResponse:
        """Handle list files requests.

        :param Request request: The request object
        :return GetFilesResponse: Server response with file list
        """
        files_request = GetFilesRequest.model_validate(await request.json())
        logger.info("Received list files request for tag: %s", files_request.tag)

        files = self.metadata_manager.list_files(
            tag=files_request.tag, offset=files_request.offset, limit=files_request.limit
        )

        msg = f"Retrieved {len(files)} files successfully."
        logger.info(msg)
        return GetFilesResponse(
            message=msg,
            timestamp=GetFilesResponse.current_timestamp(),
            files=files,
        )

    async def get_file(self, request: Request, filepath: str) -> FileResponse:
        """Handle get file requests - download a file.

        :param Request request: The request object
        :param str filepath: The file path to retrieve (e.g., 'animals/cat.png')
        :return FileResponse: Server response
        :raise HTTPException: If file not found
        """
        logger.info("Received get file request for: %s", filepath)

        if not self.metadata_manager.file_exists(filepath):
            msg = f"File not found in metadata: {filepath}"
            logger.error(msg)
            raise HTTPException(status_code=ResponseCode.NOT_FOUND, detail=msg)

        if not (full_path := self.storage_directory / filepath).exists():
            msg = f"File not found on disk: {filepath}"
            logger.error(msg)
            raise HTTPException(status_code=ResponseCode.NOT_FOUND, detail=msg)

        file_metadata = self.metadata_manager.get_file_entry(filepath)

        return FileResponse(
            path=full_path,
            media_type=file_metadata.mime_type,
            filename=full_path.name,
        )

    def _check_file_too_large(self, full_path: Path, file_size: int) -> None:
        """Handle file too large scenario by deleting the file and logging.

        :param Path full_path: The full file path
        :param int file_size: The size of the file in bytes
        """
        if file_size > self.config.storage_config.max_file_size_mb * BYTES_TO_MB:
            full_path.unlink(missing_ok=True)
            msg = f"File size exceeds maximum limit: {full_path} ({file_size} bytes)"
            logger.error(msg)
            raise ValueError(msg)

    async def post_file(self, request: Request, filepath: str, file: UploadFile) -> PostFileResponse:
        """Handle post file requests - upload a file.

        :param Request request: The request object
        :param str filepath: The destination path for the file (e.g., 'animals/cat.png')
        :param UploadFile file: The uploaded file
        :return PostFileResponse: Server response
        """
        logger.info("Received post file request for: %s", filepath)

        if self.metadata_manager.file_exists(filepath):
            msg = f"File already exists: {filepath}"
            logger.error(msg)
            raise HTTPException(status_code=ResponseCode.CONFLICT, detail=msg)

        mime_type = file.content_type or "application/octet-stream"
        if mime_type == "application/octet-stream":
            guessed_type, _ = mimetypes.guess_type(filepath)
            mime_type = guessed_type or mime_type

        full_path = self.storage_directory / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        file_size = 0

        try:
            with full_path.open("wb") as f:
                while chunk := await file.read(self.config.storage_config.upload_chunk_size_kb * 1024):
                    file_size += len(chunk)
                    self._check_file_too_large(full_path, file_size)
                    f.write(chunk)
        except Exception as e:
            full_path.unlink(missing_ok=True)
            msg = f"Failed to save file: {filepath}"
            logger.exception(msg)
            raise HTTPException(status_code=ResponseCode.INTERNAL_SERVER_ERROR, detail=msg) from e

        try:
            file_metadata = FileMetadata.new_current_instance(
                filepath=filepath,
                mime_type=mime_type,
                size=file_size,
                tags=[],
            )
            self.metadata_manager.add_file_entries([file_metadata])
        except Exception as e:
            full_path.unlink(missing_ok=True)
            msg = f"Failed to save metadata for file: {filepath}"
            logger.exception(msg)
            raise HTTPException(status_code=ResponseCode.INTERNAL_SERVER_ERROR, detail=msg) from e

        msg = f"File uploaded successfully: {filepath} ({file_size} bytes)"
        logger.info(msg)
        return PostFileResponse(
            message=msg,
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

        if not self.metadata_manager.file_exists(filepath):
            msg = f"File not found in metadata: {filepath}"
            logger.error(msg)
            raise HTTPException(status_code=ResponseCode.NOT_FOUND, detail=msg)

        # Calculate new tags
        current_metadata = self.metadata_manager.get_file_entry(filepath)
        new_tags = set(current_metadata.tags).copy()

        for tag in patch_request.add_tags:
            if len(tag) > self.config.storage_config.max_tag_length:
                msg = f"Skipping tag which exceeds maximum length: {tag}"
                logger.warning(msg)
                continue
            new_tags.add(tag)

        for tag in patch_request.remove_tags:
            new_tags.discard(tag)

        if len(new_tags) > self.config.storage_config.max_tags_per_file:
            msg = f"Number of tags exceeds maximum: {len(new_tags)} > {self.config.storage_config.max_tags_per_file}"
            logger.error(msg)
            raise HTTPException(status_code=ResponseCode.BAD_REQUEST, detail=msg)

        # Handle file moving/renaming if new_filepath is specified
        final_filepath = filepath
        if patch_request.new_filepath:
            new_filepath = patch_request.new_filepath

            if self.metadata_manager.file_exists(new_filepath):
                msg = f"Destination file already exists: {new_filepath}"
                logger.error(msg)
                raise HTTPException(status_code=ResponseCode.CONFLICT, detail=msg)

            old_path = self.storage_directory / filepath
            new_path = self.storage_directory / new_filepath

            try:
                new_path.parent.mkdir(parents=True, exist_ok=True)

                old_path.rename(new_path)
                logger.info("Moved file from %s to %s", filepath, new_filepath)

                final_filepath = new_filepath

            except Exception as e:
                msg = f"Failed to move file from {filepath} to {new_filepath}"
                logger.exception(msg)
                raise HTTPException(status_code=ResponseCode.INTERNAL_SERVER_ERROR, detail=msg) from e

        try:
            updates: dict = {"tags": list(new_tags)}

            if final_filepath != filepath:
                updates["filepath"] = final_filepath

            self.metadata_manager.update_file_entry(filepath=filepath, updates=updates)

        except Exception as e:
            if final_filepath != filepath:
                new_path.rename(old_path)

            msg = f"Failed to update metadata for file: {filepath}"
            logger.exception(msg)
            raise HTTPException(status_code=ResponseCode.INTERNAL_SERVER_ERROR, detail=msg) from e

        msg = f"File updated successfully: {final_filepath}"
        logger.info(msg)
        return PatchFileResponse(
            message=msg,
            timestamp=PatchFileResponse.current_timestamp(),
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

        if not self.metadata_manager.file_exists(filepath):
            msg = f"File not found in metadata: {filepath}"
            logger.error(msg)
            raise HTTPException(status_code=ResponseCode.NOT_FOUND, detail=msg)

        full_path = self.storage_directory / filepath

        try:
            if full_path.exists():
                full_path.unlink()
                logger.info("Deleted file from disk: %s", filepath)
        except Exception as e:
            msg = f"Failed to delete file from disk: {filepath}"
            logger.exception(msg)
            raise HTTPException(status_code=ResponseCode.INTERNAL_SERVER_ERROR, detail=msg) from e

        try:
            self.metadata_manager.delete_file_entries([filepath])
        except Exception as e:
            msg = f"Failed to delete metadata for file: {filepath}"
            logger.exception(msg)
            raise HTTPException(status_code=ResponseCode.INTERNAL_SERVER_ERROR, detail=msg) from e

        msg = f"File deleted successfully: {filepath}"
        logger.info(msg)
        return DeleteFileResponse(
            message=msg,
            timestamp=DeleteFileResponse.current_timestamp(),
            filepath=filepath,
        )

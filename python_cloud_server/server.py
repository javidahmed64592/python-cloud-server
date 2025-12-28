"""Cloud server module."""

import logging
import uuid
from pathlib import Path

from fastapi import Request
from python_template_server.constants import CONFIG_DIR
from python_template_server.template_server import TemplateServer

from python_cloud_server.models import (
    CloudServerConfig,
    DeleteFileRequest,
    DeleteFileResponse,
    GetFileRequest,
    GetFileResponse,
    PostFileRequest,
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
            endpoint="/get_file",
            handler_function=self.get_file,
            response_model=GetFileResponse,
            methods=["GET"],
        )
        self.add_authenticated_route(
            endpoint="/post_file",
            handler_function=self.post_file,
            response_model=PostFileResponse,
            methods=["POST"],
        )
        self.add_authenticated_route(
            endpoint="/delete_file",
            handler_function=self.delete_file,
            response_model=DeleteFileResponse,
            methods=["DELETE"],
        )

    async def get_file(self, request: Request) -> GetFileResponse:
        """Handle get file requests.

        :param Request request: The incoming request
        :return GetFileResponse: The response model
        """
        get_file_request = GetFileRequest.model_validate(await request.json())
        # TODO: Implement file retrieval logic
        return GetFileResponse.model_validate({})

    async def post_file(self, request: Request) -> PostFileResponse:
        """Handle post file requests.

        :param Request request: The incoming request
        :return PostFileResponse: The response model
        """
        post_file_request = PostFileRequest.model_validate(await request.json())
        # TODO: Implement file storage logic
        return PostFileResponse.model_validate({})

    async def delete_file(self, request: Request) -> DeleteFileResponse:
        """Handle delete file requests.

        :param Request request: The incoming request
        :return DeleteFileResponse: The response model
        """
        delete_file_request = DeleteFileRequest.model_validate(await request.json())
        # TODO: Implement file deletion logic
        return DeleteFileResponse.model_validate({})

"""FastAPI cloud storage server using uvicorn."""

import logging
import sys
from collections.abc import Callable
from importlib.metadata import metadata

import uvicorn
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from python_cloud_server.authentication_handler import verify_token
from python_cloud_server.config import load_config
from python_cloud_server.constants import API_KEY_HEADER_NAME, API_PREFIX, PACKAGE_NAME
from python_cloud_server.models import GetHealthResponse, ResponseCode

logger = logging.getLogger(__name__)


class CloudServer:
    """Cloud storage server application."""

    def __init__(self) -> None:
        """Initialize the CloudServer."""
        package_metadata = metadata(PACKAGE_NAME)
        self.app = FastAPI(
            title=package_metadata["Name"],
            description=package_metadata["Summary"],
            version=package_metadata["Version"],
            root_path=API_PREFIX,
        )
        self.api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
        self._setup_routes()

    def _add_authenticated_route(self, endpoint: str, handler_function: Callable, response_model: BaseModel) -> None:
        """Add an authenticated API route.

        :param str endpoint: The API endpoint path
        :param Callable handler_function: The handler function for the endpoint
        :param BaseModel response_model: The Pydantic model for the response
        """
        self.app.add_api_route(
            endpoint,
            handler_function,
            methods=["GET"],
            response_model=response_model,
            dependencies=[Security(self._verify_api_key)],
        )

    def _setup_routes(self) -> None:
        """Set up API routes."""
        self._add_authenticated_route("/health", self.get_health, GetHealthResponse)

    async def _verify_api_key(
        self, api_key: str | None = Security(APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False))
    ) -> None:
        """Verify the API key from the request header.

        :param str | None api_key: The API key from the X-API-Key header
        :raise HTTPException: If the API key is missing or invalid
        """
        if api_key is None:
            logger.warning("Missing API key in request!")
            raise HTTPException(
                status_code=ResponseCode.UNAUTHORIZED,
                detail="Missing API key",
            )

        try:
            if not verify_token(api_key):
                logger.warning("Unauthorized login attempt with key: %s", api_key)
                raise HTTPException(
                    status_code=ResponseCode.UNAUTHORIZED,
                    detail="Invalid API key",
                )
        except ValueError as e:
            logger.exception("Error verifying API key!")
            raise HTTPException(
                status_code=ResponseCode.UNAUTHORIZED,
                detail=str(e),
            ) from e

    async def get_health(self) -> GetHealthResponse:
        """Get server health."""
        return GetHealthResponse(code=ResponseCode.OK, message="Server is healthy")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    :return FastAPI: The configured FastAPI application instance
    """
    server = CloudServer()
    return server.app


def run() -> None:
    """Serve the FastAPI application using uvicorn.

    :raise SystemExit: If configuration fails to load or SSL certificate files are missing
    """
    config = load_config()

    if not (
        (cert_file := config.certificate.ssl_cert_file_path).exists()
        and (key_file := config.certificate.ssl_key_file_path).exists()
    ):
        logger.error("SSL certificate files not found: '%s' or '%s'", cert_file, key_file)
        sys.exit(1)

    try:
        logger.info("Starting server: %s", config.server.full_url)
        uvicorn.run(
            "python_cloud_server.main:create_app",
            host=config.server.host,
            port=config.server.port,
            ssl_keyfile=key_file,
            ssl_certfile=cert_file,
            factory=True,
            reload=True,
        )
        logger.info("Server stopped.")
    except OSError:
        logger.exception("Failed to start server!")
        sys.exit(1)

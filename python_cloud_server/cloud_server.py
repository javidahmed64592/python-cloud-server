"""Cloud server application module."""

import logging
from collections.abc import Callable
from importlib.metadata import metadata

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from python_cloud_server.authentication_handler import verify_token
from python_cloud_server.constants import API_KEY_HEADER_NAME, API_PREFIX, PACKAGE_NAME
from python_cloud_server.models import AppConfigModel, GetHealthResponse, ResponseCode


class CloudServer:
    """Cloud storage server application."""

    def __init__(self, config: AppConfigModel) -> None:
        """Initialize the CloudServer.

        :param AppConfigModel config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        package_metadata = metadata(PACKAGE_NAME)
        self.app = FastAPI(
            title=package_metadata["Name"],
            description=package_metadata["Summary"],
            version=package_metadata["Version"],
            root_path=API_PREFIX,
        )
        self.api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)

        self._setup_rate_limiting()
        self._setup_routes()

    def _setup_rate_limiting(self) -> None:
        """Set up rate limiting middleware."""
        if not self.config.rate_limit.enabled:
            self.logger.info("Rate limiting is disabled")
            self.limiter = None
            return

        self.limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=self.config.rate_limit.storage_uri,
        )

        self.app.state.limiter = self.limiter
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        self.logger.info(
            "Rate limiting enabled: rate=%s, storage=%s",
            self.config.rate_limit.rate_limit,
            self.config.rate_limit.storage_uri or "in-memory",
        )

    def _limit_route(self, route_function: Callable) -> Callable:
        """Apply rate limiting to a route function if enabled.

        :param Callable route_function: The route handler function
        :return Callable: The potentially rate-limited route handler
        """
        if self.limiter is not None:
            return self.limiter.limit(self.config.rate_limit.rate_limit)(route_function)
        return route_function

    def _add_authenticated_route(
        self, endpoint: str, handler_function: Callable, response_model: type[BaseModel]
    ) -> None:
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
        self._add_authenticated_route("/health", self._limit_route(self.get_health), GetHealthResponse)

    async def _verify_api_key(
        self, api_key: str | None = Security(APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False))
    ) -> None:
        """Verify the API key from the request header.

        :param str | None api_key: The API key from the X-API-Key header
        :raise HTTPException: If the API key is missing or invalid
        """
        if api_key is None:
            self.logger.warning("Missing API key in request!")
            raise HTTPException(
                status_code=ResponseCode.UNAUTHORIZED,
                detail="Missing API key",
            )

        try:
            if not verify_token(api_key):
                self.logger.warning("Unauthorized login attempt with key: %s", api_key)
                raise HTTPException(
                    status_code=ResponseCode.UNAUTHORIZED,
                    detail="Invalid API key",
                )
        except ValueError as e:
            self.logger.exception("Error verifying API key!")
            raise HTTPException(
                status_code=ResponseCode.UNAUTHORIZED,
                detail=str(e),
            ) from e

    async def get_health(self, request: Request) -> GetHealthResponse:
        """Get server health.

        :param Request request: The incoming HTTP request
        :return GetHealthResponse: Health status response
        """
        return GetHealthResponse(
            code=ResponseCode.OK,
            message="Server is healthy",
            timestamp=GetHealthResponse.current_timestamp(),
        )

    def run(self) -> None:
        """Run the server using uvicorn.

        :raise FileNotFoundError: If SSL certificate files are missing
        """
        cert_file = self.config.certificate.ssl_cert_file_path
        key_file = self.config.certificate.ssl_key_file_path

        if not (cert_file.exists() and key_file.exists()):
            msg = "SSL certificate files are missing"
            self.logger.error("%s. Expected: '%s' and '%s'", msg, cert_file, key_file)
            raise FileNotFoundError(msg)

        self.logger.info("Starting server: %s", self.config.server.full_url)
        uvicorn.run(
            self.app,
            host=self.config.server.host,
            port=self.config.server.port,
            ssl_keyfile=str(key_file),
            ssl_certfile=str(cert_file),
        )
        self.logger.info("Server stopped.")

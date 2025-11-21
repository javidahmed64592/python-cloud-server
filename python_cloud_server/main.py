"""FastAPI cloud storage server using uvicorn."""

import sys
from importlib.metadata import metadata

import uvicorn
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader

from python_cloud_server.authentication_handler import verify_token
from python_cloud_server.config import load_config
from python_cloud_server.models import GetHealthResponse, ResponseCode

PACKAGE_NAME = "python-cloud-server"
API_KEY_HEADER_NAME = "X-API-Key"

package_metadata = metadata(PACKAGE_NAME)
app = FastAPI(
    title=package_metadata["Name"],
    description=package_metadata["Summary"],
    version=package_metadata["Version"],
)
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> None:
    """Verify the API key from the request header.

    :param str | None api_key: The API key from the X-API-Key header
    :raise HTTPException: If the API key is missing or invalid
    """
    if api_key is None:
        raise HTTPException(
            status_code=ResponseCode.UNAUTHORIZED,
            detail="Missing API key",
        )

    try:
        if not verify_token(api_key):
            raise HTTPException(
                status_code=ResponseCode.UNAUTHORIZED,
                detail="Invalid API key",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=ResponseCode.UNAUTHORIZED,
            detail=str(e),
        ) from e


@app.get("/health", response_model=GetHealthResponse)
async def get_health(_: None = Security(verify_api_key)) -> GetHealthResponse:
    """Get server health."""
    return GetHealthResponse(code=ResponseCode.OK, message="Server is healthy")


def run() -> None:
    """Serve the FastAPI application using uvicorn.

    :raise SystemExit: If configuration fails to load or SSL certificates are missing
    """
    config = load_config()

    # Validate SSL certificate files exist
    if not (
        (cert_file := config.certificate.ssl_cert_file_path).exists()
        and (key_file := config.certificate.ssl_key_file_path).exists()
    ):
        print(f"ERROR: SSL certificates not found: {cert_file}", file=sys.stderr)
        sys.exit(1)

    try:
        uvicorn.run(
            "python_cloud_server.main:app",
            host=config.server.host,
            port=config.server.port,
            ssl_keyfile=key_file,
            ssl_certfile=cert_file,
            reload=True,
        )
    except OSError as e:
        print(f"ERROR: Failed to start server: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)

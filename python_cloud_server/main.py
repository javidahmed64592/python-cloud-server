"""FastAPI cloud storage server."""

from importlib.metadata import metadata

import uvicorn
from fastapi import FastAPI

from python_cloud_server.config import load_config
from python_cloud_server.models import GetHealthResponse, ResponseCode

PACKAGE_NAME = "python-cloud-server"
package_metadata = metadata(PACKAGE_NAME)

app = FastAPI(
    title=package_metadata["Name"],
    description=package_metadata["Summary"],
    version=package_metadata["Version"],
)


@app.get("/health", response_model=GetHealthResponse)
async def get_health() -> GetHealthResponse:
    """Get server health."""
    return GetHealthResponse(code=ResponseCode.OK, message="Server is healthy")


def run() -> None:
    """Serve the FastAPI application using uvicorn."""
    config = load_config()
    uvicorn.run(
        "python_cloud_server.main:app",
        host=config.server.host,
        port=config.server.port,
        ssl_keyfile=config.certificate.ssl_keyfile,
        ssl_certfile=config.certificate.ssl_certfile,
        reload=True,
    )

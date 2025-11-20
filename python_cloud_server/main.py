"""FastAPI cloud storage server."""

from importlib.metadata import metadata

import uvicorn
from fastapi import FastAPI

from python_cloud_server.config import load_config

PACKAGE_NAME = "python-cloud-server"
package_metadata = metadata(PACKAGE_NAME)

app = FastAPI(
    title=package_metadata["Name"],
    description=package_metadata["Summary"],
    version=package_metadata["Version"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify the server is running."""
    return {"status": "healthy", "message": "Server is running"}


def run() -> None:
    """Run the FastAPI server."""
    config = load_config()
    uvicorn.run(
        "python_cloud_server.main:app",
        host=config.server.host,
        port=config.server.port,
        ssl_keyfile=config.certificate.ssl_keyfile,
        ssl_certfile=config.certificate.ssl_certfile,
        reload=True,
    )

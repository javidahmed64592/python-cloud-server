"""FastAPI cloud storage server."""

import uvicorn
from fastapi import FastAPI

from python_cloud_server.config import load_config

app = FastAPI(
    title="Cloud Storage Server",
    description="A FastAPI cloud server for basic file storage.",
    version="0.1.0",
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

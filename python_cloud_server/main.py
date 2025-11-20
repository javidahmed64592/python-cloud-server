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


if __name__ == "__main__":
    config = load_config()
    uvicorn.run(
        "python_cloud_server.main:app",
        host="127.0.0.1",
        port=8443,
        reload=True,
        ssl_keyfile=config.ssl_keyfile,
        ssl_certfile=config.ssl_certfile,
    )

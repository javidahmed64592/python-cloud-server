"""FastAPI cloud storage server."""

import uvicorn
from fastapi import FastAPI

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
    uvicorn.run(
        "python_cloud_server.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload on code changes during development
    )

"""FastAPI cloud storage server using uvicorn."""

from python_cloud_server.cloud_server import CloudServer


def run() -> None:
    """Serve the FastAPI application using uvicorn.

    :raise SystemExit: If configuration fails to load or SSL certificate files are missing
    """
    server = CloudServer()
    server.run()

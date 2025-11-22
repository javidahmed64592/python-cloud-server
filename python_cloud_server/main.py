"""FastAPI cloud storage server using uvicorn."""

import logging
import sys

import uvicorn

from python_cloud_server.config import load_config

logger = logging.getLogger(__name__)


def run() -> None:
    """Serve the FastAPI application using uvicorn.

    :raise SystemExit: If configuration fails to load or SSL certificate files are missing
    """
    config = load_config()

    cert_file = config.certificate.ssl_cert_file_path
    key_file = config.certificate.ssl_key_file_path

    if not (cert_file.exists() and key_file.exists()):
        logger.error("SSL certificate files not found: '%s' or '%s'", cert_file, key_file)
        sys.exit(1)

    try:
        logger.info("Starting server: %s", config.server.full_url)
        uvicorn.run(
            "python_cloud_server.cloud_server:create_app",
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

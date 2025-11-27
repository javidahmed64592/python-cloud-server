"""FastAPI cloud storage server using uvicorn."""

import logging
import sys

from python_cloud_server.cloud_server import CloudServer
from python_cloud_server.config import load_config, parse_args

logger = logging.getLogger(__name__)


def run() -> None:
    """Serve the FastAPI application using uvicorn.

    :raise SystemExit: If configuration fails to load or SSL certificate files are missing
    """
    args = parse_args()
    config = load_config(args.config_file)
    try:
        server = CloudServer(config=config)
        server.run()
    except FileNotFoundError:
        server.logger.exception("Failed to start - SSL certificate files are missing!")
        sys.exit(1)
    except OSError:
        server.logger.exception("Failed to start - ran into an OSError!")
        sys.exit(1)

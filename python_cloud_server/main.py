"""FastAPI cloud storage server using uvicorn."""

from python_cloud_server.cloud_server import CloudServer
from python_cloud_server.config import load_config, parse_args


def run() -> None:
    """Serve the FastAPI application using uvicorn.

    :raise SystemExit: If configuration fails to load or SSL certificate files are missing
    """
    args = parse_args()
    config = load_config(args.config_file)
    server = CloudServer(config)
    server.run()

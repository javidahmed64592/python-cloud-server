"""Configuration handling for the server."""

import json
import logging
import sys
from logging.handlers import RotatingFileHandler

from pydantic import ValidationError
from pyhere import here

from python_cloud_server.constants import (
    CONFIG_FILE_NAME,
    LOG_BACKUP_COUNT,
    LOG_DATE_FORMAT,
    LOG_DIR_NAME,
    LOG_FILE_NAME,
    LOG_FORMAT,
    LOG_LEVEL,
    LOG_MAX_BYTES,
)
from python_cloud_server.models import AppConfigModel

ROOT_DIR = here()
LOG_DIR = ROOT_DIR / LOG_DIR_NAME
LOG_FILE_PATH = LOG_DIR / LOG_FILE_NAME
CONFIG_PATH = ROOT_DIR / CONFIG_FILE_NAME


def setup_logging() -> None:
    """Configure logging with both console and rotating file handlers.

    Creates a logs directory if it doesn't exist and sets up:
    - Console handler for stdout
    - Rotating file handler with size-based rotation
    """
    # Create logs directory if it doesn't exist
    LOG_DIR.mkdir(exist_ok=True)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))

    # Remove any existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating file handler
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


# Setup logging on module import
setup_logging()
logger = logging.getLogger(__name__)


def load_config() -> AppConfigModel:
    """Load configuration from the config.json file.

    :return AppConfigModel: The validated configuration model
    :raise SystemExit: If configuration file is missing, invalid JSON, or fails validation
    """
    if not CONFIG_PATH.exists():
        logger.error("Configuration file not found: %s", CONFIG_PATH)
        sys.exit(1)

    config_data = {}
    try:
        with CONFIG_PATH.open() as f:
            config_data = json.load(f)
    except json.JSONDecodeError:
        logger.exception("JSON parsing error: %s", CONFIG_PATH)
        sys.exit(1)
    except OSError:
        logger.exception("JSON read error: %s", CONFIG_PATH)
        sys.exit(1)

    try:
        return AppConfigModel(**config_data)
    except ValidationError:
        logger.exception("Invalid configuration in: %s", CONFIG_PATH)
        sys.exit(1)

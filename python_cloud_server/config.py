"""Configuration handling for the server."""

import json
import logging
import sys

from pydantic import ValidationError
from pyhere import here

from python_cloud_server.constants import CONFIG_FILE_NAME
from python_cloud_server.models import AppConfigModel

logging.basicConfig(
    format="[%(asctime)s] (%(levelname)s) %(module)s: %(message)s", datefmt="%d/%m/%Y | %H:%M:%S", level=logging.INFO
)
logger = logging.getLogger(__name__)

ROOT_DIR = here()
CONFIG_PATH = ROOT_DIR / CONFIG_FILE_NAME


def load_config() -> AppConfigModel:
    """Load configuration from the config.json file.

    :return AppConfigModel: The validated configuration model
    :raise SystemExit: If configuration file is missing, invalid JSON, or fails validation
    """
    if not CONFIG_PATH.exists():
        logger.error("Configuration file not found: %s", CONFIG_PATH)
        sys.exit(1)

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

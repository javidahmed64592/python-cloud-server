"""Configuration handling for the server."""

import json
from pathlib import Path

from python_cloud_server.models import ConfigModel

ROOT_DIR = Path(".").resolve()
CONFIG_PATH = ROOT_DIR / "config.json"


def load_config() -> ConfigModel:
    """Load configuration from the config.json file."""
    with CONFIG_PATH.open() as f:
        config_data = json.load(f)
    return ConfigModel(**config_data)

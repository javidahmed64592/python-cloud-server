"""Configuration handling for the server."""

import json
import sys
from pathlib import Path

from pydantic import ValidationError

from python_cloud_server.models import AppConfigModel

ROOT_DIR = Path(__file__).parent.parent.resolve()
CONFIG_PATH = ROOT_DIR / "config.json"


def load_config() -> AppConfigModel:
    """Load configuration from the config.json file.

    :return AppConfigModel: The validated configuration model
    :raise SystemExit: If configuration file is missing, invalid JSON, or fails validation
    """
    if not CONFIG_PATH.exists():
        print(f"ERROR: Configuration file not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    try:
        with CONFIG_PATH.open() as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in configuration file: {CONFIG_PATH}", file=sys.stderr)
        print(f"JSON parsing error: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"ERROR: Failed to read configuration file: {CONFIG_PATH}", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        return AppConfigModel(**config_data)
    except ValidationError as e:
        print(f"ERROR: Invalid configuration in {CONFIG_PATH}", file=sys.stderr)
        print("Configuration validation errors:", file=sys.stderr)
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            print(f"  - {field}: {error['msg']}", file=sys.stderr)
        sys.exit(1)

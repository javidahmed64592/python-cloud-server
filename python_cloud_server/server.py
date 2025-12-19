"""Cloud server module."""

import logging
from typing import Any

from python_template_server.constants import CONFIG_DIR
from python_template_server.template_server import TemplateServer

from python_cloud_server.models import CloudServerConfig

logger = logging.getLogger(__name__)


class CloudServer(TemplateServer):
    """FastAPI cloud server."""

    def __init__(self, config: CloudServerConfig | None = None) -> None:
        """Initialize the TemplateServer.

        :param CloudServerConfig | None config: Optional pre-loaded configuration
        """
        super().__init__(
            package_name="python_cloud_server",
            config_filepath=CONFIG_DIR / "cloud_server_config.json",
            config=config,
        )

    def validate_config(self, config_data: dict[str, Any]) -> CloudServerConfig:
        """Validate configuration data against the TemplateServerConfig model.

        :param dict config_data: The configuration data to validate
        :return TemplateServerConfig: The validated configuration model
        :raise ValidationError: If the configuration data is invalid
        """
        return CloudServerConfig.model_validate(config_data)

    def setup_routes(self) -> None:
        """Set up API routes."""
        super().setup_routes()

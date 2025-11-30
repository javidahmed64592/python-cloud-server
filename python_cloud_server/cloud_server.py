"""Cloud server application module."""

from python_template_server.template_server import TemplateServer

from python_cloud_server.models import CloudServerConfig


class CloudServer(TemplateServer):
    """Cloud storage server application inheriting from TemplateServer."""

    def __init__(self, config: CloudServerConfig | None = None) -> None:
        """Initialize the CloudServer by delegating to the template server.

        :param CloudServerConfig config: Cloud server configuration
        """
        super().__init__(package_name="python-cloud-server", config=config)

    def validate_config(self, config_data: dict) -> CloudServerConfig:
        """Validate and parse the configuration data into a CloudServerConfig.

        :param dict config_data: Raw configuration data
        :return CloudServerConfig: Validated cloud server configuration
        """
        return CloudServerConfig.model_validate(config_data)

    def setup_routes(self) -> None:
        """Set up API routes."""
        super().setup_routes()

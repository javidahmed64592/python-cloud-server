"""Cloud server application module."""

from python_cloud_server.models import CloudServerConfig
from python_cloud_server.template_server import TemplateServer


class CloudServer(TemplateServer):
    """Cloud storage server application inheriting from TemplateServer."""

    def __init__(self, config: CloudServerConfig) -> None:
        """Initialize the CloudServer by delegating to the template server.

        :param CloudServerConfig config: Cloud server configuration
        """
        super().__init__(config)

    def setup_routes(self) -> None:
        """Set up API routes."""
        super().setup_routes()

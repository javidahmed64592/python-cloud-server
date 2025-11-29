"""Unit tests for the python_cloud_server.cloud_server module."""

import pytest
from fastapi.routing import APIRoute

from python_cloud_server.cloud_server import CloudServer
from python_cloud_server.models import CloudServerConfig


@pytest.fixture
def mock_cloud_server(mock_app_config: CloudServerConfig) -> CloudServer:
    """Provide a CloudServer instance for testing."""
    return CloudServer(mock_app_config)


class TestCloudServer:
    """Unit tests for the CloudServer class."""

    def test_init(self, mock_cloud_server: CloudServer) -> None:
        """Test CloudServer initialization."""
        assert isinstance(mock_cloud_server.config, CloudServerConfig)


class TestCloudServerRoutes:
    """Integration tests for the routes in CloudServer."""

    def test_setup_routes(self, mock_cloud_server: CloudServer) -> None:
        """Test that routes are set up correctly."""
        api_routes = [route for route in mock_cloud_server.app.routes if isinstance(route, APIRoute)]
        routes = [route.path for route in api_routes]
        expected_endpoints = ["/health", "/metrics"]
        for endpoint in expected_endpoints:
            assert endpoint in routes

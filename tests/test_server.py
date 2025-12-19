"""Unit tests for the python_cloud_server.server module."""

from collections.abc import Generator
from importlib.metadata import PackageMetadata
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Security
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader

from python_cloud_server.models import CloudServerConfig
from python_cloud_server.server import CloudServer


@pytest.fixture(autouse=True)
def mock_package_metadata() -> Generator[MagicMock]:
    """Mock importlib.metadata.metadata to return a mock PackageMetadata."""
    with patch("python_template_server.template_server.metadata") as mock_metadata:
        mock_pkg_metadata = MagicMock(spec=PackageMetadata)
        metadata_dict = {
            "Name": "python-cloud-server",
            "Version": "0.1.0",
            "Summary": "A lightweight FastAPI cloud server.",
        }
        mock_pkg_metadata.__getitem__.side_effect = lambda key: metadata_dict[key]
        mock_metadata.return_value = mock_pkg_metadata
        yield mock_metadata


@pytest.fixture
def mock_server(
    mock_cloud_server_config: CloudServerConfig,
) -> Generator[CloudServer]:
    """Provide a CloudServer instance for testing."""

    async def fake_verify_api_key(
        api_key: str | None = Security(APIKeyHeader(name="X-API-Key", auto_error=False)),
    ) -> None:
        """Fake verify API key that accepts the security header and always succeeds in tests."""
        return

    with (
        patch.object(CloudServer, "_verify_api_key", new=fake_verify_api_key),
        patch("python_cloud_server.server.CloudServerConfig.save_to_file"),
    ):
        server = CloudServer(mock_cloud_server_config)
        yield server


class TestCloudServer:
    """Unit tests for the CloudServer class."""

    def test_init(self, mock_server: CloudServer) -> None:
        """Test CloudServer initialization."""
        assert isinstance(mock_server.config, CloudServerConfig)

    def test_validate_config(self, mock_server: CloudServer, mock_cloud_server_config: CloudServerConfig) -> None:
        """Test configuration validation."""
        config_dict = mock_cloud_server_config.model_dump()
        validated_config = mock_server.validate_config(config_dict)
        assert validated_config == mock_cloud_server_config

    def test_validate_config_invalid_returns_default(self, mock_server: CloudServer) -> None:
        """Test invalid configuration returns default configuration."""
        invalid_config = {"model": None}
        validated_config = mock_server.validate_config(invalid_config)
        assert isinstance(validated_config, CloudServerConfig)


class TestCCloudServerRoutes:
    """Integration tests for the routes in CloudServer."""

    def test_setup_routes(self, mock_server: CloudServer) -> None:
        """Test that routes are set up correctly."""
        api_routes = [route for route in mock_server.app.routes if isinstance(route, APIRoute)]
        routes = [route.path for route in api_routes]
        expected_endpoints = [
            "/health",
            "/metrics",
            "/login",
        ]
        for endpoint in expected_endpoints:
            assert endpoint in routes, f"Expected endpoint {endpoint} not found in routes"

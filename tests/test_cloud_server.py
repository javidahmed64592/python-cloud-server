"""Unit tests for the python_cloud_server.cloud_server module."""

import asyncio
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.security import APIKeyHeader
from fastapi.testclient import TestClient

from python_cloud_server.cloud_server import CloudServer, create_app
from python_cloud_server.constants import API_PREFIX
from python_cloud_server.models import BaseResponse, ResponseCode


@pytest.fixture
def mock_verify_token() -> Generator[MagicMock, None, None]:
    """Mock the verify_token function."""
    with patch("python_cloud_server.cloud_server.verify_token") as mock_verify:
        yield mock_verify


@pytest.fixture
def mock_cloud_server() -> CloudServer:
    """Provide a CloudServer instance for testing."""
    return CloudServer()


class TestCloudServer:
    """Unit tests for the CloudServer class."""

    def test_init(self, mock_cloud_server: CloudServer) -> None:
        """Test CloudServer initialization."""
        assert isinstance(mock_cloud_server.app, FastAPI)
        assert mock_cloud_server.app.title == "python-cloud-server"
        assert mock_cloud_server.app.description == "A FastAPI cloud server for basic file storage."
        assert mock_cloud_server.app.version == "0.1.0"
        assert mock_cloud_server.app.root_path == API_PREFIX
        assert isinstance(mock_cloud_server.api_key_header, APIKeyHeader)

    def test_add_authenticated_route(self, mock_cloud_server: CloudServer) -> None:
        """Test _add_authenticated_route adds routes with authentication."""

        # Define a test endpoint and handler
        async def test_handler() -> dict:
            return {"test": "response"}

        # Add a test route
        mock_cloud_server._add_authenticated_route("/test", test_handler, BaseResponse)

        # Verify the route was added
        routes = [route.path for route in mock_cloud_server.app.routes]
        assert "/test" in routes

        # Find the specific route
        test_route = next((route for route in mock_cloud_server.app.routes if route.path == "/test"), None)
        assert test_route is not None

        # Verify the route has dependencies (authentication)
        assert len(test_route.dependencies) > 0

        # Verify the dependency is the _verify_api_key method
        dependency = test_route.dependencies[0]
        assert dependency.dependency == mock_cloud_server._verify_api_key

    def test_setup_routes(self, mock_cloud_server: CloudServer) -> None:
        """Test that routes are set up correctly."""
        routes = [route.path for route in mock_cloud_server.app.routes]
        expected_endpoints = ["/health"]
        for endpoint in expected_endpoints:
            assert endpoint in routes

    def test_verify_api_key_valid(self, mock_cloud_server: CloudServer, mock_verify_token: MagicMock) -> None:
        """Test _verify_api_key with valid API key."""
        mock_verify_token.return_value = True

        result = asyncio.run(mock_cloud_server._verify_api_key("valid_key"))
        assert result is None

    def test_verify_api_key_missing(self, mock_cloud_server: CloudServer) -> None:
        """Test _verify_api_key with missing API key."""
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(mock_cloud_server._verify_api_key(None))

        assert exc_info.value.status_code == ResponseCode.UNAUTHORIZED
        assert exc_info.value.detail == "Missing API key"

    def test_verify_api_key_invalid(self, mock_cloud_server: CloudServer, mock_verify_token: MagicMock) -> None:
        """Test _verify_api_key with invalid API key."""
        mock_verify_token.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(mock_cloud_server._verify_api_key("invalid_key"))

        assert exc_info.value.status_code == ResponseCode.UNAUTHORIZED
        assert exc_info.value.detail == "Invalid API key"

    def test_verify_api_key_value_error(self, mock_cloud_server: CloudServer, mock_verify_token: MagicMock) -> None:
        """Test _verify_api_key when verify_token raises ValueError."""
        mock_verify_token.side_effect = ValueError("No stored token hash found")

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(mock_cloud_server._verify_api_key("some_key"))

        assert exc_info.value.status_code == ResponseCode.UNAUTHORIZED
        assert "No stored token hash found" in exc_info.value.detail


class TestHealthEndpoint:
    """Integration tests for the /health endpoint."""

    def test_get_health(self, mock_cloud_server: CloudServer) -> None:
        """Test the /health endpoint method."""
        response = asyncio.run(mock_cloud_server.get_health())
        assert response.code == ResponseCode.OK
        assert response.message == "Server is healthy"

    def test_health_endpoint_with_valid_api_key(self, mock_verify_token: MagicMock) -> None:
        """Test /health endpoint with valid API key returns 200."""
        mock_verify_token.return_value = True
        app = create_app()
        client = TestClient(app)

        response = client.get("/health", headers={"X-API-Key": "valid_key"})
        assert response.status_code == ResponseCode.OK
        assert response.json() == {"code": ResponseCode.OK, "message": "Server is healthy"}

    def test_health_endpoint_without_api_key(self) -> None:
        """Test /health endpoint without API key returns 401."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == ResponseCode.UNAUTHORIZED
        assert response.json()["detail"] == "Missing API key"

    def test_health_endpoint_with_invalid_api_key(self, mock_verify_token: MagicMock) -> None:
        """Test /health endpoint with invalid API key returns 401."""
        mock_verify_token.return_value = False
        app = create_app()
        client = TestClient(app)

        response = client.get("/health", headers={"X-API-Key": "invalid_key"})
        assert response.status_code == ResponseCode.UNAUTHORIZED
        assert response.json()["detail"] == "Invalid API key"


class TestCreateApp:
    """Unit tests for the create_app function."""

    def test_create_app(self) -> None:
        """Test create_app returns a FastAPI instance."""
        app = create_app()
        assert isinstance(app, FastAPI)

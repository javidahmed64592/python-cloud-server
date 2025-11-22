"""Unit tests for the python_cloud_server.main module."""

import asyncio
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.security import APIKeyHeader
from fastapi.testclient import TestClient

from python_cloud_server.constants import API_PREFIX
from python_cloud_server.main import CloudServer, create_app, run
from python_cloud_server.models import BaseResponse, ResponseCode

TEST_PORT = 8443


@pytest.fixture
def mock_load_config() -> Generator[MagicMock, None, None]:
    """Mock the load_config function."""
    with patch("python_cloud_server.main.load_config") as mock_config:
        yield mock_config


@pytest.fixture
def mock_verify_token() -> Generator[MagicMock, None, None]:
    """Mock the verify_token function."""
    with patch("python_cloud_server.main.verify_token") as mock_verify:
        yield mock_verify


@pytest.fixture
def mock_uvicorn_run() -> Generator[MagicMock, None, None]:
    """Mock uvicorn.run."""
    with patch("python_cloud_server.main.uvicorn.run") as mock_run:
        yield mock_run


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


class TestRun:
    """Unit tests for the run function."""

    def test_run_success(
        self,
        mock_load_config: MagicMock,
        mock_uvicorn_run: MagicMock,
    ) -> None:
        """Test successful server run."""
        mock_config = MagicMock()
        mock_config.certificate.ssl_cert_file_path.exists.return_value = True
        mock_config.certificate.ssl_key_file_path.exists.return_value = True
        mock_config.server.host = "localhost"
        mock_config.server.port = TEST_PORT
        mock_load_config.return_value = mock_config

        run()

        mock_uvicorn_run.assert_called_once()
        call_kwargs = mock_uvicorn_run.call_args.kwargs
        assert call_kwargs["host"] == "localhost"
        assert call_kwargs["port"] == TEST_PORT
        assert call_kwargs["factory"] is True
        assert call_kwargs["reload"] is True

    def test_run_missing_cert_file(
        self,
        mock_load_config: MagicMock,
        mock_uvicorn_run: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Test run exits when certificate file is missing."""
        mock_config = MagicMock()
        mock_config.certificate.ssl_cert_file_path.exists.return_value = False
        mock_config.certificate.ssl_key_file_path.exists.return_value = True
        mock_load_config.return_value = mock_config

        with pytest.raises(SystemExit):
            run()

        mock_sys_exit.assert_called_once_with(1)
        mock_uvicorn_run.assert_not_called()

    def test_run_missing_key_file(
        self,
        mock_load_config: MagicMock,
        mock_uvicorn_run: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Test run exits when key file is missing."""
        mock_config = MagicMock()
        mock_config.certificate.ssl_cert_file_path.exists.return_value = True
        mock_config.certificate.ssl_key_file_path.exists.return_value = False
        mock_load_config.return_value = mock_config

        with pytest.raises(SystemExit):
            run()

        mock_sys_exit.assert_called_once_with(1)
        mock_uvicorn_run.assert_not_called()

    def test_run_os_error(
        self,
        mock_load_config: MagicMock,
        mock_uvicorn_run: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Test run handles OSError from uvicorn."""
        mock_config = MagicMock()
        mock_config.certificate.ssl_cert_file_path.exists.return_value = True
        mock_config.certificate.ssl_key_file_path.exists.return_value = True
        mock_load_config.return_value = mock_config
        mock_uvicorn_run.side_effect = OSError("Port already in use")

        with pytest.raises(SystemExit):
            run()

        mock_sys_exit.assert_called_once_with(1)

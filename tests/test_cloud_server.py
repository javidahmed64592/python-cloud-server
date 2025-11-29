"""Unit tests for the python_cloud_server.cloud_server module."""

import asyncio
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from python_cloud_server.cloud_server import CloudServer
from python_cloud_server.constants import API_PREFIX
from python_cloud_server.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from python_cloud_server.models import BaseResponse, CloudServerConfig, ResponseCode, ServerHealthStatus


@pytest.fixture(autouse=True)
def clear_prometheus_registry() -> Generator[None, None, None]:
    """Clear Prometheus registry before each test to avoid duplicate metric errors."""
    # Clear all collectors from the registry
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)
    yield
    # Clear again after the test
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)


@pytest.fixture
def mock_verify_token() -> Generator[MagicMock, None, None]:
    """Mock the verify_token function."""
    with patch("python_cloud_server.cloud_server.verify_token") as mock_verify:
        yield mock_verify


@pytest.fixture(autouse=True)
def mock_load_hashed_token() -> Generator[MagicMock, None, None]:
    """Mock the load_hashed_token function."""
    with patch("python_cloud_server.cloud_server.load_hashed_token") as mock_load:
        mock_load.return_value = "mock_hashed_token"
        yield mock_load


@pytest.fixture
def mock_timestamp() -> Generator[str, None, None]:
    """Mock the current_timestamp method to return a fixed timestamp."""
    fixed_timestamp = "2025-11-22T12:00:00.000000Z"
    with patch("python_cloud_server.models.BaseResponse.current_timestamp", return_value=fixed_timestamp):
        yield fixed_timestamp


@pytest.fixture
def mock_cloud_server(mock_app_config: CloudServerConfig) -> CloudServer:
    """Provide a CloudServer instance for testing."""
    return CloudServer(mock_app_config)


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

    def test_request_middleware_added(self, mock_cloud_server: CloudServer) -> None:
        """Test that all middleware is added to the app."""
        middlewares = [middleware.cls for middleware in mock_cloud_server.app.user_middleware]
        assert RequestLoggingMiddleware in middlewares
        assert SecurityHeadersMiddleware in middlewares

    def test_add_unauthenticated_route(self, mock_cloud_server: CloudServer) -> None:
        """Test _add_unauthenticated_route adds routes without authentication."""

        # Define a test endpoint and handler
        async def test_handler(request: Request) -> dict:
            return {"test": "response"}

        # Add a test route
        mock_cloud_server._add_unauthenticated_route("/test", test_handler, BaseResponse)

        # Verify the route was added
        api_routes = [route for route in mock_cloud_server.app.routes if isinstance(route, APIRoute)]
        routes = [route.path for route in api_routes]
        assert "/test" in routes

        # Find the specific route
        test_route = next((route for route in api_routes if route.path == "/test"), None)
        assert test_route is not None

    def test_add_authenticated_route(self, mock_cloud_server: CloudServer) -> None:
        """Test _add_authenticated_route adds routes with authentication."""

        # Define a test endpoint and handler
        async def test_handler(request: Request) -> dict:
            return {"test": "response"}

        # Add a test route
        mock_cloud_server._add_authenticated_route("/test", test_handler, BaseResponse)

        # Verify the route was added
        api_routes = [route for route in mock_cloud_server.app.routes if isinstance(route, APIRoute)]
        routes = [route.path for route in api_routes]
        assert "/test" in routes

        # Find the specific route
        test_route = next((route for route in api_routes if route.path == "/test"), None)
        assert test_route is not None

        # Verify the route has dependencies (authentication)
        assert len(test_route.dependencies) > 0

        # Verify the dependency is the _verify_api_key method
        dependency = test_route.dependencies[0]
        assert dependency.dependency == mock_cloud_server._verify_api_key

    def test_setup_routes(self, mock_cloud_server: CloudServer) -> None:
        """Test that routes are set up correctly."""
        api_routes = [route for route in mock_cloud_server.app.routes if isinstance(route, APIRoute)]
        routes = [route.path for route in api_routes]
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


class TestPrometheusMetrics:
    """Unit tests for Prometheus metrics functionality."""

    def test_metrics_endpoint_exists(self, mock_cloud_server: CloudServer) -> None:
        """Test that /metrics endpoint is exposed."""
        api_routes = [route for route in mock_cloud_server.app.routes if isinstance(route, APIRoute)]
        routes = [route.path for route in api_routes]
        assert "/metrics" in routes

    def test_metrics_setup(self, mock_cloud_server: CloudServer) -> None:
        """Test that Prometheus metrics are properly initialized."""
        assert mock_cloud_server.token_configured_gauge is not None
        assert mock_cloud_server.auth_success_counter is not None
        assert mock_cloud_server.auth_failure_counter is not None
        assert mock_cloud_server.rate_limit_exceeded_counter is not None

    def test_set_token_configured_gauge(self, mock_cloud_server: CloudServer) -> None:
        """Test that token_configured_gauge is set correctly."""
        # Initially, the token is configured in the mock_cloud_server fixture
        assert mock_cloud_server.token_configured_gauge._value.get() == 1

        # Simulate token not configured
        mock_cloud_server.hashed_token = ""
        asyncio.run(mock_cloud_server.get_health(MagicMock()))
        assert mock_cloud_server.token_configured_gauge._value.get() == 0

    def test_auth_success_metric_incremented(
        self, mock_cloud_server: CloudServer, mock_verify_token: MagicMock
    ) -> None:
        """Test that auth_success_counter is incremented on successful authentication."""
        mock_verify_token.return_value = True
        initial_value = mock_cloud_server.auth_success_counter._value.get()

        asyncio.run(mock_cloud_server._verify_api_key(api_key="valid_token"))

        assert mock_cloud_server.auth_success_counter._value.get() == initial_value + 1

    def test_auth_failure_missing_metric_incremented(self, mock_cloud_server: CloudServer) -> None:
        """Test that auth_failure_counter is incremented when API key is missing."""
        initial_value = mock_cloud_server.auth_failure_counter.labels(reason="missing")._value.get()

        with pytest.raises(HTTPException):
            asyncio.run(mock_cloud_server._verify_api_key(api_key=None))

        assert mock_cloud_server.auth_failure_counter.labels(reason="missing")._value.get() == initial_value + 1

    def test_auth_failure_invalid_metric_incremented(
        self, mock_cloud_server: CloudServer, mock_verify_token: MagicMock
    ) -> None:
        """Test that auth_failure_counter is incremented when API key is invalid."""
        mock_verify_token.return_value = False
        initial_value = mock_cloud_server.auth_failure_counter.labels(reason="invalid")._value.get()

        with pytest.raises(HTTPException):
            asyncio.run(mock_cloud_server._verify_api_key(api_key="invalid_token"))

        assert mock_cloud_server.auth_failure_counter.labels(reason="invalid")._value.get() == initial_value + 1

    def test_auth_failure_error_metric_incremented(
        self, mock_cloud_server: CloudServer, mock_verify_token: MagicMock
    ) -> None:
        """Test that auth_failure_counter is incremented when verification raises ValueError."""
        mock_verify_token.side_effect = ValueError("Verification error")
        initial_value = mock_cloud_server.auth_failure_counter.labels(reason="error")._value.get()

        with pytest.raises(HTTPException):
            asyncio.run(mock_cloud_server._verify_api_key(api_key="error_token"))

        assert mock_cloud_server.auth_failure_counter.labels(reason="error")._value.get() == initial_value + 1


class TestRateLimiting:
    """Unit tests for rate limiting functionality."""

    def test_setup_rate_limiting_enabled(self, mock_app_config: CloudServerConfig) -> None:
        """Test rate limiting setup when enabled."""
        mock_app_config.rate_limit.enabled = True

        server = CloudServer(mock_app_config)

        assert server.limiter is not None
        assert server.app.state.limiter is not None

    def test_setup_rate_limiting_disabled(self, mock_cloud_server: CloudServer) -> None:
        """Test rate limiting setup when disabled."""
        assert mock_cloud_server.limiter is None

    def test_limit_route_with_limiter_enabled(self, mock_app_config: CloudServerConfig) -> None:
        """Test _limit_route when rate limiting is enabled."""
        mock_app_config.rate_limit.enabled = True

        server = CloudServer(mock_app_config)

        async def test_route(request: Request) -> dict:
            return {"test": "data"}

        limited_route = server._limit_route(test_route)

        # When limiter is enabled, the route should be wrapped
        assert limited_route != test_route
        assert hasattr(limited_route, "__wrapped__")

    def test_limit_route_with_limiter_disabled(self, mock_cloud_server: CloudServer) -> None:
        """Test _limit_route when rate limiting is disabled."""

        async def test_route(request: Request) -> dict:
            return {"test": "data"}

        limited_route = mock_cloud_server._limit_route(test_route)

        # When limiter is disabled, the route should be returned unchanged
        assert limited_route == test_route


class TestHealthEndpoint:
    """Integration tests for the /health endpoint."""

    def test_get_health(self, mock_cloud_server: CloudServer) -> None:
        """Test the /health endpoint method."""
        request = MagicMock()
        response = asyncio.run(mock_cloud_server.get_health(request))

        assert response.code == ResponseCode.OK
        assert response.message == "Server is healthy"
        assert response.status == ServerHealthStatus.HEALTHY
        assert mock_cloud_server.token_configured_gauge._value.get() == 1

    def test_get_health_token_not_configured(self, mock_cloud_server: CloudServer) -> None:
        """Test the /health endpoint method when token is not configured."""
        mock_cloud_server.hashed_token = ""
        request = MagicMock()

        response = asyncio.run(mock_cloud_server.get_health(request))

        assert response.code == ResponseCode.INTERNAL_SERVER_ERROR
        assert response.message == "Server token is not configured"
        assert response.status == ServerHealthStatus.UNHEALTHY
        assert mock_cloud_server.token_configured_gauge._value.get() == 0

    def test_health_endpoint(
        self, mock_cloud_server: CloudServer, mock_verify_token: MagicMock, mock_timestamp: str
    ) -> None:
        """Test /health endpoint returns 200."""
        mock_verify_token.return_value = True
        app = mock_cloud_server.app
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == ResponseCode.OK
        assert response.json() == {
            "code": ResponseCode.OK,
            "message": "Server is healthy",
            "timestamp": mock_timestamp,
            "status": ServerHealthStatus.HEALTHY,
        }


class TestCloudServerRun:
    """Unit tests for CloudServer.run method."""

    def test_run_success(self, mock_cloud_server: CloudServer, mock_exists: MagicMock) -> None:
        """Test successful server run."""
        mock_exists.side_effect = [True, True]

        with patch("python_cloud_server.cloud_server.uvicorn.run") as mock_uvicorn_run:
            mock_cloud_server.run()

        mock_uvicorn_run.assert_called_once()
        call_kwargs = mock_uvicorn_run.call_args.kwargs
        assert call_kwargs["host"] == mock_cloud_server.config.server.host
        assert call_kwargs["port"] == mock_cloud_server.config.server.port

    def test_run_missing_cert_file(self, mock_cloud_server: CloudServer, mock_exists: MagicMock) -> None:
        """Test run raises FileNotFoundError when certificate file is missing."""
        mock_exists.side_effect = [False, True]

        with pytest.raises(FileNotFoundError, match="SSL certificate files are missing"):
            mock_cloud_server.run()

    def test_run_missing_key_file(self, mock_cloud_server: CloudServer, mock_exists: MagicMock) -> None:
        """Test run raises FileNotFoundError when key file is missing."""
        mock_exists.side_effect = [True, False]

        with pytest.raises(FileNotFoundError, match="SSL certificate files are missing"):
            mock_cloud_server.run()

"""Unit tests for the python_cloud_server.models module."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from python_cloud_server.models import (
    AppConfigModel,
    BaseResponse,
    CertificateConfigModel,
    GetHealthResponse,
    ResponseCode,
    ServerConfigModel,
)


@pytest.fixture
def mock_server_config_dict() -> dict:
    """Provide a mock server configuration dictionary."""
    return {"host": "localhost", "port": 8080}


@pytest.fixture
def mock_certificate_config_dict() -> dict:
    """Provide a mock certificate configuration dictionary."""
    return {
        "directory": "/path/to/certs",
        "ssl_keyfile": "key.pem",
        "ssl_certfile": "cert.pem",
        "days_valid": 365,
    }


@pytest.fixture
def mock_server_config(mock_server_config_dict: dict) -> ServerConfigModel:
    """Provide a mock ServerConfigModel instance."""
    return ServerConfigModel(**mock_server_config_dict)


@pytest.fixture
def mock_certificate_config(mock_certificate_config_dict: dict) -> CertificateConfigModel:
    """Provide a mock CertificateConfigModel instance."""
    return CertificateConfigModel(**mock_certificate_config_dict)


@pytest.fixture
def mock_app_config(
    mock_server_config: ServerConfigModel,
    mock_certificate_config: CertificateConfigModel,
) -> AppConfigModel:
    """Provide a mock AppConfigModel instance."""
    return AppConfigModel(server=mock_server_config, certificate=mock_certificate_config)


# Application Configuration Models
class TestServerConfigModel:
    """Unit tests for the ServerConfigModel class."""

    def test_model_dump(self, mock_server_config_dict: dict, mock_server_config: ServerConfigModel) -> None:
        """Test the model_dump method."""
        assert mock_server_config.model_dump() == mock_server_config_dict

    def test_address_property(self, mock_server_config: ServerConfigModel) -> None:
        """Test the address property."""
        assert mock_server_config.address == "localhost:8080"

    def test_url_property(self, mock_server_config: ServerConfigModel) -> None:
        """Test the url property."""
        assert mock_server_config.url == "https://localhost:8080"

    @pytest.mark.parametrize("port", [0, 70000])
    def test_port_field(self, mock_server_config_dict: dict, port: int) -> None:
        """Test the port field validation."""
        invalid_config_data = mock_server_config_dict.copy()
        invalid_config_data["port"] = port  # Invalid port number
        with pytest.raises(ValidationError):
            ServerConfigModel(**invalid_config_data)


class TestCertificateConfigModel:
    """Unit tests for the CertificateConfigModel class."""

    def test_model_dump(
        self, mock_certificate_config_dict: dict, mock_certificate_config: CertificateConfigModel
    ) -> None:
        """Test the model_dump method."""
        assert mock_certificate_config.model_dump() == mock_certificate_config_dict

    def test_ssl_key_file_path_property(self, mock_certificate_config: CertificateConfigModel) -> None:
        """Test the ssl_key_file_path property."""
        assert mock_certificate_config.ssl_key_file_path == Path("/path/to/certs/key.pem")

    def test_ssl_cert_file_path_property(self, mock_certificate_config: CertificateConfigModel) -> None:
        """Test the ssl_cert_file_path property."""
        assert mock_certificate_config.ssl_cert_file_path == Path("/path/to/certs/cert.pem")

    def test_days_valid_field(
        self, mock_certificate_config_dict: dict, mock_certificate_config: CertificateConfigModel
    ) -> None:
        """Test the days_valid field."""
        invalid_config_data = mock_certificate_config_dict.copy()
        invalid_config_data["days_valid"] = -10  # Invalid value

        with pytest.raises(ValidationError):
            CertificateConfigModel(**invalid_config_data)


class TestAppConfigModel:
    """Unit tests for the AppConfigModel class."""

    def test_model_dump(
        self, mock_app_config: AppConfigModel, mock_server_config_dict: dict, mock_certificate_config_dict: dict
    ) -> None:
        """Test the model_dump method."""
        expected_dict = {
            "server": mock_server_config_dict,
            "certificate": mock_certificate_config_dict,
        }
        assert mock_app_config.model_dump() == expected_dict


# API Response Models
class TestResonseCode:
    """Unit tests for the ResponseCode enum."""

    @pytest.mark.parametrize(
        ("response_code", "status_code"),
        [
            (ResponseCode.OK, 200),
            (ResponseCode.CREATED, 201),
            (ResponseCode.ACCEPTED, 202),
            (ResponseCode.NO_CONTENT, 204),
            (ResponseCode.BAD_REQUEST, 400),
            (ResponseCode.UNAUTHORIZED, 401),
            (ResponseCode.FORBIDDEN, 403),
            (ResponseCode.NOT_FOUND, 404),
            (ResponseCode.CONFLICT, 409),
            (ResponseCode.INTERNAL_SERVER_ERROR, 500),
            (ResponseCode.SERVICE_UNAVAILABLE, 503),
        ],
    )
    def test_enum_values(self, response_code: ResponseCode, status_code: int) -> None:
        """Test the enum values."""
        assert response_code.value == status_code


class TestBaseResponse:
    """Unit tests for the BaseResponse class."""

    def test_model_dump(self) -> None:
        """Test the model_dump method."""
        config_dict = {"code": ResponseCode.OK, "message": "Success"}
        response = BaseResponse(**config_dict)
        assert response.model_dump() == config_dict


class TestGetHealthResponse:
    """Unit tests for the GetHealthResponse class."""

    def test_model_dump(self) -> None:
        """Test the model_dump method."""
        config_dict = {"code": ResponseCode.OK, "message": "Server is healthy"}
        response = GetHealthResponse(**config_dict)
        assert response.model_dump() == config_dict

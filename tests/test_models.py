"""Unit tests for the python_cloud_server.models module."""

from python_cloud_server.models import CloudServerConfig


# Cloud Server Configuration Models
class TestCloudServerConfig:
    """Unit tests for the CloudServerConfig class."""

    def test_model_dump(
        self,
        mock_app_config: CloudServerConfig,
        mock_server_config_dict: dict,
        mock_security_config_dict: dict,
        mock_rate_limit_config_dict: dict,
        mock_certificate_config_dict: dict,
    ) -> None:
        """Test the model_dump method."""
        expected_dict = {
            "server": mock_server_config_dict,
            "security": mock_security_config_dict,
            "rate_limit": mock_rate_limit_config_dict,
            "certificate": mock_certificate_config_dict,
        }
        assert mock_app_config.model_dump() == expected_dict

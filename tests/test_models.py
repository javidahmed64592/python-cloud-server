"""Unit tests for the python_cloud_server.models module."""

from python_cloud_server.models import CloudServerConfig


# Cloud Server Configuration Models
class TestCloudServerConfig:
    """Unit tests for the CloudServerConfig class."""

    def test_model_dump(self, mock_cloud_server_config: CloudServerConfig) -> None:
        """Test the model_dump method."""
        assert isinstance(mock_cloud_server_config.model_dump(), dict)  # Temporary until more config is added

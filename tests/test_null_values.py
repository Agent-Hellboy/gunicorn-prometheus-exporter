"""Test null value handling in YAML configuration."""

import os
import tempfile

from unittest.mock import patch

from gunicorn_prometheus_exporter.config.loader import YamlConfigLoader


class TestNullValueHandling:
    """Test that null values in YAML are handled correctly."""

    def create_test_config(self, config_data):
        """Create a temporary YAML config file."""
        import yaml

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
        yaml.dump(config_data, temp_file)
        temp_file.close()
        return temp_file.name

    def test_null_values_not_set_as_environment_variables(self):
        """Test that null values are not converted to 'None' strings."""
        config_data = {
            "exporter": {
                "prometheus": {
                    "metrics_port": 9091,
                    "bind_address": "0.0.0.0",
                    "multiproc_dir": None,  # This should not be set
                },
                "gunicorn": {
                    "workers": 4,
                    "timeout": None,  # This should not be set
                    "keepalive": 2,
                },
                "redis": {
                    "enabled": True,
                    "host": "localhost",
                    "port": 6379,
                    "db": None,  # This should not be set
                    "password": None,  # This should not be set
                    "key_prefix": "test",
                    "ttl_seconds": None,  # This should not be set
                    "ttl_disabled": None,  # This should not be set
                },
                "cleanup": {
                    "db_files": None,  # This should not be set
                },
            }
        }

        config_file = self.create_test_config(config_data)

        try:
            loader = YamlConfigLoader()
            env_vars = loader.convert_to_environment_variables(
                loader._validate_and_normalize_config(config_data)
            )

            # Check that null values are not present in environment variables
            assert "PROMETHEUS_MULTIPROC_DIR" not in env_vars
            assert "GUNICORN_TIMEOUT" not in env_vars
            assert "REDIS_DB" not in env_vars
            assert "REDIS_PASSWORD" not in env_vars
            assert "REDIS_TTL_SECONDS" not in env_vars
            assert "REDIS_TTL_DISABLED" not in env_vars
            assert "CLEANUP_DB_FILES" not in env_vars

            # Check that non-null values are present
            assert env_vars["PROMETHEUS_METRICS_PORT"] == "9091"
            assert env_vars["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
            assert env_vars["GUNICORN_WORKERS"] == "4"
            assert env_vars["GUNICORN_KEEPALIVE"] == "2"
            assert env_vars["REDIS_ENABLED"] == "true"
            assert env_vars["REDIS_HOST"] == "localhost"
            assert env_vars["REDIS_PORT"] == "6379"
            assert env_vars["REDIS_KEY_PREFIX"] == "test"

        finally:
            os.unlink(config_file)

    def test_null_ssl_values_not_set(self):
        """Test that null SSL values are not set as environment variables."""
        config_data = {
            "exporter": {
                "prometheus": {
                    "metrics_port": 9091,
                    "bind_address": "0.0.0.0",
                    "ssl": {
                        "enabled": True,
                        "certfile": None,  # This should not be set
                        "keyfile": "/path/to/key.pem",
                        "client_cafile": None,  # This should not be set
                        "client_capath": None,  # This should not be set
                        "client_auth_required": None,  # This should not be set
                    },
                },
                "gunicorn": {"workers": 1, "timeout": 30, "keepalive": 2},
            }
        }

        config_file = self.create_test_config(config_data)

        try:
            loader = YamlConfigLoader()
            env_vars = loader.convert_to_environment_variables(
                loader._validate_and_normalize_config(config_data)
            )

            # Check that null SSL values are not present
            assert "PROMETHEUS_SSL_CERTFILE" not in env_vars
            assert "PROMETHEUS_SSL_CLIENT_CAFILE" not in env_vars
            assert "PROMETHEUS_SSL_CLIENT_CAPATH" not in env_vars
            assert "PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED" not in env_vars

            # Check that non-null SSL values are present
            assert env_vars["PROMETHEUS_SSL_KEYFILE"] == "/path/to/key.pem"

        finally:
            os.unlink(config_file)

    @patch.dict(os.environ, {}, clear=True)
    def test_load_and_apply_config_with_null_values(self):
        """Test that load_and_apply_config doesn't set null values in os.environ."""
        config_data = {
            "exporter": {
                "prometheus": {
                    "metrics_port": 9091,
                    "bind_address": "0.0.0.0",
                    "multiproc_dir": None,
                },
                "gunicorn": {
                    "workers": 1,
                    "timeout": None,
                    "keepalive": 2,
                },
            }
        }

        config_file = self.create_test_config(config_data)

        try:
            loader = YamlConfigLoader()
            loader.load_and_apply_config(config_file)

            # Check that null values are not in os.environ
            assert "PROMETHEUS_MULTIPROC_DIR" not in os.environ
            assert "GUNICORN_TIMEOUT" not in os.environ

            # Check that non-null values are in os.environ
            assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
            assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
            assert os.environ["GUNICORN_WORKERS"] == "1"
            assert os.environ["GUNICORN_KEEPALIVE"] == "2"

        finally:
            os.unlink(config_file)

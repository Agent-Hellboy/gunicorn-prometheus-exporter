"""Tests for YAML configuration loader."""

import os
import tempfile

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from gunicorn_prometheus_exporter.config.loader import (
    YamlConfigLoader,
    get_yaml_loader,
    load_yaml_config,
)


class TestYamlConfigLoader:
    """Test cases for YamlConfigLoader class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loader = YamlConfigLoader()
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.yml"

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.config_file.exists():
            self.config_file.unlink()
        os.rmdir(self.temp_dir)

    def create_test_config(self, config_data: dict) -> str:
        """Create a test YAML configuration file."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)
        return str(self.config_file)

    def test_load_config_file_success(self):
        """Test successful loading of YAML configuration file."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
            }
        }
        config_file = self.create_test_config(config_data)

        result = self.loader.load_config_file(config_file)

        assert result == config_data

    def test_load_config_file_not_found(self):
        """Test loading non-existent configuration file."""
        with pytest.raises(FileNotFoundError):
            self.loader.load_config_file("nonexistent.yml")

    def test_load_config_file_invalid_yaml(self):
        """Test loading invalid YAML file."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            self.loader.load_config_file(str(self.config_file))

    def test_load_config_file_not_dict(self):
        """Test loading YAML file that doesn't contain a dictionary."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write("not a dictionary")

        with pytest.raises(
            ValueError, match="Configuration file must contain a dictionary"
        ):
            self.loader.load_config_file(str(self.config_file))

    def test_validate_and_normalize_config_missing_exporter(self):
        """Test validation with missing exporter section."""
        config_data = {"other": "data"}

        with pytest.raises(
            ValueError, match="Configuration must contain 'exporter' section"
        ):
            self.loader._validate_and_normalize_config(config_data)

    def test_validate_and_normalize_config_missing_prometheus(self):
        """Test validation with missing prometheus section."""
        config_data = {"exporter": {"gunicorn": {"workers": 2}}}

        with pytest.raises(
            ValueError, match="Missing required section: exporter.prometheus"
        ):
            self.loader._validate_and_normalize_config(config_data)

    def test_validate_and_normalize_config_missing_gunicorn(self):
        """Test validation with missing gunicorn section."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"}
            }
        }

        with pytest.raises(
            ValueError, match="Missing required section: exporter.gunicorn"
        ):
            self.loader._validate_and_normalize_config(config_data)

    def test_validate_and_normalize_config_missing_required_fields(self):
        """Test validation with missing required prometheus fields."""
        config_data = {
            "exporter": {
                "prometheus": {
                    "metrics_port": 9091
                    # Missing bind_address
                },
                "gunicorn": {"workers": 2},
            }
        }

        with pytest.raises(
            ValueError, match="Missing required field: exporter.prometheus.bind_address"
        ):
            self.loader._validate_and_normalize_config(config_data)

    def test_validate_and_normalize_config_invalid_prometheus_type(self):
        """Test validation with invalid prometheus section type."""
        config_data = {
            "exporter": {"prometheus": "not a dict", "gunicorn": {"workers": 2}}
        }

        with pytest.raises(
            ValueError, match="'exporter.prometheus' must be a dictionary"
        ):
            self.loader._validate_and_normalize_config(config_data)

    def test_validate_and_normalize_config_invalid_gunicorn_type(self):
        """Test validation with invalid gunicorn section type."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": "not a dict",
            }
        }

        with pytest.raises(
            ValueError, match="'exporter.gunicorn' must be a dictionary"
        ):
            self.loader._validate_and_normalize_config(config_data)

    def test_validate_and_normalize_config_invalid_redis_type(self):
        """Test validation with invalid redis section type."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
                "redis": "not a dict",
            }
        }

        with pytest.raises(ValueError, match="'exporter.redis' must be a dictionary"):
            self.loader._validate_and_normalize_config(config_data)

    def test_validate_and_normalize_config_invalid_ssl_type(self):
        """Test validation with invalid ssl section type."""
        config_data = {
            "exporter": {
                "prometheus": {
                    "metrics_port": 9091,
                    "bind_address": "0.0.0.0",
                    "ssl": "not a dict",
                },
                "gunicorn": {"workers": 2},
            }
        }

        with pytest.raises(
            ValueError, match="'exporter.prometheus.ssl' must be a dictionary"
        ):
            self.loader._validate_and_normalize_config(config_data)

    def test_convert_to_environment_variables_basic(self):
        """Test converting basic configuration to environment variables."""
        config_data = {
            "exporter": {
                "prometheus": {
                    "metrics_port": 9091,
                    "bind_address": "0.0.0.0",
                    "multiproc_dir": "/tmp/prometheus",
                },
                "gunicorn": {"workers": 4, "timeout": 300, "keepalive": 5},
            }
        }

        result = self.loader.convert_to_environment_variables(config_data)

        expected = {
            "PROMETHEUS_METRICS_PORT": "9091",
            "PROMETHEUS_BIND_ADDRESS": "0.0.0.0",
            "PROMETHEUS_MULTIPROC_DIR": "/tmp/prometheus",
            "GUNICORN_WORKERS": "4",
            "GUNICORN_TIMEOUT": "300",
            "GUNICORN_KEEPALIVE": "5",
        }
        assert result == expected

    def test_convert_to_environment_variables_with_redis(self):
        """Test converting configuration with Redis to environment variables."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
                "redis": {
                    "enabled": True,
                    "host": "redis.example.com",
                    "port": 6379,
                    "db": 1,
                    "password": "secret",
                    "key_prefix": "myapp",
                    "ttl_seconds": 600,
                    "ttl_disabled": False,
                },
            }
        }

        result = self.loader.convert_to_environment_variables(config_data)

        expected = {
            "PROMETHEUS_METRICS_PORT": "9091",
            "PROMETHEUS_BIND_ADDRESS": "0.0.0.0",
            "GUNICORN_WORKERS": "2",
            "REDIS_ENABLED": "true",
            "REDIS_HOST": "redis.example.com",
            "REDIS_PORT": "6379",
            "REDIS_DB": "1",
            "REDIS_PASSWORD": "secret",
            "REDIS_KEY_PREFIX": "myapp",
            "REDIS_TTL_SECONDS": "600",
            "REDIS_TTL_DISABLED": "false",
        }
        assert result == expected

    def test_convert_to_environment_variables_with_ssl(self):
        """Test converting configuration with SSL to environment variables."""
        config_data = {
            "exporter": {
                "prometheus": {
                    "metrics_port": 9091,
                    "bind_address": "0.0.0.0",
                    "ssl": {
                        "enabled": True,
                        "certfile": "/path/to/cert.pem",
                        "keyfile": "/path/to/key.pem",
                        "client_cafile": "/path/to/ca.pem",
                        "client_capath": "/path/to/ca/dir",
                        "client_auth_required": True,
                    },
                },
                "gunicorn": {"workers": 2},
            }
        }

        result = self.loader.convert_to_environment_variables(config_data)

        expected = {
            "PROMETHEUS_METRICS_PORT": "9091",
            "PROMETHEUS_BIND_ADDRESS": "0.0.0.0",
            "GUNICORN_WORKERS": "2",
            "PROMETHEUS_SSL_CERTFILE": "/path/to/cert.pem",
            "PROMETHEUS_SSL_KEYFILE": "/path/to/key.pem",
            "PROMETHEUS_SSL_CLIENT_CAFILE": "/path/to/ca.pem",
            "PROMETHEUS_SSL_CLIENT_CAPATH": "/path/to/ca/dir",
            "PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED": "true",
        }
        assert result == expected

    def test_convert_to_environment_variables_with_cleanup(self):
        """Test converting configuration with cleanup settings to environment variables."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
                "cleanup": {"db_files": True},
            }
        }

        result = self.loader.convert_to_environment_variables(config_data)

        expected = {
            "PROMETHEUS_METRICS_PORT": "9091",
            "PROMETHEUS_BIND_ADDRESS": "0.0.0.0",
            "GUNICORN_WORKERS": "2",
            "CLEANUP_DB_FILES": "true",
        }
        assert result == expected

    @patch.dict(os.environ, {}, clear=True)
    def test_load_and_apply_config_success(self):
        """Test successful loading and applying of configuration."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
            }
        }
        config_file = self.create_test_config(config_data)

        self.loader.load_and_apply_config(config_file)

        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"

    @patch.dict(os.environ, {"PROMETHEUS_METRICS_PORT": "8080"}, clear=True)
    def test_load_and_apply_config_preserves_existing_env_vars(self):
        """Test that existing environment variables are preserved."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
            }
        }
        config_file = self.create_test_config(config_data)

        self.loader.load_and_apply_config(config_file)

        # Existing environment variable should be preserved
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "8080"
        # New environment variable should be set
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"

    def test_get_yaml_loader_singleton(self):
        """Test that get_yaml_loader returns a singleton instance."""
        loader1 = get_yaml_loader()
        loader2 = get_yaml_loader()

        assert loader1 is loader2
        assert isinstance(loader1, YamlConfigLoader)

    @patch.dict(os.environ, {}, clear=True)
    def test_load_yaml_config_function(self):
        """Test the public load_yaml_config function."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
            }
        }
        config_file = self.create_test_config(config_data)

        load_yaml_config(config_file)

        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"

    def test_load_yaml_config_file_not_found(self):
        """Test load_yaml_config with non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_yaml_config("nonexistent.yml")

    def test_load_yaml_config_invalid_yaml(self):
        """Test load_yaml_config with invalid YAML."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            load_yaml_config(str(self.config_file))

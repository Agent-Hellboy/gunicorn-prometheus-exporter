"""Tests for YAML loading functionality in hooks."""

import os
import tempfile

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from gunicorn_prometheus_exporter.hooks import load_yaml_config


class TestHooksYaml:
    """Test cases for YAML loading functionality in hooks."""

    def setup_method(self):
        """Set up test fixtures."""
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

    @patch.dict(os.environ, {}, clear=True)
    def test_load_yaml_config_success(self):
        """Test successful loading of YAML configuration through hooks."""
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
        config_file = self.create_test_config(config_data)

        load_yaml_config(config_file)

        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["PROMETHEUS_MULTIPROC_DIR"] == "/tmp/prometheus"
        assert os.environ["GUNICORN_WORKERS"] == "4"
        assert os.environ["GUNICORN_TIMEOUT"] == "300"
        assert os.environ["GUNICORN_KEEPALIVE"] == "5"

    @patch.dict(os.environ, {}, clear=True)
    def test_load_yaml_config_with_redis(self):
        """Test loading YAML configuration with Redis settings through hooks."""
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
        config_file = self.create_test_config(config_data)

        load_yaml_config(config_file)

        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"
        assert os.environ["REDIS_ENABLED"] == "true"
        assert os.environ["REDIS_HOST"] == "redis.example.com"
        assert os.environ["REDIS_PORT"] == "6379"
        assert os.environ["REDIS_DB"] == "1"
        assert os.environ["REDIS_PASSWORD"] == "secret"
        assert os.environ["REDIS_KEY_PREFIX"] == "myapp"
        assert os.environ["REDIS_TTL_SECONDS"] == "600"
        assert os.environ["REDIS_TTL_DISABLED"] == "false"

    @patch.dict(os.environ, {}, clear=True)
    def test_load_yaml_config_with_ssl(self):
        """Test loading YAML configuration with SSL settings through hooks."""
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
        config_file = self.create_test_config(config_data)

        load_yaml_config(config_file)

        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"
        assert os.environ["PROMETHEUS_SSL_CERTFILE"] == "/path/to/cert.pem"
        assert os.environ["PROMETHEUS_SSL_KEYFILE"] == "/path/to/key.pem"
        assert os.environ["PROMETHEUS_SSL_CLIENT_CAFILE"] == "/path/to/ca.pem"
        assert os.environ["PROMETHEUS_SSL_CLIENT_CAPATH"] == "/path/to/ca/dir"
        assert os.environ["PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED"] == "true"

    @patch.dict(os.environ, {}, clear=True)
    def test_load_yaml_config_with_cleanup(self):
        """Test loading YAML configuration with cleanup settings through hooks."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
                "cleanup": {"db_files": True},
            }
        }
        config_file = self.create_test_config(config_data)

        load_yaml_config(config_file)

        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"
        assert os.environ["CLEANUP_DB_FILES"] == "true"

    @patch.dict(os.environ, {"PROMETHEUS_METRICS_PORT": "8080"}, clear=True)
    def test_load_yaml_config_preserves_existing_env_vars(self):
        """Test that existing environment variables are preserved when loading YAML config."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
            }
        }
        config_file = self.create_test_config(config_data)

        load_yaml_config(config_file)

        # Existing environment variable should be preserved
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "8080"
        # New environment variable should be set
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"

    def test_load_yaml_config_file_not_found(self):
        """Test loading non-existent YAML configuration file through hooks."""
        with pytest.raises(FileNotFoundError):
            load_yaml_config("nonexistent.yml")

    def test_load_yaml_config_invalid_yaml(self):
        """Test loading invalid YAML configuration file through hooks."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            load_yaml_config(str(self.config_file))

    def test_load_yaml_config_invalid_structure(self):
        """Test loading YAML configuration file with invalid structure through hooks."""
        config_data = {
            "exporter": {
                "prometheus": {
                    "metrics_port": 9091
                    # Missing required bind_address
                },
                "gunicorn": {"workers": 2},
            }
        }
        config_file = self.create_test_config(config_data)

        with pytest.raises(
            ValueError, match="Missing required field: exporter.prometheus.bind_address"
        ):
            load_yaml_config(config_file)

    @patch.dict(os.environ, {}, clear=True)
    def test_load_yaml_config_comprehensive_settings(self):
        """Test loading YAML configuration with all possible settings through hooks."""
        config_data = {
            "exporter": {
                "prometheus": {
                    "metrics_port": 9091,
                    "bind_address": "0.0.0.0",
                    "multiproc_dir": "/var/lib/prometheus/gunicorn",
                    "ssl": {
                        "enabled": True,
                        "certfile": "/etc/ssl/certs/gunicorn-prometheus.crt",
                        "keyfile": "/etc/ssl/private/gunicorn-prometheus.key",
                        "client_cafile": "/etc/ssl/certs/ca-bundle.crt",
                        "client_capath": "/etc/ssl/certs",
                        "client_auth_required": False,
                    },
                },
                "gunicorn": {"workers": 8, "timeout": 300, "keepalive": 5},
                "redis": {
                    "enabled": True,
                    "host": "redis-cluster.internal",
                    "port": 6379,
                    "db": 0,
                    "password": "secure-redis-password",
                    "key_prefix": "gunicorn:prod",
                    "ttl_seconds": 600,
                    "ttl_disabled": False,
                },
                "cleanup": {"db_files": True},
            }
        }
        config_file = self.create_test_config(config_data)

        load_yaml_config(config_file)

        # Check all environment variables are set correctly
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["PROMETHEUS_MULTIPROC_DIR"] == "/var/lib/prometheus/gunicorn"
        assert os.environ["GUNICORN_WORKERS"] == "8"
        assert os.environ["GUNICORN_TIMEOUT"] == "300"
        assert os.environ["GUNICORN_KEEPALIVE"] == "5"
        assert os.environ["REDIS_ENABLED"] == "true"
        assert os.environ["REDIS_HOST"] == "redis-cluster.internal"
        assert os.environ["REDIS_PORT"] == "6379"
        assert os.environ["REDIS_DB"] == "0"
        assert os.environ["REDIS_PASSWORD"] == "secure-redis-password"
        assert os.environ["REDIS_KEY_PREFIX"] == "gunicorn:prod"
        assert os.environ["REDIS_TTL_SECONDS"] == "600"
        assert os.environ["REDIS_TTL_DISABLED"] == "false"
        assert (
            os.environ["PROMETHEUS_SSL_CERTFILE"]
            == "/etc/ssl/certs/gunicorn-prometheus.crt"
        )
        assert (
            os.environ["PROMETHEUS_SSL_KEYFILE"]
            == "/etc/ssl/private/gunicorn-prometheus.key"
        )
        assert (
            os.environ["PROMETHEUS_SSL_CLIENT_CAFILE"] == "/etc/ssl/certs/ca-bundle.crt"
        )
        assert os.environ["PROMETHEUS_SSL_CLIENT_CAPATH"] == "/etc/ssl/certs"
        assert os.environ["PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED"] == "false"
        assert os.environ["CLEANUP_DB_FILES"] == "true"

    @patch.dict(os.environ, {}, clear=True)
    def test_load_yaml_config_minimal_settings(self):
        """Test loading YAML configuration with minimal required settings through hooks."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 1},
            }
        }
        config_file = self.create_test_config(config_data)

        load_yaml_config(config_file)

        # Check only required environment variables are set
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "1"

        # Check optional environment variables are not set
        assert "PROMETHEUS_MULTIPROC_DIR" not in os.environ
        assert "GUNICORN_TIMEOUT" not in os.environ
        assert "GUNICORN_KEEPALIVE" not in os.environ
        assert "REDIS_ENABLED" not in os.environ
        assert "CLEANUP_DB_FILES" not in os.environ

    @patch.dict(os.environ, {}, clear=True)
    def test_load_yaml_config_redis_disabled(self):
        """Test loading YAML configuration with Redis disabled through hooks."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
                "redis": {
                    "enabled": False,
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
        config_file = self.create_test_config(config_data)

        load_yaml_config(config_file)

        # Redis should not be enabled
        assert "REDIS_ENABLED" not in os.environ
        assert "REDIS_HOST" not in os.environ
        assert "REDIS_PORT" not in os.environ
        assert "REDIS_DB" not in os.environ
        assert "REDIS_PASSWORD" not in os.environ
        assert "REDIS_KEY_PREFIX" not in os.environ
        assert "REDIS_TTL_SECONDS" not in os.environ
        assert "REDIS_TTL_DISABLED" not in os.environ

        # Other settings should be set
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"

    @patch.dict(os.environ, {}, clear=True)
    def test_load_yaml_config_ssl_disabled(self):
        """Test loading YAML configuration with SSL disabled through hooks."""
        config_data = {
            "exporter": {
                "prometheus": {
                    "metrics_port": 9091,
                    "bind_address": "0.0.0.0",
                    "ssl": {
                        "enabled": False,
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
        config_file = self.create_test_config(config_data)

        load_yaml_config(config_file)

        # SSL should not be enabled
        assert "PROMETHEUS_SSL_CERTFILE" not in os.environ
        assert "PROMETHEUS_SSL_KEYFILE" not in os.environ
        assert "PROMETHEUS_SSL_CLIENT_CAFILE" not in os.environ
        assert "PROMETHEUS_SSL_CLIENT_CAPATH" not in os.environ
        assert "PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED" not in os.environ

        # Other settings should be set
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"

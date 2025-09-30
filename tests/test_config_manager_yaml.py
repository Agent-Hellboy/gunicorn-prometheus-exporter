"""Tests for enhanced ConfigManager with YAML support."""

import os
import tempfile

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from gunicorn_prometheus_exporter.config.manager import (
    ConfigManager,
    ConfigState,
    get_config_manager,
    initialize_config,
)


class TestConfigManagerYaml:
    """Test cases for ConfigManager with YAML support."""

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
    def test_initialize_with_yaml_config_success(self):
        """Test successful initialization with YAML configuration."""
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

        manager = ConfigManager()
        manager.initialize(config_file=config_file)

        assert manager.state == ConfigState.INITIALIZED
        assert manager.is_initialized
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "4"

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_with_yaml_config_and_overrides(self):
        """Test initialization with YAML config and environment variable overrides."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
            }
        }
        config_file = self.create_test_config(config_data)

        manager = ConfigManager()
        manager.initialize(
            config_file=config_file,
            PROMETHEUS_METRICS_PORT="8080",
            GUNICORN_WORKERS="8",
        )

        assert manager.state == ConfigState.INITIALIZED
        # Environment variable overrides should take precedence
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "8080"
        assert os.environ["GUNICORN_WORKERS"] == "8"
        # YAML values should be set for non-overridden values
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_with_yaml_config_redis_enabled(self):
        """Test initialization with YAML config that enables Redis."""
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

        manager = ConfigManager()
        manager.initialize(config_file=config_file)

        assert manager.state == ConfigState.INITIALIZED
        assert os.environ["REDIS_ENABLED"] == "true"
        assert os.environ["REDIS_HOST"] == "redis.example.com"
        assert os.environ["REDIS_PORT"] == "6379"
        assert os.environ["REDIS_DB"] == "1"
        assert os.environ["REDIS_PASSWORD"] == "secret"
        assert os.environ["REDIS_KEY_PREFIX"] == "myapp"
        assert os.environ["REDIS_TTL_SECONDS"] == "600"
        assert os.environ["REDIS_TTL_DISABLED"] == "false"

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_with_yaml_config_ssl_enabled(self):
        """Test initialization with YAML config that enables SSL."""

        # Create temporary SSL files for testing
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as cert_file:
            cert_file.write("test cert content")
            cert_path = cert_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", delete=False
        ) as key_file:
            key_file.write("test key content")
            key_path = key_file.name

        try:
            config_data = {
                "exporter": {
                    "prometheus": {
                        "metrics_port": 9091,
                        "bind_address": "0.0.0.0",
                        "ssl": {
                            "enabled": True,
                            "certfile": cert_path,
                            "keyfile": key_path,
                            "client_cafile": cert_path,  # Reuse cert file for CA
                            "client_capath": os.path.dirname(cert_path),
                            "client_auth_required": True,
                        },
                    },
                    "gunicorn": {"workers": 2},
                }
            }
            config_file = self.create_test_config(config_data)

            manager = ConfigManager()
            manager.initialize(config_file=config_file)

            assert manager.state == ConfigState.INITIALIZED
            assert os.environ["PROMETHEUS_SSL_CERTFILE"] == cert_path
            assert os.environ["PROMETHEUS_SSL_KEYFILE"] == key_path
            assert os.environ["PROMETHEUS_SSL_CLIENT_CAFILE"] == cert_path
            assert os.environ["PROMETHEUS_SSL_CLIENT_CAPATH"] == os.path.dirname(
                cert_path
            )
            assert os.environ["PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED"] == "true"
        finally:
            # Clean up temporary files
            os.unlink(cert_path)
            os.unlink(key_path)

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_with_yaml_config_file_not_found(self):
        """Test initialization with non-existent YAML config file."""
        manager = ConfigManager()

        with pytest.raises(FileNotFoundError):
            manager.initialize(config_file="nonexistent.yml")

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_with_yaml_config_invalid_yaml(self):
        """Test initialization with invalid YAML config file."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")

        manager = ConfigManager()

        with pytest.raises(yaml.YAMLError):
            manager.initialize(config_file=str(self.config_file))

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_with_yaml_config_invalid_structure(self):
        """Test initialization with YAML config file with invalid structure."""
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

        manager = ConfigManager()

        with pytest.raises(
            ValueError, match="Missing required field: exporter.prometheus.bind_address"
        ):
            manager.initialize(config_file=config_file)

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_without_yaml_config(self):
        """Test initialization without YAML config (backward compatibility)."""
        manager = ConfigManager()
        manager.initialize(
            PROMETHEUS_METRICS_PORT="9091",
            PROMETHEUS_BIND_ADDRESS="0.0.0.0",
            GUNICORN_WORKERS="2",
        )

        assert manager.state == ConfigState.INITIALIZED
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_with_none_yaml_config(self):
        """Test initialization with None YAML config (backward compatibility)."""
        manager = ConfigManager()
        manager.initialize(
            config_file=None,
            PROMETHEUS_METRICS_PORT="9091",
            PROMETHEUS_BIND_ADDRESS="0.0.0.0",
            GUNICORN_WORKERS="2",
        )

        assert manager.state == ConfigState.INITIALIZED
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_config_function_with_yaml(self):
        """Test the global initialize_config function with YAML."""
        from gunicorn_prometheus_exporter.config.manager import cleanup_config

        # Clean up any existing configuration
        cleanup_config()

        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
            }
        }
        config_file = self.create_test_config(config_data)

        initialize_config(config_file=config_file)

        # Get the global config manager
        manager = get_config_manager()
        assert manager.state == ConfigState.INITIALIZED
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_config_function_with_yaml_and_overrides(self):
        """Test the global initialize_config function with YAML and overrides."""
        from gunicorn_prometheus_exporter.config.manager import cleanup_config

        # Clean up any existing configuration
        cleanup_config()

        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
            }
        }
        config_file = self.create_test_config(config_data)

        initialize_config(
            config_file=config_file,
            PROMETHEUS_METRICS_PORT="8080",
            GUNICORN_WORKERS="8",
        )

        # Get the global config manager
        manager = get_config_manager()
        assert manager.state == ConfigState.INITIALIZED
        # Environment variable overrides should take precedence
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "8080"
        assert os.environ["GUNICORN_WORKERS"] == "8"
        # YAML values should be set for non-overridden values
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_config_function_without_yaml(self):
        """Test the global initialize_config function without YAML (backward compatibility)."""
        from gunicorn_prometheus_exporter.config.manager import cleanup_config

        # Clean up any existing configuration
        cleanup_config()

        initialize_config(
            PROMETHEUS_METRICS_PORT="9091",
            PROMETHEUS_BIND_ADDRESS="0.0.0.0",
            GUNICORN_WORKERS="2",
        )

        # Get the global config manager
        manager = get_config_manager()
        assert manager.state == ConfigState.INITIALIZED
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_config_function_with_none_yaml(self):
        """Test the global initialize_config function with None YAML (backward compatibility)."""
        from gunicorn_prometheus_exporter.config.manager import cleanup_config

        # Clean up any existing configuration
        cleanup_config()

        initialize_config(
            config_file=None,
            PROMETHEUS_METRICS_PORT="9091",
            PROMETHEUS_BIND_ADDRESS="0.0.0.0",
            GUNICORN_WORKERS="2",
        )

        # Get the global config manager
        manager = get_config_manager()
        assert manager.state == ConfigState.INITIALIZED
        assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
        assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
        assert os.environ["GUNICORN_WORKERS"] == "2"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns a singleton instance."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()

        assert manager1 is manager2
        assert isinstance(manager1, ConfigManager)

    @patch.dict(os.environ, {}, clear=True)
    def test_yaml_config_with_cleanup_settings(self):
        """Test YAML configuration with cleanup settings."""
        config_data = {
            "exporter": {
                "prometheus": {"metrics_port": 9091, "bind_address": "0.0.0.0"},
                "gunicorn": {"workers": 2},
                "cleanup": {"db_files": True},
            }
        }
        config_file = self.create_test_config(config_data)

        manager = ConfigManager()
        manager.initialize(config_file=config_file)

        assert manager.state == ConfigState.INITIALIZED
        assert os.environ["CLEANUP_DB_FILES"] == "true"

    @patch.dict(os.environ, {}, clear=True)
    def test_yaml_config_with_comprehensive_settings(self):
        """Test YAML configuration with all possible settings."""

        # Create temporary directory and SSL files for testing
        temp_dir = tempfile.mkdtemp()
        ssl_dir = os.path.join(temp_dir, "ssl")
        os.makedirs(ssl_dir, exist_ok=True)

        cert_path = os.path.join(ssl_dir, "cert.pem")
        key_path = os.path.join(ssl_dir, "key.pem")
        ca_path = os.path.join(ssl_dir, "ca.pem")

        with open(cert_path, "w") as f:
            f.write("test cert content")
        with open(key_path, "w") as f:
            f.write("test key content")
        with open(ca_path, "w") as f:
            f.write("test ca content")

        try:
            config_data = {
                "exporter": {
                    "prometheus": {
                        "metrics_port": 9091,
                        "bind_address": "0.0.0.0",
                        "multiproc_dir": os.path.join(temp_dir, "prometheus"),
                        "ssl": {
                            "enabled": True,
                            "certfile": cert_path,
                            "keyfile": key_path,
                            "client_cafile": ca_path,
                            "client_capath": ssl_dir,
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

            manager = ConfigManager()
            manager.initialize(config_file=config_file)

            assert manager.state == ConfigState.INITIALIZED

            # Check all environment variables are set correctly
            assert os.environ["PROMETHEUS_METRICS_PORT"] == "9091"
            assert os.environ["PROMETHEUS_BIND_ADDRESS"] == "0.0.0.0"
            assert os.environ["PROMETHEUS_MULTIPROC_DIR"] == os.path.join(
                temp_dir, "prometheus"
            )
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
            assert os.environ["PROMETHEUS_SSL_CERTFILE"] == cert_path
            assert os.environ["PROMETHEUS_SSL_KEYFILE"] == key_path
            assert os.environ["PROMETHEUS_SSL_CLIENT_CAFILE"] == ca_path
            assert os.environ["PROMETHEUS_SSL_CLIENT_CAPATH"] == ssl_dir
            assert os.environ["PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED"] == "false"
            assert os.environ["CLEANUP_DB_FILES"] == "true"
        finally:
            # Clean up temporary files and directory
            import shutil

            shutil.rmtree(temp_dir)

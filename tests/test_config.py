"""Tests for the configuration system."""

import os
import tempfile

from gunicorn_prometheus_exporter.config import ExporterConfig, get_config


class TestExporterConfig:
    """Test the ExporterConfig class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        # Save original environment
        original_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")

        # Clear environment to test defaults
        if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
            del os.environ["PROMETHEUS_MULTIPROC_DIR"]

        config = ExporterConfig()

        assert config.prometheus_multiproc_dir == "/tmp/prometheus"
        assert config.prometheus_metrics_port == 9091
        assert config.prometheus_bind_address == "127.0.0.1"
        assert config.gunicorn_workers == 2
        assert config.gunicorn_timeout == 30
        assert config.gunicorn_keepalive == 2

        # Restore original environment
        if original_multiproc_dir:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = original_multiproc_dir

    def test_environment_variables(self):
        """Test that environment variables override defaults."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = temp_dir
            os.environ["PROMETHEUS_METRICS_PORT"] = "9092"
            os.environ["GUNICORN_WORKERS"] = "4"

            config = ExporterConfig()

            assert config.prometheus_multiproc_dir == temp_dir
            assert config.prometheus_metrics_port == 9092
            assert config.gunicorn_workers == 4

            # Clean up
            del os.environ["PROMETHEUS_MULTIPROC_DIR"]
            del os.environ["PROMETHEUS_METRICS_PORT"]
            del os.environ["GUNICORN_WORKERS"]

    def test_gunicorn_config(self):
        """Test that gunicorn config is generated correctly."""
        config = ExporterConfig()
        gunicorn_config = config.get_gunicorn_config()

        assert gunicorn_config["bind"] == "127.0.0.1:8084"
        assert gunicorn_config["workers"] == 2
        assert (
            gunicorn_config["worker_class"]
            == "gunicorn_prometheus_exporter.plugin.PrometheusWorker"
        )
        assert gunicorn_config["loglevel"] == "info"

    def test_prometheus_config(self):
        """Test that prometheus config is generated correctly."""
        config = ExporterConfig()
        prometheus_config = config.get_prometheus_config()

        assert prometheus_config["bind_address"] == "127.0.0.1"
        assert prometheus_config["port"] == 9091
        assert prometheus_config["multiproc_dir"] == "/tmp/prometheus"

    def test_validation(self):
        """Test configuration validation."""
        config = ExporterConfig()
        assert config.validate() is True

    def test_validation_invalid_port(self):
        """Test validation with invalid port."""
        os.environ["PROMETHEUS_METRICS_PORT"] = "99999"  # Invalid port
        config = ExporterConfig()
        assert config.validate() is False
        del os.environ["PROMETHEUS_METRICS_PORT"]

    def test_validation_invalid_workers(self):
        """Test validation with invalid worker count."""
        os.environ["GUNICORN_WORKERS"] = "0"  # Invalid worker count
        config = ExporterConfig()
        assert config.validate() is False
        del os.environ["GUNICORN_WORKERS"]


class TestConfigFunctions:
    """Test configuration utility functions."""

    def test_get_config(self):
        """Test get_config function."""
        config_instance = get_config()
        assert isinstance(config_instance, ExporterConfig)

    def test_config_singleton(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

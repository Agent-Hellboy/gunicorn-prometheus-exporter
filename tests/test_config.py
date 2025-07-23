"""Tests for the configuration system."""

import os
import tempfile

import pytest

from gunicorn_prometheus_exporter.config import ExporterConfig, get_config


class TestExporterConfig:
    """Test the ExporterConfig class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        # Save original environment
        original_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
        original_bind_address = os.environ.get("PROMETHEUS_BIND_ADDRESS")
        original_metrics_port = os.environ.get("PROMETHEUS_METRICS_PORT")
        original_workers = os.environ.get("GUNICORN_WORKERS")

        # Clear environment to test defaults
        if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
            del os.environ["PROMETHEUS_MULTIPROC_DIR"]
        if "PROMETHEUS_BIND_ADDRESS" in os.environ:
            del os.environ["PROMETHEUS_BIND_ADDRESS"]
        if "PROMETHEUS_METRICS_PORT" in os.environ:
            del os.environ["PROMETHEUS_METRICS_PORT"]
        if "GUNICORN_WORKERS" in os.environ:
            del os.environ["GUNICORN_WORKERS"]

        config = ExporterConfig()

        assert config.prometheus_multiproc_dir == "/tmp/prometheus"
        # These should raise ValueError when not set
        with pytest.raises(ValueError):
            _ = config.prometheus_metrics_port
        with pytest.raises(ValueError):
            _ = config.prometheus_bind_address
        with pytest.raises(ValueError):
            _ = config.gunicorn_workers
        assert config.gunicorn_timeout == 30
        assert config.gunicorn_keepalive == 2

        # Restore original environment
        if original_multiproc_dir:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = original_multiproc_dir
        if original_bind_address:
            os.environ["PROMETHEUS_BIND_ADDRESS"] = original_bind_address
        if original_metrics_port:
            os.environ["PROMETHEUS_METRICS_PORT"] = original_metrics_port
        if original_workers:
            os.environ["GUNICORN_WORKERS"] = original_workers

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
        # Set required environment variables for this test
        os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"
        os.environ["PROMETHEUS_METRICS_PORT"] = "9091"
        os.environ["GUNICORN_WORKERS"] = "2"

        config = ExporterConfig()
        gunicorn_config = config.get_gunicorn_config()

        assert gunicorn_config["workers"] == 2
        assert (
            gunicorn_config["worker_class"]
            == "gunicorn_prometheus_exporter.plugin.PrometheusWorker"
        )
        assert gunicorn_config["loglevel"] == "info"

    def test_prometheus_config(self):
        """Test that prometheus config is generated correctly."""
        # Set required environment variables for this test
        os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"
        os.environ["PROMETHEUS_METRICS_PORT"] = "9091"
        os.environ["GUNICORN_WORKERS"] = "2"

        config = ExporterConfig()
        prometheus_config = config.get_prometheus_config()

        assert prometheus_config["bind_address"] == "127.0.0.1"
        assert prometheus_config["port"] == 9091
        assert prometheus_config["multiproc_dir"] == "/tmp/prometheus"

    def test_validation(self):
        """Test configuration validation."""
        # Set required environment variables for this test
        os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"
        os.environ["PROMETHEUS_METRICS_PORT"] = "9091"
        os.environ["GUNICORN_WORKERS"] = "2"

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

    def test_validation_missing_required_vars(self):
        """Test validation with missing required environment variables."""
        # Save original environment
        original_bind_address = os.environ.get("PROMETHEUS_BIND_ADDRESS")
        original_metrics_port = os.environ.get("PROMETHEUS_METRICS_PORT")
        original_workers = os.environ.get("GUNICORN_WORKERS")

        # Remove required variables
        if "PROMETHEUS_BIND_ADDRESS" in os.environ:
            del os.environ["PROMETHEUS_BIND_ADDRESS"]
        if "PROMETHEUS_METRICS_PORT" in os.environ:
            del os.environ["PROMETHEUS_METRICS_PORT"]
        if "GUNICORN_WORKERS" in os.environ:
            del os.environ["GUNICORN_WORKERS"]

        config = ExporterConfig()
        assert config.validate() is False

        # Restore original environment
        if original_bind_address:
            os.environ["PROMETHEUS_BIND_ADDRESS"] = original_bind_address
        if original_metrics_port:
            os.environ["PROMETHEUS_METRICS_PORT"] = original_metrics_port
        if original_workers:
            os.environ["GUNICORN_WORKERS"] = original_workers


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

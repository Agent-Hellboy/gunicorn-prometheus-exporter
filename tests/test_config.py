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

        expected_default = os.path.join(os.path.expanduser("~"), ".gunicorn_prometheus")
        assert config.prometheus_multiproc_dir == expected_default
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
        # Save original environment variables
        original_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
        original_metrics_port = os.environ.get("PROMETHEUS_METRICS_PORT")
        original_workers = os.environ.get("GUNICORN_WORKERS")

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.environ["PROMETHEUS_MULTIPROC_DIR"] = temp_dir
                os.environ["PROMETHEUS_METRICS_PORT"] = "9092"
                os.environ["GUNICORN_WORKERS"] = "4"

                config = ExporterConfig()

                assert config.prometheus_multiproc_dir == temp_dir
                assert config.prometheus_metrics_port == 9092
                assert config.gunicorn_workers == 4
        finally:
            # Restore original environment
            if original_multiproc_dir:
                os.environ["PROMETHEUS_MULTIPROC_DIR"] = original_multiproc_dir
            elif "PROMETHEUS_MULTIPROC_DIR" in os.environ:
                del os.environ["PROMETHEUS_MULTIPROC_DIR"]

            if original_metrics_port:
                os.environ["PROMETHEUS_METRICS_PORT"] = original_metrics_port
            elif "PROMETHEUS_METRICS_PORT" in os.environ:
                del os.environ["PROMETHEUS_METRICS_PORT"]

            if original_workers:
                os.environ["GUNICORN_WORKERS"] = original_workers
            elif "GUNICORN_WORKERS" in os.environ:
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
        # Save original environment variables
        original_bind_address = os.environ.get("PROMETHEUS_BIND_ADDRESS")
        original_metrics_port = os.environ.get("PROMETHEUS_METRICS_PORT")
        original_workers = os.environ.get("GUNICORN_WORKERS")
        original_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")

        try:
            # Set required environment variables for this test
            os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"
            os.environ["PROMETHEUS_METRICS_PORT"] = "9091"
            os.environ["GUNICORN_WORKERS"] = "2"
            # Clear multiprocess dir to test default behavior
            if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
                del os.environ["PROMETHEUS_MULTIPROC_DIR"]

            config = ExporterConfig()
            prometheus_config = config.get_prometheus_config()

            assert prometheus_config["bind_address"] == "127.0.0.1"
            assert prometheus_config["port"] == 9091
            expected_default = os.path.join(
                os.path.expanduser("~"), ".gunicorn_prometheus"
            )
            assert prometheus_config["multiproc_dir"] == expected_default
        finally:
            # Restore original environment
            if original_bind_address:
                os.environ["PROMETHEUS_BIND_ADDRESS"] = original_bind_address
            if original_metrics_port:
                os.environ["PROMETHEUS_METRICS_PORT"] = original_metrics_port
            if original_workers:
                os.environ["GUNICORN_WORKERS"] = original_workers
            if original_multiproc_dir:
                os.environ["PROMETHEUS_MULTIPROC_DIR"] = original_multiproc_dir

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
        # Save original environment variable
        original_metrics_port = os.environ.get("PROMETHEUS_METRICS_PORT")

        try:
            os.environ["PROMETHEUS_METRICS_PORT"] = "99999"  # Invalid port
            config = ExporterConfig()
            assert config.validate() is False
        finally:
            # Restore original environment
            if original_metrics_port:
                os.environ["PROMETHEUS_METRICS_PORT"] = original_metrics_port
            elif "PROMETHEUS_METRICS_PORT" in os.environ:
                del os.environ["PROMETHEUS_METRICS_PORT"]

    def test_validation_invalid_workers(self):
        """Test validation with invalid worker count."""
        # Save original environment variable
        original_workers = os.environ.get("GUNICORN_WORKERS")

        try:
            os.environ["GUNICORN_WORKERS"] = "0"  # Invalid worker count
            config = ExporterConfig()
            assert config.validate() is False
        finally:
            # Restore original environment
            if original_workers:
                os.environ["GUNICORN_WORKERS"] = original_workers
            elif "GUNICORN_WORKERS" in os.environ:
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

    def test_print_config(self, caplog):
        """Test that print_config logs configuration information."""
        # Set required environment variables
        os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"
        os.environ["PROMETHEUS_METRICS_PORT"] = "9091"
        os.environ["GUNICORN_WORKERS"] = "2"

        config = ExporterConfig()
        config.print_config()

        # Check that configuration was logged
        assert "Gunicorn Prometheus Exporter Configuration:" in caplog.text
        assert "Prometheus Metrics Port: 9091" in caplog.text
        assert "Gunicorn Workers: 2" in caplog.text

    def test_validation_timeout_error(self):
        """Test validation with invalid timeout."""
        # Save original environment variables
        original_bind_address = os.environ.get("PROMETHEUS_BIND_ADDRESS")
        original_metrics_port = os.environ.get("PROMETHEUS_METRICS_PORT")
        original_workers = os.environ.get("GUNICORN_WORKERS")
        original_timeout = os.environ.get("GUNICORN_TIMEOUT")

        try:
            # Set required variables
            os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"
            os.environ["PROMETHEUS_METRICS_PORT"] = "9091"
            os.environ["GUNICORN_WORKERS"] = "2"
            os.environ["GUNICORN_TIMEOUT"] = "0"  # Invalid timeout

            config = ExporterConfig()
            assert config.validate() is False
        finally:
            # Restore original environment
            if original_bind_address:
                os.environ["PROMETHEUS_BIND_ADDRESS"] = original_bind_address
            if original_metrics_port:
                os.environ["PROMETHEUS_METRICS_PORT"] = original_metrics_port
            if original_workers:
                os.environ["GUNICORN_WORKERS"] = original_workers
            if original_timeout:
                os.environ["GUNICORN_TIMEOUT"] = original_timeout
            elif "GUNICORN_TIMEOUT" in os.environ:
                del os.environ["GUNICORN_TIMEOUT"]

    def test_validation_exception_handling(self, monkeypatch):
        """Test validation handles exceptions gracefully."""
        # Save original environment variables
        original_bind_address = os.environ.get("PROMETHEUS_BIND_ADDRESS")
        original_metrics_port = os.environ.get("PROMETHEUS_METRICS_PORT")
        original_workers = os.environ.get("GUNICORN_WORKERS")

        try:
            # Set required variables
            os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"
            os.environ["PROMETHEUS_METRICS_PORT"] = "9091"
            os.environ["GUNICORN_WORKERS"] = "2"

            # Mock os.path.exists to raise an exception
            def mock_exists(path):
                raise OSError("Mock error")

            monkeypatch.setattr("os.path.exists", mock_exists)

            config = ExporterConfig()
            assert config.validate() is False
        finally:
            # Restore original environment
            if original_bind_address:
                os.environ["PROMETHEUS_BIND_ADDRESS"] = original_bind_address
            if original_metrics_port:
                os.environ["PROMETHEUS_METRICS_PORT"] = original_metrics_port
            if original_workers:
                os.environ["GUNICORN_WORKERS"] = original_workers

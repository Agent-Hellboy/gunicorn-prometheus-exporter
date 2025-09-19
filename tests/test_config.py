"""Tests for the configuration system."""

import os
import shutil
import tempfile

from unittest.mock import patch

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


class TestExporterConfigAdditional:
    """Additional tests for the ExporterConfig class to improve coverage."""

    def test_ssl_configuration_properties(self):
        """Test SSL configuration properties."""
        # Save original environment
        original_certfile = os.environ.get("PROMETHEUS_SSL_CERTFILE")
        original_keyfile = os.environ.get("PROMETHEUS_SSL_KEYFILE")
        original_client_cafile = os.environ.get("PROMETHEUS_SSL_CLIENT_CAFILE")
        original_client_capath = os.environ.get("PROMETHEUS_SSL_CLIENT_CAPATH")
        original_client_auth = os.environ.get("PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED")

        try:
            # Test SSL certificate file
            os.environ["PROMETHEUS_SSL_CERTFILE"] = "/path/to/cert.pem"
            config = ExporterConfig()
            assert config.prometheus_ssl_certfile == "/path/to/cert.pem"

            # Test SSL key file
            os.environ["PROMETHEUS_SSL_KEYFILE"] = "/path/to/key.pem"
            config = ExporterConfig()
            assert config.prometheus_ssl_keyfile == "/path/to/key.pem"

            # Test SSL client CA file
            os.environ["PROMETHEUS_SSL_CLIENT_CAFILE"] = "/path/to/ca.pem"
            config = ExporterConfig()
            assert config.prometheus_ssl_client_cafile == "/path/to/ca.pem"

            # Test SSL client CA path
            os.environ["PROMETHEUS_SSL_CLIENT_CAPATH"] = "/path/to/ca/dir"
            config = ExporterConfig()
            assert config.prometheus_ssl_client_capath == "/path/to/ca/dir"

            # Test SSL client auth required
            os.environ["PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED"] = "true"
            config = ExporterConfig()
            assert config.prometheus_ssl_client_auth_required is True

            os.environ["PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED"] = "false"
            config = ExporterConfig()
            assert config.prometheus_ssl_client_auth_required is False

            # Test SSL enabled property
            os.environ["PROMETHEUS_SSL_CERTFILE"] = "/path/to/cert.pem"
            os.environ["PROMETHEUS_SSL_KEYFILE"] = "/path/to/key.pem"
            config = ExporterConfig()
            assert config.prometheus_ssl_enabled is True

            # Test SSL disabled when only certfile is set
            del os.environ["PROMETHEUS_SSL_KEYFILE"]
            config = ExporterConfig()
            assert config.prometheus_ssl_enabled is False

        finally:
            # Restore original environment
            if original_certfile:
                os.environ["PROMETHEUS_SSL_CERTFILE"] = original_certfile
            elif "PROMETHEUS_SSL_CERTFILE" in os.environ:
                del os.environ["PROMETHEUS_SSL_CERTFILE"]

            if original_keyfile:
                os.environ["PROMETHEUS_SSL_KEYFILE"] = original_keyfile
            elif "PROMETHEUS_SSL_KEYFILE" in os.environ:
                del os.environ["PROMETHEUS_SSL_KEYFILE"]

            if original_client_cafile:
                os.environ["PROMETHEUS_SSL_CLIENT_CAFILE"] = original_client_cafile
            elif "PROMETHEUS_SSL_CLIENT_CAFILE" in os.environ:
                del os.environ["PROMETHEUS_SSL_CLIENT_CAFILE"]

            if original_client_capath:
                os.environ["PROMETHEUS_SSL_CLIENT_CAPATH"] = original_client_capath
            elif "PROMETHEUS_SSL_CLIENT_CAPATH" in os.environ:
                del os.environ["PROMETHEUS_SSL_CLIENT_CAPATH"]

            if original_client_auth:
                os.environ["PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED"] = original_client_auth
            elif "PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED" in os.environ:
                del os.environ["PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED"]


class TestConfigEdgeCases:
    """Test edge cases and error conditions in configuration."""

    def test_invalid_redis_ttl_values(self):
        """Test handling of invalid Redis TTL values."""
        test_cases = [
            ("-1", "Negative TTL should be handled"),
            ("0", "Zero TTL should be handled"),
            ("invalid", "Non-numeric TTL should be handled"),
            ("", "Empty TTL should be handled"),
            ("999999999", "Very large TTL should be handled"),
        ]

        for ttl_value, description in test_cases:
            with patch.dict(os.environ, {"REDIS_TTL_SECONDS": ttl_value}):
                try:
                    config = ExporterConfig()
                    # Should handle invalid TTL gracefully
                    assert isinstance(
                        config.redis_ttl_seconds, int
                    ), f"{description}: {ttl_value}"
                except ValueError:
                    # If ValueError is raised, that's also acceptable behavior
                    pass

    def test_invalid_port_values(self):
        """Test handling of invalid port values."""
        # Test negative port - should fail validation
        with patch.dict(os.environ, {"PROMETHEUS_METRICS_PORT": "-1"}):
            config = ExporterConfig()
            assert config.validate() is False

        # Test port 0 - should fail validation
        with patch.dict(os.environ, {"PROMETHEUS_METRICS_PORT": "0"}):
            config = ExporterConfig()
            assert config.validate() is False

        # Test port too large - should fail validation
        with patch.dict(os.environ, {"PROMETHEUS_METRICS_PORT": "65536"}):
            config = ExporterConfig()
            assert config.validate() is False

        # Test non-numeric port - should raise ValueError when accessing property
        with patch.dict(os.environ, {"PROMETHEUS_METRICS_PORT": "invalid"}):
            config = ExporterConfig()
            with pytest.raises(ValueError):
                _ = config.prometheus_metrics_port

        # Test empty port - should raise ValueError when accessing property
        with patch.dict(os.environ, {"PROMETHEUS_METRICS_PORT": ""}):
            config = ExporterConfig()
            with pytest.raises(ValueError):
                _ = config.prometheus_metrics_port

    def test_invalid_worker_count_values(self):
        """Test handling of invalid worker count values."""
        test_cases = [
            ("-1", "Negative worker count should be handled"),
            ("0", "Zero worker count should be handled"),
            ("invalid", "Non-numeric worker count should be handled"),
            ("", "Empty worker count should be handled"),
            ("999999", "Very large worker count should be handled"),
        ]

        for worker_value, description in test_cases:
            with patch.dict(os.environ, {"GUNICORN_WORKERS": worker_value}):
                try:
                    config = ExporterConfig()
                    # Should handle invalid worker count gracefully
                    assert isinstance(
                        config.gunicorn_workers, int
                    ), f"{description}: {worker_value}"
                except ValueError:
                    # If ValueError is raised, that's also acceptable behavior
                    pass

    def test_invalid_timeout_values(self):
        """Test handling of invalid timeout values."""
        # Test negative timeout - should fail validation
        with patch.dict(os.environ, {"GUNICORN_TIMEOUT": "-1"}):
            config = ExporterConfig()
            assert config.validate() is False

        # Test zero timeout - should fail validation
        with patch.dict(os.environ, {"GUNICORN_TIMEOUT": "0"}):
            config = ExporterConfig()
            assert config.validate() is False

        # Test non-numeric timeout - should raise ValueError when accessing property
        with patch.dict(os.environ, {"GUNICORN_TIMEOUT": "invalid"}):
            config = ExporterConfig()
            with pytest.raises(ValueError):
                _ = config.gunicorn_timeout

        # Test empty timeout - should raise ValueError when accessing property
        with patch.dict(os.environ, {"GUNICORN_TIMEOUT": ""}):
            config = ExporterConfig()
            with pytest.raises(ValueError):
                _ = config.gunicorn_timeout

        # Test very large timeout - should pass validation (no upper limit)
        with patch.dict(os.environ, {"GUNICORN_TIMEOUT": "999999"}):
            config = ExporterConfig()
            # Should not raise ValueError - large timeouts are allowed
            assert config.gunicorn_timeout == 999999

    def test_invalid_keepalive_values(self):
        """Test handling of invalid keepalive values."""
        # Test negative keepalive - should pass (no validation)
        with patch.dict(os.environ, {"GUNICORN_KEEPALIVE": "-1"}):
            config = ExporterConfig()
            assert config.gunicorn_keepalive == -1

        # Test zero keepalive - should pass (no validation)
        with patch.dict(os.environ, {"GUNICORN_KEEPALIVE": "0"}):
            config = ExporterConfig()
            assert config.gunicorn_keepalive == 0

        # Test non-numeric keepalive - should raise ValueError when accessing property
        with patch.dict(os.environ, {"GUNICORN_KEEPALIVE": "invalid"}):
            config = ExporterConfig()
            with pytest.raises(ValueError):
                _ = config.gunicorn_keepalive

        # Test empty keepalive - should raise ValueError when accessing property
        with patch.dict(os.environ, {"GUNICORN_KEEPALIVE": ""}):
            config = ExporterConfig()
            with pytest.raises(ValueError):
                _ = config.gunicorn_keepalive

        # Test very large keepalive - should pass (no upper limit)
        with patch.dict(os.environ, {"GUNICORN_KEEPALIVE": "999999"}):
            config = ExporterConfig()
            assert config.gunicorn_keepalive == 999999

    def test_invalid_redis_db_values(self):
        """Test handling of invalid Redis DB values."""
        # Test negative DB - should pass (no validation)
        with patch.dict(os.environ, {"REDIS_DB": "-1"}):
            config = ExporterConfig()
            assert config.redis_db == -1

        # Test non-numeric DB - should raise ValueError when accessing property
        with patch.dict(os.environ, {"REDIS_DB": "invalid"}):
            config = ExporterConfig()
            with pytest.raises(ValueError):
                _ = config.redis_db

        # Test empty DB - should raise ValueError when accessing property
        with patch.dict(os.environ, {"REDIS_DB": ""}):
            config = ExporterConfig()
            with pytest.raises(ValueError):
                _ = config.redis_db

        # Test very large DB - should pass (no upper limit)
        with patch.dict(os.environ, {"REDIS_DB": "999999"}):
            config = ExporterConfig()
            assert config.redis_db == 999999

    def test_invalid_redis_port_values(self):
        """Test handling of invalid Redis port values."""
        # Test negative Redis port - should pass (no validation)
        with patch.dict(os.environ, {"REDIS_PORT": "-1"}):
            config = ExporterConfig()
            assert config.redis_port == -1

        # Test zero Redis port - should pass (no validation)
        with patch.dict(os.environ, {"REDIS_PORT": "0"}):
            config = ExporterConfig()
            assert config.redis_port == 0

        # Test Redis port too large - should pass (no validation)
        with patch.dict(os.environ, {"REDIS_PORT": "65536"}):
            config = ExporterConfig()
            assert config.redis_port == 65536

        # Test non-numeric Redis port - should raise ValueError when accessing property
        with patch.dict(os.environ, {"REDIS_PORT": "invalid"}):
            config = ExporterConfig()
            with pytest.raises(ValueError):
                _ = config.redis_port

        # Test empty Redis port - should raise ValueError when accessing property
        with patch.dict(os.environ, {"REDIS_PORT": ""}):
            config = ExporterConfig()
            with pytest.raises(ValueError):
                _ = config.redis_port

    def test_malformed_bind_address(self):
        """Test handling of malformed bind addresses."""
        test_cases = [
            ("invalid_address", "Invalid address format should be handled"),
            ("", "Empty address should be handled"),
            ("999.999.999.999", "Invalid IP should be handled"),
            ("localhost:invalid_port", "Invalid port in address should be handled"),
            ("[::1]:invalid_port", "Invalid port in IPv6 address should be handled"),
        ]

        for address_value, description in test_cases:
            with patch.dict(os.environ, {"PROMETHEUS_BIND_ADDRESS": address_value}):
                config = ExporterConfig()
                # Should handle malformed address gracefully
                assert isinstance(
                    config.prometheus_bind_address, str
                ), f"{description}: {address_value}"

    def test_malformed_redis_host(self):
        """Test handling of malformed Redis host."""
        test_cases = [
            ("", "Empty Redis host should be handled"),
            (
                "invalid_host:invalid_port",
                "Invalid Redis host format should be handled",
            ),
            ("999.999.999.999", "Invalid Redis IP should be handled"),
        ]

        for host_value, description in test_cases:
            with patch.dict(os.environ, {"REDIS_HOST": host_value}):
                config = ExporterConfig()
                # Should handle malformed Redis host gracefully
                assert isinstance(
                    config.redis_host, str
                ), f"{description}: {host_value}"

    def test_boolean_parsing_edge_cases(self):
        """Test handling of edge cases in boolean parsing."""
        test_cases = [
            ("true", True),
            ("false", False),
            ("True", True),
            ("False", False),
            ("TRUE", True),
            ("FALSE", False),
            ("1", True),
            ("0", False),
            ("yes", True),
            ("no", False),
            ("on", True),
            ("off", False),
            ("invalid", False),  # Default to False for invalid values
            ("", False),  # Default to False for empty values
        ]

        for value, expected in test_cases:
            with patch.dict(os.environ, {"REDIS_ENABLED": value}):
                config = ExporterConfig()
                assert (
                    config.redis_enabled == expected
                ), f"Boolean parsing failed for: {value}"

    def test_config_validation_with_invalid_values(self):
        """Test configuration validation with various invalid values."""
        # Test with multiple invalid values at once
        with patch.dict(
            os.environ,
            {
                "PROMETHEUS_METRICS_PORT": "invalid",
                "GUNICORN_WORKERS": "-1",
                "REDIS_TTL_SECONDS": "invalid",
                "PROMETHEUS_BIND_ADDRESS": "invalid_address",
            },
        ):
            try:
                config = ExporterConfig()
                # Should handle multiple invalid values gracefully
                assert isinstance(config.prometheus_metrics_port, int)
                assert isinstance(config.gunicorn_workers, int)
                assert isinstance(config.redis_ttl_seconds, int)
                assert isinstance(config.prometheus_bind_address, str)
            except ValueError:
                # If ValueError is raised, that's also acceptable behavior
                pass

    def test_config_with_mixed_valid_invalid_values(self):
        """Test configuration with mix of valid and invalid values."""
        with patch.dict(
            os.environ,
            {
                "PROMETHEUS_METRICS_PORT": "9090",  # Valid
                "GUNICORN_WORKERS": "invalid",  # Invalid
                "REDIS_TTL_SECONDS": "30",  # Valid
                "PROMETHEUS_BIND_ADDRESS": "0.0.0.0",  # Valid
            },
        ):
            try:
                config = ExporterConfig()
                # Should handle mixed values gracefully
                assert config.prometheus_metrics_port == 9090
                assert isinstance(
                    config.gunicorn_workers, int
                )  # Should fallback to default
                assert config.redis_ttl_seconds == 30
                assert config.prometheus_bind_address == "0.0.0.0"
            except ValueError:
                # If ValueError is raised, that's also acceptable behavior
                pass

    def test_redis_enabled_property(self):
        """Test Redis enabled property."""
        # Save original environment
        original_redis_enabled = os.environ.get("REDIS_ENABLED")

        try:
            # Test various truthy values
            for value in ["true", "1", "yes", "on"]:
                os.environ["REDIS_ENABLED"] = value
                config = ExporterConfig()
                assert config.redis_enabled is True

            # Test various falsy values
            for value in ["false", "0", "no", "off", ""]:
                os.environ["REDIS_ENABLED"] = value
                config = ExporterConfig()
                assert config.redis_enabled is False

            # Test when not set
            if "REDIS_ENABLED" in os.environ:
                del os.environ["REDIS_ENABLED"]
            config = ExporterConfig()
            assert config.redis_enabled is False

        finally:
            # Restore original environment
            if original_redis_enabled:
                os.environ["REDIS_ENABLED"] = original_redis_enabled
            elif "REDIS_ENABLED" in os.environ:
                del os.environ["REDIS_ENABLED"]

    def test_redis_configuration_properties(self):
        """Test Redis configuration properties."""
        # Save original environment
        original_env = {
            "REDIS_HOST": os.environ.get("REDIS_HOST"),
            "REDIS_PORT": os.environ.get("REDIS_PORT"),
            "REDIS_DB": os.environ.get("REDIS_DB"),
            "REDIS_PASSWORD": os.environ.get("REDIS_PASSWORD"),
            "REDIS_KEY_PREFIX": os.environ.get("REDIS_KEY_PREFIX"),
        }

        try:
            # Test REDIS_HOST
            os.environ["REDIS_HOST"] = "test-host"
            config = ExporterConfig()
            assert config.redis_host == "test-host"

            # Test REDIS_HOST default
            del os.environ["REDIS_HOST"]
            config = ExporterConfig()
            assert config.redis_host == "127.0.0.1"

            # Test REDIS_PORT
            os.environ["REDIS_PORT"] = "6380"
            config = ExporterConfig()
            assert config.redis_port == 6380

            # Test REDIS_PORT default
            del os.environ["REDIS_PORT"]
            config = ExporterConfig()
            assert config.redis_port == 6379

            # Test REDIS_DB
            os.environ["REDIS_DB"] = "1"
            config = ExporterConfig()
            assert config.redis_db == 1

            # Test REDIS_DB default
            del os.environ["REDIS_DB"]
            config = ExporterConfig()
            assert config.redis_db == 0

            # Test REDIS_PASSWORD
            os.environ["REDIS_PASSWORD"] = "test-password"
            config = ExporterConfig()
            assert config.redis_password == "test-password"

            # Test REDIS_PASSWORD default (None)
            del os.environ["REDIS_PASSWORD"]
            config = ExporterConfig()
            assert config.redis_password is None

            # Test REDIS_KEY_PREFIX
            os.environ["REDIS_KEY_PREFIX"] = "custom:prefix:"
            config = ExporterConfig()
            assert config.redis_key_prefix == "custom:prefix:"

            # Test REDIS_KEY_PREFIX default
            del os.environ["REDIS_KEY_PREFIX"]
            config = ExporterConfig()
            assert config.redis_key_prefix == "gunicorn"

        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]

    def test_validation_creates_multiproc_dir(self):
        """Test that validation creates multiprocess directory if it doesn't exist."""
        # Save original environment
        original_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")

        try:
            # Create a temporary directory and remove it
            temp_dir = tempfile.mkdtemp()
            shutil.rmtree(temp_dir)

            # Set the multiproc dir to the non-existent directory
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = temp_dir
            os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"
            os.environ["PROMETHEUS_METRICS_PORT"] = "9091"
            os.environ["GUNICORN_WORKERS"] = "2"

            config = ExporterConfig()
            result = config.validate()

            # Directory should be created and validation should succeed
            assert result is True
            assert os.path.exists(temp_dir)

            # Clean up
            shutil.rmtree(temp_dir)

        finally:
            # Restore original environment
            if original_multiproc_dir:
                os.environ["PROMETHEUS_MULTIPROC_DIR"] = original_multiproc_dir
            elif "PROMETHEUS_MULTIPROC_DIR" in os.environ:
                del os.environ["PROMETHEUS_MULTIPROC_DIR"]

"""Tests for main module initialization."""

import logging

from unittest.mock import Mock, patch

import gunicorn_prometheus_exporter


class TestModuleInitialization:
    """Test module initialization and patching."""

    def test_module_imports(self):
        """Test that module imports work correctly."""
        # Test that the module can be imported
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusMaster")
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusWorker")
        assert hasattr(gunicorn_prometheus_exporter, "registry")
        assert hasattr(gunicorn_prometheus_exporter, "config")

    def test_version(self):
        """Test module version."""
        assert hasattr(gunicorn_prometheus_exporter, "__version__")
        assert gunicorn_prometheus_exporter.__version__ == "0.1.0"

    def test_all_exports(self):
        """Test __all__ exports."""
        expected_exports = [
            "PrometheusWorker",
            "PrometheusThreadWorker",
            "PrometheusMaster",
            "registry",
            "config",
            "get_config",
            "get_forwarder_manager",
            "RedisForwarder",
            "start_redis_forwarder",
            "get_prometheus_eventlet_worker",
            "get_prometheus_gevent_worker",
            "get_prometheus_tornado_worker",
        ]

        for export in expected_exports:
            assert export in gunicorn_prometheus_exporter.__all__
            assert hasattr(gunicorn_prometheus_exporter, export)

    def test_eventlet_availability(self):
        """Test Eventlet availability detection."""
        # Test that EVENTLET_AVAILABLE is defined
        assert hasattr(gunicorn_prometheus_exporter, "EVENTLET_AVAILABLE")

        # Test that PrometheusEventletWorker is available if EVENTLET_AVAILABLE is True
        if gunicorn_prometheus_exporter.EVENTLET_AVAILABLE:
            assert hasattr(gunicorn_prometheus_exporter, "PrometheusEventletWorker")
            assert "PrometheusEventletWorker" in gunicorn_prometheus_exporter.__all__
        else:
            assert gunicorn_prometheus_exporter.PrometheusEventletWorker is None

    def test_gevent_availability(self):
        """Test Gevent availability detection."""
        # Test that GEVENT_AVAILABLE is defined
        assert hasattr(gunicorn_prometheus_exporter, "GEVENT_AVAILABLE")

        # Test that PrometheusGeventWorker is available if GEVENT_AVAILABLE is True
        if gunicorn_prometheus_exporter.GEVENT_AVAILABLE:
            assert hasattr(gunicorn_prometheus_exporter, "PrometheusGeventWorker")
            assert "PrometheusGeventWorker" in gunicorn_prometheus_exporter.__all__
        else:
            assert gunicorn_prometheus_exporter.PrometheusGeventWorker is None

    def test_tornado_availability(self):
        """Test Tornado availability detection."""
        # Test that TORNADO_AVAILABLE is defined
        assert hasattr(gunicorn_prometheus_exporter, "TORNADO_AVAILABLE")

        # Test that PrometheusTornadoWorker is available if TORNADO_AVAILABLE is True
        if gunicorn_prometheus_exporter.TORNADO_AVAILABLE:
            assert hasattr(gunicorn_prometheus_exporter, "PrometheusTornadoWorker")
            assert "PrometheusTornadoWorker" in gunicorn_prometheus_exporter.__all__
        else:
            assert gunicorn_prometheus_exporter.PrometheusTornadoWorker is None

    def test_gunicorn_patching(self):
        """Test that Gunicorn classes are properly patched."""
        import gunicorn.app.base
        import gunicorn.arbiter

        # Test that Arbiter is replaced with PrometheusMaster
        assert gunicorn.arbiter.Arbiter is gunicorn_prometheus_exporter.PrometheusMaster
        assert (
            gunicorn.app.base.Arbiter is gunicorn_prometheus_exporter.PrometheusMaster
        )

        # Test that BaseApplication.run is patched
        assert gunicorn.app.base.BaseApplication.run is not None
        assert hasattr(gunicorn.app.base.BaseApplication.run, "__name__")

    def test_patched_run_function(self):
        """Test the patched run function."""
        import gunicorn.app.base

        # Test that the patched function exists and is callable
        assert hasattr(gunicorn.app.base.BaseApplication, "run")
        assert callable(gunicorn.app.base.BaseApplication.run)

        # Test that it's our patched version by checking the function name
        assert gunicorn.app.base.BaseApplication.run.__name__ == "patched_run"


class TestRedisForwarderStartup:
    """Test Redis forwarder startup functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Reset any existing state
        pass

    def test_start_redis_forwarder_disabled(self):
        """Test start_redis_forwarder when Redis is disabled."""
        with patch("gunicorn_prometheus_exporter.config") as mock_config:
            mock_config.redis_enabled = False

            result = gunicorn_prometheus_exporter.start_redis_forwarder()
            assert result is False

    def test_start_redis_forwarder_success(self):
        """Test successful Redis forwarder startup."""
        with (
            patch("gunicorn_prometheus_exporter.config") as mock_config,
            patch(
                "gunicorn_prometheus_exporter.get_forwarder_manager"
            ) as mock_get_manager,
            patch(
                "gunicorn_prometheus_exporter.RedisForwarder"
            ) as mock_redis_forwarder_class,
            patch("gunicorn_prometheus_exporter.logger") as mock_logger,
        ):
            # Configure mocks
            mock_config.redis_enabled = True
            mock_config.redis_forward_interval = 30

            mock_manager = Mock()
            mock_manager.start_forwarder.return_value = True
            mock_get_manager.return_value = mock_manager

            mock_forwarder = Mock()
            mock_redis_forwarder_class.return_value = mock_forwarder

            result = gunicorn_prometheus_exporter.start_redis_forwarder()

            assert result is True
            mock_manager.add_forwarder.assert_called_once_with("redis", mock_forwarder)
            mock_manager.start_forwarder.assert_called_once_with("redis")
            mock_logger.info.assert_called_once_with(
                "Redis forwarder started (interval: %ss)", 30
            )

    def test_start_redis_forwarder_start_failure(self):
        """Test Redis forwarder startup failure."""
        with (
            patch("gunicorn_prometheus_exporter.config") as mock_config,
            patch(
                "gunicorn_prometheus_exporter.get_forwarder_manager"
            ) as mock_get_manager,
            patch(
                "gunicorn_prometheus_exporter.RedisForwarder"
            ) as mock_redis_forwarder_class,
            patch("gunicorn_prometheus_exporter.logger") as mock_logger,
        ):
            # Configure mocks
            mock_config.redis_enabled = True
            mock_config.redis_forward_interval = 30

            mock_manager = Mock()
            mock_manager.start_forwarder.return_value = False
            mock_get_manager.return_value = mock_manager

            mock_forwarder = Mock()
            mock_redis_forwarder_class.return_value = mock_forwarder

            result = gunicorn_prometheus_exporter.start_redis_forwarder()

            assert result is False
            mock_logger.error.assert_called_once_with("Failed to start Redis forwarder")

    def test_start_redis_forwarder_exception(self):
        """Test Redis forwarder startup with exception."""
        with (
            patch("gunicorn_prometheus_exporter.config") as mock_config,
            patch(
                "gunicorn_prometheus_exporter.get_forwarder_manager",
                side_effect=Exception("Manager error"),
            ),
            patch("gunicorn_prometheus_exporter.logger") as mock_logger,
        ):
            # Configure mocks
            mock_config.redis_enabled = True

            result = gunicorn_prometheus_exporter.start_redis_forwarder()

            assert result is False
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "Failed to start Redis forwarder: %s"
            assert str(call_args[0][1]) == "Manager error"

    def test_start_redis_forwarder_manager_exception(self):
        """Test Redis forwarder startup with manager exception."""
        with (
            patch("gunicorn_prometheus_exporter.config") as mock_config,
            patch(
                "gunicorn_prometheus_exporter.get_forwarder_manager"
            ) as mock_get_manager,
            patch(
                "gunicorn_prometheus_exporter.RedisForwarder"
            ) as mock_redis_forwarder_class,
            patch("gunicorn_prometheus_exporter.logger") as mock_logger,
        ):
            # Configure mocks
            mock_config.redis_enabled = True

            mock_manager = Mock()
            mock_manager.add_forwarder.side_effect = Exception("Add forwarder error")
            mock_get_manager.return_value = mock_manager

            mock_forwarder = Mock()
            mock_redis_forwarder_class.return_value = mock_forwarder

            result = gunicorn_prometheus_exporter.start_redis_forwarder()

            assert result is False
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "Failed to start Redis forwarder: %s"
            assert str(call_args[0][1]) == "Add forwarder error"


class TestImportErrorHandling:
    """Test import error handling for optional dependencies."""

    @patch("gunicorn_prometheus_exporter.plugin.PrometheusEventletWorker", None)
    def test_eventlet_import_error(self):
        """Test handling of Eventlet import error."""
        # This test simulates what happens when Eventlet is not available
        # The module should handle the ImportError gracefully
        assert hasattr(gunicorn_prometheus_exporter, "EVENTLET_AVAILABLE")
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusEventletWorker")

    @patch("gunicorn_prometheus_exporter.plugin.PrometheusGeventWorker", None)
    def test_gevent_import_error(self):
        """Test handling of Gevent import error."""
        # This test simulates what happens when Gevent is not available
        # The module should handle the ImportError gracefully
        assert hasattr(gunicorn_prometheus_exporter, "GEVENT_AVAILABLE")
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusGeventWorker")

    @patch("gunicorn_prometheus_exporter.plugin.PrometheusTornadoWorker", None)
    def test_tornado_import_error(self):
        """Test handling of Tornado import error."""
        # This test simulates what happens when Tornado is not available
        # The module should handle the ImportError gracefully
        assert hasattr(gunicorn_prometheus_exporter, "TORNADO_AVAILABLE")
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusTornadoWorker")


class TestModuleLogger:
    """Test module logger functionality."""

    def test_logger_exists(self):
        """Test that module logger exists."""
        assert hasattr(gunicorn_prometheus_exporter, "logger")
        assert isinstance(gunicorn_prometheus_exporter.logger, logging.Logger)
        assert (
            gunicorn_prometheus_exporter.logger.name == "gunicorn_prometheus_exporter"
        )

    def test_logger_level(self):
        """Test logger level."""
        logger = gunicorn_prometheus_exporter.logger
        # Logger should be able to log at different levels
        logger.debug("Test debug message")
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")


class TestModuleConstants:
    """Test module constants and configuration."""

    def test_config_object(self):
        """Test config object availability."""
        assert hasattr(gunicorn_prometheus_exporter, "config")
        assert gunicorn_prometheus_exporter.config is not None

    def test_registry_object(self):
        """Test registry object availability."""
        assert hasattr(gunicorn_prometheus_exporter, "registry")
        assert gunicorn_prometheus_exporter.registry is not None

    def test_get_config_function(self):
        """Test get_config function availability."""
        assert hasattr(gunicorn_prometheus_exporter, "get_config")
        assert callable(gunicorn_prometheus_exporter.get_config)

    def test_get_forwarder_manager_function(self):
        """Test get_forwarder_manager function availability."""
        assert hasattr(gunicorn_prometheus_exporter, "get_forwarder_manager")
        assert callable(gunicorn_prometheus_exporter.get_forwarder_manager)

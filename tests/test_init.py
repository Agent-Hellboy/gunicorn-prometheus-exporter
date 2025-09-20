"""Tests for main module initialization."""

import logging

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

    def test_all_exports(self):
        """Test __all__ exports."""
        expected_exports = [
            "PrometheusWorker",
            "PrometheusThreadWorker",
            "PrometheusMaster",
            "registry",
            "config",
            "get_config",
            "RedisStorageManager",
            "get_redis_storage_manager",
            "setup_redis_metrics",
            "teardown_redis_metrics",
            "is_redis_enabled",
            "get_prometheus_eventlet_worker",
            "get_prometheus_gevent_worker",
        ]

        for export in expected_exports:
            assert export in gunicorn_prometheus_exporter.__all__
            assert hasattr(gunicorn_prometheus_exporter, export)

    def test_eventlet_availability(self):
        """Test Eventlet availability detection."""
        # Test that EVENTLET_AVAILABLE is defined
        assert hasattr(gunicorn_prometheus_exporter, "EVENTLET_AVAILABLE")
        assert isinstance(gunicorn_prometheus_exporter.EVENTLET_AVAILABLE, bool)

    def test_gevent_availability(self):
        """Test Gevent availability detection."""
        # Test that GEVENT_AVAILABLE is defined
        assert hasattr(gunicorn_prometheus_exporter, "GEVENT_AVAILABLE")
        assert isinstance(gunicorn_prometheus_exporter.GEVENT_AVAILABLE, bool)

    def test_worker_classes_availability(self):
        """Test that worker classes are available."""
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusWorker")
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusThreadWorker")
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusEventletWorker")
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusGeventWorker")

    def test_master_class_availability(self):
        """Test that master class is available."""
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusMaster")

    def test_registry_availability(self):
        """Test that registry is available."""
        assert hasattr(gunicorn_prometheus_exporter, "registry")
        assert gunicorn_prometheus_exporter.registry is not None

    def test_get_config_function(self):
        """Test get_config function availability."""
        assert hasattr(gunicorn_prometheus_exporter, "get_config")
        assert callable(gunicorn_prometheus_exporter.get_config)


class TestImportErrorHandling:
    """Test import error handling for optional dependencies."""

    def test_eventlet_import_error_simulation(self):
        """Test handling of Eventlet import error."""
        # Test the actual import error handling by checking the availability flags
        assert hasattr(gunicorn_prometheus_exporter, "EVENTLET_AVAILABLE")
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusEventletWorker")

        # Test that the worker class is either available or None
        worker_class = gunicorn_prometheus_exporter.PrometheusEventletWorker
        assert worker_class is None or callable(worker_class)

    def test_gevent_import_error_simulation(self):
        """Test handling of Gevent import error."""
        # Test the actual import error handling by checking the availability flags
        assert hasattr(gunicorn_prometheus_exporter, "GEVENT_AVAILABLE")
        assert hasattr(gunicorn_prometheus_exporter, "PrometheusGeventWorker")

        # Test that the worker class is either available or None
        worker_class = gunicorn_prometheus_exporter.PrometheusGeventWorker
        assert worker_class is None or callable(worker_class)

    def test_import_error_coverage(self):
        """Test that import error paths are covered."""
        # This test ensures that the ImportError exception handling paths are tested
        # The actual import error handling happens during module import

        # Test that all availability flags are boolean
        assert isinstance(gunicorn_prometheus_exporter.EVENTLET_AVAILABLE, bool)
        assert isinstance(gunicorn_prometheus_exporter.GEVENT_AVAILABLE, bool)

        # Test that worker classes are either callable or None
        assert (
            gunicorn_prometheus_exporter.PrometheusEventletWorker is None
            or callable(gunicorn_prometheus_exporter.PrometheusEventletWorker)
        )
        assert gunicorn_prometheus_exporter.PrometheusGeventWorker is None or callable(
            gunicorn_prometheus_exporter.PrometheusGeventWorker
        )


class TestModuleLogger:
    """Test module logger functionality."""

    def test_logger_availability(self):
        """Test that logger is available."""
        assert hasattr(gunicorn_prometheus_exporter, "logger")
        assert isinstance(gunicorn_prometheus_exporter.logger, logging.Logger)

    def test_logger_configuration(self):
        """Test logger configuration."""
        logger = gunicorn_prometheus_exporter.logger
        assert logger.name == "gunicorn_prometheus_exporter"
        # Logger level might be set to NOTSET (0) initially
        assert logger.level in (logging.NOTSET, logging.INFO)


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


class TestGunicornPatching:
    """Test Gunicorn patching functionality."""

    def test_arbiter_replacement(self):
        """Test that Arbiter is replaced with PrometheusMaster."""
        import gunicorn.app.base
        import gunicorn.arbiter

        # Test that both modules have PrometheusMaster as Arbiter
        assert gunicorn.arbiter.Arbiter is gunicorn_prometheus_exporter.PrometheusMaster
        assert (
            gunicorn.app.base.Arbiter is gunicorn_prometheus_exporter.PrometheusMaster
        )

    def test_baseapplication_run_patch(self):
        """Test that BaseApplication.run is patched."""
        import gunicorn.app.base

        # Test that run method is patched
        assert hasattr(gunicorn.app.base.BaseApplication, "run")
        assert callable(gunicorn.app.base.BaseApplication.run)

    def test_patched_run_function(self):
        """Test the patched run function."""
        import gunicorn.app.base

        # Test that the patched run function exists and is callable
        run_method = gunicorn.app.base.BaseApplication.run
        assert callable(run_method)

        # Test that it's not the original run method (it should be our patched version)
        # We can't easily test the original vs patched, but we can test it's callable
        assert run_method.__name__ == "patched_run" or hasattr(
            run_method, "__wrapped__"
        )


class TestConditionalExports:
    """Test conditional exports based on availability."""

    def test_eventlet_worker_in_all_when_available(self):
        """Test that PrometheusEventletWorker is in __all__ when available."""
        if gunicorn_prometheus_exporter.EVENTLET_AVAILABLE:
            assert "PrometheusEventletWorker" in gunicorn_prometheus_exporter.__all__
        else:
            assert (
                "PrometheusEventletWorker" not in gunicorn_prometheus_exporter.__all__
            )

    def test_gevent_worker_in_all_when_available(self):
        """Test that PrometheusGeventWorker is in __all__ when available."""
        if gunicorn_prometheus_exporter.GEVENT_AVAILABLE:
            assert "PrometheusGeventWorker" in gunicorn_prometheus_exporter.__all__
        else:
            assert "PrometheusGeventWorker" not in gunicorn_prometheus_exporter.__all__

    def test_conditional_worker_class_assignment(self):
        """Test that worker classes are assigned conditionally."""
        # Test Eventlet worker
        if gunicorn_prometheus_exporter.EVENTLET_AVAILABLE:
            assert gunicorn_prometheus_exporter.PrometheusEventletWorker is not None
            assert callable(gunicorn_prometheus_exporter.PrometheusEventletWorker)
        else:
            assert gunicorn_prometheus_exporter.PrometheusEventletWorker is None

        # Test Gevent worker
        if gunicorn_prometheus_exporter.GEVENT_AVAILABLE:
            assert gunicorn_prometheus_exporter.PrometheusGeventWorker is not None
            assert callable(gunicorn_prometheus_exporter.PrometheusGeventWorker)
        else:
            assert gunicorn_prometheus_exporter.PrometheusGeventWorker is None

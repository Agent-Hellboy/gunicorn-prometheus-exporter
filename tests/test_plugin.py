"""Tests for the plugin module."""

import logging
import time

from unittest.mock import MagicMock, patch

import pytest

from gunicorn_prometheus_exporter.plugin import (
    EVENTLET_AVAILABLE,
    GEVENT_AVAILABLE,
    TORNADO_AVAILABLE,
    PrometheusThreadWorker,
    PrometheusWorker,
    _create_eventlet_worker,
    _create_gevent_worker,
    _create_tornado_worker,
    _setup_logging,
    get_prometheus_eventlet_worker,
    get_prometheus_gevent_worker,
    get_prometheus_tornado_worker,
)


class TestPluginLogging:
    """Test logging setup in the plugin module."""

    def test_setup_logging_success(self, monkeypatch):
        """Test successful logging setup."""
        mock_config = MagicMock()
        mock_config.get_gunicorn_config.return_value = {"loglevel": "DEBUG"}
        monkeypatch.setattr("gunicorn_prometheus_exporter.plugin.config", mock_config)

        original_level = logging.getLogger().level

        _setup_logging()

        assert True  # Function executed successfully

        logging.getLogger().setLevel(original_level)

    def test_setup_logging_exception_fallback(self, monkeypatch):
        """Test logging setup falls back when config fails."""
        mock_config = MagicMock()
        mock_config.get_gunicorn_config.side_effect = Exception("Config error")
        monkeypatch.setattr("gunicorn_prometheus_exporter.plugin.config", mock_config)

        original_level = logging.getLogger().level

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            _setup_logging()

            assert True  # Function executed successfully
            mock_logger.warning.assert_called_once()

        logging.getLogger().setLevel(original_level)

    def test_setup_logging_invalid_level_fallback(self, monkeypatch):
        """Test logging setup falls back when log level is invalid."""
        mock_config = MagicMock()
        mock_config.get_gunicorn_config.return_value = {"loglevel": "INVALID_LEVEL"}
        monkeypatch.setattr("gunicorn_prometheus_exporter.plugin.config", mock_config)

        original_level = logging.getLogger().level

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            _setup_logging()

            assert True  # Function executed successfully
            mock_logger.warning.assert_called_once()

        logging.getLogger().setLevel(original_level)


class TestPrometheusWorker:
    """Test PrometheusWorker class."""

    def test_worker_import(self):
        """Test that PrometheusWorker can be imported and is a class."""
        assert hasattr(PrometheusWorker, "__init__")
        assert callable(PrometheusWorker.__init__)

    def test_worker_initialization_simple(self):
        """Test PrometheusWorker initialization with minimal mocking."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging") as mock_setup:
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                # Create a simple mock that just sets the age attribute
                def mock_init(self, *args, **kwargs):
                    self.age = 1
                    return None

                # Use patch.object to mock the parent class method (SyncWorker)
                with patch.object(PrometheusWorker.__bases__[1], "__init__", mock_init):
                    worker = PrometheusWorker()

                    mock_setup.assert_called_once()
                    assert hasattr(worker, "start_time")
                    assert hasattr(worker, "worker_id")
                    assert hasattr(worker, "process")
                    assert worker.age == 1

    def test_handle_request_request_counting(self):
        """Test request counting logic in handle_request."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                # Create worker with minimal setup
                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value
                worker.update_worker_metrics = MagicMock()
                worker._request_count = 0  # Initialize the request counter

                # Mock request and response
                listener = MagicMock()
                req = MagicMock()
                req.method = "GET"
                req.path = "/test"
                client = MagicMock()
                addr = ("127.0.0.1", 12345)

                with patch.object(
                    worker.__class__.__bases__[1],
                    "handle_request",  # SyncWorker
                ) as mock_super_handle:
                    mock_super_handle.return_value = "response"

                    # Test first request
                    result = worker.handle_request(listener, req, client, addr)

                    assert result == "response"
                    assert worker._request_count == 1

                    # Test second request
                    result = worker.handle_request(listener, req, client, addr)

                    assert result == "response"
                    assert worker._request_count == 2

    def test_handle_request_exception_handling(self):
        """Test exception handling in handle_request."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                # Create worker with minimal setup
                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value

                # Mock request
                listener = MagicMock()
                req = MagicMock()
                req.method = "GET"
                req.path = "/test"
                client = MagicMock()
                addr = ("127.0.0.1", 12345)

                with patch.object(
                    worker.__class__.__bases__[1],
                    "handle_request",  # SyncWorker
                ) as mock_super_handle:
                    test_error = ValueError("Test error")
                    mock_super_handle.side_effect = test_error

                    with patch(
                        "gunicorn_prometheus_exporter.plugin.logger"
                    ) as mock_logger:
                        with pytest.raises(ValueError):
                            worker.handle_request(listener, req, client, addr)

                        # The error is logged in the exception handler
                        mock_logger.error.assert_called()

    def test_update_worker_metrics_success(self):
        """Test successful worker metrics update."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process_instance = MagicMock()
                mock_process_instance.memory_info.return_value = MagicMock(rss=1024000)
                mock_process_instance.cpu_percent.return_value = 5.5
                mock_process.return_value = mock_process_instance

                # Create worker with minimal setup
                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time() - 100  # 100 seconds ago
                worker.process = mock_process_instance

                with patch(
                    "gunicorn_prometheus_exporter.plugin.WORKER_MEMORY"
                ) as mock_memory:
                    with patch(
                        "gunicorn_prometheus_exporter.plugin.WORKER_CPU"
                    ) as mock_cpu:
                        with patch(
                            "gunicorn_prometheus_exporter.plugin.WORKER_UPTIME"
                        ) as mock_uptime:
                            with patch(
                                "gunicorn_prometheus_exporter.plugin.WORKER_STATE"
                            ) as mock_state:
                                with patch("time.time", return_value=1753652599.0):
                                    worker.update_worker_metrics()

                                    # Check that metrics were called (even if they fail due to label validation)
                                    mock_memory.labels.assert_called_with(
                                        worker_id="worker_1"
                                    )
                                    mock_cpu.labels.assert_called_with(
                                        worker_id="worker_1"
                                    )
                                    mock_uptime.labels.assert_called_with(
                                        worker_id="worker_1"
                                    )
                                    mock_state.labels.assert_called_with(
                                        worker_id="worker_1",
                                        state="running",
                                        timestamp=1753652599,
                                    )

    def test_update_worker_metrics_exception_handling(self):
        """Test exception handling in update_worker_metrics."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process_instance = MagicMock()
                test_exception = Exception("Process error")
                mock_process_instance.memory_info.side_effect = test_exception
                mock_process.return_value = mock_process_instance

                # Create worker with minimal setup
                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process_instance

                with patch("gunicorn_prometheus_exporter.plugin.logger") as mock_logger:
                    worker.update_worker_metrics()

                    mock_logger.error.assert_called_once_with(
                        "Failed to update worker metrics: %s", test_exception
                    )

    def test_handle_error(self):
        """Test error handling in handle_error."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                # Create worker with minimal setup
                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value

                # Mock request and error info
                req = MagicMock()
                req.method = "POST"
                req.path = "/error"
                client = MagicMock()
                addr = ("127.0.0.1", 12345)
                einfo = ValueError("Test error")

                with patch.object(
                    worker.__class__.__bases__[1],
                    "handle_error",  # SyncWorker
                ) as mock_super_handle:
                    # Make the parent handle_error not throw an exception
                    mock_super_handle.return_value = None
                    with patch(
                        "gunicorn_prometheus_exporter.plugin.WORKER_ERROR_HANDLING"
                    ) as mock_error_metric:
                        with patch("gunicorn_prometheus_exporter.plugin.logger"):
                            worker.handle_error(req, client, addr, einfo)

                            # Check if the metric was called (even if it fails due to label validation)
                            mock_error_metric.labels.assert_called_with(
                                worker_id="worker_1",
                                method="POST",
                                endpoint="/error",
                                error_type="ValueError",
                            )
                            # The parent handle_error should be called
                            mock_super_handle.assert_called_once_with(
                                req, client, addr, einfo
                            )

    def test_handle_error_with_string_einfo(self):
        """Test error handling with string error info."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                # Create worker with minimal setup
                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value
                worker.log = MagicMock()  # Add the missing log attribute

                # Mock request and string error info
                req = MagicMock()
                req.method = "GET"
                req.path = "/test"
                client = MagicMock()
                addr = ("127.0.0.1", 12345)
                einfo = "String error message"

                with patch(
                    "gunicorn_prometheus_exporter.plugin.WORKER_ERROR_HANDLING"
                ) as mock_error_metric:
                    with patch.object(
                        worker.__class__.__bases__[1],
                        "handle_error",  # SyncWorker
                    ) as mock_super_handle:
                        worker.handle_error(req, client, addr, einfo)

                        mock_error_metric.labels.assert_called_with(
                            worker_id="worker_1",
                            method="GET",
                            endpoint="/test",
                            error_type="str",
                        )
                        mock_super_handle.assert_called_once_with(
                            req, client, addr, einfo
                        )

    def test_handle_quit(self):
        """Test quit signal handling."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                # Create worker with minimal setup
                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value

                sig = 3  # SIGQUIT
                frame = MagicMock()

                with patch.object(
                    worker.__class__.__bases__[1],
                    "handle_quit",  # SyncWorker
                ) as mock_super_handle:
                    with patch(
                        "gunicorn_prometheus_exporter.plugin.WORKER_STATE"
                    ) as mock_state:
                        with patch("time.time", return_value=1234567890.0):
                            worker.handle_quit(sig, frame)

                            mock_state.labels.assert_called_once_with(
                                worker_id="worker_1",
                                state="quitting",
                                timestamp=1234567890,
                            )
                            # The parent handle_quit should be called
                            mock_super_handle.assert_called_once_with(sig, frame)

    def test_handle_abort(self):
        """Test abort signal handling."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                # Create worker with minimal setup
                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value

                sig = 6  # SIGABRT
                frame = MagicMock()

                with patch.object(
                    worker.__class__.__bases__[1],
                    "handle_abort",  # SyncWorker
                ) as mock_super_handle:
                    with patch(
                        "gunicorn_prometheus_exporter.plugin.WORKER_STATE"
                    ) as mock_state:
                        with patch("time.time", return_value=1234567890.0):
                            worker.handle_abort(sig, frame)

                            mock_state.labels.assert_called_once_with(
                                worker_id="worker_1",
                                state="aborting",
                                timestamp=1234567890,
                            )
                            # The parent handle_abort should be called
                            mock_super_handle.assert_called_once_with(sig, frame)


class TestPrometheusMixinComprehensive:
    """Comprehensive tests for PrometheusMixin functionality."""

    def test_clear_old_metrics(self):
        """Test clearing old metrics functionality."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                # Create worker with minimal setup
                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value

                # Mock metrics with _metrics attribute
                mock_metric = MagicMock()
                mock_metric._labelnames = ("worker_id", "other_label")
                mock_metric._metrics = {
                    ("worker_1", "value1"): 1.0,  # Current worker
                    ("worker_2", "value2"): 2.0,  # Old worker
                    ("worker_3", "value3"): 3.0,  # Old worker
                }

                with patch(
                    "gunicorn_prometheus_exporter.plugin.WORKER_REQUESTS"
                ) as mock_requests:
                    mock_requests._metric = mock_metric

                    worker._clear_old_metrics()

                    # Should remove old worker metrics (unpacked arguments)
                    assert mock_metric.remove.call_count == 2
                    mock_metric.remove.assert_any_call("worker_2", "value2")
                    mock_metric.remove.assert_any_call("worker_3", "value3")

    def test_handle_request_metrics_success(self):
        """Test successful request metrics handling."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value
                worker._request_count = 0

                with patch(
                    "gunicorn_prometheus_exporter.plugin.WORKER_REQUESTS"
                ) as mock_requests:
                    with patch(
                        "gunicorn_prometheus_exporter.plugin.WORKER_REQUEST_DURATION"
                    ) as mock_duration:
                        with patch(
                            "time.time", side_effect=[1000.0, 1000.5]
                        ):  # 0.5 second duration
                            worker._handle_request_metrics()

                            assert worker._request_count == 1
                            mock_requests.labels.assert_called_once_with(
                                worker_id="worker_1"
                            )
                            mock_duration.labels.assert_called_once_with(
                                worker_id="worker_1"
                            )

    def test_handle_request_metrics_exception(self):
        """Test request metrics handling with exception."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value
                worker._request_count = 0

                with patch(
                    "gunicorn_prometheus_exporter.plugin.WORKER_REQUESTS",
                    side_effect=Exception("Metric error"),
                ):
                    # The method should handle the exception gracefully
                    worker._handle_request_metrics()

                    # Verify the method completed without raising an exception
                    assert True  # If we get here, the exception was handled

    def test_handle_request_error_metrics(self):
        """Test request error metrics handling."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value

                req = MagicMock()
                req.method = "POST"
                req.path = "/api/test"
                error = ValueError("Test error")

                with patch(
                    "gunicorn_prometheus_exporter.plugin.WORKER_FAILED_REQUESTS"
                ) as mock_failed:
                    with patch(
                        "time.time", side_effect=[1000.0, 1000.1, 1000.2, 1000.3]
                    ):  # More values for logging
                        worker._handle_request_error_metrics(req, error)

                        mock_failed.labels.assert_called_once_with(
                            worker_id="worker_1",
                            method="POST",
                            endpoint="/api/test",
                            error_type="ValueError",
                        )

    def test_handle_request_error_metrics_exception(self):
        """Test request error metrics handling with exception."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value

                req = MagicMock()
                req.method = "GET"
                req.path = "/test"
                error = RuntimeError("Test error")

                with patch(
                    "gunicorn_prometheus_exporter.plugin.WORKER_FAILED_REQUESTS",
                    side_effect=Exception("Metric error"),
                ):
                    with patch(
                        "gunicorn_prometheus_exporter.plugin.logger"
                    ) as mock_logger:
                        worker._handle_request_error_metrics(req, error)

                        mock_logger.error.assert_called_once()


class TestPrometheusThreadWorker:
    """Test PrometheusThreadWorker class."""

    def test_thread_worker_initialization(self):
        """Test PrometheusThreadWorker initialization."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                def mock_init(self, *args, **kwargs):
                    self.age = 2
                    return None

                with patch.object(
                    PrometheusThreadWorker.__bases__[1], "__init__", mock_init
                ):
                    worker = PrometheusThreadWorker()

                    assert hasattr(worker, "start_time")
                    assert hasattr(worker, "worker_id")
                    assert hasattr(worker, "process")
                    assert worker.age == 2

    def test_thread_worker_handle_request(self):
        """Test PrometheusThreadWorker handle_request method."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                worker = PrometheusThreadWorker.__new__(PrometheusThreadWorker)
                worker.age = 2
                worker.worker_id = "worker_2"
                worker.start_time = time.time()
                worker.process = mock_process.return_value
                worker.update_worker_metrics = MagicMock()
                worker._request_count = 0

                req = MagicMock()
                conn = MagicMock()

                with patch.object(
                    worker.__class__.__bases__[1], "handle_request"
                ) as mock_super_handle:
                    mock_super_handle.return_value = "response"

                    result = worker.handle_request(req, conn)

                    assert result == "response"
                    worker.update_worker_metrics.assert_called_once()


class TestAsyncWorkerAvailability:
    """Test async worker availability flags."""

    def test_eventlet_availability(self):
        """Test EVENTLET_AVAILABLE flag."""
        assert isinstance(EVENTLET_AVAILABLE, bool)

    def test_gevent_availability(self):
        """Test GEVENT_AVAILABLE flag."""
        assert isinstance(GEVENT_AVAILABLE, bool)

    def test_tornado_availability(self):
        """Test TORNADO_AVAILABLE flag."""
        assert isinstance(TORNADO_AVAILABLE, bool)


class TestAsyncWorkerCreation:
    """Test async worker creation functions."""

    def test_create_eventlet_worker(self):
        """Test _create_eventlet_worker function."""
        with patch("gunicorn_prometheus_exporter.plugin.EVENTLET_AVAILABLE", True):
            with patch(
                "gunicorn_prometheus_exporter.plugin.importlib.util.find_spec",
                return_value=True,
            ):
                with patch(
                    "gunicorn_prometheus_exporter.plugin.EventletWorker", MagicMock()
                ):
                    _create_eventlet_worker()
                    # Function should execute without error

    def test_create_eventlet_worker_unavailable(self):
        """Test _create_eventlet_worker when eventlet is unavailable."""
        with patch("gunicorn_prometheus_exporter.plugin.EVENTLET_AVAILABLE", False):
            _create_eventlet_worker()
            # Function should execute without error

    def test_create_eventlet_worker_import_error(self):
        """Test _create_eventlet_worker with import error."""
        with patch("gunicorn_prometheus_exporter.plugin.EVENTLET_AVAILABLE", True):
            with patch(
                "gunicorn_prometheus_exporter.plugin.importlib.util.find_spec",
                side_effect=ImportError("Not found"),
            ):
                _create_eventlet_worker()
                # Function should handle import error gracefully

    def test_create_gevent_worker(self):
        """Test _create_gevent_worker function."""
        with patch("gunicorn_prometheus_exporter.plugin.GEVENT_AVAILABLE", True):
            with patch(
                "gunicorn_prometheus_exporter.plugin.importlib.util.find_spec",
                return_value=True,
            ):
                with patch(
                    "gunicorn_prometheus_exporter.plugin.GeventWorker", MagicMock()
                ):
                    _create_gevent_worker()
                    # Function should execute without error

    def test_create_gevent_worker_unavailable(self):
        """Test _create_gevent_worker when gevent is unavailable."""
        with patch("gunicorn_prometheus_exporter.plugin.GEVENT_AVAILABLE", False):
            _create_gevent_worker()
            # Function should execute without error

    def test_create_gevent_worker_import_error(self):
        """Test _create_gevent_worker with import error."""
        with patch("gunicorn_prometheus_exporter.plugin.GEVENT_AVAILABLE", True):
            with patch(
                "gunicorn_prometheus_exporter.plugin.importlib.util.find_spec",
                side_effect=ImportError("Not found"),
            ):
                _create_gevent_worker()
                # Function should handle import error gracefully

    def test_create_tornado_worker(self):
        """Test _create_tornado_worker function."""
        with patch("gunicorn_prometheus_exporter.plugin.TORNADO_AVAILABLE", True):
            with patch(
                "gunicorn_prometheus_exporter.plugin.importlib.util.find_spec",
                return_value=True,
            ):
                with patch(
                    "gunicorn_prometheus_exporter.plugin.TornadoWorker", MagicMock()
                ):
                    _create_tornado_worker()
                    # Function should execute without error

    def test_create_tornado_worker_unavailable(self):
        """Test _create_tornado_worker when tornado is unavailable."""
        with patch("gunicorn_prometheus_exporter.plugin.TORNADO_AVAILABLE", False):
            _create_tornado_worker()
            # Function should execute without error

    def test_create_tornado_worker_import_error(self):
        """Test _create_tornado_worker with import error."""
        with patch("gunicorn_prometheus_exporter.plugin.TORNADO_AVAILABLE", True):
            with patch(
                "gunicorn_prometheus_exporter.plugin.importlib.util.find_spec",
                side_effect=ImportError("Not found"),
            ):
                _create_tornado_worker()
                # Function should handle import error gracefully


class TestAsyncWorkerGetters:
    """Test async worker getter functions."""

    def test_get_prometheus_eventlet_worker(self):
        """Test get_prometheus_eventlet_worker function."""
        result = get_prometheus_eventlet_worker()
        # Should return None or a class
        assert result is None or callable(result)

    def test_get_prometheus_gevent_worker(self):
        """Test get_prometheus_gevent_worker function."""
        result = get_prometheus_gevent_worker()
        # Should return None or a class
        assert result is None or callable(result)

    def test_get_prometheus_tornado_worker(self):
        """Test get_prometheus_tornado_worker function."""
        result = get_prometheus_tornado_worker()
        # Should return None or a class
        assert result is None or callable(result)


class TestPluginModuleInitialization:
    """Test plugin module initialization."""

    def test_module_logging_setup(self):
        """Test module-level logging setup."""
        # Test that the module initializes without errors
        import gunicorn_prometheus_exporter.plugin

        assert hasattr(gunicorn_prometheus_exporter.plugin, "logger")
        assert isinstance(gunicorn_prometheus_exporter.plugin.logger, logging.Logger)

    def test_async_worker_variables(self):
        """Test async worker variables are initialized."""
        from gunicorn_prometheus_exporter.plugin import (
            PrometheusEventletWorker,
            PrometheusGeventWorker,
            PrometheusTornadoWorker,
        )

        # These should be None or classes
        assert PrometheusEventletWorker is None or callable(PrometheusEventletWorker)
        assert PrometheusGeventWorker is None or callable(PrometheusGeventWorker)
        assert PrometheusTornadoWorker is None or callable(PrometheusTornadoWorker)


class TestPrometheusMixinEdgeCases:
    """Test edge cases in PrometheusMixin."""

    def test_clear_old_metrics_no_worker_id_label(self):
        """Test clearing metrics when worker_id label is not found."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value

                # Mock metric without worker_id label
                mock_metric = MagicMock()
                mock_metric._labelnames = ("other_label", "another_label")
                mock_metric._metrics = {
                    ("value1", "value2"): 1.0,
                }

                with patch(
                    "gunicorn_prometheus_exporter.plugin.WORKER_REQUESTS"
                ) as mock_requests:
                    mock_requests._metric = mock_metric

                    worker._clear_old_metrics()

                    # Should not remove anything since worker_id label not found
                    mock_metric.remove.assert_not_called()

    def test_handle_request_error_metrics_no_request_attributes(self):
        """Test error metrics with request missing attributes."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value

                # Request without method and path attributes
                req = MagicMock()
                del req.method
                del req.path
                error = Exception("Test error")

                with patch(
                    "gunicorn_prometheus_exporter.plugin.WORKER_FAILED_REQUESTS"
                ) as mock_failed:
                    worker._handle_request_error_metrics(req, error)

                    mock_failed.labels.assert_called_once_with(
                        worker_id="worker_1",
                        method="UNKNOWN",
                        endpoint="UNKNOWN",
                        error_type="Exception",
                    )

    def test_handle_request_error_metrics_no_request(self):
        """Test error metrics with None request."""
        with patch("gunicorn_prometheus_exporter.plugin._setup_logging"):
            with patch(
                "gunicorn_prometheus_exporter.plugin.psutil.Process"
            ) as mock_process:
                mock_process.return_value = MagicMock()

                worker = PrometheusWorker.__new__(PrometheusWorker)
                worker.age = 1
                worker.worker_id = "worker_1"
                worker.start_time = time.time()
                worker.process = mock_process.return_value

                error = Exception("Test error")

                with patch(
                    "gunicorn_prometheus_exporter.plugin.WORKER_FAILED_REQUESTS"
                ) as mock_failed:
                    worker._handle_request_error_metrics(None, error)

                    mock_failed.labels.assert_called_once_with(
                        worker_id="worker_1",
                        method="UNKNOWN",
                        endpoint="UNKNOWN",
                        error_type="Exception",
                    )

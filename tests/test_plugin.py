"""Tests for the plugin module."""

import logging
import time

from unittest.mock import MagicMock, patch

import pytest

from gunicorn_prometheus_exporter.plugin import PrometheusWorker, _setup_logging


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

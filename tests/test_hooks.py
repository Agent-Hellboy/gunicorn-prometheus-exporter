"""Tests for Gunicorn hooks."""

import os
import unittest

from unittest.mock import MagicMock, patch

from gunicorn_prometheus_exporter.hooks import (
    _handle_worker_shutdown,
    _update_bind_env,
    _update_env_from_cli,
    _update_worker_class_env,
    _update_worker_metrics,
    _update_workers_env,
    default_on_starting,
    default_post_fork,
    default_worker_int,
)


class TestPostForkHook(unittest.TestCase):
    """Test post_fork hook functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing environment variables
        for var in [
            "GUNICORN_WORKERS",
            "GUNICORN_BIND",
            "GUNICORN_WORKER_CLASS",
        ]:
            if var in os.environ:
                del os.environ[var]

    def test_post_fork_with_timeout(self):
        """Test post_fork hook with CLI options."""
        # Mock server and worker
        server = MagicMock()
        server.cfg.workers = 4
        server.cfg.bind = "0.0.0.0:8000"
        server.cfg.worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

        worker = MagicMock()
        worker.pid = 12345

        # Call the hook
        with patch("gunicorn_prometheus_exporter.hooks.logging.getLogger"):
            default_post_fork(server, worker)

        # Verify environment variables were set
        self.assertEqual(os.environ.get("GUNICORN_WORKERS"), "4")
        self.assertEqual(os.environ.get("GUNICORN_BIND"), "0.0.0.0:8000")
        self.assertEqual(
            os.environ.get("GUNICORN_WORKER_CLASS"),
            "gunicorn_prometheus_exporter.PrometheusWorker",
        )

    def test_post_fork_without_cli_options(self):
        """Test post_fork hook without CLI options."""
        # Mock server and worker without CLI options
        server = MagicMock()
        server.cfg.workers = None
        server.cfg.bind = None
        server.cfg.worker_class = None

        worker = MagicMock()
        worker.pid = 12345

        # Call the hook
        with patch("gunicorn_prometheus_exporter.hooks.logging.getLogger"):
            default_post_fork(server, worker)

        # Verify environment variables were not set
        self.assertIsNone(os.environ.get("GUNICORN_WORKERS"))
        self.assertIsNone(os.environ.get("GUNICORN_BIND"))
        self.assertIsNone(os.environ.get("GUNICORN_WORKER_CLASS"))

    def test_post_fork_logs_worker_configuration(self):
        """Test that post_fork hook logs worker configuration."""
        # Mock server and worker
        server = MagicMock()
        server.cfg.workers = 4
        server.cfg.bind = "0.0.0.0:8000"
        server.cfg.worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

        worker = MagicMock()
        worker.pid = 12345

        # Mock logger
        mock_logger = MagicMock()
        with patch(
            "gunicorn_prometheus_exporter.hooks.logging.getLogger",
            return_value=mock_logger,
        ):
            default_post_fork(server, worker)

        # Verify logger was called
        mock_logger.info.assert_called()
        # Check that the log message contains configuration info
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        config_log = any("Gunicorn configuration:" in call for call in log_calls)
        self.assertTrue(config_log)

    def test_post_fork_handles_missing_attributes(self):
        """Test post_fork hook handles missing configuration attributes."""
        # Mock server and worker with missing attributes
        server = MagicMock()
        # Don't set any attributes on cfg

        worker = MagicMock()
        worker.pid = 12345

        # Call the hook - should not raise an exception
        with patch("gunicorn_prometheus_exporter.hooks.logging.getLogger"):
            try:
                default_post_fork(server, worker)
            except AttributeError:
                self.fail("post_fork hook should handle missing attributes gracefully")

    def tearDown(self):
        """Clean up after tests."""
        # Clear any environment variables set during tests
        for var in [
            "GUNICORN_WORKERS",
            "GUNICORN_BIND",
            "GUNICORN_WORKER_CLASS",
        ]:
            if var in os.environ:
                del os.environ[var]


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions in hooks module."""

    def test_update_workers_env_with_valid_value(self):
        """Test _update_workers_env with valid CLI value."""
        cfg = MagicMock()
        cfg.workers = 4
        mock_logger = MagicMock()

        _update_workers_env(cfg, mock_logger)

        self.assertEqual(os.environ.get("GUNICORN_WORKERS"), "4")
        mock_logger.info.assert_called_once_with(
            "Updated GUNICORN_WORKERS from CLI: %s", 4
        )

    def test_update_workers_env_with_default_value(self):
        """Test _update_workers_env with default value (should not set env var)."""
        cfg = MagicMock()
        cfg.workers = 1  # Default value
        mock_logger = MagicMock()

        _update_workers_env(cfg, mock_logger)

        self.assertIsNone(os.environ.get("GUNICORN_WORKERS"))
        mock_logger.info.assert_not_called()

    def test_update_bind_env_with_valid_value(self):
        """Test _update_bind_env with valid CLI value."""
        cfg = MagicMock()
        cfg.bind = "0.0.0.0:8000"
        mock_logger = MagicMock()

        _update_bind_env(cfg, mock_logger)

        self.assertEqual(os.environ.get("GUNICORN_BIND"), "0.0.0.0:8000")
        mock_logger.info.assert_called_once_with(
            "Updated GUNICORN_BIND from CLI: %s", "0.0.0.0:8000"
        )

    def test_update_bind_env_with_default_value(self):
        """Test _update_bind_env with default value (should not set env var)."""
        cfg = MagicMock()
        cfg.bind = ["127.0.0.1:8000"]  # Default value
        mock_logger = MagicMock()

        _update_bind_env(cfg, mock_logger)

        self.assertIsNone(os.environ.get("GUNICORN_BIND"))
        mock_logger.info.assert_not_called()

    def test_update_worker_class_env_with_valid_value(self):
        """Test _update_worker_class_env with valid CLI value."""
        cfg = MagicMock()
        cfg.worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
        mock_logger = MagicMock()

        _update_worker_class_env(cfg, mock_logger)

        self.assertEqual(
            os.environ.get("GUNICORN_WORKER_CLASS"),
            "gunicorn_prometheus_exporter.PrometheusWorker",
        )
        mock_logger.info.assert_called_once_with(
            "Updated GUNICORN_WORKER_CLASS from CLI: %s",
            "gunicorn_prometheus_exporter.PrometheusWorker",
        )

    def test_update_worker_class_env_with_default_value(self):
        """Test _update_worker_class_env with default value (should not set env var)."""
        cfg = MagicMock()
        cfg.worker_class = "sync"  # Default value
        mock_logger = MagicMock()

        _update_worker_class_env(cfg, mock_logger)

        self.assertIsNone(os.environ.get("GUNICORN_WORKER_CLASS"))
        mock_logger.info.assert_not_called()

    def test_update_env_from_cli_calls_all_helpers(self):
        """Test _update_env_from_cli calls all helper functions."""
        cfg = MagicMock()
        cfg.workers = 4
        cfg.bind = "0.0.0.0:8000"
        cfg.worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks._update_workers_env"
        ) as mock_workers:
            with patch(
                "gunicorn_prometheus_exporter.hooks._update_bind_env"
            ) as mock_bind:
                with patch(
                    "gunicorn_prometheus_exporter.hooks._update_worker_class_env"
                ) as mock_class:
                    _update_env_from_cli(cfg, mock_logger)

                    mock_workers.assert_called_once_with(cfg, mock_logger)
                    mock_bind.assert_called_once_with(cfg, mock_logger)
                    mock_class.assert_called_once_with(cfg, mock_logger)

    def test_update_worker_metrics_success(self):
        """Test _update_worker_metrics with successful update."""
        worker = MagicMock()
        worker.update_worker_metrics = MagicMock()
        worker.worker_id = "worker_1"
        mock_logger = MagicMock()

        _update_worker_metrics(worker, mock_logger)

        worker.update_worker_metrics.assert_called_once()
        mock_logger.debug.assert_called_once_with(
            "Updated worker metrics for %s", "worker_1"
        )

    def test_update_worker_metrics_exception(self):
        """Test _update_worker_metrics with exception."""
        worker = MagicMock()
        worker.update_worker_metrics = MagicMock(side_effect=Exception("Test error"))
        mock_logger = MagicMock()

        _update_worker_metrics(worker, mock_logger)

        # Check that error was called with the correct message format
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        self.assertEqual(call_args[0][0], "Failed to update worker metrics: %s")
        self.assertIsInstance(call_args[0][1], Exception)
        self.assertEqual(str(call_args[0][1]), "Test error")

    def test_update_worker_metrics_no_method(self):
        """Test _update_worker_metrics when worker has no update_worker_metrics method."""
        worker = MagicMock()
        delattr(worker, "update_worker_metrics")  # Remove the method
        mock_logger = MagicMock()

        _update_worker_metrics(worker, mock_logger)

        # Should not call any logger methods
        mock_logger.debug.assert_not_called()
        mock_logger.error.assert_not_called()

    def test_handle_worker_shutdown_with_handle_quit(self):
        """Test _handle_worker_shutdown with handle_quit method."""
        worker = MagicMock()
        worker.handle_quit = MagicMock()
        mock_logger = MagicMock()

        _handle_worker_shutdown(worker, mock_logger)

        worker.handle_quit.assert_called_once()
        mock_logger.info.assert_not_called()

    def test_handle_worker_shutdown_handle_quit_exception(self):
        """Test _handle_worker_shutdown when handle_quit raises exception."""
        worker = MagicMock()
        worker.handle_quit = MagicMock(side_effect=Exception("Test error"))
        worker.alive = True
        mock_logger = MagicMock()

        _handle_worker_shutdown(worker, mock_logger)

        # Check that error was called with the correct message format
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        self.assertEqual(call_args[0][0], "Failed to call parent handle_quit: %s")
        self.assertIsInstance(call_args[0][1], Exception)
        self.assertEqual(str(call_args[0][1]), "Test error")
        self.assertFalse(worker.alive)

    def test_handle_worker_shutdown_without_handle_quit(self):
        """Test _handle_worker_shutdown without handle_quit method."""
        worker = MagicMock()
        delattr(worker, "handle_quit")  # Remove the method
        worker.alive = True
        mock_logger = MagicMock()

        _handle_worker_shutdown(worker, mock_logger)

        mock_logger.info.assert_called_once_with(
            "Set worker.alive = False for graceful shutdown"
        )
        self.assertFalse(worker.alive)

    def test_handle_worker_shutdown_no_alive_attribute(self):
        """Test _handle_worker_shutdown when worker has no alive attribute."""
        worker = MagicMock()
        delattr(worker, "alive")  # Remove the attribute
        mock_logger = MagicMock()

        # Should not raise an exception
        _handle_worker_shutdown(worker, mock_logger)

        mock_logger.info.assert_not_called()

    def tearDown(self):
        """Clean up after tests."""
        # Clear any environment variables set during tests
        for var in [
            "GUNICORN_WORKERS",
            "GUNICORN_BIND",
            "GUNICORN_WORKER_CLASS",
        ]:
            if var in os.environ:
                del os.environ[var]


class TestOnStartingHook(unittest.TestCase):
    """Test on_starting hook functionality."""

    def test_default_on_starting(self):
        """Test default_on_starting hook."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks.logging.getLogger",
            return_value=mock_logger,
        ):
            default_on_starting(mock_server)

        # Check that info was called at least once (may be called multiple times)
        mock_logger.info.assert_called()


class TestWorkerIntHook(unittest.TestCase):
    """Test worker_int hook functionality."""

    def test_default_worker_int(self):
        """Test default_worker_int hook."""
        mock_worker = MagicMock()
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks.logging.getLogger",
            return_value=mock_logger,
        ):
            with patch(
                "gunicorn_prometheus_exporter.hooks._update_worker_metrics"
            ) as mock_update:
                with patch(
                    "gunicorn_prometheus_exporter.hooks._handle_worker_shutdown"
                ) as mock_shutdown:
                    default_worker_int(mock_worker)

        mock_logger.info.assert_called_once_with("Worker received interrupt signal")
        mock_update.assert_called_once_with(mock_worker, mock_logger)
        mock_shutdown.assert_called_once_with(mock_worker, mock_logger)


if __name__ == "__main__":
    unittest.main()

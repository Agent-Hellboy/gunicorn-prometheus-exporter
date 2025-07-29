"""Tests for Gunicorn hooks."""

import os
import unittest

from unittest.mock import MagicMock, patch

from gunicorn_prometheus_exporter.hooks import default_post_fork


class TestPostForkHook(unittest.TestCase):
    """Test the post_fork hook functionality."""

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


if __name__ == "__main__":
    unittest.main()

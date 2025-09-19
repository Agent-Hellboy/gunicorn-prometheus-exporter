"""Comprehensive tests for Gunicorn hooks."""

import logging
import os
import unittest

from unittest.mock import MagicMock, Mock, patch

from gunicorn_prometheus_exporter.hooks import (
    EnvironmentManager,
    HookContext,
    HookManager,
    MetricsServerManager,
    ProcessManager,
    _get_hook_manager,
    _get_metrics_manager,
    _get_process_manager,
    _setup_redis_storage_if_enabled,
    default_on_exit,
    default_on_starting,
    default_post_fork,
    default_when_ready,
    default_worker_int,
    redis_when_ready,
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

    def test_post_fork_with_cli_options(self):
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
            "gunicorn_prometheus_exporter.hooks._get_hook_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_logger.return_value = mock_logger
            mock_get_manager.return_value = mock_manager

            default_post_fork(server, worker)

        # Verify logger was called
        mock_logger.info.assert_called()
        # Check that the log message contains configuration info
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        config_log = any("Gunicorn configuration:" in call for call in log_calls)
        self.assertTrue(config_log)

    def test_post_fork_handles_missing_attributes(self):
        """Test post_fork hook handles missing attributes gracefully."""
        # Mock server and worker with missing attributes
        server = MagicMock()
        server.cfg = MagicMock()
        # Don't set any attributes on cfg

        worker = MagicMock()
        worker.pid = 12345

        # Call the hook - should not raise an exception
        with patch("gunicorn_prometheus_exporter.hooks.logging.getLogger"):
            try:
                default_post_fork(server, worker)
            except Exception as e:
                self.fail(f"post_fork hook raised an exception: {e}")

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
    """Test helper functions for environment management."""

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

    def test_update_workers_env_with_valid_value(self):
        """Test update_workers_env with valid value."""
        mock_logger = MagicMock()
        env_manager = EnvironmentManager(mock_logger)

        # Mock server config
        server = MagicMock()
        server.cfg.workers = 4

        env_manager._update_workers_env(server.cfg)

        self.assertEqual(os.environ.get("GUNICORN_WORKERS"), "4")
        mock_logger.info.assert_called_once_with(
            "Updated GUNICORN_WORKERS from CLI: %s", 4
        )

    def test_update_workers_env_with_default_value(self):
        """Test update_workers_env with default value."""
        mock_logger = MagicMock()
        env_manager = EnvironmentManager(mock_logger)

        # Mock server config with default value
        server = MagicMock()
        server.cfg.workers = 1  # Default value

        env_manager._update_workers_env(server.cfg)

        # Should not set environment variable for default value
        self.assertIsNone(os.environ.get("GUNICORN_WORKERS"))
        mock_logger.info.assert_not_called()

    def test_update_bind_env_with_valid_value(self):
        """Test update_bind_env with valid value."""
        mock_logger = MagicMock()
        env_manager = EnvironmentManager(mock_logger)

        # Mock server config
        server = MagicMock()
        server.cfg.bind = "0.0.0.0:8000"

        env_manager._update_bind_env(server.cfg)

        self.assertEqual(os.environ.get("GUNICORN_BIND"), "0.0.0.0:8000")
        mock_logger.info.assert_called_once_with(
            "Updated GUNICORN_BIND from CLI: %s", "0.0.0.0:8000"
        )

    def test_update_bind_env_with_default_value(self):
        """Test update_bind_env with default value."""
        mock_logger = MagicMock()
        env_manager = EnvironmentManager(mock_logger)

        # Mock server config with default value
        server = MagicMock()
        server.cfg.bind = ["127.0.0.1:8000"]  # Default value

        env_manager._update_bind_env(server.cfg)

        # Should not set environment variable for default value
        self.assertIsNone(os.environ.get("GUNICORN_BIND"))
        mock_logger.info.assert_not_called()

    def test_update_worker_class_env_with_valid_value(self):
        """Test update_worker_class_env with valid value."""
        mock_logger = MagicMock()
        env_manager = EnvironmentManager(mock_logger)

        # Mock server config
        server = MagicMock()
        server.cfg.worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

        env_manager._update_worker_class_env(server.cfg)

        self.assertEqual(
            os.environ.get("GUNICORN_WORKER_CLASS"),
            "gunicorn_prometheus_exporter.PrometheusWorker",
        )
        mock_logger.info.assert_called_once_with(
            "Updated GUNICORN_WORKER_CLASS from CLI: %s",
            "gunicorn_prometheus_exporter.PrometheusWorker",
        )

    def test_update_worker_class_env_with_default_value(self):
        """Test update_worker_class_env with default value."""
        mock_logger = MagicMock()
        env_manager = EnvironmentManager(mock_logger)

        # Mock server config with default value
        server = MagicMock()
        server.cfg.worker_class = "sync"  # Default value

        env_manager._update_worker_class_env(server.cfg)

        # Should not set environment variable for default value
        self.assertIsNone(os.environ.get("GUNICORN_WORKER_CLASS"))
        mock_logger.info.assert_not_called()

    def test_update_env_from_cli_calls_all_helpers(self):
        """Test update_from_cli calls all helper methods."""
        mock_logger = MagicMock()
        env_manager = EnvironmentManager(mock_logger)

        # Mock server config
        server = MagicMock()
        server.cfg.workers = 4
        server.cfg.bind = "0.0.0.0:8000"
        server.cfg.worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

        # Mock the helper methods
        with patch.object(env_manager, "_update_workers_env") as mock_workers:
            with patch.object(env_manager, "_update_bind_env") as mock_bind:
                with patch.object(
                    env_manager, "_update_worker_class_env"
                ) as mock_class:
                    env_manager.update_from_cli(server.cfg)

                    mock_workers.assert_called_once_with(server.cfg)
                    mock_bind.assert_called_once_with(server.cfg)
                    mock_class.assert_called_once_with(server.cfg)

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


class TestMetricsServerManager(unittest.TestCase):
    """Test MetricsServerManager functionality."""

    def test_setup_server_success(self):
        """Test setup_server with successful initialization."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)

        with patch(
            "gunicorn_prometheus_exporter.utils.get_multiprocess_dir",
            return_value="/tmp/test",
        ):
            with patch("gunicorn_prometheus_exporter.hooks.config") as mock_config:
                mock_config.prometheus_metrics_port = 9090

                with patch(
                    "gunicorn_prometheus_exporter.hooks.MultiProcessCollector"
                ) as mock_collector:
                    result = manager.setup_server()

                    self.assertIsNotNone(result)
                    port, registry = result
                    self.assertEqual(port, 9090)
                    # The registry is now imported from metrics module, so it's the real registry
                    from gunicorn_prometheus_exporter.metrics import (
                        registry as metrics_registry,
                    )

                    self.assertEqual(registry, metrics_registry)
                    mock_collector.assert_called_once_with(metrics_registry)
                    mock_logger.info.assert_called_once_with(
                        "Successfully initialized MultiProcessCollector"
                    )

    def test_setup_server_no_multiprocess_dir(self):
        """Test setup_server when multiprocess directory is not set."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)

        with patch(
            "gunicorn_prometheus_exporter.utils.get_multiprocess_dir", return_value=None
        ):
            result = manager.setup_server()

            self.assertIsNone(result)
            mock_logger.warning.assert_called_once_with(
                "PROMETHEUS_MULTIPROC_DIR not set; skipping metrics server"
            )

    def test_setup_server_collector_exception(self):
        """Test setup_server when MultiProcessCollector initialization fails."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)

        with patch(
            "gunicorn_prometheus_exporter.utils.get_multiprocess_dir",
            return_value="/tmp/test",
        ):
            with patch("gunicorn_prometheus_exporter.hooks.config") as mock_config:
                mock_config.prometheus_metrics_port = 9090

                with patch(
                    "gunicorn_prometheus_exporter.hooks.MultiProcessCollector",
                    side_effect=Exception("Test error"),
                ):
                    result = manager.setup_server()

                    self.assertIsNone(result)
                    mock_logger.error.assert_called_once()
                    call_args = mock_logger.error.call_args
                    self.assertEqual(
                        call_args[0][0],
                        "Failed to initialize MultiProcessCollector: %s",
                    )
                    self.assertIsInstance(call_args[0][1], Exception)
                    self.assertEqual(str(call_args[0][1]), "Test error")

    def test_start_server_success_first_attempt(self):
        """Test start_server with successful first attempt."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)
        port = 9090
        registry = MagicMock()

        with patch("prometheus_client.exposition.start_http_server") as mock_start:
            result = manager.start_server(port, registry)

            self.assertTrue(result)
            mock_start.assert_called_once_with(port, registry=registry)
            mock_logger.info.assert_called_once_with(
                "HTTP metrics server started successfully on :%s", port
            )

    def test_start_server_success_after_retry(self):
        """Test start_server with success after retry."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)
        port = 9090
        registry = MagicMock()

        with patch("prometheus_client.exposition.start_http_server") as mock_start:
            # First call raises OSError, second call succeeds
            mock_start.side_effect = [OSError(98, "Address already in use"), None]

            # The OSError with errno 98 gets re-raised, so we expect it
            with self.assertRaises(OSError):
                manager.start_server(port, registry)

    def test_start_server_all_attempts_fail(self):
        """Test start_server when all attempts fail."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)
        port = 9090
        registry = MagicMock()

        with patch(
            "prometheus_client.exposition.start_http_server",
            side_effect=OSError(98, "Address already in use"),
        ):
            # All attempts will fail with OSError that gets re-raised
            with self.assertRaises(OSError):
                manager.start_server(port, registry)

    def test_start_server_other_oserror_handled(self):
        """Test start_server when OSError with other errno is handled."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)
        port = 9090
        registry = MagicMock()

        with patch(
            "prometheus_client.exposition.start_http_server",
            side_effect=OSError(13, "Permission denied"),
        ):
            result = manager.start_server(port, registry)

            self.assertFalse(result)
            mock_logger.error.assert_called_with(
                "Failed to start metrics server after %s attempts", 3
            )

    def test_start_single_attempt_success(self):
        """Test _start_single_attempt with success."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)
        port = 9090
        registry = MagicMock()

        with patch("prometheus_client.exposition.start_http_server") as mock_start:
            result = manager._start_single_attempt(port, registry)

            self.assertTrue(result)
            mock_start.assert_called_once_with(port, registry=registry)
            mock_logger.info.assert_called_once_with(
                "HTTP metrics server started successfully on :%s", port
            )

    def test_start_single_attempt_oserror_address_in_use(self):
        """Test _start_single_attempt with OSError for address in use."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)
        port = 9090
        registry = MagicMock()

        with patch(
            "prometheus_client.exposition.start_http_server",
            side_effect=OSError(98, "Address already in use"),
        ):
            with self.assertRaises(OSError):
                manager._start_single_attempt(port, registry)

    def test_start_single_attempt_oserror_other(self):
        """Test _start_single_attempt with other OSError."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)
        port = 9090
        registry = MagicMock()

        with patch(
            "prometheus_client.exposition.start_http_server",
            side_effect=OSError(13, "Permission denied"),
        ):
            result = manager._start_single_attempt(port, registry)

            self.assertFalse(result)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            self.assertEqual(call_args[0][0], "Failed to start metrics server: %s")
            self.assertIsInstance(call_args[0][1], OSError)

    def test_start_single_attempt_general_exception(self):
        """Test _start_single_attempt with general exception."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)
        port = 9090
        registry = MagicMock()

        with patch(
            "prometheus_client.exposition.start_http_server",
            side_effect=Exception("Test error"),
        ):
            result = manager._start_single_attempt(port, registry)

            self.assertFalse(result)
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            self.assertEqual(call_args[0][0], "Failed to start metrics server: %s")
            self.assertIsInstance(call_args[0][1], Exception)
            self.assertEqual(str(call_args[0][1]), "Test error")


class TestProcessManager(unittest.TestCase):
    """Test ProcessManager functionality."""

    def test_cleanup_processes_success(self):
        """Test cleanup_processes with successful cleanup."""
        mock_logger = MagicMock()
        manager = ProcessManager(mock_logger)

        mock_child = MagicMock()
        mock_child.name.return_value = "test_process"
        mock_child.pid = 12345

        with patch("gunicorn_prometheus_exporter.hooks.psutil.Process") as mock_process:
            mock_process.return_value.children.return_value = [mock_child]

            with patch.object(manager, "_terminate_child") as mock_terminate:
                manager.cleanup_processes()

                mock_terminate.assert_called_once_with(mock_child)

    def test_cleanup_processes_exception(self):
        """Test cleanup_processes with exception."""
        mock_logger = MagicMock()
        manager = ProcessManager(mock_logger)

        with patch(
            "gunicorn_prometheus_exporter.hooks.psutil.Process",
            side_effect=Exception("Test error"),
        ):
            manager.cleanup_processes()

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            self.assertEqual(call_args[0][0], "Error during cleanup: %s")
            self.assertIsInstance(call_args[0][1], Exception)
            self.assertEqual(str(call_args[0][1]), "Test error")

    def test_terminate_child_success(self):
        """Test _terminate_child with successful termination."""
        mock_logger = MagicMock()
        manager = ProcessManager(mock_logger)

        mock_child = MagicMock()
        mock_child.name.return_value = "test_process"
        mock_child.pid = 12345

        with patch("gunicorn_prometheus_exporter.hooks.psutil.TimeoutExpired"):
            manager._terminate_child(mock_child)

            mock_child.terminate.assert_called_once()
            mock_child.wait.assert_called_once_with(timeout=5)
            mock_logger.info.assert_called_once_with(
                "Terminating child process: %s (PID: %s)", "test_process", 12345
            )

    def test_terminate_child_timeout(self):
        """Test _terminate_child with timeout."""
        mock_logger = MagicMock()
        manager = ProcessManager(mock_logger)

        mock_child = MagicMock()
        mock_child.name.return_value = "test_process"
        mock_child.pid = 12345
        mock_child.wait.side_effect = Exception("Timeout")

        with patch(
            "gunicorn_prometheus_exporter.hooks.psutil.TimeoutExpired", Exception
        ):
            manager._terminate_child(mock_child)

            mock_child.terminate.assert_called_once()
            mock_child.kill.assert_called_once()
            mock_logger.warning.assert_called_once_with(
                "Force killing child process: %s (PID: %s)", "test_process", 12345
            )

    def test_terminate_child_exception(self):
        """Test _terminate_child with exception."""
        mock_logger = MagicMock()
        manager = ProcessManager(mock_logger)

        mock_child = MagicMock()
        mock_child.name.return_value = "test_process"
        mock_child.pid = 12345
        mock_child.terminate.side_effect = Exception("Test error")

        manager._terminate_child(mock_child)

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        self.assertEqual(call_args[0][0], "Error terminating child process %s: %s")
        self.assertEqual(call_args[0][1], 12345)
        self.assertIsInstance(call_args[0][2], Exception)
        self.assertEqual(str(call_args[0][2]), "Test error")


class TestHookManager(unittest.TestCase):
    """Test HookManager functionality."""

    def test_hook_manager_initialization(self):
        """Test HookManager initialization."""
        manager = HookManager()

        self.assertIsNotNone(manager.logger)
        self.assertEqual(manager.logger.name, "gunicorn_prometheus_exporter.hooks")

    def test_get_logger(self):
        """Test get_logger method."""
        manager = HookManager()
        logger = manager.get_logger()

        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "gunicorn_prometheus_exporter.hooks")

    def test_safe_execute_success(self):
        """Test safe_execute with successful execution."""
        manager = HookManager()

        def test_func():
            return "success"

        result = manager.safe_execute(test_func)
        self.assertTrue(result)

    def test_safe_execute_exception(self):
        """Test safe_execute with exception."""
        manager = HookManager()

        def test_func():
            raise Exception("Test error")

        result = manager.safe_execute(test_func)
        self.assertFalse(result)


class TestOnStartingHook(unittest.TestCase):
    """Test on_starting hook."""

    def test_default_on_starting(self):
        """Test default_on_starting hook."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks._get_hook_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.logger = mock_logger
            mock_get_manager.return_value = mock_manager

            with patch(
                "gunicorn_prometheus_exporter.utils.get_multiprocess_dir",
                return_value="/tmp/test",
            ):
                with patch(
                    "gunicorn_prometheus_exporter.utils.ensure_multiprocess_dir"
                ):
                    default_on_starting(mock_server)

        # Check that info was called at least once (may be called multiple times)
        mock_logger.info.assert_called()

    def test_default_on_starting_no_multiprocess_dir(self):
        """Test default_on_starting hook when multiprocess dir is not set."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks._get_hook_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.logger = mock_logger
            mock_get_manager.return_value = mock_manager

            with patch(
                "gunicorn_prometheus_exporter.utils.get_multiprocess_dir",
                return_value=None,
            ):
                default_on_starting(mock_server)

        mock_logger.warning.assert_called_once_with(
            "PROMETHEUS_MULTIPROC_DIR not set; skipping master metrics initialization"
        )


class TestWorkerIntHook(unittest.TestCase):
    """Test worker_int hook."""

    def test_default_worker_int(self):
        """Test default_worker_int hook."""
        mock_worker = MagicMock()
        mock_worker.worker_id = "worker-1"
        mock_worker.update_worker_metrics = MagicMock()

        # Test with worker that has update_worker_metrics method
        default_worker_int(mock_worker)

        # Verify the worker's update_worker_metrics method was called
        mock_worker.update_worker_metrics.assert_called_once()

    def test_default_worker_int_no_update_method(self):
        """Test default_worker_int hook when worker has no update_worker_metrics method."""
        mock_worker = MagicMock()
        # Remove the update_worker_metrics method
        del mock_worker.update_worker_metrics

        # Should not raise an exception
        default_worker_int(mock_worker)

    def test_default_worker_int_exception(self):
        """Test default_worker_int hook when update_worker_metrics raises an exception."""
        mock_worker = MagicMock()
        mock_worker.worker_id = "worker-1"
        mock_worker.update_worker_metrics.side_effect = Exception("Test error")

        # Should not raise an exception, should handle it gracefully
        default_worker_int(mock_worker)


class TestWhenReadyHook(unittest.TestCase):
    """Test when_ready hook."""

    def test_default_when_ready_success(self):
        """Test default_when_ready hook with successful setup."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks._get_hook_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_logger.return_value = mock_logger
            mock_get_manager.return_value = mock_manager

            with patch(
                "gunicorn_prometheus_exporter.hooks._get_metrics_manager"
            ) as mock_get_metrics_manager:
                mock_metrics_manager = MagicMock()
                mock_metrics_manager.setup_server.return_value = (9090, MagicMock())
                mock_metrics_manager.start_server.return_value = True
                mock_get_metrics_manager.return_value = mock_metrics_manager

                default_when_ready(mock_server)

        mock_logger.info.assert_called_with(
            "Starting Prometheus multiprocess metrics server on :%s",
            9090,
        )

    def test_default_when_ready_setup_fails(self):
        """Test default_when_ready hook when setup fails."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks._get_hook_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_logger.return_value = mock_logger
            mock_get_manager.return_value = mock_manager

            with patch(
                "gunicorn_prometheus_exporter.hooks._get_metrics_manager"
            ) as mock_get_metrics_manager:
                mock_metrics_manager = MagicMock()
                mock_metrics_manager.setup_server.return_value = None
                mock_get_metrics_manager.return_value = mock_metrics_manager

                default_when_ready(mock_server)

        # Should not call any logging methods when setup fails
        mock_logger.info.assert_not_called()

    def test_default_when_ready_start_fails(self):
        """Test default_when_ready hook when start fails."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks._get_hook_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_logger.return_value = mock_logger
            mock_get_manager.return_value = mock_manager

            with patch(
                "gunicorn_prometheus_exporter.hooks._get_metrics_manager"
            ) as mock_get_metrics_manager:
                mock_metrics_manager = MagicMock()
                mock_metrics_manager.setup_server.return_value = (9090, MagicMock())
                mock_metrics_manager.start_server.return_value = False
                mock_get_metrics_manager.return_value = mock_metrics_manager

                default_when_ready(mock_server)

        mock_logger.error.assert_called_once_with("Failed to start metrics server")


class TestOnExitHook(unittest.TestCase):
    """Test on_exit hook."""

    def test_default_on_exit(self):
        """Test default_on_exit hook."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks._get_hook_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_logger.return_value = mock_logger
            mock_get_manager.return_value = mock_manager

            with patch(
                "gunicorn_prometheus_exporter.hooks._get_process_manager"
            ) as mock_get_process_manager:
                mock_process_manager = MagicMock()
                mock_get_process_manager.return_value = mock_process_manager

                default_on_exit(mock_server)

        mock_logger.info.assert_any_call("Server shutting down")
        mock_logger.info.assert_any_call(
            "Server shutdown complete - Redis TTL handles automatic cleanup"
        )
        # Note: cleanup_processes is no longer called in default_on_exit


class TestRedisWhenReadyHook(unittest.TestCase):
    """Test redis_when_ready hook."""

    def test_redis_when_ready_success(self):
        """Test redis_when_ready hook with successful setup."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks._get_hook_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_logger.return_value = mock_logger
            mock_get_manager.return_value = mock_manager

            with patch(
                "gunicorn_prometheus_exporter.hooks._get_metrics_manager"
            ) as mock_get_metrics_manager:
                mock_metrics_manager = MagicMock()
                mock_metrics_manager.setup_server.return_value = (9090, MagicMock())
                mock_metrics_manager.start_server.return_value = True
                mock_get_metrics_manager.return_value = mock_metrics_manager

                with patch(
                    "gunicorn_prometheus_exporter.hooks._setup_redis_storage_if_enabled"
                ) as mock_start_redis:
                    redis_when_ready(mock_server)

        mock_logger.info.assert_called_with(
            "Starting Prometheus multiprocess metrics server on :%s",
            9090,
        )
        mock_start_redis.assert_called_once_with(mock_logger)

    def test_redis_when_ready_metrics_fails(self):
        """Test redis_when_ready hook when metrics setup fails."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks._get_hook_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_logger.return_value = mock_logger
            mock_get_manager.return_value = mock_manager

            with patch(
                "gunicorn_prometheus_exporter.hooks._get_metrics_manager"
            ) as mock_get_metrics_manager:
                mock_metrics_manager = MagicMock()
                mock_metrics_manager.setup_server.return_value = None
                mock_get_metrics_manager.return_value = mock_metrics_manager

                redis_when_ready(mock_server)

        # Should not call any logging methods when setup fails
        mock_logger.info.assert_not_called()

    def test_redis_when_ready_start_fails(self):
        """Test redis_when_ready hook when start fails."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        with patch(
            "gunicorn_prometheus_exporter.hooks._get_hook_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_logger.return_value = mock_logger
            mock_get_manager.return_value = mock_manager

            with patch(
                "gunicorn_prometheus_exporter.hooks._get_metrics_manager"
            ) as mock_get_metrics_manager:
                mock_metrics_manager = MagicMock()
                mock_metrics_manager.setup_server.return_value = (9090, MagicMock())
                mock_metrics_manager.start_server.return_value = False
                mock_get_metrics_manager.return_value = mock_metrics_manager

                redis_when_ready(mock_server)

        mock_logger.error.assert_called_once_with("Failed to start metrics server")


class TestRedisForwarder(unittest.TestCase):
    """Test Redis forwarder functionality."""

    def test_start_redis_forwarder_enabled(self):
        """Test _setup_redis_storage_if_enabled when Redis is enabled."""
        mock_logger = MagicMock()

        with patch("gunicorn_prometheus_exporter.hooks.config") as mock_config:
            mock_config.redis_enabled = True

            with patch(
                "gunicorn_prometheus_exporter.backend.setup_redis_metrics"
            ) as mock_setup_redis:
                mock_setup_redis.return_value = True

                _setup_redis_storage_if_enabled(mock_logger)

                mock_setup_redis.assert_called_once()
                mock_logger.info.assert_called_once_with(
                    "Redis storage enabled - using Redis instead of files"
                )

    def test_start_redis_forwarder_disabled(self):
        """Test _setup_redis_storage_if_enabled when Redis is disabled."""
        mock_logger = MagicMock()

        with patch("gunicorn_prometheus_exporter.hooks.config") as mock_config:
            mock_config.redis_enabled = False

            _setup_redis_storage_if_enabled(mock_logger)

            mock_logger.info.assert_called_once_with("Redis storage disabled")

    def test_start_redis_forwarder_exception(self):
        """Test _setup_redis_storage_if_enabled with exception."""
        mock_logger = MagicMock()

        with patch("gunicorn_prometheus_exporter.hooks.config") as mock_config:
            mock_config.redis_enabled = True

            with patch(
                "gunicorn_prometheus_exporter.backend.setup_redis_metrics",
                side_effect=Exception("Test error"),
            ):
                _setup_redis_storage_if_enabled(mock_logger)

                mock_logger.error.assert_called_once()
                call_args = mock_logger.error.call_args
                self.assertEqual(call_args[0][0], "Failed to setup Redis storage: %s")
                self.assertIsInstance(call_args[0][1], Exception)
                self.assertEqual(str(call_args[0][1]), "Test error")


class TestHookContextComprehensive(unittest.TestCase):
    """Comprehensive tests for HookContext class."""

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        mock_server = Mock()
        mock_worker = Mock()
        mock_logger = Mock()

        context = HookContext(
            server=mock_server, worker=mock_worker, logger=mock_logger
        )

        self.assertEqual(context.server, mock_server)
        self.assertEqual(context.worker, mock_worker)
        self.assertEqual(context.logger, mock_logger)

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        mock_server = Mock()

        context = HookContext(server=mock_server)

        self.assertEqual(context.server, mock_server)
        self.assertIsNone(context.worker)
        self.assertIsNotNone(context.logger)
        self.assertIsInstance(context.logger, logging.Logger)

    def test_post_init_logger_creation(self):
        """Test logger creation in __post_init__."""
        mock_server = Mock()

        with patch(
            "gunicorn_prometheus_exporter.hooks.logging.getLogger"
        ) as mock_get_logger:
            HookContext(server=mock_server)

            mock_get_logger.assert_called_once_with(
                "gunicorn_prometheus_exporter.hooks"
            )


class TestHookManagerComprehensive(unittest.TestCase):
    """Comprehensive tests for HookManager class."""

    def test_init(self):
        """Test HookManager initialization."""
        with patch(
            "gunicorn_prometheus_exporter.hooks.logging.getLogger"
        ) as mock_get_logger:
            manager = HookManager()

            self.assertIsNotNone(manager.logger)
            mock_get_logger.assert_called_once_with(
                "gunicorn_prometheus_exporter.hooks"
            )

    def test_setup_logging(self):
        """Test _setup_logging method."""
        manager = HookManager()

        # Should not raise any exceptions
        manager._setup_logging()

    def test_get_logger(self):
        """Test get_logger method."""
        manager = HookManager()
        logger = manager.get_logger()

        self.assertEqual(logger, manager.logger)
        self.assertIsInstance(logger, logging.Logger)

    def test_safe_execute_success(self):
        """Test safe_execute with successful execution."""
        manager = HookManager()
        mock_func = Mock()

        with patch.object(manager.logger, "error") as mock_error:
            result = manager.safe_execute(mock_func, "arg1", "arg2", key="value")

            mock_func.assert_called_once_with("arg1", "arg2", key="value")
            self.assertTrue(result)
            mock_error.assert_not_called()

    def test_safe_execute_exception(self):
        """Test safe_execute with exception."""
        manager = HookManager()
        mock_func = Mock(side_effect=Exception("Test error"))

        with patch.object(manager.logger, "error") as mock_error:
            result = manager.safe_execute(mock_func, "arg1", "arg2")

            mock_func.assert_called_once_with("arg1", "arg2")
            self.assertFalse(result)
            mock_error.assert_called_once()


class TestEnvironmentManagerComprehensive(unittest.TestCase):
    """Comprehensive tests for EnvironmentManager class."""

    def test_init(self):
        """Test EnvironmentManager initialization."""
        mock_logger = Mock()
        manager = EnvironmentManager(mock_logger)

        self.assertEqual(manager.logger, mock_logger)
        self.assertEqual(
            manager._defaults,
            {
                "workers": 1,
                "bind": ["127.0.0.1:8000"],
                "worker_class": "sync",
            },
        )

    def test_update_from_cli(self):
        """Test update_from_cli method."""
        mock_logger = Mock()
        manager = EnvironmentManager(mock_logger)
        mock_cfg = Mock()

        with (
            patch.object(manager, "_update_workers_env") as mock_workers,
            patch.object(manager, "_update_bind_env") as mock_bind,
            patch.object(manager, "_update_worker_class_env") as mock_worker_class,
        ):
            manager.update_from_cli(mock_cfg)

            mock_workers.assert_called_once_with(mock_cfg)
            mock_bind.assert_called_once_with(mock_cfg)
            mock_worker_class.assert_called_once_with(mock_cfg)

    def test_update_workers_env(self):
        """Test _update_workers_env method."""
        mock_logger = Mock()
        manager = EnvironmentManager(mock_logger)
        mock_cfg = Mock()
        mock_cfg.workers = 4

        with patch.dict(os.environ, {}, clear=True):
            manager._update_workers_env(mock_cfg)
            self.assertEqual(os.environ.get("GUNICORN_WORKERS"), "4")

    def test_update_bind_env(self):
        """Test _update_bind_env method."""
        mock_logger = Mock()
        manager = EnvironmentManager(mock_logger)
        mock_cfg = Mock()
        mock_cfg.bind = ["127.0.0.1:8000", "127.0.0.1:8001"]

        with patch.dict(os.environ, {}, clear=True):
            manager._update_bind_env(mock_cfg)
            self.assertEqual(
                os.environ.get("GUNICORN_BIND"), "['127.0.0.1:8000', '127.0.0.1:8001']"
            )

    def test_update_worker_class_env(self):
        """Test _update_worker_class_env method."""
        mock_logger = Mock()
        manager = EnvironmentManager(mock_logger)
        mock_cfg = Mock()
        mock_cfg.worker_class = "gevent"

        with patch.dict(os.environ, {}, clear=True):
            manager._update_worker_class_env(mock_cfg)
            self.assertEqual(os.environ.get("GUNICORN_WORKER_CLASS"), "gevent")


class TestMetricsServerManagerComprehensive(unittest.TestCase):
    """Comprehensive tests for MetricsServerManager class."""

    def test_init(self):
        """Test MetricsServerManager initialization."""
        mock_logger = Mock()
        manager = MetricsServerManager(mock_logger)

        self.assertEqual(manager.logger, mock_logger)
        self.assertIsNone(manager._server_thread)
        self.assertEqual(manager.max_retries, 3)
        self.assertEqual(manager.retry_delay, 1)

    def test_setup_server_success(self):
        """Test setup_server with success."""
        mock_logger = Mock()
        manager = MetricsServerManager(mock_logger)

        with (
            patch("gunicorn_prometheus_exporter.hooks.config") as mock_config,
            patch(
                "gunicorn_prometheus_exporter.utils.get_multiprocess_dir"
            ) as mock_get_dir,
        ):
            mock_config.prometheus_metrics_port = 9091
            mock_config.redis_enabled = False
            mock_get_dir.return_value = "/tmp/test"

            result = manager.setup_server()

            self.assertIsNotNone(result)
            self.assertEqual(len(result), 2)  # Should return (port, registry)

    def test_setup_server_failure(self):
        """Test setup_server with failure."""
        mock_logger = Mock()
        manager = MetricsServerManager(mock_logger)

        with (
            patch("gunicorn_prometheus_exporter.hooks.config") as mock_config,
            patch(
                "gunicorn_prometheus_exporter.utils.get_multiprocess_dir",
                return_value=None,
            ),
        ):
            mock_config.prometheus_metrics_port = 9091
            mock_config.redis_enabled = False

            result = manager.setup_server()

            self.assertIsNone(result)

    def test_start_server_success(self):
        """Test start_server with success."""
        mock_logger = Mock()
        manager = MetricsServerManager(mock_logger)

        with patch.object(
            manager, "_start_single_attempt", return_value=True
        ) as mock_start:
            result = manager.start_server(9091, Mock())

            self.assertTrue(result)
            mock_start.assert_called_once()

    def test_start_server_failure(self):
        """Test start_server with failure."""
        mock_logger = Mock()
        manager = MetricsServerManager(mock_logger)

        with patch.object(
            manager, "_start_single_attempt", return_value=False
        ) as mock_start:
            result = manager.start_server(9091, Mock())

            self.assertFalse(result)
            # Should be called multiple times due to retry logic
            self.assertGreaterEqual(mock_start.call_count, 1)

    def test_stop_server(self):
        """Test stop_server method."""
        mock_logger = Mock()
        manager = MetricsServerManager(mock_logger)
        mock_thread = Mock()
        manager._server_thread = mock_thread

        manager.stop_server()

        # Should clean up the thread reference
        self.assertIsNone(manager._server_thread)

    def test_stop_server_no_server(self):
        """Test stop_server when no server is running."""
        mock_logger = Mock()
        manager = MetricsServerManager(mock_logger)

        # Should not raise exception
        manager.stop_server()


class TestProcessManagerComprehensive(unittest.TestCase):
    """Comprehensive tests for ProcessManager class."""

    def test_init(self):
        """Test ProcessManager initialization."""
        mock_logger = Mock()
        manager = ProcessManager(mock_logger)

        self.assertEqual(manager.logger, mock_logger)
        self.assertEqual(manager.timeout, 5)

    def test_terminate_child(self):
        """Test _terminate_child method."""
        mock_logger = Mock()
        manager = ProcessManager(mock_logger)
        mock_child = Mock()

        with patch.object(manager.logger, "info") as mock_info:
            manager._terminate_child(mock_child)

            mock_child.terminate.assert_called_once()
            mock_info.assert_called_once()

    def test_terminate_child_exception(self):
        """Test _terminate_child with exception."""
        mock_logger = Mock()
        manager = ProcessManager(mock_logger)
        mock_child = Mock()
        mock_child.terminate.side_effect = Exception("Termination failed")

        with patch.object(manager.logger, "error") as mock_error:
            manager._terminate_child(mock_child)

            mock_child.terminate.assert_called_once()
            mock_error.assert_called_once()


class TestHookUtilities(unittest.TestCase):
    """Test hook utility functions."""

    def test_get_hook_manager(self):
        """Test _get_hook_manager function."""
        manager1 = _get_hook_manager()
        manager2 = _get_hook_manager()

        self.assertIs(manager1, manager2)
        self.assertIsInstance(manager1, HookManager)

    def test_get_metrics_manager(self):
        """Test _get_metrics_manager function."""
        manager1 = _get_metrics_manager()
        manager2 = _get_metrics_manager()

        self.assertIs(manager1, manager2)
        self.assertIsInstance(manager1, MetricsServerManager)

    def test_get_process_manager(self):
        """Test _get_process_manager function."""
        manager1 = _get_process_manager()
        manager2 = _get_process_manager()

        self.assertIs(manager1, manager2)
        self.assertIsInstance(manager1, ProcessManager)


class TestHookIntegration(unittest.TestCase):
    """Test hook integration scenarios."""

    def test_hook_manager_integration(self):
        """Test HookManager integration."""
        manager = HookManager()
        mock_func = Mock()

        result = manager.safe_execute(mock_func, "arg1", "arg2")

        mock_func.assert_called_once_with("arg1", "arg2")
        self.assertTrue(result)

    def test_hook_context_integration(self):
        """Test HookContext integration."""
        mock_server = Mock()
        mock_worker = Mock()

        context = HookContext(server=mock_server, worker=mock_worker)

        self.assertIsInstance(context, HookContext)
        self.assertEqual(context.server, mock_server)
        self.assertEqual(context.worker, mock_worker)
        self.assertIsNotNone(context.logger)

    def test_default_hooks_integration(self):
        """Test default hooks integration."""
        mock_server = Mock()

        with (
            patch("gunicorn_prometheus_exporter.hooks.config") as mock_config,
            patch(
                "gunicorn_prometheus_exporter.utils.get_multiprocess_dir"
            ) as mock_get_dir,
            patch(
                "gunicorn_prometheus_exporter.hooks._get_metrics_manager"
            ) as mock_get_manager,
        ):
            mock_manager = Mock()
            mock_manager.setup_server.return_value = (9091, Mock())
            mock_manager.start_server.return_value = True
            mock_get_manager.return_value = mock_manager
            mock_config.prometheus_metrics_port = 9091
            mock_config.redis_enabled = False
            mock_get_dir.return_value = "/tmp/test"

            # Test multiple hooks
            default_on_starting(mock_server)
            default_when_ready(mock_server)
            default_on_exit(mock_server)

            # Verify that the manager methods were called
            mock_manager.setup_server.assert_called_once()
            mock_manager.start_server.assert_called_once()
            # Note: stop_server is no longer called in default_on_exit


if __name__ == "__main__":
    unittest.main()

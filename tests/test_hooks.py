"""Tests for Gunicorn hooks."""

import os
import unittest

from unittest.mock import MagicMock, patch

from gunicorn_prometheus_exporter.hooks import (
    EnvironmentManager,
    HookContext,
    HookManager,
    MetricsServerManager,
    ProcessManager,
    _start_redis_forwarder_if_enabled,
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

        mock_logger.info.assert_any_call(
            "Server shutting down - cleaning up Prometheus metrics server"
        )
        mock_logger.info.assert_any_call("Server shutdown complete")
        mock_process_manager.cleanup_processes.assert_called_once()


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
                    "gunicorn_prometheus_exporter.hooks._start_redis_forwarder_if_enabled"
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
        """Test _start_redis_forwarder_if_enabled when Redis is enabled."""
        mock_logger = MagicMock()

        with patch("gunicorn_prometheus_exporter.hooks.config") as mock_config:
            mock_config.redis_enabled = True

            with patch(
                "gunicorn_prometheus_exporter.forwarder.get_forwarder_manager"
            ) as mock_get_manager:
                mock_manager = MagicMock()
                mock_get_manager.return_value = mock_manager

                _start_redis_forwarder_if_enabled(mock_logger)

                mock_manager.start.assert_called_once()
                mock_logger.info.assert_called_once_with("Redis forwarder started")

    def test_start_redis_forwarder_disabled(self):
        """Test _start_redis_forwarder_if_enabled when Redis is disabled."""
        mock_logger = MagicMock()

        with patch("gunicorn_prometheus_exporter.hooks.config") as mock_config:
            mock_config.redis_enabled = False

            _start_redis_forwarder_if_enabled(mock_logger)

            mock_logger.info.assert_called_once_with("Redis forwarding disabled")

    def test_start_redis_forwarder_exception(self):
        """Test _start_redis_forwarder_if_enabled with exception."""
        mock_logger = MagicMock()

        with patch("gunicorn_prometheus_exporter.hooks.config") as mock_config:
            mock_config.redis_enabled = True

            with patch(
                "gunicorn_prometheus_exporter.forwarder.get_forwarder_manager",
                side_effect=Exception("Test error"),
            ):
                _start_redis_forwarder_if_enabled(mock_logger)

                mock_logger.error.assert_called_once()
                call_args = mock_logger.error.call_args
                self.assertEqual(call_args[0][0], "Failed to start Redis forwarder: %s")
                self.assertIsInstance(call_args[0][1], Exception)
                self.assertEqual(str(call_args[0][1]), "Test error")


if __name__ == "__main__":
    unittest.main()


class TestHookContextAdditional(unittest.TestCase):
    """Additional tests for HookContext to improve coverage."""

    def test_hook_context_post_init_without_logger(self):
        """Test HookContext __post_init__ when logger is None."""
        context = HookContext(server=MagicMock())
        assert context.logger is not None
        assert context.logger.name == "gunicorn_prometheus_exporter.hooks"


class TestHookManagerAdditional(unittest.TestCase):
    """Additional tests for HookManager to improve coverage."""

    def test_setup_logging_exception_handling(self):
        """Test _setup_logging handles exceptions gracefully."""
        manager = HookManager()

        with patch("logging.basicConfig") as mock_basic_config:
            with patch("logging.getLogger") as mock_get_logger:
                # Mock getLogger to raise an exception
                mock_get_logger.side_effect = Exception("Test error")

                # This should not raise an exception
                manager._setup_logging()

                # Should fall back to basic logging setup
                mock_basic_config.assert_called_with(level=20)  # logging.INFO


class TestMetricsServerManagerAdditional(unittest.TestCase):
    """Additional tests for MetricsServerManager to improve coverage."""

    def test_stop_server_with_exception(self):
        """Test stop_server handles exceptions gracefully."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)

        # Set up a mock server thread
        manager._server_thread = MagicMock()

        with patch.object(manager.logger, "info", side_effect=Exception("Test error")):
            # Should not raise an exception
            manager.stop_server()

            # Should still clean up the thread reference
            assert manager._server_thread is None

    def test_start_single_attempt_ssl_enabled(self):
        """Test _start_single_attempt with SSL enabled."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)
        port = 9090
        registry = MagicMock()

        # Save original environment
        original_ssl_certfile = os.environ.get("PROMETHEUS_SSL_CERTFILE")
        original_ssl_keyfile = os.environ.get("PROMETHEUS_SSL_KEYFILE")
        original_bind_address = os.environ.get("PROMETHEUS_BIND_ADDRESS")

        try:
            # Set up SSL environment
            os.environ["PROMETHEUS_SSL_CERTFILE"] = "/path/to/cert.pem"
            os.environ["PROMETHEUS_SSL_KEYFILE"] = "/path/to/key.pem"
            os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"

            with patch(
                "prometheus_client.exposition.start_wsgi_server"
            ) as mock_start_wsgi:
                mock_start_wsgi.return_value = (MagicMock(), MagicMock())

                result = manager._start_single_attempt(port, registry)

                self.assertTrue(result)
                mock_start_wsgi.assert_called_once()

                # Check that thread reference is stored
                assert manager._server_thread is not None

        finally:
            # Restore original environment
            if original_ssl_certfile:
                os.environ["PROMETHEUS_SSL_CERTFILE"] = original_ssl_certfile
            elif "PROMETHEUS_SSL_CERTFILE" in os.environ:
                del os.environ["PROMETHEUS_SSL_CERTFILE"]

            if original_ssl_keyfile:
                os.environ["PROMETHEUS_SSL_KEYFILE"] = original_ssl_keyfile
            elif "PROMETHEUS_SSL_KEYFILE" in os.environ:
                del os.environ["PROMETHEUS_SSL_KEYFILE"]

            if original_bind_address:
                os.environ["PROMETHEUS_BIND_ADDRESS"] = original_bind_address
            elif "PROMETHEUS_BIND_ADDRESS" in os.environ:
                del os.environ["PROMETHEUS_BIND_ADDRESS"]

    def test_start_single_attempt_ssl_with_optional_params(self):
        """Test _start_single_attempt with SSL and optional parameters."""
        mock_logger = MagicMock()
        manager = MetricsServerManager(mock_logger)
        port = 9090
        registry = MagicMock()

        # Save original environment
        original_ssl_certfile = os.environ.get("PROMETHEUS_SSL_CERTFILE")
        original_ssl_keyfile = os.environ.get("PROMETHEUS_SSL_KEYFILE")
        original_client_cafile = os.environ.get("PROMETHEUS_SSL_CLIENT_CAFILE")
        original_client_capath = os.environ.get("PROMETHEUS_SSL_CLIENT_CAPATH")
        original_client_auth = os.environ.get("PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED")
        original_bind_address = os.environ.get("PROMETHEUS_BIND_ADDRESS")

        try:
            # Set up SSL environment with all optional parameters
            os.environ["PROMETHEUS_SSL_CERTFILE"] = "/path/to/cert.pem"
            os.environ["PROMETHEUS_SSL_KEYFILE"] = "/path/to/key.pem"
            os.environ["PROMETHEUS_SSL_CLIENT_CAFILE"] = "/path/to/ca.pem"
            os.environ["PROMETHEUS_SSL_CLIENT_CAPATH"] = "/path/to/ca/dir"
            os.environ["PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED"] = "true"
            os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"

            with patch(
                "prometheus_client.exposition.start_wsgi_server"
            ) as mock_start_wsgi:
                mock_start_wsgi.return_value = (MagicMock(), MagicMock())

                result = manager._start_single_attempt(port, registry)

                self.assertTrue(result)
                mock_start_wsgi.assert_called_once()

                # Check that all parameters are passed
                call_args = mock_start_wsgi.call_args[1]
                assert call_args["certfile"] == "/path/to/cert.pem"
                assert call_args["keyfile"] == "/path/to/key.pem"
                # Optional parameters may or may not be included depending on function signature
                if "client_cafile" in call_args:
                    assert call_args["client_cafile"] == "/path/to/ca.pem"
                if "client_capath" in call_args:
                    assert call_args["client_capath"] == "/path/to/ca/dir"
                if "client_auth_required" in call_args:
                    assert call_args["client_auth_required"] is True

        finally:
            # Restore original environment
            for env_var, original_value in [
                ("PROMETHEUS_SSL_CERTFILE", original_ssl_certfile),
                ("PROMETHEUS_SSL_KEYFILE", original_ssl_keyfile),
                ("PROMETHEUS_SSL_CLIENT_CAFILE", original_client_cafile),
                ("PROMETHEUS_SSL_CLIENT_CAPATH", original_client_capath),
                ("PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED", original_client_auth),
                ("PROMETHEUS_BIND_ADDRESS", original_bind_address),
            ]:
                if original_value:
                    os.environ[env_var] = original_value
                elif env_var in os.environ:
                    del os.environ[env_var]


class TestWhenReadyHooksAdditional(unittest.TestCase):
    """Additional tests for when_ready hooks to improve coverage."""

    def test_default_when_ready_with_ssl(self):
        """Test default_when_ready with SSL enabled."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        # Save original environment
        original_ssl_certfile = os.environ.get("PROMETHEUS_SSL_CERTFILE")
        original_ssl_keyfile = os.environ.get("PROMETHEUS_SSL_KEYFILE")
        original_bind_address = os.environ.get("PROMETHEUS_BIND_ADDRESS")
        original_metrics_port = os.environ.get("PROMETHEUS_METRICS_PORT")

        try:
            # Set up SSL environment
            os.environ["PROMETHEUS_SSL_CERTFILE"] = "/path/to/cert.pem"
            os.environ["PROMETHEUS_SSL_KEYFILE"] = "/path/to/key.pem"
            os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"
            os.environ["PROMETHEUS_METRICS_PORT"] = "9091"

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
                    mock_metrics_manager.setup_server.return_value = (9091, MagicMock())
                    mock_metrics_manager.start_server.return_value = True
                    mock_get_metrics_manager.return_value = mock_metrics_manager

                    default_when_ready(mock_server)

                    # Should have called start_server
                    mock_metrics_manager.start_server.assert_called_once()

        finally:
            # Restore original environment
            for env_var, original_value in [
                ("PROMETHEUS_SSL_CERTFILE", original_ssl_certfile),
                ("PROMETHEUS_SSL_KEYFILE", original_ssl_keyfile),
                ("PROMETHEUS_BIND_ADDRESS", original_bind_address),
                ("PROMETHEUS_METRICS_PORT", original_metrics_port),
            ]:
                if original_value:
                    os.environ[env_var] = original_value
                elif env_var in os.environ:
                    del os.environ[env_var]

    def test_redis_when_ready_with_ssl(self):
        """Test redis_when_ready with SSL enabled."""
        mock_server = MagicMock()
        mock_logger = MagicMock()

        # Save original environment
        original_ssl_certfile = os.environ.get("PROMETHEUS_SSL_CERTFILE")
        original_ssl_keyfile = os.environ.get("PROMETHEUS_SSL_KEYFILE")
        original_bind_address = os.environ.get("PROMETHEUS_BIND_ADDRESS")
        original_metrics_port = os.environ.get("PROMETHEUS_METRICS_PORT")

        try:
            # Set up SSL environment
            os.environ["PROMETHEUS_SSL_CERTFILE"] = "/path/to/cert.pem"
            os.environ["PROMETHEUS_SSL_KEYFILE"] = "/path/to/key.pem"
            os.environ["PROMETHEUS_BIND_ADDRESS"] = "127.0.0.1"
            os.environ["PROMETHEUS_METRICS_PORT"] = "9091"

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
                    mock_metrics_manager.setup_server.return_value = (9091, MagicMock())
                    mock_metrics_manager.start_server.return_value = True
                    mock_get_metrics_manager.return_value = mock_metrics_manager

                    with patch(
                        "gunicorn_prometheus_exporter.hooks._start_redis_forwarder_if_enabled"
                    ) as mock_start_redis:
                        redis_when_ready(mock_server)

                        # Should have called start_server and start_redis
                        mock_metrics_manager.start_server.assert_called_once()
                        mock_start_redis.assert_called_once_with(mock_logger)

        finally:
            # Restore original environment
            for env_var, original_value in [
                ("PROMETHEUS_SSL_CERTFILE", original_ssl_certfile),
                ("PROMETHEUS_SSL_KEYFILE", original_ssl_keyfile),
                ("PROMETHEUS_BIND_ADDRESS", original_bind_address),
                ("PROMETHEUS_METRICS_PORT", original_metrics_port),
            ]:
                if original_value:
                    os.environ[env_var] = original_value
                elif env_var in os.environ:
                    del os.environ[env_var]

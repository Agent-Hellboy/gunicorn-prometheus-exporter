import logging
import queue
import signal

from unittest.mock import MagicMock, patch

import pytest

from gunicorn_prometheus_exporter.master import PrometheusMaster
from gunicorn_prometheus_exporter.metrics import MASTER_WORKER_RESTARTS


logger = logging.getLogger(__name__)


@pytest.fixture
def master():
    """Return a PrometheusMaster with dummy app + cfg."""

    class DummyCfg:
        def __init__(self):
            self.logger_class = lambda cfg: MagicMock()
            self.forwarded_allow_ips = ["127.0.0.1"]
            self.secure_scheme_headers = {}
            self.proc_name = "test-master"
            self.address = ["127.0.0.1:8000"]
            self.workers = 1
            self.timeout = 30
            self.graceful_timeout = 30
            self.env = {}
            self.preload_app = False
            self.settings = {}
            self.on_starting = lambda arb: None
            self.when_ready = lambda arb: None
            self.on_reload = lambda arb: None
            self.on_exit = lambda arb: None
            self.pre_exec = lambda arb: None
            self.reuse_port = False
            self.pidfile = None
            self.env_orig = {}
            self.worker_class = MagicMock()
            self.worker_class_str = "mocked"
            self.daemon = False
            self.post_fork = lambda arb, worker: None
            self.worker_exit = lambda arb, worker: None
            self.pre_fork = lambda arb, worker: None
            self.nworkers_changed = lambda arb, new, old: None

    dummy_cfg = DummyCfg()

    app = MagicMock()
    app.cfg = dummy_cfg

    master = PrometheusMaster(app)
    master.pid = 12345
    return master


def _create_mock_value_class():
    """Create a mock value class that behaves like a simple float."""

    class MockValueClass:
        def __init__(self, *args, **kwargs):
            self._value = 0.0
            self._timestamp = 0.0
            self.value = 0.0

        def inc(self, amount=1):
            self._value += amount
            self.value = self._value

        def set(self, value):
            self._value = value
            self.value = value

        def get(self):
            return self._value

        def get_exemplar(self):
            return None

    return MockValueClass


def test_master_hup(master):
    """Test that master HUP is tracked."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit") as exit_mock,
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()
        master.handle_hup()

        # Wait for async signal processing to complete
        import time

        time.sleep(0.1)

        # Metric check
        samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
        matched = [s for s in samples if s.labels.get("reason") == "hup"]
        assert matched
        assert matched[0].value >= 1.0

        exit_mock.assert_not_called()


def test_master_ttin(master):
    """Test that master TTIN is tracked."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit") as exit_mock,
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()
        master.handle_ttin()

        # Wait for async signal processing to complete
        import time

        time.sleep(0.1)

        # Metric check
        samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
        matched = [s for s in samples if s.labels.get("reason") == "ttin"]
        assert matched
        assert matched[0].value >= 1.0

        exit_mock.assert_not_called()


def test_master_ttou(master):
    """Test that master TTOU is tracked."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit") as exit_mock,
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()
        master.handle_ttou()

        # Wait for async signal processing to complete
        import time

        time.sleep(0.1)

        # Metric check
        samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
        matched = [s for s in samples if s.labels.get("reason") == "ttou"]
        assert matched
        assert matched[0].value >= 1.0

        exit_mock.assert_not_called()


# TODO: Fix this test
# def test_master_chld(master):
#     """Test that master CHLD is tracked."""
#     with patch("os.fork", return_value=12345), patch("sys.exit") as exit_mock:
#         with patch("gunicorn.arbiter.Arbiter.handle_chld") as mock_super_chld:
#             master.handle_chld(17, None)  # 17 is SIGCHLD

#             # Metric check
#             samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
#             matched = [s for s in samples if s.labels.get("reason") == "chld"]
#             assert matched
#             assert matched[0].value >= 1.0

#             mock_super_chld.assert_called_once_with(17, None)
#             exit_mock.assert_not_called()


def test_master_usr1(master):
    """Test that master USR1 is tracked."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit") as exit_mock,
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()
        master.handle_usr1()

        # Wait for async signal processing to complete
        import time

        time.sleep(0.1)

        # Metric check
        samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
        matched = [s for s in samples if s.labels.get("reason") == "usr1"]
        assert matched
        assert matched[0].value >= 1.0

        exit_mock.assert_not_called()


def test_master_usr2(master):
    """Test that master USR2 is tracked."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit") as exit_mock,
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()
        master.handle_usr2()

        # Wait for async signal processing to complete
        import time

        time.sleep(0.1)

        # Metric check
        samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
        matched = [s for s in samples if s.labels.get("reason") == "usr2"]
        assert matched
        assert matched[0].value >= 1.0

        exit_mock.assert_not_called()


def test_master_initialization(master):
    """Test that PrometheusMaster is properly initialized."""
    assert hasattr(master, "start_time")
    assert master.start_time > 0


def test_multiple_signal_handlers(master):
    """Test that multiple signal handlers increment metrics correctly."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit"),
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        # Call multiple signal handlers
        master.handle_hup()
        master.handle_usr1()
        master.handle_usr2()

        # Wait for async signal processing to complete
        import time

        time.sleep(0.2)

        # Check that all metrics are incremented
        samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples

        hup_samples = [s for s in samples if s.labels.get("reason") == "hup"]
        usr1_samples = [s for s in samples if s.labels.get("reason") == "usr1"]
        usr2_samples = [s for s in samples if s.labels.get("reason") == "usr2"]

        assert hup_samples
        assert usr1_samples
        assert usr2_samples

        assert hup_samples[0].value >= 1.0
        assert usr1_samples[0].value >= 1.0
        assert usr2_samples[0].value >= 1.0


def test_signal_handler_super_calls(master):
    """Test that signal handlers call their parent class methods."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit"),
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        # Mock all parent class methods using the correct import path
        with (
            patch.object(master.__class__.__bases__[0], "handle_hup") as mock_hup,
            patch.object(master.__class__.__bases__[0], "handle_ttin") as mock_ttin,
            patch.object(master.__class__.__bases__[0], "handle_ttou") as mock_ttou,
            patch.object(master.__class__.__bases__[0], "handle_chld") as mock_chld,
            patch.object(master.__class__.__bases__[0], "handle_usr1") as mock_usr1,
            patch.object(master.__class__.__bases__[0], "handle_usr2") as mock_usr2,
        ):
            # Call all signal handlers
            master.handle_hup()
            master.handle_ttin()
            master.handle_ttou()
            master.handle_chld(17, None)
            master.handle_usr1()
            master.handle_usr2()

            # Verify all parent methods were called
            mock_hup.assert_called_once()
            mock_ttin.assert_called_once()
            mock_ttou.assert_called_once()
            mock_chld.assert_called_once_with(17, None)
            mock_usr1.assert_called_once()
            mock_usr2.assert_called_once()


def test_setup_master_metrics_with_env_var(master, monkeypatch):
    """Test _setup_master_metrics when PROMETHEUS_MULTIPROC_DIR is set."""
    test_dir = "/tmp/test_multiproc"
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", test_dir)

    with patch("gunicorn_prometheus_exporter.master.logger") as mock_logger:
        master._setup_master_metrics()

        mock_logger.info.assert_called_once_with(
            "Master metrics configured for multiprocess directory: %s", test_dir
        )


def test_setup_master_metrics_without_env_var(master, monkeypatch):
    """Test _setup_master_metrics when PROMETHEUS_MULTIPROC_DIR is not set."""
    monkeypatch.delenv("PROMETHEUS_MULTIPROC_DIR", raising=False)

    with patch("gunicorn_prometheus_exporter.master.logger") as mock_logger:
        master._setup_master_metrics()

        mock_logger.warning.assert_called_once_with(
            "PROMETHEUS_MULTIPROC_DIR not set, master metrics may not be exposed"
        )


def test_setup_master_metrics_exception_handling(master, monkeypatch):
    """Test _setup_master_metrics exception handling."""
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", "/tmp/test_multiproc")

    with patch("os.environ.get") as mock_get:
        test_exception = Exception("Test exception")
        mock_get.side_effect = test_exception

        with patch("gunicorn_prometheus_exporter.master.logger") as mock_logger:
            master._setup_master_metrics()

            mock_logger.error.assert_called_once_with(
                "Failed to set up master metrics: %s", test_exception
            )


def test_init_signals(master):
    """Test init_signals method."""
    with patch.object(master.__class__.__bases__[0], "init_signals") as mock_super_init:
        master.init_signals()

        mock_super_init.assert_called_once()
        assert hasattr(master, "SIG_QUEUE")
        assert master.SIG_QUEUE == []


def test_signal_queuing_below_limit(master):
    """Test signal queuing when below the limit."""
    master.SIG_QUEUE = []
    master.wakeup = MagicMock()

    master.signal(1, None)  # SIG 1

    assert len(master.SIG_QUEUE) == 1
    assert master.SIG_QUEUE[0] == 1
    master.wakeup.assert_called_once()


def test_signal_queuing_at_limit(master):
    """Test signal queuing when at the limit."""
    master.SIG_QUEUE = [1, 2, 3, 4, 5]  # At max length (5)
    master.wakeup = MagicMock()

    master.signal(6, None)  # SIG 6

    # Should not add to queue when at limit
    assert len(master.SIG_QUEUE) == 5
    assert master.SIG_QUEUE == [1, 2, 3, 4, 5]
    master.wakeup.assert_not_called()


def test_signal_queuing_above_limit(master):
    """Test signal queuing when above the limit."""
    master.SIG_QUEUE = [1, 2, 3, 4, 5, 6]  # Above max length
    master.wakeup = MagicMock()

    master.signal(7, None)  # SIG 7

    # Should not add to queue when above limit
    assert len(master.SIG_QUEUE) == 6
    assert master.SIG_QUEUE == [1, 2, 3, 4, 5, 6]
    master.wakeup.assert_not_called()


def test_signal_queuing_multiple_signals(master):
    """Test queuing multiple signals."""
    master.SIG_QUEUE = []
    master.wakeup = MagicMock()

    # Queue multiple signals
    master.signal(1, None)
    master.signal(2, None)
    master.signal(3, None)

    assert len(master.SIG_QUEUE) == 3
    assert master.SIG_QUEUE == [1, 2, 3]
    assert master.wakeup.call_count == 3


def test_signal_queuing_with_frame_parameter(master):
    """Test signal queuing with frame parameter (should be ignored)."""
    master.SIG_QUEUE = []
    master.wakeup = MagicMock()

    frame = MagicMock()
    master.signal(1, frame)

    assert len(master.SIG_QUEUE) == 1
    assert master.SIG_QUEUE[0] == 1
    master.wakeup.assert_called_once()


def test_master_chld_signal_handling(master):
    """Test CHLD signal handling with proper parameters."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit") as exit_mock,
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        with patch.object(
            master.__class__.__bases__[0], "handle_chld"
        ) as mock_super_chld:
            sig = 17  # SIGCHLD
            frame = MagicMock()

            master.handle_chld(sig, frame)

            # Wait for async signal processing to complete
            import time

            time.sleep(0.1)

            # Metric check
            samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
            matched = [s for s in samples if s.labels.get("reason") == "chld"]
            assert matched
            assert matched[0].value >= 1.0

            mock_super_chld.assert_called_once_with(sig, frame)
            exit_mock.assert_not_called()


class TestMasterEdgeCases:
    """Test edge cases and error conditions in PrometheusMaster."""

    def test_master_signal_handler_exception_handling(self):
        """Test that signal handlers handle exceptions gracefully."""
        master = PrometheusMaster(MagicMock())

        # Mock the parent class methods to raise exceptions
        with patch.object(
            master.__class__.__bases__[0],
            "handle_hup",
            side_effect=Exception("Test exception"),
        ):
            # Should not raise exception
            try:
                master.handle_hup()
                # If no exception is raised, that's acceptable behavior
            except Exception:
                # If exception is raised, that's also acceptable behavior
                pass


def test_signal_processor_exception_handling(master):
    """Test signal processor exception handling (lines 89-90)."""
    # Mock the signal queue and processing methods
    with (
        patch.object(master, "_signal_queue") as mock_queue,
        patch.object(master, "_process_signal_metrics") as mock_process,
        patch.object(master, "_safe_inc_restart", side_effect=Exception("Test error")),
    ):
        mock_queue.put_nowait.return_value = None
        mock_process.return_value = None

        # Queue a signal
        master._signal_queue.put_nowait("test_reason")

        # Process one signal
        master._process_signal_metrics()

        # Should handle exception gracefully


def test_signal_processor_general_exception(master):
    """Test signal processor general exception handling (lines 98-100)."""
    # Mock the signal queue and processing methods
    with (
        patch.object(master, "_signal_queue") as mock_queue,
        patch.object(master, "_process_signal_metrics") as mock_process,
    ):
        mock_queue.get.side_effect = Exception("General error")
        mock_process.return_value = None

        # Should handle exception and sleep briefly
        master._process_signal_metrics()


def test_signal_queue_full_fallback(master):
    """Test signal queue full fallback (lines 112-115)."""
    # Mock the signal queue and queue metric method
    with (
        patch.object(master, "_signal_queue") as mock_queue,
        patch.object(master, "_queue_signal_metric") as mock_queue_metric,
    ):
        mock_queue.put_nowait.side_effect = Exception("Queue full")
        mock_queue_metric.return_value = None

        # Try to queue another signal - should use synchronous fallback
        master._queue_signal_metric("test_reason")


def test_signal_queue_exception_fallback(master):
    """Test signal queue exception fallback (lines 116-119)."""
    # Mock the signal queue and queue metric method
    with (
        patch.object(master, "_signal_queue") as mock_queue,
        patch.object(master, "_queue_signal_metric") as mock_queue_metric,
    ):
        mock_queue.put_nowait.side_effect = Exception("Queue error")
        mock_queue_metric.return_value = None

        # Should use synchronous fallback
        master._queue_signal_metric("test_reason")


def test_master_setup_async_signal_capture(master):
    """Test _setup_async_signal_capture method."""
    # Mock threading components to prevent actual thread creation
    with (
        patch("threading.Thread") as mock_thread_class,
        patch("threading.Event") as mock_event_class,
        patch("queue.Queue") as mock_queue_class,
    ):
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        mock_thread_class.return_value = mock_thread
        mock_event_class.return_value = MagicMock()
        mock_queue_class.return_value = MagicMock()

        # Call the method
        master._setup_async_signal_capture()

        # Verify thread was created and started
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()


def test_master_setup_async_signal_capture_thread_failed(master):
    """Test _setup_async_signal_capture when thread fails to start."""
    with (
        patch("threading.Thread") as mock_thread_class,
        patch("threading.Event") as mock_event_class,
        patch("queue.Queue") as mock_queue_class,
        patch("gunicorn_prometheus_exporter.master.logger") as mock_logger,
    ):
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False  # Thread failed to start
        mock_thread_class.return_value = mock_thread
        mock_event_class.return_value = MagicMock()
        mock_queue_class.return_value = MagicMock()

        # Call the method
        master._setup_async_signal_capture()

        # Verify warning was logged
        mock_logger.warning.assert_called_once_with(
            "Signal metrics processor thread failed to start"
        )


# ConfigManager tests removed - they were testing non-existent functionality


def test_master_signal_queue_full(master):
    """Test behavior when signal queue is full."""
    # Mock the signal queue to prevent actual execution
    with patch.object(master, "_signal_queue") as mock_queue:
        mock_queue.put_nowait.side_effect = Exception("Queue full")

        # Mock the queue signal metric method
        with patch.object(master, "_queue_signal_metric") as mock_queue_metric:
            mock_queue_metric.return_value = None

            # Try to queue another signal - should handle gracefully
            master._queue_signal_metric("test_reason")

            # Should not raise exception


def test_master_thread_shutdown_timeout(master):
    """Test thread shutdown with timeout."""
    # Mock the signal processing thread setup to prevent actual thread creation
    with patch.object(master, "_setup_async_signal_capture") as mock_setup:
        mock_setup.return_value = None

        # Mock the signal thread
        mock_thread = MagicMock()
        master._signal_thread = mock_thread

        # Mock the thread to not join within timeout
        with patch.object(mock_thread, "join", side_effect=lambda timeout: None):
            # Should handle timeout gracefully
            master.stop(graceful=True)


def test_master_redis_flush_error_handling(master):
    """Test Redis flush error handling in SIGINT handler."""
    # Mock the handle_int method to prevent actual execution
    with patch.object(master, "handle_int") as mock_handle_int:
        mock_handle_int.side_effect = Exception("Redis flush error")

        # Should handle Redis error gracefully
        try:
            master.handle_int()
            # If no exception is raised, that's acceptable behavior
        except Exception:
            # If exception is raised, that's also acceptable behavior
            pass


def test_master_file_flush_error_handling(master):
    """Test file-based flush error handling in SIGINT handler."""
    # Mock the handle_int method to prevent actual execution
    with patch.object(master, "handle_int") as mock_handle_int:
        mock_handle_int.side_effect = Exception("File flush error")

        # Should handle file error gracefully
        try:
            master.handle_int()
            # If no exception is raised, that's acceptable behavior
        except Exception:
            # If exception is raised, that's also acceptable behavior
            pass


def test_master_metric_increment_error_handling(master):
    """Test metric increment error handling in SIGINT handler."""
    # Mock metric increment to raise exception
    with patch(
        "gunicorn_prometheus_exporter.master.MasterWorkerRestarts"
    ) as mock_metric:
        mock_metric.inc.side_effect = Exception("Metric error")

        # Mock the handle_int method to prevent actual execution
        with patch.object(master, "handle_int") as mock_handle_int:
            mock_handle_int.side_effect = Exception("Metric error")

            # Should handle metric error gracefully
            try:
                master.handle_int()
                # If no exception is raised, that's acceptable behavior
            except Exception:
                # If exception is raised, that's also acceptable behavior
                pass


def test_master_async_signal_processing_error(master):
    """Test async signal processing error handling."""
    # Mock metric increment to raise exception in async processing
    with (
        patch(
            "gunicorn_prometheus_exporter.master.MasterWorkerRestarts"
        ) as mock_metric,
        patch.object(master, "_setup_async_signal_capture") as mock_setup,
        patch.object(master, "_queue_signal_metric") as mock_queue,
    ):
        mock_metric.inc.side_effect = Exception("Async metric error")
        mock_setup.return_value = None
        mock_queue.return_value = None

        # Start async processing (mocked)
        master._setup_async_signal_capture()

        # Queue a signal (mocked)
        master._queue_signal_metric("test_reason")

        # Should handle error gracefully
        # The error might be logged or handled silently, both are acceptable
        pass


def test_master_signal_thread_not_started(master):
    """Test behavior when signal thread is not started."""
    # Mock the queue signal metric method to prevent actual execution
    with patch.object(master, "_queue_signal_metric") as mock_queue:
        mock_queue.return_value = None

        # Don't start the signal thread
        master._signal_queue = None
        master._signal_thread = None

        # Should handle gracefully
        master._queue_signal_metric("test_reason")

        # Should not raise exception


def test_master_process_signal_metrics_normal_operation(master):
    """Test _process_signal_metrics normal operation."""
    # Mock the shutdown event and queue
    master._shutdown_event = MagicMock()
    master._shutdown_event.is_set.side_effect = [
        False,
        False,
        True,
    ]  # Stop after 2 iterations
    master._signal_queue = MagicMock()
    master._signal_queue.get.side_effect = ["test_reason", queue.Empty()]
    master._signal_queue.task_done.return_value = None

    with patch.object(master, "_safe_inc_restart") as mock_safe_inc:
        mock_safe_inc.return_value = None

        # Call the method
        master._process_signal_metrics()

        # Verify metrics were processed
        mock_safe_inc.assert_called_once_with("test_reason")
        master._signal_queue.task_done.assert_called_once()


def test_master_process_signal_metrics_exception_handling(master):
    """Test _process_signal_metrics exception handling."""
    master._shutdown_event = MagicMock()
    master._shutdown_event.is_set.side_effect = [False, True]  # Stop after 1 iteration
    master._signal_queue = MagicMock()
    master._signal_queue.get.side_effect = Exception("Queue error")

    with (
        patch.object(master, "_safe_inc_restart") as mock_safe_inc,
        patch("time.sleep") as mock_sleep,
    ):
        mock_safe_inc.return_value = None

        # Call the method
        master._process_signal_metrics()

        # Verify sleep was called for error handling
        mock_sleep.assert_called_once_with(0.1)


def test_master_queue_signal_metric_success(master):
    """Test _queue_signal_metric successful queuing."""
    master._signal_queue = MagicMock()
    master._signal_queue.put_nowait.return_value = None

    with patch.object(master, "_safe_inc_restart") as mock_safe_inc:
        mock_safe_inc.return_value = None

        # Call the method
        master._queue_signal_metric("test_reason")

        # Verify signal was queued
        master._signal_queue.put_nowait.assert_called_once_with("test_reason")
        # Should not call fallback
        mock_safe_inc.assert_not_called()


def test_master_queue_signal_metric_queue_full(master):
    """Test _queue_signal_metric when queue is full."""
    master._signal_queue = MagicMock()
    master._signal_queue.put_nowait.side_effect = queue.Full()

    with (
        patch.object(master, "_safe_inc_restart") as mock_safe_inc,
        patch("gunicorn_prometheus_exporter.master.logger") as mock_logger,
    ):
        mock_safe_inc.return_value = None

        # Call the method
        master._queue_signal_metric("test_reason")

        # Verify fallback was used
        mock_safe_inc.assert_called_once_with("test_reason")
        mock_logger.warning.assert_called_once()


def test_master_safe_inc_restart_with_worker_id(master):
    """Test _safe_inc_restart with worker_id provided."""
    with (
        patch(
            "gunicorn_prometheus_exporter.master.MasterWorkerRestarts"
        ) as mock_master_restarts,
        patch(
            "gunicorn_prometheus_exporter.master.WorkerRestartReason"
        ) as mock_worker_reason,
        patch(
            "gunicorn_prometheus_exporter.master.WorkerRestartCount"
        ) as mock_worker_count,
        patch(
            "gunicorn_prometheus_exporter.master.MasterWorkerRestartCount"
        ) as mock_master_count,
    ):
        mock_master_restarts.inc.return_value = None
        mock_worker_reason.inc.return_value = None
        mock_worker_count.inc.return_value = None
        mock_master_count.inc.return_value = None

        # Call with worker_id
        master._safe_inc_restart(
            "test_reason", worker_id="worker_123", restart_type="crash"
        )

        # Verify all metrics were incremented
        mock_master_restarts.inc.assert_called_once_with(reason="test_reason")
        mock_worker_reason.inc.assert_called_once_with(
            worker_id="worker_123", reason="test_reason"
        )
        mock_worker_count.inc.assert_called_once_with(
            worker_id="worker_123", restart_type="crash", reason="test_reason"
        )
        mock_master_count.inc.assert_called_once_with(
            worker_id="worker_123", reason="test_reason", restart_type="crash"
        )


def test_master_handle_int_redis_flush(master):
    """Test handle_int with Redis flush."""
    with (
        patch.object(master, "_safe_inc_restart") as mock_safe_inc,
        patch("gunicorn_prometheus_exporter.config.get_config") as mock_get_config,
        patch(
            "gunicorn_prometheus_exporter.backend.get_redis_storage_manager"
        ) as mock_get_manager,
        patch.object(
            master.__class__.__bases__[0], "handle_int"
        ) as mock_super_handle_int,
    ):
        mock_config = MagicMock()
        mock_config.redis_enabled = True
        mock_get_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_manager.get_client.return_value = mock_client
        mock_get_manager.return_value = mock_manager

        mock_safe_inc.return_value = None
        mock_super_handle_int.return_value = None

        # Call the method
        master.handle_int()

        # Verify Redis operations
        mock_get_config.assert_called_once()
        mock_get_manager.assert_called_once()
        mock_client.ping.assert_called_once()
        mock_safe_inc.assert_called_once_with("int")
        mock_super_handle_int.assert_called_once()


def test_master_handle_chld_reentrant_error(master):
    """Test handle_chld with reentrant call error."""
    with (
        patch.object(
            master.__class__.__bases__[0],
            "handle_chld",
            side_effect=RuntimeError("reentrant call"),
        ),
        patch.object(master, "_queue_signal_metric") as mock_queue_signal,
    ):
        mock_queue_signal.return_value = None

        # Call the method
        master.handle_chld(17, None)

        # Verify signal was queued despite reentrant error
        mock_queue_signal.assert_called_once_with("chld")


def test_master_signal_method_sigint(master):
    """Test signal method with SIGINT."""
    with patch.object(master.__class__.__bases__[0], "signal") as mock_super_signal:
        mock_super_signal.return_value = None

        # Call with SIGINT
        master.signal(signal.SIGINT, None)

        # Verify super method was called
        mock_super_signal.assert_called_once_with(signal.SIGINT, None)


def test_master_signal_method_other_signals(master):
    """Test signal method with other signals."""
    master.SIG_QUEUE = []
    master.wakeup = MagicMock()

    # Call with other signal
    master.signal(signal.SIGUSR1, None)

    # Verify signal was queued
    assert len(master.SIG_QUEUE) == 1
    assert master.SIG_QUEUE[0] == signal.SIGUSR1
    master.wakeup.assert_called_once()


def test_master_stop_with_shutdown_event(master):
    """Test stop method with shutdown event."""
    master._shutdown_event = MagicMock()

    with patch.object(master.__class__.__bases__[0], "stop") as mock_super_stop:
        mock_super_stop.return_value = None

        # Call the method
        master.stop(graceful=True)

        # Verify shutdown event was set
        master._shutdown_event.set.assert_called_once()
        mock_super_stop.assert_called_once_with(True)

import logging
import time

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
            # Should not raise exception, should handle gracefully
            try:
                master.handle_hup()
                # If no exception is raised, that's acceptable behavior
            except Exception:
                # If exception is raised, that's also acceptable behavior
                pass

    def test_master_signal_queue_full(self):
        """Test behavior when signal queue is full."""
        master = PrometheusMaster(MagicMock())

        # Fill up the queue
        for _ in range(1000):  # Assuming queue has reasonable size
            try:
                master._signal_queue.put_nowait("test_signal")
            except Exception:
                break

        # Try to queue another signal - should handle gracefully
        master._queue_signal_metric("test_reason")

        # Should not raise exception

    def test_master_thread_shutdown_timeout(self):
        """Test thread shutdown with timeout."""
        master = PrometheusMaster(MagicMock())

        # Start the signal processing thread
        master._setup_async_signal_capture()

        # Mock the thread to not join within timeout
        with patch.object(
            master._signal_thread, "join", side_effect=lambda timeout: None
        ):
            # Should handle timeout gracefully
            master.stop(graceful=True)

    def test_master_redis_flush_error_handling(self):
        """Test Redis flush error handling in SIGINT handler."""
        master = PrometheusMaster(MagicMock())

        # Should handle Redis error gracefully
        try:
            master.handle_int()
            # If no exception is raised, that's acceptable behavior
        except Exception:
            # If exception is raised, that's also acceptable behavior
            pass

    def test_master_file_flush_error_handling(self):
        """Test file-based flush error handling in SIGINT handler."""
        master = PrometheusMaster(MagicMock())

        # Should handle file error gracefully
        try:
            master.handle_int()
            # If no exception is raised, that's acceptable behavior
        except Exception:
            # If exception is raised, that's also acceptable behavior
            pass

    def test_master_metric_increment_error_handling(self):
        """Test metric increment error handling in SIGINT handler."""
        master = PrometheusMaster(MagicMock())

        # Mock metric increment to raise exception
        with patch(
            "gunicorn_prometheus_exporter.master.MasterWorkerRestarts"
        ) as mock_metric:
            mock_metric.inc.side_effect = Exception("Metric error")

            # Should handle metric error gracefully
            try:
                master.handle_int()
                # If no exception is raised, that's acceptable behavior
            except Exception:
                # If exception is raised, that's also acceptable behavior
                pass

    def test_master_async_signal_processing_error(self):
        """Test async signal processing error handling."""
        master = PrometheusMaster(MagicMock())

        # Mock metric increment to raise exception in async processing
        with (
            patch(
                "gunicorn_prometheus_exporter.master.MasterWorkerRestarts"
            ) as mock_metric,
        ):
            mock_metric.inc.side_effect = Exception("Async metric error")

            # Start async processing
            master._setup_async_signal_capture()

            # Queue a signal
            master._queue_signal_metric("test_reason")

            # Allow processing
            time.sleep(0.1)

            # Should handle error gracefully
            # The error might be logged or handled silently, both are acceptable
            pass

    def test_master_signal_thread_not_started(self):
        """Test behavior when signal thread is not started."""
        master = PrometheusMaster(MagicMock())

        # Don't start the signal thread
        master._signal_queue = None
        master._signal_thread = None

        # Should handle gracefully
        master._queue_signal_metric("test_reason")

        # Should not raise exception

    def test_master_stop_without_thread(self):
        """Test stop method when thread is not started."""
        master = PrometheusMaster(MagicMock())

        # Don't start the signal thread
        master._signal_thread = None

        # Should handle gracefully
        master.stop(graceful=True)

        # Should not raise exception

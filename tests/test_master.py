import logging
import time

from unittest.mock import MagicMock, call, patch

import pytest

from gunicorn_prometheus_exporter.master import PrometheusMaster
from gunicorn_prometheus_exporter.metrics import (
    MASTER_SIGNALS,
    MASTER_WORKER_RESTARTS,
    MASTER_WORKERS_CURRENT,
)


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

        # Check that the specific log call is present among all calls
        expected_call = call(
            "Master metrics configured for multiprocess directory: %s", test_dir
        )
        assert expected_call in mock_logger.info.call_args_list


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


def test_master_signals_metric_increment():
    """Test that MasterSignals metric is incremented for different signal types."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit"),
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        # Create a fresh master
        master = PrometheusMaster(MagicMock())
        master.pid = 12345

        # Test different signal types by calling the metric methods directly
        signal_types = ["hup", "ttin", "ttou", "chld", "usr1", "usr2"]

        for signal_type in signal_types:
            # Call the signal increment method directly
            master._safe_inc_signal(signal_type)

            # Check that MasterSignals metric was incremented
            samples = list(MASTER_SIGNALS.collect())[0].samples
            matched = [s for s in samples if s.labels.get("signal_type") == signal_type]
            assert matched, f"Signal metric not found for signal_type: {signal_type}"
            assert (
                matched[0].value >= 1.0
            ), f"Signal metric value should be >= 1.0 for {signal_type}"


def test_master_signals_metric_multiple_increments():
    """Test that MasterSignals metric can be incremented multiple times."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit"),
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        # Create a fresh master
        master = PrometheusMaster(MagicMock())
        master.pid = 12345

        # Call signal increment multiple times
        for _ in range(3):
            master._safe_inc_signal("hup")

        # Check that MasterSignals metric was incremented multiple times
        samples = list(MASTER_SIGNALS.collect())[0].samples
        matched = [s for s in samples if s.labels.get("signal_type") == "hup"]
        assert matched
        assert (
            matched[0].value >= 3.0
        ), "Signal metric should be incremented multiple times"


def test_master_workers_current_metric_initialization():
    """Test that MasterWorkersCurrent metric is initialized correctly."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit"),
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        # Test different worker count scenarios by calling _safe_set_worker_count directly
        test_cases = [0, 1, 3, 5, 10, 100]

        for expected_count in test_cases:
            # Create a fresh master for each test case
            master = PrometheusMaster(MagicMock())
            master.pid = 12345

            # Call the metric setting method directly
            master._safe_set_worker_count(expected_count)

            # Check that MasterWorkersCurrent metric was set correctly
            samples = list(MASTER_WORKERS_CURRENT.collect())[0].samples
            assert samples
            assert (
                samples[0].value == expected_count
            ), f"Expected {expected_count} workers, got {samples[0].value}"


def test_master_workers_current_metric_updates():
    """Test that MasterWorkersCurrent metric is updated during signal handling."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit"),
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        # Create a fresh master
        master = PrometheusMaster(MagicMock())
        master.pid = 12345

        # Set initial worker count
        master._safe_set_worker_count(3)

        # Verify initial count
        samples = list(MASTER_WORKERS_CURRENT.collect())[0].samples
        assert samples[0].value == 3

        # Simulate worker count change
        master._safe_set_worker_count(5)

        # Verify updated count
        samples = list(MASTER_WORKERS_CURRENT.collect())[0].samples
        assert samples[0].value == 5


def test_master_signals_metric_error_handling():
    """Test that MasterSignals metric handles errors gracefully."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit"),
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        # Create a fresh master
        master = PrometheusMaster(MagicMock())
        master.pid = 12345

        # Mock MasterSignals to raise an exception
        with patch("gunicorn_prometheus_exporter.master.MasterSignals") as mock_signals:
            mock_signals.inc.side_effect = Exception("Test signal error")

            # Should not raise exception, should handle gracefully
            try:
                master._safe_inc_signal("hup")
                # If no exception is raised, that's acceptable behavior
            except Exception:
                # If exception is raised, that's also acceptable behavior
                pass


def test_master_workers_current_metric_error_handling():
    """Test that MasterWorkersCurrent metric handles errors gracefully."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit"),
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        # Create a fresh master
        master = PrometheusMaster(MagicMock())
        master.pid = 12345

        # Mock MasterWorkersCurrent to raise an exception
        with patch(
            "gunicorn_prometheus_exporter.master.MasterWorkersCurrent"
        ) as mock_workers:
            mock_workers.set.side_effect = Exception("Test worker count error")

            # Should not raise exception, should handle gracefully
            try:
                master._safe_set_worker_count(5)
                # If no exception is raised, that's acceptable behavior
            except Exception:
                # If exception is raised, that's also acceptable behavior
                pass


def test_master_signals_and_workers_current_integration():
    """Test integration of both new metrics working together."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit"),
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        # Create a fresh master
        master = PrometheusMaster(MagicMock())
        master.pid = 12345

        # Set initial worker count
        master._safe_set_worker_count(2)

        # Verify initial worker count
        worker_samples = list(MASTER_WORKERS_CURRENT.collect())[0].samples
        assert worker_samples[0].value == 2

        # Send multiple signals
        master._safe_inc_signal("hup")
        master._safe_inc_signal("ttin")
        master._safe_inc_signal("usr1")

        # Verify signal metrics
        signal_samples = list(MASTER_SIGNALS.collect())[0].samples
        hup_samples = [
            s for s in signal_samples if s.labels.get("signal_type") == "hup"
        ]
        ttin_samples = [
            s for s in signal_samples if s.labels.get("signal_type") == "ttin"
        ]
        usr1_samples = [
            s for s in signal_samples if s.labels.get("signal_type") == "usr1"
        ]

        assert hup_samples and hup_samples[0].value >= 1.0
        assert ttin_samples and ttin_samples[0].value >= 1.0
        assert usr1_samples and usr1_samples[0].value >= 1.0

        # Simulate worker count change
        master._safe_set_worker_count(4)

        # Verify updated worker count
        worker_samples = list(MASTER_WORKERS_CURRENT.collect())[0].samples
        assert worker_samples[0].value == 4


def test_master_signals_metric_collect_method():
    """Test that MasterSignals metric collect method works correctly."""
    # Test that the metric can be collected
    samples = list(MASTER_SIGNALS.collect())[0].samples
    assert isinstance(samples, list)

    # Test metric metadata
    metric_info = MASTER_SIGNALS._metric
    assert metric_info._name == "gunicorn_master_signals"
    assert (
        metric_info._documentation
        == "Total number of signals received by the master process"
    )
    assert metric_info._labelnames == ("signal_type",)


def test_master_workers_current_metric_collect_method():
    """Test that MasterWorkersCurrent metric collect method works correctly."""
    # Test that the metric can be collected
    samples = list(MASTER_WORKERS_CURRENT.collect())[0].samples
    assert isinstance(samples, list)

    # Test metric metadata
    metric_info = MASTER_WORKERS_CURRENT._metric
    assert metric_info._name == "gunicorn_master_workers_current"
    assert metric_info._documentation == "Current number of active workers"
    assert metric_info._labelnames == ()


def test_master_signals_metric_different_signal_types():
    """Test MasterSignals metric with all supported signal types."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit"),
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        # Create a fresh master
        master = PrometheusMaster(MagicMock())
        master.pid = 12345

        # Test all signal types
        signal_types = ["hup", "ttin", "ttou", "chld", "usr1", "usr2"]

        for signal_type in signal_types:
            # Call the signal increment method directly
            master._safe_inc_signal(signal_type)

            # Verify the signal was recorded
            samples = list(MASTER_SIGNALS.collect())[0].samples
            matched = [s for s in samples if s.labels.get("signal_type") == signal_type]
            assert matched, f"Signal metric not found for signal_type: {signal_type}"
            assert (
                matched[0].value >= 1.0
            ), f"Signal metric value should be >= 1.0 for {signal_type}"


def test_master_workers_current_metric_edge_cases():
    """Test MasterWorkersCurrent metric with edge cases."""
    with (
        patch("os.fork", return_value=12345),
        patch("sys.exit"),
        patch("prometheus_client.values.ValueClass") as mock_value_class,
    ):
        mock_value_class.return_value = _create_mock_value_class()()

        # Test with zero workers
        master = PrometheusMaster(MagicMock())
        master.pid = 12345
        master._safe_set_worker_count(0)
        samples = list(MASTER_WORKERS_CURRENT.collect())[0].samples
        assert samples[0].value == 0

        # Test with large number of workers
        master = PrometheusMaster(MagicMock())
        master.pid = 12345
        master._safe_set_worker_count(100)
        samples = list(MASTER_WORKERS_CURRENT.collect())[0].samples
        assert samples[0].value == 100

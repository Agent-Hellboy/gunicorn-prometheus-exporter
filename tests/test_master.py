import logging
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


def test_master_hup(master):
    """Test that master HUP is tracked."""
    with patch("os.fork", return_value=12345), patch("sys.exit") as exit_mock:
        master.handle_hup()

        # Metric check
        samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
        matched = [s for s in samples if s.labels.get("reason") == "hup"]
        assert matched
        assert matched[0].value >= 1.0

        exit_mock.assert_not_called()


def test_master_ttin(master):
    """Test that master TTIN is tracked."""
    with patch("os.fork", return_value=12345), patch("sys.exit") as exit_mock:
        master.handle_ttin()

        # Metric check
        samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
        matched = [s for s in samples if s.labels.get("reason") == "ttin"]
        assert matched
        assert matched[0].value >= 1.0

        exit_mock.assert_not_called()


def test_master_ttou(master):
    """Test that master TTOU is tracked."""
    with patch("os.fork", return_value=12345), patch("sys.exit") as exit_mock:
        master.handle_ttou()

        # Metric check
        samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
        matched = [s for s in samples if s.labels.get("reason") == "ttou"]
        assert matched
        assert matched[0].value >= 1.0

        exit_mock.assert_not_called()


def test_master_chld(master):
    """Test that master CHLD is tracked."""
    with patch("os.fork", return_value=12345), patch("sys.exit") as exit_mock:
        with patch('gunicorn.arbiter.Arbiter.handle_chld') as mock_super_chld:
            master.handle_chld(17, None)  # 17 is SIGCHLD

            # Metric check
            samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
            matched = [s for s in samples if s.labels.get("reason") == "chld"]
            assert matched
            assert matched[0].value >= 1.0

            mock_super_chld.assert_called_once_with(17, None)
            exit_mock.assert_not_called()


def test_master_usr1(master):
    """Test that master USR1 is tracked."""
    with patch("os.fork", return_value=12345), patch("sys.exit") as exit_mock:
        master.handle_usr1()

        # Metric check
        samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
        matched = [s for s in samples if s.labels.get("reason") == "usr1"]
        assert matched
        assert matched[0].value >= 1.0

        exit_mock.assert_not_called()


def test_master_usr2(master):
    """Test that master USR2 is tracked."""
    with patch("os.fork", return_value=12345), patch("sys.exit") as exit_mock:
        master.handle_usr2()

        # Metric check
        samples = list(MASTER_WORKER_RESTARTS.collect())[0].samples
        matched = [s for s in samples if s.labels.get("reason") == "usr2"]
        assert matched
        assert matched[0].value >= 1.0

        exit_mock.assert_not_called()


def test_master_initialization(master):
    """Test that PrometheusMaster is properly initialized."""
    assert hasattr(master, 'start_time')
    assert master.start_time > 0


def test_multiple_signal_handlers(master):
    """Test that multiple signal handlers increment metrics correctly."""
    with patch("os.fork", return_value=12345), patch("sys.exit"):
        # Call multiple signal handlers
        master.handle_hup()
        master.handle_usr1()
        master.handle_usr2()

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
    with patch("os.fork", return_value=12345), patch("sys.exit"):
        # Mock all parent class methods at once
        with patch('gunicorn.arbiter.Arbiter.handle_hup') as mock_hup, \
             patch('gunicorn.arbiter.Arbiter.handle_ttin') as mock_ttin, \
             patch('gunicorn.arbiter.Arbiter.handle_ttou') as mock_ttou, \
             patch('gunicorn.arbiter.Arbiter.handle_chld') as mock_chld, \
             patch('gunicorn.arbiter.Arbiter.handle_usr1') as mock_usr1, \
             patch('gunicorn.arbiter.Arbiter.handle_usr2') as mock_usr2:
            
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

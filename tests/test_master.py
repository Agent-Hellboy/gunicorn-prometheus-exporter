from unittest.mock import MagicMock, patch

import pytest

from gunicorn_prometheus_exporter.master import PrometheusMaster
from gunicorn_prometheus_exporter.metrics import MASTER_WORKER_RESTARTS


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
        matched = [s for s in samples if s.labels.get("reason") == "restart"]
        assert matched
        assert matched[0].value >= 1.0

        # Ensure sys.exit was not called (we're only simulating parent)
        exit_mock.assert_not_called()

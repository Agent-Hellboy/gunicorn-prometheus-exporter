"""
Tests for Gunicorn Prometheus Exporter worker.
"""

import os
import time
from unittest.mock import MagicMock, patch

import pytest

from gunicorn_prometheus_exporter.metrics import (
    WORKER_CPU,
    WORKER_FAILED_REQUESTS,
    WORKER_MEMORY,
    WORKER_REQUEST_DURATION,
    WORKER_REQUESTS,
    WORKER_UPTIME,
    WORKER_ERROR_HANDLING,
)
from gunicorn_prometheus_exporter.plugin import PrometheusWorker
from gunicorn.http.errors import InvalidRequestLine


@pytest.fixture
def worker():
    """Create a PrometheusWorker instance for testing."""
    age = 0
    ppid = os.getppid()
    sockets = [MagicMock()]
    app = MagicMock()
    timeout = MagicMock()
    cfg = MagicMock()  # Gunicorn Arbiter (manager )
    cfg.max_requests = 0  # Set max_requests to 0 for testing
    cfg.max_requests_jitter = 0
    cfg.worker_tmp_dir = None  # Don't use a tmp dir for testing
    cfg.umask = 0  # Default umask
    cfg.uid = os.getuid()  # Current user ID
    cfg.gid = os.getgid()  # Current group ID
    log = MagicMock()
    worker = PrometheusWorker(age, ppid, sockets, app, timeout, cfg, log)
    return worker


def test_worker_initialization(worker):
    """Test that worker initializes correctly."""
    assert worker.worker_id == os.getpid()
    assert worker.process is not None
    assert worker.start_time > 0


def test_handle_request(worker):
    """Test that handle_request updates worker metrics correctly."""
    listener = MagicMock()
    req = MagicMock()
    client = MagicMock()
    addr = MagicMock()

    with patch(
        "gunicorn_prometheus_exporter.plugin.SyncWorker.handle_request"
    ) as mock_handle:
        mock_handle.return_value = ["response"]
        response = worker.handle_request(listener, req, client, addr)

        assert response == ["response"]
        mock_handle.assert_called_once_with(listener, req, client, addr)

        # Check that worker metrics were updated
        samples = list(WORKER_REQUESTS.collect())
        assert len(samples) == 1
        assert samples[0].samples[0].value == 1.0
        assert samples[0].samples[0].labels["worker_id"] == str(worker.worker_id)


def test_worker_metrics_update(worker):
    """Test that worker metrics are updated correctly."""
    # Call update_worker_metrics directly
    worker.update_worker_metrics()

    # Check that worker metrics were updated
    samples = list(WORKER_MEMORY.collect())
    assert len(samples) == 1
    assert samples[0].samples[0].value > 0
    assert samples[0].samples[0].labels["worker_id"] == str(worker.worker_id)


def test_error_handling(worker):
    """Test that errors are properly tracked in worker metrics."""
    listener = MagicMock()
    req = MagicMock()
    client = MagicMock()
    addr = MagicMock()

    with patch(
        "gunicorn_prometheus_exporter.plugin.SyncWorker.handle_request"
    ) as mock_handle:
        mock_handle.side_effect = ValueError("Test error")

        with pytest.raises(ValueError):
            worker.handle_request(listener, req, client, addr)

        # Check that error was tracked in worker metrics
        samples = list(WORKER_FAILED_REQUESTS.collect())
        assert len(samples) == 1
        assert samples[0].samples[0].value == 1.0
        assert samples[0].samples[0].labels["worker_id"] == str(worker.worker_id)


def test_worker_uptime(worker):
    """Test that worker uptime is tracked correctly."""
    initial_uptime = time.time() - worker.start_time
    time.sleep(0.1)  # Wait a bit
    worker.update_worker_metrics()

    samples = list(WORKER_UPTIME.collect())
    assert len(samples) == 1
    assert samples[0].samples[0].value > initial_uptime
    assert samples[0].samples[0].labels["worker_id"] == str(worker.worker_id)


def test_worker_cpu(worker):
    """Test that worker CPU usage is tracked."""
    worker.update_worker_metrics()

    samples = list(WORKER_CPU.collect())
    assert len(samples) == 1
    assert samples[0].samples[0].labels["worker_id"] == str(worker.worker_id)
    # CPU usage could be 0 if the process is idle, so we just check that the
    # metric exists


def test_request_duration(worker):
    """Test that request duration is properly tracked."""
    listener = MagicMock()
    req = MagicMock()
    client = MagicMock()
    addr = MagicMock()

    with patch("gunicorn.workers.sync.SyncWorker.handle_request") as mock_handle:
        mock_handle.return_value = ["response"]
        worker.handle_request(listener, req, client, addr)

    # Check that duration was recorded
    samples = list(WORKER_REQUEST_DURATION._samples())
    assert len(samples) > 0
    assert samples[0].value > 0


def test_handle_error(worker):
    """Test that handle_error updates worker metrics correctly."""
    req = MagicMock()
    client = MagicMock()
    addr = ("127.0.0.1", 12345)
    exc = InvalidRequestLine("Malformed request")

    with patch("gunicorn.workers.sync.SyncWorker.handle_error") as mock_handle:
        worker.handle_error(req, client, addr, exc)
        mock_handle.assert_called_once_with(req, client, addr, exc)

        # Collect and assert on the metric
        samples = list(WORKER_FAILED_REQUESTS.collect())[0].samples
        matched = [
            s for s in samples if s.labels.get("worker_id") == str(worker.worker_id)
        ]
        assert matched
        assert matched[0].value >= 1.0

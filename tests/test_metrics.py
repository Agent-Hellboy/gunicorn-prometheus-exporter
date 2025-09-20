"""
Tests for Gunicorn Prometheus Exporter metrics.
"""

import os

from prometheus_client import CollectorRegistry

from gunicorn_prometheus_exporter.metrics import (
    MASTER_SIGNALS,
    MASTER_WORKER_RESTARTS,
    MASTER_WORKERS_CURRENT,
    WORKER_CPU,
    WORKER_ERROR_HANDLING,
    WORKER_FAILED_REQUESTS,
    WORKER_MEMORY,
    WORKER_REQUEST_DURATION,
    WORKER_REQUESTS,
    WORKER_STATE,
    WORKER_UPTIME,
    registry,
)


def test_registry_setup():
    """Test that the registry is properly configured."""
    assert isinstance(registry, CollectorRegistry)
    assert registry._collector_to_names


def test_master_worker_restarts_metric():
    """Test MASTER_WORKER_RESTARTS metric configuration."""
    assert MASTER_WORKER_RESTARTS._metric._name == "gunicorn_master_worker_restart"
    assert (
        MASTER_WORKER_RESTARTS._metric._documentation
        == "Total number of Gunicorn worker restarts"
    )
    assert MASTER_WORKER_RESTARTS._metric._labelnames == ("reason",)


def test_master_signals_metric():
    """Test MASTER_SIGNALS metric configuration."""
    assert MASTER_SIGNALS._metric._name == "gunicorn_master_signals"
    assert (
        MASTER_SIGNALS._metric._documentation
        == "Total number of signals received by the master process"
    )
    assert MASTER_SIGNALS._metric._labelnames == ("signal_type",)


def test_master_workers_current_metric():
    """Test MASTER_WORKERS_CURRENT metric configuration."""
    assert MASTER_WORKERS_CURRENT._metric._name == "gunicorn_master_workers_current"
    assert (
        MASTER_WORKERS_CURRENT._metric._documentation
        == "Current number of active workers"
    )
    assert MASTER_WORKERS_CURRENT._metric._labelnames == ()


def test_worker_state_metric():
    """Test WORKER_STATE metric configuration."""
    assert WORKER_STATE._metric._name == "gunicorn_worker_state"
    assert (
        WORKER_STATE._metric._documentation
        == "Current state of the worker (1=running, 0=stopped)"
    )
    assert WORKER_STATE._metric._labelnames == ("worker_id", "state", "timestamp")


def test_worker_requests_metric():
    """Test WORKER_REQUESTS metric configuration."""
    assert WORKER_REQUESTS._metric._name == "gunicorn_worker_requests"
    assert (
        WORKER_REQUESTS._metric._documentation
        == "Total number of requests handled by this worker"
    )
    assert WORKER_REQUESTS._metric._labelnames == ("worker_id",)


def test_worker_request_duration_metric():
    """Test WORKER_REQUEST_DURATION metric configuration."""
    assert (
        WORKER_REQUEST_DURATION._metric._name
        == "gunicorn_worker_request_duration_seconds"
    )
    assert (
        WORKER_REQUEST_DURATION._metric._documentation == "Request duration in seconds"
    )
    assert WORKER_REQUEST_DURATION._metric._labelnames == ("worker_id",)


def test_worker_memory_metric():
    """Test WORKER_MEMORY metric configuration."""
    assert WORKER_MEMORY._metric._name == "gunicorn_worker_memory_bytes"
    assert WORKER_MEMORY._metric._documentation == "Memory usage of the worker process"
    assert WORKER_MEMORY._metric._labelnames == ("worker_id",)


def test_worker_cpu_metric():
    """Test WORKER_CPU metric configuration."""
    assert WORKER_CPU._metric._name == "gunicorn_worker_cpu_percent"
    assert WORKER_CPU._metric._documentation == "CPU usage of the worker process"
    assert WORKER_CPU._metric._labelnames == ("worker_id",)


def test_worker_uptime_metric():
    """Test WORKER_UPTIME metric configuration."""
    assert WORKER_UPTIME._metric._name == "gunicorn_worker_uptime_seconds"
    assert WORKER_UPTIME._metric._documentation == "Uptime of the worker process"
    assert WORKER_UPTIME._metric._labelnames == ("worker_id",)


def test_worker_failed_requests_metric():
    """Test WORKER_FAILED_REQUESTS metric configuration."""
    assert WORKER_FAILED_REQUESTS._metric._name == "gunicorn_worker_failed_requests"
    assert (
        WORKER_FAILED_REQUESTS._metric._documentation
        == "Total number of failed requests handled by this worker"
    )
    assert WORKER_FAILED_REQUESTS._metric._labelnames == (
        "worker_id",
        "method",
        "endpoint",
        "error_type",
    )


def test_multiprocess_dir_setup():
    """Test that PROMETHEUS_MULTIPROC_DIR is set."""
    from gunicorn_prometheus_exporter.config import config

    assert config.prometheus_multiproc_dir is not None

    # The directory should be set, but might not exist if cleaned up by other tests
    if not os.path.exists(config.prometheus_multiproc_dir):
        os.makedirs(config.prometheus_multiproc_dir, exist_ok=True)

    assert os.path.exists(config.prometheus_multiproc_dir)


def test_metric_registration():
    """Test that all metrics are registered with the registry."""
    collectors = list(registry._collector_to_names.keys())
    metric_classes = [
        WORKER_REQUESTS,
        WORKER_REQUEST_DURATION,
        WORKER_MEMORY,
        WORKER_CPU,
        WORKER_UPTIME,
        WORKER_FAILED_REQUESTS,
        WORKER_ERROR_HANDLING,
        WORKER_STATE,
        MASTER_WORKER_RESTARTS,
        MASTER_SIGNALS,
        MASTER_WORKERS_CURRENT,
    ]
    assert all(metric._metric in collectors for metric in metric_classes)

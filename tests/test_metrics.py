"""
Tests for Gunicorn Prometheus Exporter metrics.
"""

import os

from prometheus_client import CollectorRegistry

from gunicorn_prometheus_exporter.metrics import (
    MASTER_WORKER_RESTART_COUNT,
    MASTER_WORKER_RESTARTS,
    WORKER_CPU,
    WORKER_ERROR_HANDLING,
    WORKER_FAILED_REQUESTS,
    WORKER_MEMORY,
    WORKER_REQUEST_DURATION,
    WORKER_REQUEST_SIZE,
    WORKER_REQUESTS,
    WORKER_RESPONSE_SIZE,
    WORKER_RESTART_COUNT,
    WORKER_RESTART_REASON,
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


def test_master_worker_restart_count_metric():
    """Test MASTER_WORKER_RESTART_COUNT metric configuration."""
    assert (
        MASTER_WORKER_RESTART_COUNT._metric._name
        == "gunicorn_master_worker_restart_count"
    )
    assert (
        MASTER_WORKER_RESTART_COUNT._metric._documentation
        == "Total number of worker restarts by reason and worker"
    )
    assert MASTER_WORKER_RESTART_COUNT._metric._labelnames == (
        "worker_id",
        "reason",
        "restart_type",
    )


def test_worker_restart_reason_metric():
    """Test WORKER_RESTART_REASON metric configuration."""
    assert WORKER_RESTART_REASON._metric._name == "gunicorn_worker_restart"
    assert (
        WORKER_RESTART_REASON._metric._documentation
        == "Total number of worker restarts by reason"
    )
    assert WORKER_RESTART_REASON._metric._labelnames == ("worker_id", "reason")


def test_worker_restart_count_metric():
    """Test WORKER_RESTART_COUNT metric configuration."""
    assert WORKER_RESTART_COUNT._metric._name == "gunicorn_worker_restart_count"
    assert (
        WORKER_RESTART_COUNT._metric._documentation
        == "Total number of worker restarts by worker and restart type"
    )
    assert WORKER_RESTART_COUNT._metric._labelnames == (
        "worker_id",
        "restart_type",
        "reason",
    )


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


def test_worker_request_size_metric():
    """Test WORKER_REQUEST_SIZE metric configuration."""
    assert WORKER_REQUEST_SIZE._metric._name == "gunicorn_worker_request_size_bytes"
    assert WORKER_REQUEST_SIZE._metric._documentation == "Request size in bytes"
    assert WORKER_REQUEST_SIZE._metric._labelnames == ("worker_id",)


def test_worker_response_size_metric():
    """Test WORKER_RESPONSE_SIZE metric configuration."""
    assert WORKER_RESPONSE_SIZE._metric._name == "gunicorn_worker_response_size_bytes"
    assert WORKER_RESPONSE_SIZE._metric._documentation == "Response size in bytes"
    assert WORKER_RESPONSE_SIZE._metric._labelnames == ("worker_id",)


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
        WORKER_REQUEST_SIZE,
        WORKER_RESPONSE_SIZE,
        WORKER_RESTART_REASON,
        WORKER_RESTART_COUNT,
        MASTER_WORKER_RESTARTS,
        MASTER_WORKER_RESTART_COUNT,
    ]
    assert all(metric._metric in collectors for metric in metric_classes)

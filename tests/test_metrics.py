"""
Tests for Gunicorn Prometheus Exporter metrics.
"""

import os

from prometheus_client import CollectorRegistry

from gunicorn_prometheus_exporter.metrics import (
    WORKER_CPU,
    WORKER_FAILED_REQUESTS,
    WORKER_MEMORY,
    WORKER_REQUEST_DURATION,
    WORKER_REQUESTS,
    WORKER_UPTIME,
    registry,
)


def test_registry_setup():
    """Test that the registry is properly configured."""
    assert isinstance(registry, CollectorRegistry)
    assert registry._collector_to_names  # Should have collectors registered


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
    assert os.environ.get("PROMETHEUS_MULTIPROC_DIR") is not None
    assert os.path.exists(os.environ["PROMETHEUS_MULTIPROC_DIR"])


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
    ]
    assert all(metric._metric in collectors for metric in metric_classes)

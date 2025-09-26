"""
Tests for Gunicorn Prometheus Exporter metrics.
"""

import os
import tempfile

from unittest.mock import patch

import pytest

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
    from gunicorn_prometheus_exporter.config import get_config

    config = get_config()
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


class TestMetricsExceptionHandling:
    """Test exception handling in metrics module."""

    def test_get_shared_registry(self):
        """Test get_shared_registry function."""
        from gunicorn_prometheus_exporter.metrics import get_shared_registry

        registry = get_shared_registry()
        assert registry is not None
        assert hasattr(registry, "register")
        assert hasattr(registry, "collect")

    def test_master_metrics_dict(self):
        """Test MASTER_METRICS dictionary."""
        from gunicorn_prometheus_exporter.metrics import MASTER_METRICS

        assert isinstance(MASTER_METRICS, dict)
        assert "worker_restart_total" in MASTER_METRICS
        assert "worker_restart_count_total" in MASTER_METRICS

        # Test that the values are metric instances
        for key, metric in MASTER_METRICS.items():
            assert hasattr(metric, "_metric")
            assert metric._metric is not None

    def test_metric_meta_collect_method(self):
        """Test BaseMetric collect method."""
        from gunicorn_prometheus_exporter.metrics import BaseMetric

        # Test that collect method exists and is callable
        assert hasattr(BaseMetric, "collect")
        assert callable(BaseMetric.collect)

    def test_metric_meta_samples_method(self):
        """Test BaseMetric _samples method."""
        from gunicorn_prometheus_exporter.metrics import BaseMetric

        # Test that _samples method exists and is callable
        assert hasattr(BaseMetric, "_samples")
        assert callable(BaseMetric._samples)

    def test_metric_meta_labels_method(self):
        """Test BaseMetric labels method."""
        from gunicorn_prometheus_exporter.metrics import BaseMetric

        # Test that labels method exists and is callable
        assert hasattr(BaseMetric, "labels")
        assert callable(BaseMetric.labels)

    def test_metric_meta_inc_method(self):
        """Test BaseMetric inc method."""
        from gunicorn_prometheus_exporter.metrics import BaseMetric

        # Test that inc method exists and is callable
        assert hasattr(BaseMetric, "inc")
        assert callable(BaseMetric.inc)

    def test_metric_meta_set_method(self):
        """Test BaseMetric set method."""
        from gunicorn_prometheus_exporter.metrics import BaseMetric

        # Test that set method exists and is callable
        assert hasattr(BaseMetric, "set")
        assert callable(BaseMetric.set)

    def test_metric_meta_observe_method(self):
        """Test BaseMetric observe method."""
        from gunicorn_prometheus_exporter.metrics import BaseMetric

        # Test that observe method exists and is callable
        assert hasattr(BaseMetric, "observe")
        assert callable(BaseMetric.observe)

    def test_metric_meta_describe_method(self):
        """Test BaseMetric describe method."""
        from gunicorn_prometheus_exporter.metrics import BaseMetric

        # Test that describe method exists and is callable
        assert hasattr(BaseMetric, "describe")
        assert callable(BaseMetric.describe)

    def test_metric_meta_clear_method(self):
        """Test BaseMetric clear method."""
        from gunicorn_prometheus_exporter.metrics import BaseMetric

        # Test that clear method exists and is callable
        assert hasattr(BaseMetric, "clear")
        assert callable(BaseMetric.clear)

    def test_ensure_multiproc_dir_success(self):
        """Test _ensure_multiproc_dir with valid directory."""
        from gunicorn_prometheus_exporter.metrics import _ensure_multiproc_dir

        # Use a temporary directory that we can create
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the environment variable directly
            with patch.dict(os.environ, {"PROMETHEUS_MULTIPROC_DIR": temp_dir}):
                # Should not raise an exception
                _ensure_multiproc_dir()

                # Directory should exist
                assert os.path.exists(temp_dir)
                assert os.path.isdir(temp_dir)

    def test_ensure_multiproc_dir_failure_permission_denied(self):
        """Test _ensure_multiproc_dir with permission denied error."""
        from gunicorn_prometheus_exporter.metrics import _ensure_multiproc_dir

        # Use a path that will cause permission denied
        invalid_path = "/root/forbidden/prometheus_multiproc"

        with patch.dict(os.environ, {"PROMETHEUS_MULTIPROC_DIR": invalid_path}):
            with patch("os.makedirs", side_effect=PermissionError("Permission denied")):
                # Should raise the exception
                with pytest.raises(PermissionError, match="Permission denied"):
                    _ensure_multiproc_dir()

    def test_ensure_multiproc_dir_failure_invalid_path(self):
        """Test _ensure_multiproc_dir with invalid path error."""
        from gunicorn_prometheus_exporter.metrics import _ensure_multiproc_dir

        # Use an invalid path
        invalid_path = "/invalid/path/with/nonexistent/parent"

        with patch.dict(os.environ, {"PROMETHEUS_MULTIPROC_DIR": invalid_path}):
            with patch("os.makedirs", side_effect=OSError("No such file or directory")):
                # Should raise the exception
                with pytest.raises(OSError, match="No such file or directory"):
                    _ensure_multiproc_dir()

    def test_ensure_multiproc_dir_failure_disk_full(self):
        """Test _ensure_multiproc_dir with disk full error."""
        from gunicorn_prometheus_exporter.metrics import _ensure_multiproc_dir

        # Use a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"PROMETHEUS_MULTIPROC_DIR": temp_dir}):
                with patch(
                    "os.makedirs", side_effect=OSError("No space left on device")
                ):
                    # Should raise the exception
                    with pytest.raises(OSError, match="No space left on device"):
                        _ensure_multiproc_dir()

    def test_get_shared_registry_calls_ensure_multiproc_dir(self):
        """Test that get_shared_registry calls _ensure_multiproc_dir."""
        from gunicorn_prometheus_exporter.metrics import (
            get_shared_registry,
        )

        # Mock _ensure_multiproc_dir to verify it's called
        with patch(
            "gunicorn_prometheus_exporter.metrics._ensure_multiproc_dir"
        ) as mock_ensure:
            # Call get_shared_registry
            registry = get_shared_registry()

            # Verify _ensure_multiproc_dir was called
            mock_ensure.assert_called_once()

            # Verify registry is returned
            assert registry is not None
            assert hasattr(registry, "register")
            assert hasattr(registry, "collect")

    def test_get_shared_registry_fails_on_directory_error(self):
        """Test that get_shared_registry fails when _ensure_multiproc_dir fails."""
        from gunicorn_prometheus_exporter.metrics import get_shared_registry

        # Mock _ensure_multiproc_dir to raise an exception
        with patch(
            "gunicorn_prometheus_exporter.metrics._ensure_multiproc_dir",
            side_effect=OSError("Directory creation failed"),
        ):
            # Should raise the exception
            with pytest.raises(OSError, match="Directory creation failed"):
                get_shared_registry()

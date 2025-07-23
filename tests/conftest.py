"""Test configuration and fixtures."""

import os
import tempfile

import pytest

from prometheus_client import CollectorRegistry

from gunicorn_prometheus_exporter.config import config


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment with required variables."""
    # Set up required environment variables for testing
    os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")
    os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
    os.environ.setdefault("GUNICORN_WORKERS", "2")

    # Set up the Prometheus multiprocess directory
    temp_dir = tempfile.mkdtemp()
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = temp_dir
    # Update config to use the test directory
    config._setup_multiproc_dir()
    yield
    os.environ.pop("PROMETHEUS_MULTIPROC_DIR", None)


@pytest.fixture
def prometheus_registry():
    """Create a fresh Prometheus registry for testing."""
    return CollectorRegistry()


@pytest.fixture
def worker_id():
    """Return a test worker ID."""
    return "test_worker"

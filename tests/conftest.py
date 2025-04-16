"""Test configuration and fixtures."""

import os
import tempfile

import pytest
from prometheus_client import CollectorRegistry


@pytest.fixture(scope="session", autouse=True)
def setup_prometheus_multiproc_dir():
    """Set up the Prometheus multiprocess directory."""
    temp_dir = tempfile.mkdtemp()
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = temp_dir
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

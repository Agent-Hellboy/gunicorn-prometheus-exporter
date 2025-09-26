"""Test configuration and fixtures."""

import os
import tempfile

from unittest.mock import Mock, patch

import pytest

from prometheus_client import CollectorRegistry

from gunicorn_prometheus_exporter.config import initialize_config


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

    # Initialize configuration with explicit parameters
    # Handle case where config might already be initialized
    try:
        initialize_config(
            PROMETHEUS_BIND_ADDRESS="127.0.0.1",
            PROMETHEUS_METRICS_PORT="9091",
            GUNICORN_WORKERS="2",
            PROMETHEUS_MULTIPROC_DIR=temp_dir,
        )
    except RuntimeError as e:
        if "Configuration already initialized" in str(e):
            # Config is already initialized, that's fine
            pass
        else:
            raise

    yield

    # Don't cleanup config to avoid global state issues between tests
    # Just clean up the environment variable
    os.environ.pop("PROMETHEUS_MULTIPROC_DIR", None)


@pytest.fixture
def prometheus_registry():
    """Create a fresh Prometheus registry for testing."""
    return CollectorRegistry()


@pytest.fixture
def worker_id():
    """Return a test worker ID."""
    return "test_worker"


@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis to prevent actual Redis connections and return proper values."""
    # Create a mock Redis client that returns appropriate values
    mock_redis_client = Mock()

    # Mock hget to return string values that can be converted to float
    def mock_hget(key, field):
        if field == "value":
            return "0.0"  # Return string representation of number
        elif field == "timestamp":
            return "0.0"
        return None

    mock_redis_client.hget.side_effect = mock_hget
    mock_redis_client.hset.return_value = True
    mock_redis_client.delete.return_value = 1
    mock_redis_client.keys.return_value = []

    with (
        patch("redis.Redis", return_value=mock_redis_client),
        patch("redis.StrictRedis", return_value=mock_redis_client),
    ):
        yield mock_redis_client

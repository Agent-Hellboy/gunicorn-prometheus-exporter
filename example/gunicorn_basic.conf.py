"""Custom Gunicorn configuration with extended functionality.

This example shows how to extend the default hooks with custom functionality
while still using the pre-built hooks as a foundation.
"""

import os

from gunicorn_prometheus_exporter.hooks import (
    default_on_exit,
    default_on_starting,
    default_when_ready,
    default_worker_int,
)


# Gunicorn settings
bind = "0.0.0.0:8210"  # nosec B104
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Environment configuration
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")  # nosec B108
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # nosec B104
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "127.0.0.1")  # Configure for your environment
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_FORWARD_INTERVAL", "15")
os.environ.setdefault("CLEANUP_DB_FILES", "true")


# Custom hook that extends the default functionality
def custom_when_ready(server):
    """Custom when_ready hook that extends default functionality."""
    # Call the default hook first
    default_when_ready(server)

    # Add custom functionality here
    print("Custom hook: Server is ready with extended functionality!")


# Use custom hooks
when_ready = custom_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit

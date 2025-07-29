"""
Example Gunicorn configuration for tornado workers with Prometheus metrics.

This configuration uses the PrometheusTornadoWorker which provides Prometheus
metrics support for Gunicorn's tornado worker model.

Tornado workers use async I/O loops and are good for applications that
need high concurrency with async/await patterns.

Usage:
    gunicorn -c gunicorn_tornado_async.conf.py async_app:app
"""

import os  # noqa: E402


# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9097")  # noqa: E501
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # nosec B104  # noqa: E501
os.environ.setdefault("GUNICORN_WORKERS", "2")  # noqa: E501
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/home/proshan/.gunicorn_prometheus")  # noqa: E501
os.environ.setdefault("REDIS_ENABLED", "false")  # noqa: E501

# Force early import to ensure PrometheusMaster patching happens
from gunicorn_prometheus_exporter.hooks import (  # noqa: E402
    default_on_exit,
    default_on_starting,
    default_when_ready,
    default_worker_int,
)


# Basic Gunicorn settings
bind = "0.0.0.0:8007"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusTornadoWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"


# Gunicorn hooks for Prometheus setup
def when_ready(server):
    """Setup Prometheus metrics server when Gunicorn is ready."""
    default_when_ready(server)


def on_starting(server):
    """Setup master metrics when Gunicorn is starting."""
    default_on_starting(server)


def worker_int(worker):
    """Handle worker interrupt signals."""
    default_worker_int(worker)


def on_exit(server):
    """Cleanup when Gunicorn exits."""
    default_on_exit(server)

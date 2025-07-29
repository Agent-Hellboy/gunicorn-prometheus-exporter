"""
Example Gunicorn configuration for threaded workers with Prometheus metrics.

This configuration uses the PrometheusThreadWorker which provides Prometheus
metrics support for Gunicorn's threaded worker model.

Threaded workers are good for I/O-bound applications and provide better
concurrency than sync workers while being simpler than async workers.

Usage:
    gunicorn -c gunicorn_thread_worker.conf.py app:app
"""

import os  # noqa: E402


# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")  # noqa: E501
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
bind = "0.0.0.0:8001"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
worker_connections = 1000
threads = 4  # Number of threads per worker
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

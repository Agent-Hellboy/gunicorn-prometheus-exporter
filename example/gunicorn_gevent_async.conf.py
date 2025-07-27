"""
Example Gunicorn configuration for gevent workers with Prometheus metrics.

This configuration uses the PrometheusGeventWorker which provides Prometheus
metrics support for Gunicorn's gevent worker model.

Gevent workers use greenlets for cooperative multitasking and are good
for I/O-bound applications with many concurrent connections.

Usage:
    gunicorn -c gunicorn_gevent_async.conf.py async_app:app
"""

import os

# Force early import to ensure PrometheusMaster patching happens
from gunicorn_prometheus_exporter.hooks import (
    default_on_exit,
    default_on_starting,
    default_when_ready,
    default_worker_int,
)


# Basic Gunicorn settings
bind = "0.0.0.0:8006"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Prometheus configuration
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9096")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # nosec B104
os.environ.setdefault("GUNICORN_WORKERS", "2")
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/home/proshan/.gunicorn_prometheus")

# Optional: Redis forwarding (disabled by default)
os.environ.setdefault("REDIS_ENABLED", "false")


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

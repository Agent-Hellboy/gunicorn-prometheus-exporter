"""Gunicorn configuration with Redis forwarding enabled.

This example demonstrates Redis forwarding functionality.
"""

import os

from gunicorn_prometheus_exporter.hooks import (
    default_on_exit,
    default_on_starting,
    default_worker_int,
    redis_when_ready,
)


# Set up multiprocess directory for Prometheus
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prometheus_multiproc"  # nosec B108

# Gunicorn settings
bind = "0.0.0.0:8300"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Redis configuration
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "127.0.0.1")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_FORWARD_INTERVAL", "10")
os.environ.setdefault("CLEANUP_DB_FILES", "false")

# Prometheus configuration
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # nosec B104

# Use Redis-enabled hooks
when_ready = redis_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit

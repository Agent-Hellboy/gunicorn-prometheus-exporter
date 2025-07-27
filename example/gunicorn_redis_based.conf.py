"""Gunicorn configuration with Redis forwarding (formerly Redis-based).

This example demonstrates Redis forwarding functionality.
Note: Redis-based metrics collection (i.e., reading aggregated metrics from Redis in a multiprocess setup) is not yet implemented; only forwarding to Redis is supported.
"""

import os

from gunicorn_prometheus_exporter.hooks import (
    default_on_exit,
    default_on_starting,
    default_worker_int,
    redis_when_ready,
)


# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Environment variables for configuration
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")  # nosec B108
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # nosec B104

# Redis configuration
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "127.0.0.1")  # Configure for your environment
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_FORWARD_INTERVAL", "5")
os.environ.setdefault("CLEANUP_DB_FILES", "false")

# Use Redis-enabled hooks
when_ready = redis_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit

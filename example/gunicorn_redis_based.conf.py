"""Gunicorn configuration with Redis forwarding (formerly Redis-based).

This example demonstrates Redis forwarding functionality.
Note: Redis-based metrics collection (i.e., reading aggregated metrics from Redis in a multiprocess setup) is not yet implemented; only forwarding to Redis is supported.
"""

import os  # noqa: E402


# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")  # nosec B108  # noqa: E501
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")  # noqa: E501
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # nosec B104  # noqa: E501
os.environ.setdefault("REDIS_ENABLED", "true")  # noqa: E501
os.environ.setdefault(
    "REDIS_HOST", "127.0.0.1"
)  # Configure for your environment  # noqa: E501
os.environ.setdefault("REDIS_PORT", "6379")  # noqa: E501
os.environ.setdefault("REDIS_FORWARD_INTERVAL", "5")  # noqa: E501
os.environ.setdefault("CLEANUP_DB_FILES", "false")  # noqa: E501

from gunicorn_prometheus_exporter.hooks import (  # noqa: E402
    default_on_exit,
    default_on_starting,
    default_worker_int,
    redis_when_ready,
)


# Gunicorn settings
bind = "0.0.0.0:8008"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Use Redis-enabled hooks
when_ready = redis_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit

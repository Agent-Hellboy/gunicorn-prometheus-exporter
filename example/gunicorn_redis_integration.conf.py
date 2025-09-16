"""Gunicorn configuration with Redis-based metrics storage.

This configuration uses Redis for storing Prometheus metrics instead of files.
Perfect for distributed deployments where multiple processes need to share metrics.

Features:
- Redis-based metrics storage (no files created)
- Redis multiprocess collector for /metrics endpoint
- Shared metrics across multiple Gunicorn instances
- Redis keys: gunicorn:*:metric:* and gunicorn:*:meta:*

Redis Flags:
- REDIS_ENABLED=true: Enable Redis integration
- REDIS_HOST: Redis server host (default: 127.0.0.1)
- REDIS_PORT: Redis server port (default: 6379)
- REDIS_DB: Redis database number (default: 0)

Usage:
    gunicorn --config gunicorn_redis_integration.conf.py app:app
"""

import os  # noqa: E402


# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9093")  # Changed from 9091 to 9092
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # nosec B104  # noqa: E501
os.environ.setdefault("REDIS_ENABLED", "true")  # noqa: E501
os.environ.setdefault("REDIS_HOST", "127.0.0.1")  # Configure for your environment  # noqa: E501
os.environ.setdefault("REDIS_PORT", "6379")  # noqa: E501
os.environ.setdefault("REDIS_DB", "0")  # noqa: E501

from gunicorn_prometheus_exporter.hooks import (  # noqa: E402
    default_on_exit,
    default_on_starting,
    default_worker_int,
    redis_when_ready,
)


# Gunicorn settings
bind = "0.0.0.0:8088"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Use Redis-enabled hooks for Redis-based metrics storage
when_ready = redis_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit

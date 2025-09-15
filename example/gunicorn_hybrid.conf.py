"""Gunicorn configuration with hybrid metrics storage (Files + Redis).

This configuration uses BOTH file-based storage AND Redis storage simultaneously.
Perfect for migration scenarios or when you need metrics in both places.

Features:
- File-based metrics storage (standard Prometheus multiprocess)
- Redis forwarder sends metrics to Redis every 5 seconds
- Dual storage: files for /metrics endpoint + Redis for external tools
- Redis keys: gunicorn_forwarder:latest, gunicorn_forwarder:metadata, gunicorn_forwarder:timestamp

Redis Forwarder Flags:
- REDIS_FORWARD_ENABLED=true: Enable Redis forwarding
- REDIS_HOST: Redis server host (default: 127.0.0.1)
- REDIS_PORT: Redis server port (default: 6379)
- REDIS_DB: Redis database number (default: 0)
- REDIS_KEY_PREFIX: Key prefix for Redis (default: gunicorn_forwarder:)
- REDIS_FORWARD_INTERVAL: Forward interval in seconds (default: 5)

Usage:
    gunicorn --config gunicorn_hybrid.conf.py app:app
"""

import os  # noqa: E402

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")  # noqa: E501
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # nosec B104  # noqa: E501
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")  # nosec B108  # noqa: E501

# Redis forwarder configuration
os.environ.setdefault("REDIS_FORWARD_ENABLED", "true")  # noqa: E501
os.environ.setdefault("REDIS_HOST", "127.0.0.1")  # noqa: E501
os.environ.setdefault("REDIS_PORT", "6379")  # noqa: E501
os.environ.setdefault("REDIS_DB", "0")  # noqa: E501
os.environ.setdefault("REDIS_FORWARD_INTERVAL", "5")  # noqa: E501

from gunicorn_prometheus_exporter.hooks import (  # noqa: E402
    default_on_exit,
    default_on_starting,
    default_worker_int,
    default_when_ready,
)


# Gunicorn settings
bind = "0.0.0.0:8008"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Use standard hooks (no Redis integration)
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit


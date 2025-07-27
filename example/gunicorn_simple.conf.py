"""Simple Gunicorn configuration with Prometheus metrics only.

This example shows the simplest setup for gunicorn-prometheus-exporter
with only Prometheus metrics (no Redis forwarding).
"""

import os

from gunicorn_prometheus_exporter.hooks import (
    default_on_exit,
    default_on_starting,
    default_when_ready,
    default_worker_int,
)


# Gunicorn settings
bind = "0.0.0.0:8200"  # nosec B104
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Prometheus-only configuration
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")  # nosec B108
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # nosec B104
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Use pre-built hooks
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit

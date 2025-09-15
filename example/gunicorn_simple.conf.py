"""Simple Gunicorn configuration with Prometheus metrics only.

This example shows the simplest setup for gunicorn-prometheus-exporter
with only Prometheus metrics (no Redis forwarding).
"""
print("Starting gunicorn_simple.conf.py")  # noqa: T201
import os  # noqa: E402


# Prometheus-only configuration we need to place these over import because
# the config is loaded before the environment variables are set.
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")  # nosec B108  # noqa: E501
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")  # noqa: E501
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # nosec B104  # noqa: E501
os.environ.setdefault("GUNICORN_WORKERS", "2")  # noqa: E501

from gunicorn_prometheus_exporter.hooks import (  # noqa: E402
    default_on_exit,
    default_on_starting,
    default_post_fork,
    default_when_ready,
    default_worker_int,
)


# Gunicorn settings
bind = "0.0.0.0:8200"  # nosec B104  # noqa: E501
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
timeout = 300  # Set timeout directly in config file

# Use pre-built hooks
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork  # Configure CLI options after worker fork

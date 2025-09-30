"""Gunicorn configuration with YAML-based Prometheus metrics.

This configuration demonstrates how to use YAML configuration files
with the Gunicorn Prometheus Exporter.

Features:
- YAML-based configuration loading
- Environment variable overrides
- Standard Gunicorn worker with metrics
- Metrics endpoint on port 9093

Usage:
    gunicorn --config gunicorn_yaml_config.conf.py app:app
"""

import os  # noqa: E402

# Load YAML configuration before importing hooks
from gunicorn_prometheus_exporter.hooks import load_yaml_config  # noqa: E402


# Load YAML configuration
config_file = os.environ.get(
    "PROMETHEUS_CONFIG_FILE", "gunicorn-prometheus-exporter-basic.yml"
)
load_yaml_config(config_file)

from gunicorn_prometheus_exporter.hooks import (  # noqa: E402
    default_on_exit,
    default_on_starting,
    default_post_fork,
    default_when_ready,
    default_worker_int,
)


# Gunicorn settings
bind = "0.0.0.0:8088"  # nosec B104  # noqa: E501
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
timeout = 300  # Set timeout directly in config file

# Use pre-built hooks
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork  # Configure CLI options after worker fork

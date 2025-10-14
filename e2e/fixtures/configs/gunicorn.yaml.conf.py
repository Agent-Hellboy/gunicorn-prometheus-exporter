"""Gunicorn configuration with YAML-based Prometheus metrics for Docker testing."""

import os

from gunicorn_prometheus_exporter.hooks import load_yaml_config


# Load YAML configuration
config_file = os.environ.get("PROMETHEUS_CONFIG_FILE", "/app/config/basic.yml")
load_yaml_config(config_file)

from gunicorn_prometheus_exporter.hooks import (  # noqa: E402
    default_on_exit,
    default_on_starting,
    default_post_fork,
    default_when_ready,
    default_worker_int,
)


# Gunicorn settings
bind = "0.0.0.0:8089"
workers = 1
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
timeout = 30

# Use pre-built hooks
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork

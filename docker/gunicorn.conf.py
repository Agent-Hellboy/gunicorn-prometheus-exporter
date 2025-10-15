"""
Gunicorn configuration for the sample Flask application.
This config enables the Prometheus exporter with Redis storage.
"""

import os

from gunicorn_prometheus_exporter import load_yaml_config


# Load YAML configuration (use default if not provided)
yaml_config_path = os.getenv("YAML_CONFIG_PATH")
if yaml_config_path:
    load_yaml_config(yaml_config_path)
else:
    # Load default configuration for proper hook initialization
    load_yaml_config("gunicorn-prometheus-exporter-basic.yml")

# Import hooks and worker class after loading YAML config
from gunicorn_prometheus_exporter import PrometheusWorker  # noqa: E402
from gunicorn_prometheus_exporter.hooks import (  # noqa: E402
    default_on_exit,
    default_on_starting,
    default_post_fork,
    default_worker_int,
    redis_sidecar_when_ready,
)


# Basic Gunicorn settings
bind = "0.0.0.0:8000"
workers = int(os.getenv("GUNICORN_WORKERS", 2))

# Always use PrometheusWorker for worker-level metrics collection
# The storage backend (Redis vs multiprocess files) is handled by hooks and sidecar
worker_class = PrometheusWorker

worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "gunicorn-prometheus-exporter-app"

# Use Prometheus exporter hooks
# In sidecar mode, always use redis_sidecar_when_ready (Redis storage setup without metrics server)
when_ready = redis_sidecar_when_ready

on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork

# Additional settings for production
preload_app = True
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL settings (if needed)
keyfile = None
certfile = None

# Worker process settings
worker_tmp_dir = "/dev/shm"  # nosec B108

# Graceful timeout
graceful_timeout = 30

# Worker lifecycle settings
max_requests = 1000  # Restart workers after this many requests
max_requests_jitter = (
    100
)  # Add randomness to prevent all workers restarting simultaneously

# Connection settings
max_worker_connections = 1000  # Max pending connections for async workers
backlog = 2048  # Max number of pending connections in the listen queue

# Reload settings
reload = False  # Auto-reload workers when code changes (disable in production)
reload_engine = "auto"  # Reload detection engine
reload_extra_files = []  # Additional files to watch for reload triggers

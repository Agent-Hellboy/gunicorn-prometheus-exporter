"""
Gunicorn configuration for the sample Flask application.
This config enables the Prometheus exporter with Redis storage.
"""

import os

from gunicorn_prometheus_exporter import load_yaml_config


# Load YAML configuration if available
yaml_config_path = os.getenv("YAML_CONFIG_PATH", "gunicorn-prometheus-exporter.yml")
if os.path.exists(yaml_config_path):
    load_yaml_config(yaml_config_path)

# Import hooks after loading YAML config
from gunicorn_prometheus_exporter.hooks import (  # noqa: E402
    default_on_exit,
    default_on_starting,
    default_post_fork,
    default_when_ready,
    default_worker_int,
)


# Basic Gunicorn settings
bind = "0.0.0.0:8000"
workers = int(os.getenv("GUNICORN_WORKERS", 2))
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "gunicorn-prometheus-exporter-app"

# Use pre-built hooks
when_ready = default_when_ready
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
worker_class = "sync"  # Use sync worker for simple Flask app

# Graceful timeout
graceful_timeout = 30

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Restart workers after this many seconds, to help prevent memory leaks
max_worker_connections = 1000

# The maximum number of pending connections
backlog = 2048

# The maximum number of requests a worker will process before restarting
max_requests = 1000

# The maximum number of requests a worker will process before restarting
max_requests_jitter = 100

# The maximum number of seconds a worker may take to reload
reload = False

# The maximum number of seconds a worker may take to reload
reload_extra_files = []

# The maximum number of seconds a worker may take to reload
reload_engine = "auto"

# The maximum number of seconds a worker may take to reload
reload_extra_files = []

# The maximum number of seconds a worker may take to reload
reload_engine = "auto"

"""
Gunicorn configuration file demonstrating Prometheus metrics exporter.

This configuration:
- Binds to localhost:8080 for the application
- Uses 2 worker processes
- Uses our PrometheusWorker class
- Exports metrics on port 9090 at /metrics endpoint
"""

import logging
import os

from prometheus_client import start_http_server
from gunicorn_prometheus_exporter.plugin import PrometheusMaster

import gunicorn.arbiter
gunicorn.arbiter.Arbiter = PrometheusMaster

def when_ready(server):
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.info("Starting Prometheus metrics server on port 9090")
        start_http_server(9090)

# Gunicorn configuration
bind = "127.0.0.1:8080"
workers = 2
worker_class = "gunicorn_prometheus_exporter.plugin.PrometheusWorker"
threads = 1
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "debug"

# Process naming
proc_name = "gunicorn-example"

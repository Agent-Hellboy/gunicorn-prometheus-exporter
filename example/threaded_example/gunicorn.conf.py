"""
Gunicorn configuration for threaded worker example.
"""

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gunicorn_prometheus_exporter.PrometheusGthreadWorker"
threads = 4  # Number of threads per worker
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "gunicorn_threaded_example"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None


# Server hooks
def on_starting(server):
    """Log when the server starts."""
    server.log.info("Starting threaded worker server")


def on_exit(server):
    """Log when the server exits."""
    server.log.info("Exiting threaded worker server")


def worker_int(worker):
    """Log when a worker receives SIGINT or SIGQUIT."""
    worker.log.info("Worker received INT or QUIT signal")


def worker_abort(worker):
    """Log when a worker receives SIGABRT."""
    worker.log.info("Worker received ABORT signal")

"""
Gunicorn configuration file demonstrating Prometheus metrics exporter.

This configuration:
- Binds to localhost:8080 for the application
- Uses 2 worker processes
- Uses our PrometheusWorker class
- Exports metrics on port 9090 at /metrics endpoint, aggregating across all workers
"""

import logging
import os

from prometheus_client import CollectorRegistry, multiprocess, start_http_server


# —————————————————————————————————————————————————————————————————————————————
# Hook to start a multiprocess‐aware Prometheus metrics server when Gunicorn is ready
# —————————————————————————————————————————————————————————————————————————————
def when_ready(server):
    mp_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if not mp_dir:
        logging.warning("PROMETHEUS_MULTIPROC_DIR not set; skipping metrics server")
        return

    port = int(os.environ.get("PROMETHEUS_METRICS_PORT", 9091))
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Prometheus multiprocess metrics server on :{port}")

    # Build a fresh registry that merges all worker files in PROMETHEUS_MULTIPROC_DIR
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)

    # Serve that registry on HTTP
    start_http_server(port, registry=registry)


# —————————————————————————————————————————————————————————————————————————————
# Hook to mark dead workers so their metric files get merged & cleaned up
# —————————————————————————————————————————————————————————————————————————————
def child_exit(server, worker):
    try:
        multiprocess.mark_process_dead(worker.pid)
    except Exception:
        logging.exception(
            f"Failed to mark process {worker.pid} dead in multiprocess collector"
        )


# —————————————————————————————————————————————————————————————————————————————
# Gunicorn configuration
# —————————————————————————————————————————————————————————————————————————————
bind = "127.0.0.1:8080"
workers = 2
threads = 1
timeout = 30
keepalive = 2

worker_class = "gunicorn_prometheus_exporter.plugin.PrometheusGeventWorker"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "debug"

# Process naming
proc_name = "gunicorn-example"

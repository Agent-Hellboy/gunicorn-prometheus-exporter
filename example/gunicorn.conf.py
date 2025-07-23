"""
Gunicorn configuration file demonstrating Prometheus metrics exporter.

This configuration:
- Binds to localhost:8080 for the application
- Uses 2 worker processe
- Uses our PrometheusWorker class for worker metrics
- Uses our PrometheusMaster class for master metrics
- Exports metrics on port 9091 at /metrics endpoint, aggregating across all workers
"""

import logging
import os

import gunicorn.arbiter
from prometheus_client import multiprocess, start_http_server

from gunicorn_prometheus_exporter.metrics import create_master_registry

# Import our custom master to replace the default Gunicorn Arbiter
from gunicorn_prometheus_exporter.master import PrometheusMaster


# —————————————————————————————————————————————————————————————————————————————
# Hook to start a multiprocess‐aware Prometheus metrics server when Gunicorn is ready
# —————————————————————————————————————————————————————————————————————————————
def when_ready(server):
    mp_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if not mp_dir:
        logging.warning("PROMETHEUS_MULTIPROC_DIR not set; skipping metrics server")
        return

    port = int(os.environ.get("PROMETHEUS_METRICS_PORT", 9090))
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Prometheus multiprocess metrics server on :{port}")

    # Use the existing registry from our metrics module
    from gunicorn_prometheus_exporter.metrics import registry
    
    # Serve that registry on HTTP
    start_http_server(port, registry=registry)
    
    # Log that we're using our custom master
    logger.info("Using PrometheusMaster for signal handling and worker restart tracking")
    logger.info("✅ Metrics server started successfully - includes both worker and master metrics")
    

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
# Hook to initialize master metrics when the master starts
# —————————————————————————————————————————————————————————————————————————————
def on_starting(server):
    """Initialize master metrics when the master starts."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("🚀 Master starting - initializing PrometheusMaster metrics")
    
    # Import master metrics to ensure they're initialized
    from gunicorn_prometheus_exporter.metrics import MASTER_WORKER_RESTARTS
    logger.info("✅ Master metrics initialized")


# —————————————————————————————————————————————————————————————————————————————
# Gunicorn configuration
# —————————————————————————————————————————————————————————————————————————————
bind = "127.0.0.1:8080"
workers = 2
threads = 1
timeout = 30
keepalive = 2

# Use our custom worker class for worker metrics
worker_class = "gunicorn_prometheus_exporter.plugin.PrometheusWorker"

# Replace the default Gunicorn Arbiter with our PrometheusMaster
# This allows us to capture master-level metrics like signal handling
gunicorn.arbiter.Arbiter = PrometheusMaster


# Logging
accesslog = "-"
errorlog = "-"
loglevel = "debug"

# Process naming
proc_name = "gunicorn-example"

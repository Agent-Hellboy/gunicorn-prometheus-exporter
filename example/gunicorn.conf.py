"""
Gunicorn configuration file demonstrating Prometheus metrics exporter.

This configuration:
- Binds to localhost:8080 for the application
- Uses 2 worker processes
- Uses our PrometheusWorker class for worker metrics
- Uses our PrometheusMaster class for master metrics
- Exports metrics on port 9090 at /metri    cs endpoint, aggregating across all workers
"""

import logging
import os

from prometheus_client import multiprocess, start_http_server

from gunicorn_prometheus_exporter.utils import (
    ensure_multiprocess_dir,
    get_multiprocess_dir,
)


# —————————————————————————————————————————————————————————————————————————————
# Hook to start a multiprocess‐aware Prometheus metrics server when Gunicorn is ready
# —————————————————————————————————————————————————————————————————————————————
def when_ready(server):
    mp_dir = get_multiprocess_dir()
    if not mp_dir:
        logging.warning("PROMETHEUS_MULTIPROC_DIR not set; skipping metrics server")
        return

    port = int(os.environ.get("PROMETHEUS_METRICS_PORT", 9091))
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Prometheus multiprocess metrics server on :{port}")

    # Get the shared registry from metrics module
    from gunicorn_prometheus_exporter.metrics import registry

    # Initialize MultiProcessCollector
    try:
        multiprocess.MultiProcessCollector(registry)
        logger.info("Successfully initialized MultiProcessCollector")
    except Exception as e:
        logger.error(f"Failed to initialize MultiProcessCollector: {e}")
        return
    
    # Start HTTP server for metrics with retry logic for USR2 upgrades
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            start_http_server(port, registry=registry)
            logger.info("Using PrometheusMaster for signal handling and worker restart tracking")
            logger.info("Metrics server started successfully - includes both worker and master metrics")
            break
        except OSError as e:
            if e.errno == 98 and attempt < max_retries - 1:  # Address already in use
                logger.warning(f"Port {port} in use (attempt {attempt + 1}/{max_retries}), retrying in 1 second...")
                time.sleep(1)
                continue
            else:
                logger.error(f"Failed to start metrics server after {max_retries} attempts: {e}")
                break
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            break


# —————————————————————————————————————————————————————————————————————————————
# Hook to initialize master metrics when Gunicorn starts
# —————————————————————————————————————————————————————————————————————————————
def on_starting(server):
    mp_dir = get_multiprocess_dir()
    if not mp_dir:
        logging.warning("PROMETHEUS_MULTIPROC_DIR not set; skipping master metrics initialization")
        return

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Master starting - initializing PrometheusMaster metrics")
    

    
    # Ensure the multiprocess directory exists
    ensure_multiprocess_dir(mp_dir)
    logger.info(" Multiprocess directory ready: %s", mp_dir)
    
    logger.info(" Master metrics initialized")






# —————————————————————————————————————————————————————————————————————————————
# Gunicorn configuration
# —————————————————————————————————————————————————————————————————————————————
bind = "127.0.0.1:8086"
workers = 2
threads = 1
timeout = 30
keepalive = 2

# Use our custom worker class for worker metrics
worker_class = "gunicorn_prometheus_exporter.plugin.PrometheusWorker"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "debug"

# Process naming
proc_name = "gunicorn-example"

"""
Gunicorn Prometheus Exporter - A worker plugin for Gunicorn that
exports Prometheus metrics.

This module provides a worker plugin for Gunicorn that exports Prometheus
metrics. It includes functionality to update worker metrics and handle
request durations.

It simply patch into the request flow cycle of webserver and application server
and gather info as a middleware/wrapper refer to the test_worker.py for more details

"""

import logging
import os
import time

import psutil
from gunicorn.workers.sync import SyncWorker

from .metrics import (
    WORKER_CPU,
    WORKER_ERROR_HANDLING,
    WORKER_FAILED_REQUESTS,
    WORKER_MEMORY,
    WORKER_REQUEST_DURATION,
    WORKER_REQUESTS,
    WORKER_UPTIME,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrometheusWorker(SyncWorker):
    """Gunicorn worker that exports Prometheus metrics."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()
        self.worker_id = os.getpid()
        self.process = psutil.Process()
        logger.info("PrometheusWorker initialized")

    def init_process(self):
        """Initialize the worker process."""
        logger.info("Initializing worker process")

        super().init_process()
        logger.info("Worker process initialized")

    def update_worker_metrics(self):
        """Update worker metrics."""
        try:
            WORKER_MEMORY.labels(worker_id=self.worker_id).set(
                self.process.memory_info().rss
            )
            WORKER_CPU.labels(worker_id=self.worker_id).set(self.process.cpu_percent())
            WORKER_UPTIME.labels(worker_id=self.worker_id).set(
                time.time() - self.start_time
            )
        except Exception as e:
            logger.error(f"Error updating worker metrics: {e}")

    def handle_request(self, listener, req, client, addr):
        """Handle a request and update metrics."""
        start_time = time.time()
        try:
            # Update worker metrics before handling request
            self.update_worker_metrics()

            # Let parent class handle the request
            resp = super().handle_request(listener, req, client, addr)
            duration = time.time() - start_time

            # Update request metrics
            WORKER_REQUESTS.labels(worker_id=self.worker_id).inc()
            WORKER_REQUEST_DURATION.labels(worker_id=self.worker_id).observe(duration)

            return resp
        except Exception as e:
            WORKER_FAILED_REQUESTS.labels(worker_id=self.worker_id).inc()
            logger.error(f"Error handling request: {e}")
            raise

    def handle_error(self, req, client, addr, einfo):
        """Handle error."""
        error_type = (
            type(einfo).__name__ if isinstance(einfo, BaseException) else str(einfo)
        )
        WORKER_ERROR_HANDLING.labels(
            worker_id=self.worker_id, error_type=error_type
        ).inc()
        logger.info("Handling error")
        super().handle_error(req, client, addr, einfo)

    def handle_quit(self, sig, frame):
        """Handle quit signal."""
        logger.info("Received quit signal")
        super().handle_quit(sig, frame)

    def handle_abort(self, sig, frame):
        """Handle abort signal."""
        logger.info("Handling abort signal")
        super().handle_abort(sig, frame)

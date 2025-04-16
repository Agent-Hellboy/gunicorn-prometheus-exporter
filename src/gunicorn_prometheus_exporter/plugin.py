"""
Gunicorn Prometheus Exporter - A worker plugin for Gunicorn that
exports Prometheus metrics.

This module provides a worker plugin for Gunicorn that exports Prometheus
metrics. It includes functionality to update worker metrics and handle
request durations.

It patches into the request flow cycle of the Gunicorn web server and
exposes internal telemetry (CPU, memory, request count, latency, errors)
via Prometheus-compatible metrics.

You can also subclass the Gunicorn Arbiter to capture master process events.
Refer to `test_worker.py` and `test_metrics.py` for usage and test coverage.
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
    WORKER_STATE,
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
            self.update_worker_metrics()
            resp = super().handle_request(listener, req, client, addr)
            duration = time.time() - start_time

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
        WORKER_STATE.labels(
            worker_id=self.worker_id, state="quit", timestamp=str(time.time())
        ).set(1)
        super().handle_quit(sig, frame)

    def handle_abort(self, sig, frame):
        """Handle abort signal."""
        logger.info("Handling abort signal")
        WORKER_STATE.labels(
            worker_id=self.worker_id, state="abort", timestamp=str(time.time())
        ).set(1)
        super().handle_abort(sig, frame)

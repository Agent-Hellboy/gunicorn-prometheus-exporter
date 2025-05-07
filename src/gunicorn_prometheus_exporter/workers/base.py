"""
Base worker implementations for Gunicorn Prometheus Exporter.
This module provides the base mixin and worker classes with Prometheus metrics support.
"""

import logging
import os
import time

import psutil
from prometheus_client import multiprocess

from ..metrics import (
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


class PrometheusMetricsMixin:
    """Mixin adding Prometheus metrics to a Gunicorn worker.

    This mixin adds Prometheus metrics collection to any Gunicorn worker type.
    It delegates the actual worker implementation to the parent class.

    Example usage:
    class PrometheusSyncWorker(PrometheusMetricsMixin, SyncWorker):
        pass
    """

    def __init__(self, *args, **kwargs):
        """Initialize the worker with metrics support."""
        # Initialize the parent worker class
        super().__init__(*args, **kwargs)
        # Initialize metrics-specific attributes
        self.start_time = time.time()
        self.worker_id = os.getpid()
        self.process = psutil.Process()
        logger.info("PrometheusMetricsMixin initialized for worker %s", self.worker_id)

    def init_process(self):
        """Initialize the worker process with metrics support."""
        # Call parent's init_process first
        super().init_process()
        # Initialize metrics for this worker
        self._init_metrics()
        logger.info("Worker %s process initialized with metrics", self.worker_id)

    def _init_metrics(self):
        """Initialize metrics for this worker."""
        try:
            # Initialize all metrics with default values
            WORKER_MEMORY.set(0, worker_id=self.worker_id)
            WORKER_CPU.set(0, worker_id=self.worker_id)
            WORKER_UPTIME.set(0, worker_id=self.worker_id)
            WORKER_STATE.set(
                1, worker_id=self.worker_id, state="running", timestamp=str(time.time())
            )
            # Force a metrics update
            self.update_worker_metrics()
        except Exception as e:
            logger.error(
                "Error initializing metrics for worker %s: %s", self.worker_id, e
            )

    def update_worker_metrics(self):
        """Update worker metrics."""
        try:
            WORKER_MEMORY.set(self.process.memory_info().rss, worker_id=self.worker_id)
            WORKER_CPU.set(self.process.cpu_percent(), worker_id=self.worker_id)
            WORKER_UPTIME.set(
                time.time() - self.start_time,
                worker_id=self.worker_id,
            )
        except Exception as e:
            logger.error("Error updating worker metrics: %s", e)

    def handle_request(self, listener, req, client, addr):
        """Handle an HTTP request with metrics collection."""
        start = time.time()
        try:
            # Update metrics before handling request
            self.update_worker_metrics()
            # Delegate to parent's handle_request
            response = super().handle_request(listener, req, client, addr)
            # Record metrics after successful request
            duration = time.time() - start
            WORKER_REQUESTS.inc(worker_id=self.worker_id)
            WORKER_REQUEST_DURATION.observe(duration, worker_id=self.worker_id)
            return response
        except Exception as e:
            # Record metrics for failed request
            WORKER_FAILED_REQUESTS.inc(
                worker_id=self.worker_id,
                method=req.method,
                endpoint=req.path,
                error_type=type(e).__name__,
            )
            logger.error("Error handling request: %s", e)
            raise

    def handle_error(self, req, client, addr, einfo):
        """Handle an error with metrics collection."""
        error_type = (
            type(einfo).__name__ if isinstance(einfo, BaseException) else str(einfo)
        )
        WORKER_ERROR_HANDLING.inc(
            worker_id=self.worker_id,
            method=req.method,
            endpoint=req.path,
            error_type=error_type,
        )
        logger.info("Handling error in worker %s", self.worker_id)
        # Delegate to parent's handle_error
        super().handle_error(req, client, addr, einfo)

    def handle_quit(self, sig, frame):
        """Handle quit signal with metrics collection."""
        logger.info("Worker %s received quit signal", self.worker_id)
        WORKER_STATE.set(
            0,
            worker_id=self.worker_id,
            state="quit",
            timestamp=str(time.time()),
        )
        try:
            multiprocess.mark_process_dead(self.worker_id)
        except Exception as e:
            logger.error("Failed to mark process %s dead: %s", self.worker_id, e)
        # Delegate to parent's handle_quit
        super().handle_quit(sig, frame)

    def handle_abort(self, sig, frame):
        """Handle abort signal with metrics collection."""
        logger.info("Worker %s received abort signal", self.worker_id)
        WORKER_STATE.set(
            0,
            worker_id=self.worker_id,
            state="abort",
            timestamp=str(time.time()),
        )
        try:
            multiprocess.mark_process_dead(self.worker_id)
        except Exception as e:
            logger.error("Failed to mark process %s dead: %s", self.worker_id, e)
        # Delegate to parent's handle_abort
        super().handle_abort(sig, frame)

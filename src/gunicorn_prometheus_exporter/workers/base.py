"""
Base worker implementations for Gunicorn Prometheus Exporter.
This module provides the base mixin and worker classes with Prometheus metrics support.
"""

import logging
import os
import time

import psutil

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
    """Mixin adding Prometheus metrics to a Gunicorn worker."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()
        self.worker_id = os.getpid()
        self.process = psutil.Process()
        logger.info("PrometheusMetricsMixin initialized for worker %s", self.worker_id)

    def init_process(self):
        logger.info("Initializing worker process %s", self.worker_id)
        super().init_process()
        logger.info("Worker %s process initialized", self.worker_id)

    def update_worker_metrics(self):
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
        start = time.time()
        try:
            self.update_worker_metrics()
            response = super().handle_request(listener, req, client, addr)
            duration = time.time() - start

            WORKER_REQUESTS.inc(worker_id=self.worker_id)
            WORKER_REQUEST_DURATION.observe(duration, worker_id=self.worker_id)

            return response
        except Exception as e:
            WORKER_FAILED_REQUESTS.inc(
                worker_id=self.worker_id,
                method=req.method,
                endpoint=req.path,
                error_type=type(e).__name__,
            )
            logger.error("Error handling request: %s", e)
            raise

    def handle_error(self, req, client, addr, einfo):
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
        super().handle_error(req, client, addr, einfo)

    def handle_quit(self, sig, frame):
        logger.info("Worker %s received quit signal", self.worker_id)
        WORKER_STATE.set(
            1,
            worker_id=self.worker_id,
            state="quit",
            timestamp=str(time.time()),
        )
        super().handle_quit(sig, frame)

    def handle_abort(self, sig, frame):
        logger.info("Worker %s received abort signal", self.worker_id)
        WORKER_STATE.set(
            1,
            worker_id=self.worker_id,
            state="abort",
            timestamp=str(time.time()),
        )
        super().handle_abort(sig, frame)

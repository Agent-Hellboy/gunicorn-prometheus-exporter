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
import time

import psutil
from gunicorn.workers.sync import SyncWorker

from .config import config
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

# Use configuration for logging level - with fallback for testing
try:
    log_level = config.get_gunicorn_config().get("loglevel", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level))
except Exception:
    # Fallback for testing when config is not fully set up
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


class PrometheusWorker(SyncWorker):
    """Gunicorn worker that exports Prometheus metrics."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()
        # Create a unique worker ID using worker age and timestamp
        # Format: worker_<age>_<timestamp>
        self.worker_id = f"worker_{self.age}_{int(self.start_time)}"
        self.process = psutil.Process()

        logger.info(f"PrometheusWorker initialized with ID: {self.worker_id}")

    def _clear_old_metrics(self):
        """Clear only the old PID‐based worker samples."""
        for MetricClass in [
            WORKER_REQUESTS,
            WORKER_REQUEST_DURATION,
            WORKER_MEMORY,
            WORKER_CPU,
            WORKER_UPTIME,
            WORKER_FAILED_REQUESTS,
            WORKER_ERROR_HANDLING,
            WORKER_STATE,
        ]:
            metric = MetricClass._metric
            labelnames = list(metric._labelnames)

            # 1) Collect the old label‐tuples to delete
            to_delete = []
            for label_values in list(metric._metrics.keys()):
                try:
                    wid = label_values[labelnames.index("worker_id")]
                except ValueError:
                    continue

                if not isinstance(wid, str) or not wid.startswith("worker_"):
                    to_delete.append(label_values)

            # 2) Remove them from the internal store
            for key in to_delete:
                metric._metrics.pop(key, None)

    def update_worker_metrics(self):
        """Update worker metrics."""
        try:
            WORKER_MEMORY.set(
                self.process.memory_info().rss,
                worker_id=self.worker_id,
            )
            # Use cpu_percent with interval=0 to avoid blocking
            WORKER_CPU.set(
                self.process.cpu_percent(interval=0),
                worker_id=self.worker_id,
            )
            WORKER_UPTIME.set(
                time.time() - self.start_time,
                worker_id=self.worker_id,
            )
        except Exception as e:
            logger.error(f"Error updating worker metrics: {e}")

    def handle_request(self, listener, req, client, addr):
        """Handle a request and update metrics."""
        start_time = time.time()
        try:
            # Only update metrics occasionally to avoid performance impact
            if hasattr(self, "_request_count"):
                self._request_count += 1
            else:
                self._request_count = 1

            # Update metrics every 10 requests
            if self._request_count % 10 == 0:
                self.update_worker_metrics()

            resp = super().handle_request(listener, req, client, addr)
            duration = time.time() - start_time

            WORKER_REQUESTS.inc(worker_id=self.worker_id)
            WORKER_REQUEST_DURATION.observe(duration, worker_id=self.worker_id)

            return resp
        except Exception as e:
            WORKER_FAILED_REQUESTS.inc(
                worker_id=self.worker_id,
                method=req.method,
                endpoint=req.path,
                error_type=type(e).__name__,
            )
            logger.error(f"Error handling request: {e}")
            raise

    def handle_error(self, req, client, addr, einfo):
        """Handle error."""
        error_type = (
            type(einfo).__name__ if isinstance(einfo, BaseException) else str(einfo)
        )
        WORKER_ERROR_HANDLING.inc(
            worker_id=self.worker_id,
            method=req.method,
            endpoint=req.path,
            error_type=error_type,
        )
        logger.info("Handling error")
        super().handle_error(req, client, addr, einfo)

    def handle_quit(self, sig, frame):
        """Handle quit signal."""
        logger.info("Received quit signal")
        WORKER_STATE.set(
            1,
            worker_id=self.worker_id,
            state="quit",
            timestamp=str(time.time()),
        )
        super().handle_quit(sig, frame)

    def handle_abort(self, sig, frame):
        """Handle abort signal."""
        logger.info("Handling abort signal")
        WORKER_STATE.set(
            1,
            worker_id=self.worker_id,
            state="abort",
            timestamp=str(time.time()),
        )
        super().handle_abort(sig, frame)

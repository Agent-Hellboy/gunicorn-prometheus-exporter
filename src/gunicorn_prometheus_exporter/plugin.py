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

import importlib.util
import logging
import time

import psutil

from gunicorn.workers.gthread import ThreadWorker
from gunicorn.workers.sync import SyncWorker

from .config import get_config
from .metrics import (
    WORKER_CPU,
    WORKER_ERROR_HANDLING,
    WORKER_FAILED_REQUESTS,
    WORKER_MEMORY,
    WORKER_REQUEST_DURATION,
    WORKER_REQUESTS,
    WORKER_RESTART_COUNT,
    WORKER_RESTART_REASON,
    WORKER_STATE,
    WORKER_UPTIME,
)


# Initialize variables for async workers
EventletWorker = None
GeventWorker = None


EVENTLET_AVAILABLE = importlib.util.find_spec("eventlet") is not None
GEVENT_AVAILABLE = importlib.util.find_spec("gevent") is not None


# Use configuration for logging level - with fallback for testing
try:
    log_level = get_config().get_gunicorn_config().get("loglevel", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level))
except Exception:
    # Fallback for testing when config is not fully set up
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def _setup_logging():
    """Setup logging with configuration."""
    try:
        log_level = get_config().get_gunicorn_config().get("loglevel", "INFO").upper()
        logging.basicConfig(level=getattr(logging, log_level))
    except Exception as e:
        # Fallback to INFO level if config is not available
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).warning(
            "Could not setup logging from config: %s", e
        )


class PrometheusMixin:
    """Mixin class that adds Prometheus metrics functionality to any worker type."""

    def __init__(self, *args, **kwargs):
        # Call the parent class's __init__ first
        super().__init__(*args, **kwargs)

        # Setup logging when worker is initialized
        _setup_logging()
        self.start_time = time.time()
        # Create a unique worker ID using worker age and timestamp
        # Format: worker_<age>_<timestamp>
        self.worker_id = f"worker_{self.age}_{int(self.start_time)}"
        self.process = psutil.Process()
        # Initialize request counter
        self._request_count = 0

        logger.debug("PrometheusMixin initialized with ID: %s", self.worker_id)

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
            WORKER_RESTART_REASON,
            WORKER_RESTART_COUNT,
        ]:
            metric = MetricClass._metric  # pylint: disable=protected-access
            labelnames = list(metric._labelnames)  # pylint: disable=protected-access

            # 1) Collect the old label‐tuples to delete
            to_delete = []
            for label_values in list(metric._metrics.keys()):  # pylint: disable=protected-access
                try:
                    wid = label_values[labelnames.index("worker_id")]
                except ValueError:
                    continue

                # Check if this is an old worker ID (different from current)
                if wid != self.worker_id:
                    to_delete.append(label_values)

            # 2) Delete the old samples
            for label_values in to_delete:
                metric.remove(*label_values)

    def update_worker_metrics(self):
        """Update worker metrics."""
        try:
            # Clear old metrics for this worker
            self._clear_old_metrics()

            # Update current metrics
            memory_info = self.process.memory_info()
            cpu_percent = self.process.cpu_percent()
            uptime = time.time() - self.start_time

            WORKER_MEMORY.labels(worker_id=self.worker_id).set(memory_info.rss)
            WORKER_CPU.labels(worker_id=self.worker_id).set(cpu_percent)
            WORKER_UPTIME.labels(worker_id=self.worker_id).set(uptime)
            timestamp = int(time.time())
            WORKER_STATE.labels(
                worker_id=self.worker_id, state="running", timestamp=timestamp
            ).set(1)

            logger.debug(
                "Updated metrics for worker %s: memory=%s, cpu=%s, uptime=%s",
                self.worker_id,
                memory_info.rss,
                cpu_percent,
                uptime,
            )
        except Exception as e:
            logger.error("Failed to update worker metrics: %s", e)

    def _handle_request_metrics(self, start_time=None):
        """Handle request metrics tracking.

        Args:
            start_time: Optional start time for request duration calculation
        """
        if start_time is None:
            start_time = time.time()

        try:
            # Increment request counter
            self._request_count += 1

            # Update request metrics
            WORKER_REQUESTS.labels(worker_id=self.worker_id).inc()

            # Calculate and record request duration
            duration = time.time() - start_time
            WORKER_REQUEST_DURATION.labels(worker_id=self.worker_id).observe(duration)

            logger.debug(
                "Request metrics updated for worker %s: duration=%s, total_requests=%s",
                self.worker_id,
                duration,
                self._request_count,
            )
        except Exception as e:
            logger.error("Failed to update request metrics: %s", e)

    def _handle_request_error_metrics(self, req, e, start_time=None):
        """Handle request error metrics tracking.

        Args:
            req: The HTTP request object
            e: The exception that occurred
            start_time: Optional start time for request duration calculation
        """
        if start_time is None:
            start_time = time.time()

        try:
            # Calculate request duration
            duration = time.time() - start_time

            # Update failed request metrics
            method, endpoint = self._extract_request_info(req)
            error_type = type(e).__name__

            WORKER_FAILED_REQUESTS.labels(
                worker_id=self.worker_id,
                method=method,
                endpoint=endpoint,
                error_type=error_type,
            ).inc()

            logger.error(
                "Request failed in worker %s: %s (duration=%s)",
                self.worker_id,
                e,
                duration,
            )
        except Exception as metric_error:
            logger.error("Failed to update error metrics: %s", metric_error)

    def _extract_request_from_args(self, args):
        """Extract request object from method arguments using attribute-based detection.

        Args:
            args: Method arguments tuple

        Returns:
            Request object or None if not found
        """
        for arg in args:
            # Check if this looks like a request object
            if hasattr(arg, "method") and hasattr(arg, "path"):
                return arg
        return None

    def _extract_request_info(self, req):
        """Extract method and endpoint information from request object.

        Args:
            req: Request object or None

        Returns:
            tuple: (method, endpoint) both as strings
        """
        method = req.method if req and hasattr(req, "method") else "UNKNOWN"
        endpoint = req.path if req and hasattr(req, "path") else "UNKNOWN"
        return method, endpoint

    def _generic_handle_request(self, parent_method, *args, **kwargs):
        """Generic handle_request wrapper for all worker types.

        Args:
            parent_method: The parent class's handle_request method
            *args: Arguments to pass to parent method
            **kwargs: Keyword arguments to pass to parent method
        """
        start_time = time.time()

        try:
            # Update worker metrics on each request
            self.update_worker_metrics()

            # Call parent handle_request
            result = parent_method(*args, **kwargs)

            # Update request metrics after successful request
            self._handle_request_metrics(start_time)

            return result
        except Exception as e:
            # Handle request error metrics
            # Extract req from args using robust attribute-based detection
            req = self._extract_request_from_args(args)
            self._handle_request_error_metrics(req, e, start_time)
            raise

    def _generic_handle_error(self, req, client, addr, e):
        """Generic handle_error wrapper for all worker types.

        Args:
            req: The HTTP request
            client: The client socket
            addr: The client address
            e: The exception that occurred
        """
        # Extract method and endpoint from request if available
        method, endpoint = self._extract_request_info(req)

        # Update error metrics
        error_type = type(e).__name__
        WORKER_ERROR_HANDLING.labels(
            worker_id=self.worker_id,
            method=method,
            endpoint=endpoint,
            error_type=error_type,
        ).inc()

        # Call parent handle_error
        super().handle_error(req, client, addr, e)

    def _generic_handle_quit(self, sig, frame):
        """Generic handle_quit wrapper for all worker types.

        Args:
            sig: The signal number
            frame: The current frame
        """
        # Update worker state to quitting
        timestamp = int(time.time())
        WORKER_STATE.labels(
            worker_id=self.worker_id, state="quitting", timestamp=timestamp
        ).set(1)

        # Track worker restart
        WORKER_RESTART_REASON.labels(worker_id=self.worker_id, reason="quit").inc()

        WORKER_RESTART_COUNT.labels(
            worker_id=self.worker_id, restart_type="graceful", reason="quit"
        ).inc()

        # Call parent handle_quit
        super().handle_quit(sig, frame)

    def _generic_handle_abort(self, sig, frame):
        """Generic handle_abort wrapper for all worker types.

        Args:
            sig: The signal number
            frame: The current frame
        """
        # Update worker state to aborting
        timestamp = int(time.time())
        WORKER_STATE.labels(
            worker_id=self.worker_id, state="aborting", timestamp=timestamp
        ).set(1)

        # Track worker restart
        WORKER_RESTART_REASON.labels(worker_id=self.worker_id, reason="abort").inc()

        WORKER_RESTART_COUNT.labels(
            worker_id=self.worker_id, restart_type="forced", reason="abort"
        ).inc()

        # Call parent handle_abort
        super().handle_abort(sig, frame)


# Worker classes with Prometheus metrics support
class PrometheusWorker(PrometheusMixin, SyncWorker):
    """Sync worker with Prometheus metrics."""

    def handle_request(self, listener, req, client, addr):
        """Handle a request and update metrics."""
        return self._generic_handle_request(
            super().handle_request, listener, req, client, addr
        )

    def handle_error(self, req, client, addr, e):  # pylint: disable=arguments-renamed
        """Handle request errors and update error metrics."""
        return self._generic_handle_error(req, client, addr, e)

    def handle_quit(self, sig, frame):
        """Handle quit signal and update worker state."""
        self._generic_handle_quit(sig, frame)

    def handle_abort(self, sig, frame):
        """Handle abort signal and update worker state."""
        self._generic_handle_abort(sig, frame)


class PrometheusThreadWorker(PrometheusMixin, ThreadWorker):
    """Thread worker with Prometheus metrics."""

    def handle_request(self, req, conn):
        """Handle a request and update metrics."""
        return self._generic_handle_request(super().handle_request, req, conn)

    def handle_error(self, req, client, addr, e):  # pylint: disable=arguments-renamed
        """Handle request errors and update error metrics."""
        return self._generic_handle_error(req, client, addr, e)

    def handle_quit(self, sig, frame):
        """Handle quit signal and update worker state."""
        self._generic_handle_quit(sig, frame)

    def handle_abort(self, sig, frame):
        """Handle abort signal and update worker state."""
        self._generic_handle_abort(sig, frame)


# Initialize async worker classes as None
PrometheusEventletWorker = None
PrometheusGeventWorker = None


def _create_eventlet_worker():
    """Create PrometheusEventletWorker class if available."""
    global PrometheusEventletWorker
    if EVENTLET_AVAILABLE:
        try:
            from gunicorn.workers.geventlet import EventletWorker

            class PrometheusEventletWorker(PrometheusMixin, EventletWorker):  # pylint: disable=unused-variable
                """Eventlet worker with Prometheus metrics."""

                def handle_request(self, listener_name, req, sock, addr):
                    """Handle a request and update metrics."""
                    return self._generic_handle_request(
                        super().handle_request, listener_name, req, sock, addr
                    )

                def handle_error(self, req, client, addr, e):  # pylint: disable=arguments-renamed
                    """Handle request errors and update error metrics."""
                    return self._generic_handle_error(req, client, addr, e)

                def handle_quit(self, sig, frame):
                    """Handle quit signal and update worker state."""
                    self._generic_handle_quit(sig, frame)

                def handle_abort(self, sig, frame):
                    """Handle abort signal and update worker state."""
                    self._generic_handle_abort(sig, frame)
        except (ImportError, RuntimeError):
            PrometheusEventletWorker = None


def _create_gevent_worker():
    """Create PrometheusGeventWorker class if available."""
    global PrometheusGeventWorker
    if GEVENT_AVAILABLE:
        try:
            from gunicorn.workers.ggevent import GeventWorker

            class PrometheusGeventWorker(PrometheusMixin, GeventWorker):  # pylint: disable=unused-variable
                """Gevent worker with Prometheus metrics."""

                def handle_request(self, listener_name, req, sock, addr):
                    """Handle a request and update metrics."""
                    return self._generic_handle_request(
                        super().handle_request, listener_name, req, sock, addr
                    )

                def handle_error(self, req, client, addr, e):  # pylint: disable=arguments-renamed
                    """Handle request errors and update error metrics."""
                    return self._generic_handle_error(req, client, addr, e)

                def handle_quit(self, sig, frame):
                    """Handle quit signal and update worker state."""
                    self._generic_handle_quit(sig, frame)

                def handle_abort(self, sig, frame):
                    """Handle abort signal and update worker state."""
                    self._generic_handle_abort(sig, frame)
        except (ImportError, RuntimeError):
            PrometheusGeventWorker = None


# Create async worker classes
_create_eventlet_worker()
_create_gevent_worker()


def get_prometheus_eventlet_worker():
    """Get PrometheusEventletWorker class if available."""
    return PrometheusEventletWorker


def get_prometheus_gevent_worker():
    """Get PrometheusGeventWorker class if available."""
    return PrometheusGeventWorker

import logging
import os
import queue
import threading
import time

from gunicorn.arbiter import Arbiter

from .metrics import MasterWorkerRestarts


# Use configuration for logging level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrometheusMaster(Arbiter):
    def __init__(self, app):
        super().__init__(app)
        self.start_time = time.time()

        # Set up multiprocess metrics for master process
        self._setup_master_metrics()

        # Set up asynchronous signal metric capture
        self._setup_async_signal_capture()

        logger.info("PrometheusMaster initialized")

    def _setup_master_metrics(self):
        """Set up multiprocess metrics for the master process."""
        try:
            # Get the multiprocess directory from environment
            mp_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
            if mp_dir:
                logger.info(
                    "Master metrics configured for multiprocess directory: %s", mp_dir
                )
            else:
                logger.warning(
                    "PROMETHEUS_MULTIPROC_DIR not set, "
                    "master metrics may not be exposed"
                )
        except Exception as e:
            logger.error("Failed to set up master metrics: %s", e)

    def _setup_async_signal_capture(self):
        """Set up async signal metric capture to avoid blocking signal handlers."""
        self._signal_queue = queue.Queue()
        self._signal_thread = None
        self._shutdown_event = threading.Event()

        # Start background thread for processing signal metrics
        self._signal_thread = threading.Thread(
            target=self._process_signal_metrics,
            name="signal-metrics-processor",
            daemon=True,
        )
        self._signal_thread.start()
        logger.info(
            "Asynchronous signal metric capture started (thread: %s)",
            self._signal_thread.name,
        )

        # Verify thread is running
        if self._signal_thread.is_alive():
            logger.info("Signal metrics processor thread is running")
        else:
            logger.warning("Signal metrics processor thread failed to start")

    def _process_signal_metrics(self):
        """Background thread that processes signal metrics asynchronously."""
        logger.info("Signal metrics processor thread started")  # Add debug logging
        while not self._shutdown_event.is_set():
            try:
                # Wait for signal metric with timeout
                reason = self._signal_queue.get(timeout=1.0)
                logger.info("Processing signal metric: %s", reason)  # Add debug logging

                # Safely increment metric
                try:
                    MasterWorkerRestarts.inc(reason=reason)
                    logger.info(
                        "Signal metric captured successfully: %s", reason
                    )  # Change to info level
                except Exception as e:
                    logger.warning("Failed to capture signal metric %s: %s", reason, e)

                # Mark task as done
                self._signal_queue.task_done()

            except queue.Empty:
                # Timeout - continue loop to check shutdown event
                continue
            except Exception as e:
                logger.error("Error in signal metrics processor: %s", e)
                time.sleep(0.1)  # Brief pause before retry

        logger.info("Signal metrics processor thread stopped")  # Add debug logging

    def _queue_signal_metric(self, reason: str) -> None:
        """Queue a signal metric for asynchronous processing with fallback."""
        # Try asynchronous approach first
        try:
            logger.info("Queuing signal metric: %s", reason)
            self._signal_queue.put(reason, timeout=0.1)
            logger.info("Signal metric queued successfully: %s", reason)
            return
        except queue.Full:
            logger.warning(
                "Signal metric queue full, trying synchronous fallback: %s", reason
            )
        except Exception as e:
            logger.error(
                "Failed to queue signal metric %s, trying synchronous fallback: %s",
                reason,
                e,
            )

        # Fallback: synchronous approach
        try:
            logger.info("Fallback: synchronous metric capture for %s", reason)
            MasterWorkerRestarts.inc(reason=reason)
            logger.info("Fallback synchronous metric capture successful: %s", reason)
        except Exception as fallback_e:
            logger.error(
                "Fallback synchronous metric capture also failed for %s: %s",
                reason,
                fallback_e,
            )

    def _safe_inc_restart(self, reason: str) -> None:
        """Safely increment MasterWorkerRestarts without blocking signal handling."""
        try:
            MasterWorkerRestarts.inc(reason=reason)
        except Exception:  # nosec
            logger.debug(
                "Failed to inc MasterWorkerRestarts(reason=%s)", reason, exc_info=True
            )

    def handle_int(self):
        """Handle INT signal (Ctrl+C)."""
        try:
            logger.info("Gunicorn master INT signal received (Ctrl+C)")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass

        # For SIGINT, capture metric synchronously BEFORE calling super().handle_int()
        # because super().handle_int() will terminate the process immediately
        try:
            logger.info("Capturing SIGINT metric synchronously before termination")
            MasterWorkerRestarts.inc(reason="int")

            # Force a small delay to ensure the metric is written to storage
            # This is critical for SIGINT since the process terminates immediately
            time.sleep(0.1)  # 100ms delay to allow metric to be written

            # Try to force flush metrics to storage (if possible)
            try:
                from .config import config

                if config.redis_enabled:
                    # For Redis storage, try to force flush Redis connection
                    try:
                        from .backend import get_redis_storage_manager

                        manager = get_redis_storage_manager()
                        if hasattr(manager, "_redis_client") and manager._redis_client:
                            # Force Redis to flush any pending writes
                            manager._redis_client.ping()  # Test connection and flush
                            logger.info("Forced Redis metrics flush")
                    except Exception as redis_e:
                        logger.debug("Could not force Redis flush: %s", redis_e)
                else:
                    # For file-based multiprocess storage
                    from prometheus_client import values

                    if hasattr(values, "ValueClass") and hasattr(
                        values.ValueClass, "_write_to_file"
                    ):
                        # Force write to multiprocess files
                        values.ValueClass._write_to_file()
                        logger.info("Forced file-based metrics flush")
            except Exception as flush_e:
                logger.debug("Could not force metrics flush: %s", flush_e)

            logger.info("SIGINT metric captured successfully before termination")
        except Exception as e:
            logger.error("Failed to capture SIGINT metric: %s", e)

        # Now call the parent handler which will terminate the process
        super().handle_int()

    def handle_hup(self):
        """Handle HUP signal."""
        try:
            logger.info("Gunicorn master HUP signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_hup()
        # Queue signal metric for asynchronous processing (non-blocking)
        self._queue_signal_metric("hup")

    def handle_ttin(self):
        """Handle TTIN signal."""
        try:
            logger.info("Gunicorn master TTIN signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_ttin()
        # Queue signal metric for asynchronous processing (non-blocking)
        self._queue_signal_metric("ttin")

    def handle_ttou(self):
        """Handle TTOU signal."""
        try:
            logger.info("Gunicorn master TTOU signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_ttou()
        # Queue signal metric for asynchronous processing (non-blocking)
        self._queue_signal_metric("ttou")

    def handle_chld(self, sig, frame):
        """Handle CHLD signal."""
        # Note: No logging here to avoid reentrant call issues
        # CHLD signals are very frequent and logging can cause recursion
        super().handle_chld(sig, frame)
        # Queue signal metric for asynchronous processing (non-blocking)
        self._queue_signal_metric("chld")

    def handle_usr1(self):
        """Handle USR1 signal."""
        try:
            logger.info("Gunicorn master USR1 signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_usr1()
        # Queue signal metric for asynchronous processing (non-blocking)
        self._queue_signal_metric("usr1")

    def handle_usr2(self):
        """Handle USR2 signal."""
        try:
            logger.info("Gunicorn master USR2 signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_usr2()
        # Queue signal metric for asynchronous processing (non-blocking)
        self._queue_signal_metric("usr2")

    def init_signals(self):
        """Initialize signal handlers."""
        super().init_signals()
        self.SIG_QUEUE = []

    def stop(self, graceful=True):
        """Stop the master and clean up resources."""
        # Signal shutdown to background thread
        if hasattr(self, "_shutdown_event"):
            self._shutdown_event.set()

        # Wait for signal processing thread to finish (with timeout)
        if (
            hasattr(self, "_signal_thread")
            and self._signal_thread
            and self._signal_thread.is_alive()
        ):
            self._signal_thread.join(timeout=2.0)
            if self._signal_thread.is_alive():
                logger.warning("Signal metrics thread did not stop gracefully")

        # Call parent stop method
        super().stop(graceful)

    def signal(self, sig, frame):  # pylint: disable=unused-argument
        """Override signal method to queue signals for processing."""
        if len(self.SIG_QUEUE) < 5:
            self.SIG_QUEUE.append(sig)
            self.wakeup()
        # Don't call super().signal() as it would queue the signal again
        # The signals will be processed in the main loop via self.SIG_QUEUE

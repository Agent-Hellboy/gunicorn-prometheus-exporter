import logging
import os
import queue
import signal
import threading
import time

from gunicorn.arbiter import Arbiter

from .metrics import (
    MasterWorkerRestartCount,
    MasterWorkerRestarts,
    WorkerRestartCount,
    WorkerRestartReason,
)


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
        # Bound queue to prevent unbounded growth under CHLD storms
        self._signal_queue = queue.Queue(maxsize=1024)
        self._signal_thread = None
        self._shutdown_event = threading.Event()

        # Start background thread for processing signal metrics
        self._signal_thread = threading.Thread(
            target=self._process_signal_metrics,
            name="signal-metrics-processor",
            daemon=True,
        )
        self._signal_thread.start()
        logger.debug(
            "Asynchronous signal metric capture started (thread: %s)",
            self._signal_thread.name,
        )

        # Verify thread is running
        if not self._signal_thread.is_alive():
            logger.warning("Signal metrics processor thread failed to start")

    def _process_signal_metrics(self):
        """Background thread that processes signal metrics asynchronously."""
        logger.debug("Signal metrics processor thread started")
        while not self._shutdown_event.is_set():
            try:
                # Wait for signal metric with timeout
                reason = self._signal_queue.get(timeout=1.0)
                logger.debug("Processing signal metric: %s", reason)

                # Safely increment metric
                try:
                    self._safe_inc_restart(reason)
                    logger.debug("Signal metric captured successfully: %s", reason)
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

        logger.debug("Signal metrics processor thread stopped")

    def _queue_signal_metric(self, reason: str) -> None:
        """Queue a signal metric for asynchronous processing with fallback."""
        # Try asynchronous approach first
        try:
            logger.debug("Queuing signal metric: %s", reason)
            self._signal_queue.put_nowait(reason)
            logger.debug("Signal metric queued successfully: %s", reason)
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
            logger.debug("Fallback: synchronous metric capture for %s", reason)
            self._safe_inc_restart(reason)
            logger.debug("Fallback synchronous metric capture successful: %s", reason)
        except Exception as fallback_e:
            logger.error(
                "Fallback synchronous metric capture also failed for %s: %s",
                reason,
                fallback_e,
            )

    def _safe_inc_restart(
        self, reason: str, worker_id: str = None, restart_type: str = "signal"
    ) -> None:
        """Safely increment restart metrics without blocking signal handling."""
        try:
            # Increment master-level restart metric
            MasterWorkerRestarts.inc(reason=reason)

            # Increment worker-level restart metrics if worker_id is provided
            if worker_id:
                WorkerRestartReason.inc(worker_id=worker_id, reason=reason)
                WorkerRestartCount.inc(
                    worker_id=worker_id, restart_type=restart_type, reason=reason
                )
                # Also increment master-level detailed restart count metric
                MasterWorkerRestartCount.inc(
                    worker_id=worker_id, reason=reason, restart_type=restart_type
                )
        except Exception:  # nosec
            logger.debug(
                "Failed to inc restart metrics(worker_id=%s, reason=%s)",
                worker_id,
                reason,
                exc_info=True,
            )

    def handle_int(self):
        """Handle INT signal (Ctrl+C)."""
        try:
            logger.debug("SIGINT received - capturing metric")
            self._safe_inc_restart("int")
            logger.debug("SIGINT metric incremented")

            # Force flush to storage for SIGINT to ensure metric is written before
            # termination
            try:
                from .config import get_config

                if get_config().redis_enabled:
                    logger.debug("SIGINT - forcing Redis flush")
                    # For Redis storage
                    from .backend import get_redis_storage_manager

                    manager = get_redis_storage_manager()
                    client = manager.get_client()
                    if client and hasattr(client, "ping"):
                        try:
                            client.ping()
                            logger.debug("SIGINT - Redis flush completed")
                        except Exception:
                            logger.warning(
                                "Redis ping failed while forcing metrics flush",
                                exc_info=True,
                            )
                else:
                    logger.debug("SIGINT - forcing file flush")
                    # For file-based multiprocess storage
                    from prometheus_client import values

                    if hasattr(values, "ValueClass") and hasattr(
                        values.ValueClass, "_write_to_file"
                    ):
                        values.ValueClass._write_to_file()  # Force file flush
                        logger.debug("SIGINT - file flush completed")
            except Exception:  # nosec
                logger.debug("Could not force metrics flush", exc_info=True)

            logger.debug("SIGINT - metric capture and flush completed")
        except Exception:  # nosec
            logger.error("Failed to capture SIGINT metric", exc_info=True)

        logger.debug("SIGINT - calling super().handle_int()")
        super().handle_int()

    def handle_hup(self):
        """Handle HUP signal."""
        try:
            logger.debug("Gunicorn master HUP signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_hup()
        # Queue signal metric for asynchronous processing (non-blocking)
        self._queue_signal_metric("hup")

    def handle_ttin(self):
        """Handle TTIN signal."""
        try:
            logger.debug("Gunicorn master TTIN signal received")
        except Exception:  # nosec
            pass
        super().handle_ttin()
        self._queue_signal_metric("ttin")

    def handle_ttou(self):
        """Handle TTOU signal."""
        try:
            logger.debug("Gunicorn master TTOU signal received")
        except Exception:  # nosec
            pass
        super().handle_ttou()
        self._queue_signal_metric("ttou")

    def handle_chld(self, sig, frame):
        """Handle CHLD signal."""
        # Handle CHLD signal with protection against logging reentrancy
        # The parent handle_chld method may log worker termination messages
        # which can cause RuntimeError: reentrant call when called from signal context
        try:
            super().handle_chld(sig, frame)
        except RuntimeError as e:
            if "reentrant call" in str(e):
                # Silently ignore logging reentrancy errors during signal handling
                # This prevents crashes when logging happens during signal context
                pass
            else:
                # Re-raise other RuntimeErrors
                raise

        # Queue signal metric for asynchronous processing
        self._queue_signal_metric("chld")

    def handle_usr1(self):
        """Handle USR1 signal."""
        try:
            logger.debug("Gunicorn master USR1 signal received")
        except Exception:  # nosec
            pass
        super().handle_usr1()
        self._queue_signal_metric("usr1")

    def handle_usr2(self):
        """Handle USR2 signal."""
        try:
            logger.debug("Gunicorn master USR2 signal received")
        except Exception:  # nosec
            pass
        super().handle_usr2()
        self._queue_signal_metric("usr2")

    def init_signals(self):
        """Initialize signal handlers."""
        super().init_signals()
        self.SIG_QUEUE = []

    def stop(self, graceful=True):
        """Stop the master and clean up resources."""
        # Signal shutdown to background thread immediately
        if hasattr(self, "_shutdown_event"):
            self._shutdown_event.set()

        # Call parent stop method
        super().stop(graceful)

    def signal(self, sig, frame):  # pylint: disable=unused-argument
        """Override signal method to queue signals for processing."""
        # Allow SIGINT to be processed normally for immediate termination
        if sig == signal.SIGINT:
            super().signal(sig, frame)
            return

        # Queue other signals for processing
        if len(self.SIG_QUEUE) < 5:
            self.SIG_QUEUE.append(sig)
            self.wakeup()
        # Don't call super().signal() as it would queue the signal again
        # The signals will be processed in the main loop via self.SIG_QUEUE

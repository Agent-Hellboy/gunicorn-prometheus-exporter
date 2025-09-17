import logging
import os
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

    def handle_int(self):
        """Handle INT signal (Ctrl+C)."""
        try:
            logger.info("Gunicorn master INT signal received (Ctrl+C)")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        MasterWorkerRestarts.labels(reason="int").inc()
        super().handle_int()

    def handle_hup(self):
        """Handle HUP signal."""
        try:
            logger.info("Gunicorn master HUP signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        MasterWorkerRestarts.labels(reason="hup").inc()
        super().handle_hup()

    def handle_ttin(self):
        """Handle TTIN signal."""
        logger.info("Gunicorn master TTIN signal received")
        MasterWorkerRestarts.labels(reason="ttin").inc()
        super().handle_ttin()

    def handle_ttou(self):
        """Handle TTOU signal."""
        logger.info("Gunicorn master TTOU signal received")
        MasterWorkerRestarts.labels(reason="ttou").inc()
        super().handle_ttou()

    def handle_chld(self, sig, frame):
        """Handle CHLD signal."""
        try:
            logger.info("Gunicorn master CHLD signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        MasterWorkerRestarts.labels(reason="chld").inc()
        super().handle_chld(sig, frame)

    def handle_usr1(self):
        """Handle USR1 signal."""
        try:
            logger.info("Gunicorn master USR1 signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        MasterWorkerRestarts.labels(reason="usr1").inc()
        super().handle_usr1()

    def handle_usr2(self):
        """Handle USR2 signal."""
        try:
            logger.info("Gunicorn master USR2 signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        MasterWorkerRestarts.labels(reason="usr2").inc()
        super().handle_usr2()

    def init_signals(self):
        """Initialize signal handlers."""
        super().init_signals()
        self.SIG_QUEUE = []

    def signal(self, sig, frame):  # pylint: disable=unused-argument
        """Override signal method to queue signals for processing."""
        if len(self.SIG_QUEUE) < 5:
            self.SIG_QUEUE.append(sig)
            self.wakeup()
        # Don't call super().signal() as it would queue the signal again
        # The signals will be processed in the main loop via self.SIG_QUEUE

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
        super().handle_int()
        self._safe_inc_restart("int")

    def handle_hup(self):
        """Handle HUP signal."""
        try:
            logger.info("Gunicorn master HUP signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_hup()
        self._safe_inc_restart("hup")

    def handle_ttin(self):
        """Handle TTIN signal."""
        try:
            logger.info("Gunicorn master TTIN signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_ttin()
        self._safe_inc_restart("ttin")

    def handle_ttou(self):
        """Handle TTOU signal."""
        try:
            logger.info("Gunicorn master TTOU signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_ttou()
        self._safe_inc_restart("ttou")

    def handle_chld(self, sig, frame):
        """Handle CHLD signal."""
        try:
            logger.info("Gunicorn master CHLD signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_chld(sig, frame)
        self._safe_inc_restart("chld")

    def handle_usr1(self):
        """Handle USR1 signal."""
        try:
            logger.info("Gunicorn master USR1 signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_usr1()
        self._safe_inc_restart("usr1")

    def handle_usr2(self):
        """Handle USR2 signal."""
        try:
            logger.info("Gunicorn master USR2 signal received")
        except Exception:  # nosec
            # Avoid logging errors in signal handlers
            pass
        super().handle_usr2()
        self._safe_inc_restart("usr2")

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

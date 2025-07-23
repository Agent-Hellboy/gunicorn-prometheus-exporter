import logging
import os
import time

from gunicorn.arbiter import Arbiter
from prometheus_client import multiprocess

from .metrics import MASTER_WORKER_RESTARTS

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
                # Set the multiprocess directory for this process
                multiprocess.MultiProcessCollector._registry = None
                multiprocess.MultiProcessCollector._pid = os.getpid()
                multiprocess.MultiProcessCollector._mp_dir = mp_dir
                logger.info(f"Master metrics configured for multiprocess directory: {mp_dir}")
            else:
                logger.warning("PROMETHEUS_MULTIPROC_DIR not set, master metrics may not be exposed")
        except Exception as e:
            logger.error(f"Failed to set up master metrics: {e}")

    def handle_hup(self):
        """Handle HUP signal."""
        logger.info("Gunicorn master HUP signal received")
        MASTER_WORKER_RESTARTS.inc(reason="hup")
        self._write_master_metrics()
        super().handle_hup()

    def handle_ttin(self):
        """Handle TTI signal."""
        logger.info("Gunicorn master TTI signal received")
        MASTER_WORKER_RESTARTS.inc(reason="ttin")
        self._write_master_metrics()
        super().handle_ttin()

    def handle_ttou(self):
        """Handle TTOU signal."""
        logger.info("Gunicorn master TTOU signal received")
        MASTER_WORKER_RESTARTS.inc(reason="ttou")
        self._write_master_metrics()
        super().handle_ttou()

    def handle_chld(self, sig, frame):
        """Handle CHLD signal."""
        logger.info("Gunicorn master CHLD signal received")
        MASTER_WORKER_RESTARTS.inc(reason="chld")
        self._write_master_metrics()
        super().handle_chld(sig, frame)

    def handle_usr1(self):
        """Handle USR1 signal."""
        logger.info("Gunicorn master USR1 signal received")
        MASTER_WORKER_RESTARTS.inc(reason="usr1")
        self._write_master_metrics()
        super().handle_usr1()

    def handle_usr2(self):
        """Handle USR2 signal."""
        logger.info("Gunicorn master USR2 signal received")
        MASTER_WORKER_RESTARTS.inc(reason="usr2")
        self._write_master_metrics()
        super().handle_usr2()

    def _write_master_metrics(self):
        """Write master metrics to multiprocess directory."""
        try:
            # Force write metrics to multiprocess directory
            multiprocess.mark_process_dead(os.getpid())
            logger.debug("Master metrics written to multiprocess directory")
        except Exception as e:
            logger.error(f"Failed to write master metrics: {e}")

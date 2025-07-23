import logging
import time

from gunicorn.arbiter import Arbiter

from .metrics import MASTER_WORKER_RESTARTS

logger = logging.getLogger(__name__)


class PrometheusMaster(Arbiter):
    def __init__(self, app):
        super().__init__(app)
        self.start_time = time.time()
        logger.info("PrometheusMaster initialized")

    def handle_hup(self):
        """Handle HUP signal."""
        logger.info("Gunicorn master HUP signal received")
        MASTER_WORKER_RESTARTS.inc(reason="hup")
        super().handle_hup()

    def handle_ttin(self):
        """Handle TTI signal."""
        logger.info("Gunicorn master TTI signal received")
        MASTER_WORKER_RESTARTS.inc(reason="ttin")
        super().handle_ttin()

    def handle_ttou(self):
        """Handle TTOU signal."""
        logger.info("Gunicorn master TTOU signal received")
        MASTER_WORKER_RESTARTS.inc(reason="ttou")
        super().handle_ttou()

    def handle_chld(self, sig, frame):
        """Handle CHLD signal."""
        logger.info("Gunicorn master CHLD signal received")
        MASTER_WORKER_RESTARTS.inc(reason="chld")
        super().handle_chld(sig, frame)

    def handle_usr1(self):
        """Handle USR1 signal."""
        logger.info("Gunicorn master USR1 signal received")
        MASTER_WORKER_RESTARTS.inc(reason="usr1")
        super().handle_usr1()

    def handle_usr2(self):
        """Handle USR2 signal."""
        logger.info("Gunicorn master USR2 signal received")
        MASTER_WORKER_RESTARTS.inc(reason="usr2")
        super().handle_usr2()

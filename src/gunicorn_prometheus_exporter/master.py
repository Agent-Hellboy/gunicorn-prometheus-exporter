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
        MASTER_WORKER_RESTARTS.inc(reason="restart")
        super().handle_hup()

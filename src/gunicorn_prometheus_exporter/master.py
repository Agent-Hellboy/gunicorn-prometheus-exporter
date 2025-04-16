from gunicorn.arbiter import Arbiter
import time
import logging

logger = logging.getLogger(__name__)

from .metrics import MASTER_WORKER_RESTARTS


class PrometheusMaster(Arbiter):
    def __init__(self, app):
        super().__init__(app)
        self.start_time = time.time()
        logger.info("PrometheusMaster initialized")

    def handle_hup(self):
        """Handle HUP signal."""
        logger.info("Gunicorn master HUP signal received")
        MASTER_WORKER_RESTARTS.labels(reason="restart").inc()
        super().handle_hup()

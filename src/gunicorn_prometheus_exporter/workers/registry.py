"""
Worker registry for Gunicorn Prometheus Exporter.
This module provides a registry for managing worker types.
"""

import logging
from typing import Dict, Optional, Type

from gunicorn.workers.sync import SyncWorker

from .gevent import GEVENT_AVAILABLE, PrometheusGeventWorker
from .sync import PrometheusSyncWorker

logger = logging.getLogger(__name__)


class WorkerRegistry:
    """Registry for managing worker types."""

    def __init__(self):
        """Initialize the worker registry."""
        self._workers: Dict[str, Type[SyncWorker]] = {
            "sync": PrometheusSyncWorker,
        }

        if GEVENT_AVAILABLE:
            self._workers["gevent"] = PrometheusGeventWorker

    def get_worker_class(self, worker_class_name: str) -> Optional[Type[SyncWorker]]:
        """Get a worker class by name.

        Args:
            worker_class_name: The name of the worker class to get.

        Returns:
            The worker class if found, None otherwise.
        """
        worker_class = self._workers.get(worker_class_name)
        if worker_class is None:
            logger.warning(f"Worker class {worker_class_name} not found")
            if worker_class_name == "gevent" and not GEVENT_AVAILABLE:
                logger.error(
                    "GeventWorker requested but gevent is not installed. "
                    "Please install gevent to use GeventWorker."
                )
            return PrometheusSyncWorker
        return worker_class

    def register_worker(self, name: str, worker_class: Type[SyncWorker]) -> None:
        """Register a new worker class.

        Args:
            name: The name to register the worker class under.
            worker_class: The worker class to register.
        """
        self._workers[name] = worker_class
        logger.info(f"Registered worker class {name}")


# Create a global registry instance
registry = WorkerRegistry()

"""Base forwarder class for metrics forwarding."""

import logging
import threading

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


class BaseForwarder(ABC):
    """Abstract base class for metric forwarders."""

    def __init__(
        self,
        forward_interval: int = 30,
        name: Optional[str] = None,
    ):
        """Initialize base forwarder."""
        self.forward_interval = forward_interval
        self.name = name or self.__class__.__name__

        # Threading
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

        logger.info(
            "Initialized %s forwarder (interval: %ds)", self.name, self.forward_interval
        )

    @abstractmethod
    def _connect(self) -> bool:
        """Connect to the target backend. Returns True if successful."""
        raise NotImplementedError

    @abstractmethod
    def _forward_metrics(self, metrics_data: str) -> bool:
        """Forward metrics data to backend. Returns True if successful."""
        raise NotImplementedError

    @abstractmethod
    def _disconnect(self):
        """Disconnect from the target backend."""
        raise NotImplementedError

    def _generate_metrics(self) -> Optional[str]:
        """Generate metrics data. Override if custom logic needed."""
        try:
            from prometheus_client import generate_latest

            from ..metrics import get_shared_registry

            registry = get_shared_registry()
            metrics_data = generate_latest(registry).decode("utf-8")

            if not metrics_data.strip():
                logger.debug("No metrics data generated")
                return None

            return metrics_data

        except Exception as e:
            logger.debug("Failed to generate metrics: %s", e)
            return None

    def _cleanup_multiprocess_files(self) -> bool:
        """Clean up multiprocess DB files after successful forwarding."""
        try:
            import glob
            import os

            from ..config import config

            # Check if cleanup is enabled
            if not config.cleanup_db_files:
                logger.debug("DB file cleanup disabled via config")
                return True

            multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
            if not multiproc_dir or not os.path.exists(multiproc_dir):
                logger.debug("No multiprocess directory to clean up")
                return True

            # Find all .db files in the multiprocess directory
            db_files = glob.glob(os.path.join(multiproc_dir, "*.db"))

            if not db_files:
                logger.debug("No DB files to clean up")
                return True

            # Remove all DB files
            cleaned_count = 0
            for db_file in db_files:
                try:
                    os.remove(db_file)
                    cleaned_count += 1
                    logger.debug("Removed DB file: %s", os.path.basename(db_file))
                except OSError as e:
                    logger.warning("Failed to remove DB file %s: %s", db_file, e)

            logger.info("Cleaned up %d multiprocess DB files", cleaned_count)
            return True

        except Exception as e:
            logger.error("Failed to cleanup multiprocess files: %s", e)
            return False

    def _forward_loop(self):
        """Main forwarding loop."""
        logger.info("%s forwarder thread started", self.name)

        while not self._stop_event.is_set():
            try:
                # Generate metrics
                metrics_data = self._generate_metrics()
                if metrics_data:
                    # Forward to backend
                    success = self._forward_metrics(metrics_data)
                    if success:
                        logger.debug(
                            "%s: Forwarded %d bytes", self.name, len(metrics_data)
                        )

                        # Clean up multiprocess DB files after successful forward
                        cleanup_success = self._cleanup_multiprocess_files()
                        if not cleanup_success:
                            logger.warning("%s: Failed to cleanup DB files", self.name)
                    else:
                        logger.warning("%s: Failed to forward metrics", self.name)

            except Exception as e:
                logger.error("%s: Error in forward loop: %s", self.name, e)

            # Wait for next interval or stop signal
            if self._stop_event.wait(self.forward_interval):
                break

        logger.info("%s forwarder thread stopped", self.name)

    def start(self) -> bool:
        """Start the forwarder. Returns True if successful."""
        if self._running:
            logger.warning("%s forwarder is already running", self.name)
            return False

        # Connect to backend
        if not self._connect():
            logger.error("%s: Failed to connect to backend", self.name)
            return False

        # Start thread
        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(
            target=self._forward_loop, name=f"{self.name}Forwarder", daemon=True
        )
        self._thread.start()

        logger.info("%s forwarder started", self.name)
        return True

    def stop(self):
        """Stop the forwarder."""
        if not self._running:
            return

        logger.info("Stopping %s forwarder...", self.name)
        self._stop_event.set()
        self._running = False

        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                logger.warning("%s thread did not stop gracefully", self.name)

        # Disconnect from backend
        try:
            self._disconnect()
        except Exception as e:
            logger.warning("%s: Error during disconnect: %s", self.name, e)

    def is_running(self) -> bool:
        """Check if forwarder is running."""
        return self._running and self._thread and self._thread.is_alive()

    def get_status(self) -> Dict[str, Any]:
        """Get forwarder status."""
        return {
            "name": self.name,
            "running": self.is_running(),
            "forward_interval": self.forward_interval,
            "thread_alive": self._thread.is_alive() if self._thread else False,
        }

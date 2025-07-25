"""Forwarder manager for handling multiple forwarders."""

import logging

from typing import Dict, List, Optional, Type

from .base import BaseForwarder
from .redis import RedisForwarder


logger = logging.getLogger(__name__)


class ForwarderManager:
    """Manages multiple metric forwarders."""

    # Registry of available forwarder types
    FORWARDER_TYPES: Dict[str, Type[BaseForwarder]] = {
        "redis": RedisForwarder,
    }

    def __init__(self):
        """Initialize forwarder manager."""
        self._forwarders: Dict[str, BaseForwarder] = {}
        logger.info("ForwarderManager initialized")

    def add_forwarder(self, name: str, forwarder: BaseForwarder) -> bool:
        """Add a forwarder instance."""
        if name in self._forwarders:
            logger.warning("Forwarder '%s' already exists, stopping existing one", name)
            self.stop_forwarder(name)

        self._forwarders[name] = forwarder
        logger.info("Added forwarder: %s (%s)", name, forwarder.__class__.__name__)
        return True

    def create_forwarder(self, forwarder_type: str, name: str, **kwargs) -> bool:
        """Create and add a forwarder by type."""
        if forwarder_type not in self.FORWARDER_TYPES:
            logger.error(
                "Unknown forwarder type: %s. Available: %s",
                forwarder_type,
                list(self.FORWARDER_TYPES.keys()),
            )
            return False

        try:
            forwarder_class = self.FORWARDER_TYPES[forwarder_type]
            forwarder = forwarder_class(**kwargs)
            return self.add_forwarder(name, forwarder)
        except Exception as e:
            logger.error("Failed to create %s forwarder: %s", forwarder_type, e)
            return False

    def start_forwarder(self, name: str) -> bool:
        """Start a specific forwarder."""
        if name not in self._forwarders:
            logger.error("Forwarder '%s' not found", name)
            return False

        return self._forwarders[name].start()

    def stop_forwarder(self, name: str) -> bool:
        """Stop a specific forwarder."""
        if name not in self._forwarders:
            logger.warning("Forwarder '%s' not found", name)
            return False

        self._forwarders[name].stop()
        return True

    def remove_forwarder(self, name: str) -> bool:
        """Remove a forwarder (stops it first)."""
        if name not in self._forwarders:
            logger.warning("Forwarder '%s' not found", name)
            return False

        self.stop_forwarder(name)
        del self._forwarders[name]
        logger.info("Removed forwarder: %s", name)
        return True

    def start_all(self) -> bool:
        """Start all forwarders."""
        success = True
        for name in self._forwarders:
            if not self.start_forwarder(name):
                success = False
        return success

    def stop_all(self):
        """Stop all forwarders."""
        for name in list(self._forwarders.keys()):
            self.stop_forwarder(name)

    def get_forwarder(self, name: str) -> Optional[BaseForwarder]:
        """Get a forwarder by name."""
        return self._forwarders.get(name)

    def list_forwarders(self) -> List[str]:
        """List all forwarder names."""
        return list(self._forwarders.keys())

    def get_status(self) -> Dict[str, dict]:
        """Get status of all forwarders."""
        return {
            name: forwarder.get_status() for name, forwarder in self._forwarders.items()
        }

    def get_running_forwarders(self) -> List[str]:
        """Get list of currently running forwarder names."""
        return [
            name
            for name, forwarder in self._forwarders.items()
            if forwarder.is_running()
        ]

    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available forwarder types."""
        return list(cls.FORWARDER_TYPES.keys())


# Global manager instance
_global_manager: Optional[ForwarderManager] = None


def get_forwarder_manager() -> ForwarderManager:
    """Get or create global forwarder manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = ForwarderManager()
    return _global_manager


def create_redis_forwarder(name: str = "redis", **kwargs) -> bool:
    """Convenience function to create Redis forwarder."""
    manager = get_forwarder_manager()
    return manager.create_forwarder("redis", name, **kwargs)

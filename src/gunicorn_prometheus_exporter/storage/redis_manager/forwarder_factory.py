"""Forwarder Factory for creating and managing metric forwarders.

This module provides a clean factory pattern for creating forwarders with proper
dependency injection and testability.
"""

import logging

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, Type


logger = logging.getLogger(__name__)


class ForwarderProtocol(Protocol):
    """Protocol for forwarder interface."""

    def start(self) -> bool:
        """Start the forwarder."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop the forwarder."""
        raise NotImplementedError

    def is_running(self) -> bool:
        """Check if forwarder is running."""
        raise NotImplementedError

    def get_status(self) -> Dict[str, Any]:
        """Get forwarder status."""
        raise NotImplementedError


@dataclass
class ForwarderConfig:
    """Configuration for forwarder creation."""

    name: str
    forwarder_type: str
    enabled: bool = True
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


class ForwarderFactory:
    """Factory for creating forwarders with proper dependency injection."""

    def __init__(self):
        """Initialize forwarder factory."""
        self._forwarder_types: Dict[str, Type[ForwarderProtocol]] = {}
        self._register_default_types()

    def register_forwarder_type(
        self, name: str, forwarder_class: Type[ForwarderProtocol]
    ) -> None:
        """Register a new forwarder type.

        Args:
            name: Name of the forwarder type
            forwarder_class: Forwarder class to register
        """
        self._forwarder_types[name] = forwarder_class
        logger.debug("Registered forwarder type: %s", name)

    def create_forwarder(self, config: ForwarderConfig) -> Optional[ForwarderProtocol]:
        """Create a forwarder from configuration.

        Args:
            config: Forwarder configuration

        Returns:
            Forwarder instance or None if creation failed
        """
        if not config.enabled:
            logger.debug("Forwarder '%s' is disabled", config.name)
            return None

        if config.forwarder_type not in self._forwarder_types:
            logger.error(
                "Unknown forwarder type: %s. Available: %s",
                config.forwarder_type,
                list(self._forwarder_types.keys()),
            )
            return None

        try:
            forwarder_class = self._forwarder_types[config.forwarder_type]
            forwarder = forwarder_class(**config.config)
            logger.info(
                "Created forwarder: %s (%s)", config.name, config.forwarder_type
            )
            return forwarder

        except Exception as e:
            logger.error(
                "Failed to create %s forwarder '%s': %s",
                config.forwarder_type,
                config.name,
                e,
            )
            return None

    def get_available_types(self) -> list[str]:
        """Get list of available forwarder types."""
        return list(self._forwarder_types.keys())

    def _register_default_types(self) -> None:
        """Register default forwarder types."""
        try:
            from ..metrics_forwarder.redis_forwarder import RedisForwarder

            self.register_forwarder_type("redis", RedisForwarder)
        except ImportError:
            logger.warning("Redis forwarder not available")


class ForwarderManager:
    """Manages multiple metric forwarders with proper lifecycle management."""

    def __init__(self, factory: Optional[ForwarderFactory] = None):
        """Initialize forwarder manager.

        Args:
            factory: Forwarder factory instance (for testing)
        """
        self._factory = factory or ForwarderFactory()
        self._forwarders: Dict[str, ForwarderProtocol] = {}
        logger.info("ForwarderManager initialized")

    def add_forwarder(self, name: str, forwarder: ForwarderProtocol) -> bool:
        """Add a forwarder instance.

        Args:
            name: Name of the forwarder
            forwarder: Forwarder instance

        Returns:
            True if added successfully, False otherwise
        """
        if name in self._forwarders:
            logger.warning("Forwarder '%s' already exists, stopping existing one", name)
            self.stop_forwarder(name)

        self._forwarders[name] = forwarder
        logger.info("Added forwarder: %s (%s)", name, forwarder.__class__.__name__)
        return True

    def create_forwarder(self, config: ForwarderConfig) -> bool:
        """Create and add a forwarder from configuration.

        Args:
            config: Forwarder configuration

        Returns:
            True if created and added successfully, False otherwise
        """
        forwarder = self._factory.create_forwarder(config)
        if forwarder is None:
            return False

        return self.add_forwarder(config.name, forwarder)

    def start_forwarder(self, name: str) -> bool:
        """Start a specific forwarder.

        Args:
            name: Name of the forwarder

        Returns:
            True if started successfully, False otherwise
        """
        if name not in self._forwarders:
            logger.error("Forwarder '%s' not found", name)
            return False

        return self._forwarders[name].start()

    def stop_forwarder(self, name: str) -> bool:
        """Stop a specific forwarder.

        Args:
            name: Name of the forwarder

        Returns:
            True if stopped successfully, False otherwise
        """
        if name not in self._forwarders:
            logger.warning("Forwarder '%s' not found", name)
            return False

        self._forwarders[name].stop()
        return True

    def remove_forwarder(self, name: str) -> bool:
        """Remove a forwarder (stops it first).

        Args:
            name: Name of the forwarder

        Returns:
            True if removed successfully, False otherwise
        """
        if name not in self._forwarders:
            logger.warning("Forwarder '%s' not found", name)
            return False

        self.stop_forwarder(name)
        del self._forwarders[name]
        logger.info("Removed forwarder: %s", name)
        return True

    def start_all(self) -> bool:
        """Start all forwarders.

        Returns:
            True if all started successfully, False if any failed
        """
        success = True
        for name in self._forwarders:
            if not self.start_forwarder(name):
                success = False
        return success

    def stop_all(self) -> None:
        """Stop all forwarders."""
        for name in list(self._forwarders.keys()):
            self.stop_forwarder(name)

    def get_forwarder(self, name: str) -> Optional[ForwarderProtocol]:
        """Get a forwarder by name.

        Args:
            name: Name of the forwarder

        Returns:
            Forwarder instance or None if not found
        """
        return self._forwarders.get(name)

    def list_forwarders(self) -> list[str]:
        """List all forwarder names.

        Returns:
            List of forwarder names
        """
        return list(self._forwarders.keys())

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all forwarders.

        Returns:
            Dictionary mapping forwarder names to their status
        """
        return {
            name: forwarder.get_status() for name, forwarder in self._forwarders.items()
        }

    def get_running_forwarders(self) -> list[str]:
        """Get list of currently running forwarder names.

        Returns:
            List of running forwarder names
        """
        return [
            name
            for name, forwarder in self._forwarders.items()
            if forwarder.is_running()
        ]

    def get_available_types(self) -> list[str]:
        """Get list of available forwarder types.

        Returns:
            List of available forwarder type names
        """
        return self._factory.get_available_types()


# Global manager instance
_global_manager: Optional[ForwarderManager] = None


def get_forwarder_manager() -> ForwarderManager:
    """Get or create global forwarder manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = ForwarderManager()
    return _global_manager


def create_redis_forwarder(name: str = "redis", **kwargs) -> bool:
    """Convenience function to create Redis forwarder.

    Args:
        name: Name of the forwarder
        **kwargs: Additional configuration for Redis forwarder

    Returns:
        True if created successfully, False otherwise
    """
    manager = get_forwarder_manager()
    config = ForwarderConfig(name=name, forwarder_type="redis", config=kwargs)
    return manager.create_forwarder(config)

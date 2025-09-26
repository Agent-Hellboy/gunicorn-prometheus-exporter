"""Redis Storage Manager for Gunicorn Prometheus Exporter.

This module provides a clean, testable interface for managing Redis-based metrics
storage. Uses dependency injection and proper separation of concerns.
"""

import logging
import os

from typing import Optional, Protocol

from ...config import get_config
from ..core import get_redis_value_class
from ..core.client import RedisClientProtocol, _should_set_ttl


# Conditional Redis import - only import when needed
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


logger = logging.getLogger(__name__)


class PrometheusValueClassProtocol(Protocol):
    """Protocol for Prometheus value class interface."""

    def __call__(self, *args, **kwargs):
        """Value class constructor."""
        raise NotImplementedError


class FactoryUtilsMixin:
    """Mixin class for factory utilities."""

    def create_redis_value_class(self, redis_client, redis_key_prefix=None):
        """Create a RedisValue class configured with Redis client.

        Args:
            redis_client: Redis client instance
            redis_key_prefix: Prefix for Redis keys (defaults to \
                get_config().redis_key_prefix)

        Returns:
            Configured RedisValue class
        """
        if redis_key_prefix is None:
            redis_key_prefix = get_config().redis_key_prefix
        return get_redis_value_class(redis_client, redis_key_prefix)

    def create_storage_manager(
        self, redis_client_factory=None, value_class_factory=None
    ):
        """Create a new Redis storage manager.

        Args:
            redis_client_factory: Factory function for Redis client
            value_class_factory: Factory function for value class

        Returns:
            New RedisStorageManager instance
        """
        return RedisStorageManager(redis_client_factory, value_class_factory)


class RedisStorageManager:
    """Manages Redis-based metrics storage with proper lifecycle management."""

    def __init__(self, redis_client_factory=None, value_class_factory=None):
        """Initialize Redis storage manager.

        Args:
            redis_client_factory: Factory function to create Redis client (for testing)
            value_class_factory: Factory function to create value class (for testing)
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis is not available. Install redis package to use "
                "RedisStorageManager."
            )

        self._redis_client: Optional[RedisClientProtocol] = None
        self._redis_value_class: Optional[PrometheusValueClassProtocol] = None
        self._original_value_class: Optional[PrometheusValueClassProtocol] = None
        self._is_initialized = False

        # Dependency injection for testing
        self._redis_client_factory = redis_client_factory or self._create_redis_client
        self._value_class_factory = value_class_factory or self._create_value_class

    def setup(self) -> bool:
        """Set up Redis-based metrics storage.

        Returns:
            bool: True if setup was successful, False otherwise.
        """
        if not get_config().redis_enabled:
            logger.debug("Redis is not enabled, skipping Redis metrics setup")
            return False

        if self._is_initialized:
            logger.warning("Redis storage already initialized")
            return True

        try:
            # Create Redis client
            self._redis_client = self._redis_client_factory()

            # Test connection
            self._redis_client.ping()
            logger.debug(
                "Connected to Redis at %s:%s (TTL: %s)",
                get_config().redis_host,
                get_config().redis_port,
                "disabled"
                if not _should_set_ttl()
                else f"{get_config().redis_ttl_seconds}s",
            )

            # Create value class
            prefix = get_config().redis_key_prefix.rstrip(":")
            self._redis_value_class = self._value_class_factory(
                self._redis_client, prefix
            )

            # Replace Prometheus value class
            self._replace_prometheus_value_class()

            self._is_initialized = True
            logger.debug("Redis metrics storage enabled - using Redis instead of files")
            return True

        except Exception as e:
            logger.error("Failed to setup Redis metrics: %s", e)
            self._cleanup()
            return False

    def teardown(self) -> None:
        """Teardown Redis-based metrics storage and restore original behavior."""
        if not self._is_initialized:
            return

        # Restore original value class
        self._restore_prometheus_value_class()

        # Close Redis connection
        self._cleanup()

        self._is_initialized = False
        logger.debug("Redis storage teardown completed")

    def is_enabled(self) -> bool:
        """Check if Redis storage is enabled and working."""
        return self._is_initialized and self._redis_client is not None

    def get_client(self) -> Optional[RedisClientProtocol]:
        """Get the Redis client instance."""
        return self._redis_client

    def cleanup_keys(self) -> None:
        """Clean up Redis keys for dead processes."""
        if not self._redis_client:
            return

        try:
            from ..core import mark_process_dead_redis

            pid = os.getpid()
            mark_process_dead_redis(
                pid, self._redis_client, get_config().redis_key_prefix.rstrip(":")
            )
            logger.debug("Cleaned up Redis keys for process %d", pid)

        except Exception as e:
            logger.warning("Failed to cleanup Redis keys: %s", e)

    def get_collector(self):
        """Get Redis-based collector for metrics collection."""
        if not self.is_enabled():
            return None

        try:
            from ...metrics import get_shared_registry
            from ..core import RedisMultiProcessCollector

            registry = get_shared_registry()
            return RedisMultiProcessCollector(
                registry, self._redis_client, get_config().redis_key_prefix.rstrip(":")
            )

        except Exception as e:
            logger.error("Failed to create Redis collector: %s", e)
            return None

    def _create_redis_client(self) -> RedisClientProtocol:
        """Create Redis client from configuration."""
        config = get_config()
        redis_url = f"redis://{config.redis_host}:{config.redis_port}/{config.redis_db}"
        if get_config().redis_password:
            redis_url = (
                f"redis://:{get_config().redis_password}@{get_config().redis_host}:"
                f"{get_config().redis_port}/{get_config().redis_db}"
            )

        os.environ["PROMETHEUS_REDIS_URL"] = redis_url
        return redis.from_url(
            redis_url,
            decode_responses=False,
            socket_timeout=5.0,  # 5 second timeout for socket operations
            socket_connect_timeout=5.0,  # 5 second timeout for connection
            retry_on_timeout=True,  # Retry on timeout
            health_check_interval=30,  # Health check every 30 seconds
        )

    def _create_value_class(self, client: RedisClientProtocol, prefix: str):
        """Create Redis value class."""
        from ..core import get_redis_value_class

        return get_redis_value_class(client, prefix)

    def _replace_prometheus_value_class(self) -> None:
        """Replace Prometheus value class with Redis-backed one."""
        from prometheus_client import values

        self._original_value_class = values.ValueClass
        values.ValueClass = self._redis_value_class

    def _restore_prometheus_value_class(self) -> None:
        """Restore original Prometheus value class."""
        if self._original_value_class is not None:
            from prometheus_client import values

            values.ValueClass = self._original_value_class
            self._original_value_class = None
            logger.debug("Restored original Prometheus value class")

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._redis_client is not None:
            try:
                # Close Redis connection with timeout to avoid blocking
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError("Redis close operation timed out")

                # Set a 2-second timeout for Redis close operation
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(2)

                try:
                    self._redis_client.close()
                    logger.debug("Disconnected from Redis")
                except TimeoutError:
                    logger.warning(
                        "Redis close operation timed out, forcing disconnect"
                    )
                finally:
                    signal.alarm(0)  # Cancel the alarm
                    signal.signal(signal.SIGALRM, old_handler)  # Restore old handler

            except Exception as e:
                logger.warning("Error disconnecting from Redis: %s", e)
            finally:
                self._redis_client = None

        self._redis_value_class = None


# Global manager instance
_global_manager: Optional[RedisStorageManager] = None


def get_redis_storage_manager() -> RedisStorageManager:
    """Get or create global Redis storage manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = RedisStorageManager()
    return _global_manager


# Convenience functions for backward compatibility
def setup_redis_metrics() -> bool:
    """Set up Redis-based metrics storage."""
    manager = get_redis_storage_manager()
    return manager.setup()


def teardown_redis_metrics() -> None:
    """Teardown Redis-based metrics storage."""
    manager = get_redis_storage_manager()
    manager.teardown()


def is_redis_enabled() -> bool:
    """Check if Redis metrics are enabled and working."""
    manager = get_redis_storage_manager()
    return manager.is_enabled()


def get_redis_client():
    """Get the Redis client instance."""
    manager = get_redis_storage_manager()
    return manager.get_client()


def cleanup_redis_keys() -> None:
    """Clean up Redis keys for dead processes."""
    manager = get_redis_storage_manager()
    manager.cleanup_keys()


def get_redis_collector():
    """Get Redis-based collector for metrics collection."""
    manager = get_redis_storage_manager()
    return manager.get_collector()

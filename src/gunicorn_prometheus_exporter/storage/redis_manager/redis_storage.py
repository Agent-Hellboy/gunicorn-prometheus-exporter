"""Redis integration for Gunicorn Prometheus Exporter.

This module provides Redis-based metrics storage using prometheus-redis-client
when Redis storage is enabled, replacing the file-based multiprocess storage.
"""

import logging
import os

from ...config import config


logger = logging.getLogger(__name__)

# Global Redis client and value class
_redis_client = None
_redis_value_class = None
_original_value_class = None


def setup_redis_metrics() -> bool:
    """Set up Redis-based metrics storage.

    Returns:
        bool: True if Redis setup was successful, False otherwise.
    """
    global _redis_client, _redis_value_class, _original_value_class

    if not config.redis_enabled:
        logger.debug("Redis is not enabled, skipping Redis metrics setup")
        return False

    try:
        # Import prometheus-redis-client from local copy
        import redis

        from .redis_storage_client import get_redis_value_class

        # Create Redis client
        redis_url = f"redis://{config.redis_host}:{config.redis_port}/{config.redis_db}"
        if config.redis_password:
            redis_url = (
                f"redis://:{config.redis_password}@{config.redis_host}:"
                f"{config.redis_port}/{config.redis_db}"
            )

        os.environ["PROMETHEUS_REDIS_URL"] = redis_url
        _redis_client = redis.from_url(redis_url, decode_responses=False)

        # Test Redis connection
        _redis_client.ping()
        logger.info("Connected to Redis at %s:%s", config.redis_host, config.redis_port)

        # Get Redis value class
        _redis_value_class = get_redis_value_class(_redis_client, "gunicorn")

        # Store original value class and replace it
        from prometheus_client import values

        _original_value_class = values.ValueClass
        values.ValueClass = _redis_value_class

        logger.info("Redis metrics storage enabled - using Redis instead of files")
        return True

    except ImportError:
        logger.error(
            "prometheus-redis-client not installed. Install with: "
            "pip install prometheus-redis-client"
        )
        return False
    except Exception as e:
        logger.error("Failed to setup Redis metrics: %s", e)
        return False


def teardown_redis_metrics():
    """Teardown Redis-based metrics storage and restore original behavior."""
    global _redis_client, _redis_value_class, _original_value_class

    if _original_value_class is not None:
        from prometheus_client import values

        values.ValueClass = _original_value_class
        _original_value_class = None
        logger.info("Restored original Prometheus value class")

    if _redis_client is not None:
        try:
            _redis_client.close()
            _redis_client = None
            logger.info("Disconnected from Redis")
        except Exception as e:
            logger.warning("Error disconnecting from Redis: %s", e)

    _redis_value_class = None


def is_redis_enabled() -> bool:
    """Check if Redis metrics are enabled and working."""
    return _redis_client is not None and _redis_value_class is not None


def get_redis_client():
    """Get the Redis client instance."""
    return _redis_client


def cleanup_redis_keys():
    """Clean up Redis keys for dead processes."""
    if not _redis_client:
        return

    try:
        from .redis_storage_client import mark_process_dead_redis

        # Clean up keys for current process
        pid = os.getpid()
        mark_process_dead_redis(pid, _redis_client, "gunicorn")
        logger.debug("Cleaned up Redis keys for process %d", pid)

    except Exception as e:
        logger.warning("Failed to cleanup Redis keys: %s", e)


def get_redis_collector():
    """Get Redis-based collector for metrics collection."""
    if not is_redis_enabled():
        return None

    try:
        from .metrics import get_shared_registry
        from .redis_storage_client import RedisMultiProcessCollector

        registry = get_shared_registry()
        return RedisMultiProcessCollector(registry, _redis_client, "gunicorn")

    except Exception as e:
        logger.error("Failed to create Redis collector: %s", e)
        return None

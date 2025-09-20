"""Redis Storage Package for Gunicorn Prometheus Exporter.

This package provides Redis-based storage capabilities for Prometheus metrics.
It includes improved design patterns for better testability and maintainability.

Modules:
- manager: Main Redis storage manager with lifecycle management
"""

from .manager import (
    FactoryUtilsMixin,
    RedisStorageManager,
    cleanup_redis_keys,
    get_redis_client,
    get_redis_collector,
    get_redis_storage_manager,
    is_redis_enabled,
    setup_redis_metrics,
    teardown_redis_metrics,
)


__all__ = [
    # Main classes
    "RedisStorageManager",
    "FactoryUtilsMixin",
    # Manager functions
    "get_redis_storage_manager",
    # Convenience functions
    "setup_redis_metrics",
    "teardown_redis_metrics",
    "is_redis_enabled",
    "get_redis_client",
    "cleanup_redis_keys",
    "get_redis_collector",
]

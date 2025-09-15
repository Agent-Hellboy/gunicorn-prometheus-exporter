"""Redis Storage Package for Gunicorn Prometheus Exporter.

This package provides Redis-based storage and forwarding capabilities for
Prometheus metrics. It includes improved design patterns for better testability
and maintainability.

Modules:
- redis_storage_manager: Main Redis storage manager with lifecycle management
- redis_storage_client: Redis client and storage operations
- redis_storage: Legacy compatibility module
- forwarder_factory: Factory pattern for creating and managing forwarders
"""

from ..redis_backend.redis_storage_client import (
    RedisStorageClient,
    RedisStorageDict,
    RedisValueClass,
    get_redis_value_class,
    mark_process_dead_redis,
)
from .forwarder_factory import (
    ForwarderConfig,
    ForwarderFactory,
    ForwarderManager,
    create_redis_forwarder,
    get_forwarder_manager,
)

# Legacy compatibility imports
from .redis_storage import (
    cleanup_redis_keys as legacy_cleanup_redis_keys,
    get_redis_client as legacy_get_redis_client,
    get_redis_collector as legacy_get_redis_collector,
    is_redis_enabled as legacy_is_redis_enabled,
    setup_redis_metrics as legacy_setup_redis_metrics,
    teardown_redis_metrics as legacy_teardown_redis_metrics,
)
from .redis_storage_manager import (
    RedisStorageManager,
    cleanup_redis_keys,
    get_redis_client,
    get_redis_collector,
    get_redis_storage_manager,
    is_redis_enabled,
    setup_redis_metrics,
    teardown_redis_metrics,
)


__version__ = "0.1.0"
__all__ = [
    # Main classes
    "RedisStorageManager",
    "ForwarderFactory",
    "ForwarderManager",
    "ForwarderConfig",
    "RedisStorageClient",
    "RedisStorageDict",
    "RedisValueClass",
    # Manager functions
    "get_redis_storage_manager",
    "get_forwarder_manager",
    # Convenience functions
    "setup_redis_metrics",
    "teardown_redis_metrics",
    "is_redis_enabled",
    "get_redis_client",
    "cleanup_redis_keys",
    "get_redis_collector",
    "create_redis_forwarder",
    # Client functions
    "get_redis_value_class",
    "mark_process_dead_redis",
    # Legacy compatibility
    "legacy_setup_redis_metrics",
    "legacy_teardown_redis_metrics",
    "legacy_is_redis_enabled",
    "legacy_get_redis_client",
    "legacy_cleanup_redis_keys",
    "legacy_get_redis_collector",
]

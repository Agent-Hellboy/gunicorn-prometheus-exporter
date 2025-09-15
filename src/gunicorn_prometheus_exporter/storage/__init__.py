"""Storage Package for Gunicorn Prometheus Exporter.

This package provides all storage-related functionality including Redis management,
metrics forwarding, and backend storage operations.

Package Structure:
- redis_manager: Redis storage management and lifecycle
- redis_backend: Low-level Redis operations and storage
- metrics_forwarder: Metrics forwarding to external systems

Design Patterns:
- Manager Pattern: Centralized management of storage systems
- Factory Pattern: Creation of forwarders and storage clients
- Protocol Pattern: Type-safe interfaces
- Dependency Injection: Testable and maintainable code
"""

from .metrics_forwarder import (
    BaseForwarder,
    ForwarderManager as LegacyForwarderManager,
    RedisForwarder,
    get_forwarder_manager as get_legacy_forwarder_manager,
)
from .redis_backend import (
    RedisStorageClient,
    RedisStorageDict,
    RedisValueClass,
    get_redis_value_class,
    mark_process_dead_redis,
)
from .redis_manager import (
    ForwarderConfig,
    ForwarderFactory,
    ForwarderManager,
    RedisStorageManager,
    cleanup_redis_keys,
    create_redis_forwarder,
    get_forwarder_manager,
    get_redis_client,
    get_redis_collector,
    get_redis_storage_manager,
    is_redis_enabled,
    setup_redis_metrics,
    teardown_redis_metrics,
)


__version__ = "0.1.0"
__all__ = [
    # Redis Manager
    "RedisStorageManager",
    "get_redis_storage_manager",
    "setup_redis_metrics",
    "teardown_redis_metrics",
    "is_redis_enabled",
    "get_redis_client",
    "cleanup_redis_keys",
    "get_redis_collector",
    # Forwarder Factory
    "ForwarderFactory",
    "ForwarderManager",
    "ForwarderConfig",
    "get_forwarder_manager",
    "create_redis_forwarder",
    # Redis Backend
    "RedisStorageClient",
    "RedisStorageDict",
    "RedisValueClass",
    "get_redis_value_class",
    "mark_process_dead_redis",
    # Metrics Forwarder
    "BaseForwarder",
    "RedisForwarder",
    "LegacyForwarderManager",
    "get_legacy_forwarder_manager",
]

"""Storage Package for Gunicorn Prometheus Exporter.

This package provides Redis-based storage functionality for Prometheus metrics,
replacing traditional file-based storage with Redis for better scalability and
storage-compute separation.

Package Structure:
- redis_manager: Redis storage management and lifecycle
- redis_backend: Low-level Redis operations and storage

Design Patterns:
- Manager Pattern: Centralized management of storage systems
- Protocol Pattern: Type-safe interfaces
- Dependency Injection: Testable and maintainable code
"""

from .redis_backend import (
    RedisStorageClient,
    RedisStorageDict,
    RedisValueClass,
    get_redis_value_class,
    mark_process_dead_redis,
)
from .redis_manager import (
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
    # Redis Manager
    "RedisStorageManager",
    "get_redis_storage_manager",
    "setup_redis_metrics",
    "teardown_redis_metrics",
    "is_redis_enabled",
    "get_redis_client",
    "cleanup_redis_keys",
    "get_redis_collector",
    # Redis Backend
    "RedisStorageClient",
    "RedisStorageDict",
    "RedisValueClass",
    "get_redis_value_class",
    "mark_process_dead_redis",
]

"""
Prometheus Redis Client - Redis-based metrics storage for Prometheus Python client.

This package provides Redis-based storage for Prometheus metrics in multi-process
environments, replacing the default file-based storage mechanism.
"""

from .client import (
    RedisStorageClient,
    RedisStorageDict,
    RedisValueClass,
)
from .dict import redis_key
from .values import (
    CleanupUtilsMixin,
    RedisValue,
    cleanup_process_keys_for_pid,
    get_redis_value_class,
    mark_process_dead_redis,
)


# Conditional import of Redis collector
try:
    from .collector import RedisMultiProcessCollector

    REDIS_COLLECTOR_AVAILABLE = True
except ImportError:
    RedisMultiProcessCollector = None
    REDIS_COLLECTOR_AVAILABLE = False


__all__ = [
    "redis_key",
    "RedisValue",
    "get_redis_value_class",
    "mark_process_dead_redis",
    "cleanup_process_keys_for_pid",
    "CleanupUtilsMixin",
    "RedisStorageClient",
    "RedisStorageDict",
    "RedisValueClass",
]

# Conditionally add Redis collector to __all__
if REDIS_COLLECTOR_AVAILABLE:
    __all__.append("RedisMultiProcessCollector")

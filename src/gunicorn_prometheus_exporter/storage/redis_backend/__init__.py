"""
Prometheus Redis Client - Redis-based metrics storage for Prometheus Python client.

This package provides Redis-based storage for Prometheus metrics in multi-process
environments, replacing the default file-based storage mechanism.
"""

from .redis_storage_client import (
    RedisStorageClient,
    RedisStorageDict,
    RedisValueClass,
)
from .storage_collector import RedisMultiProcessCollector
from .storage_dict import RedisDict, redis_key
from .storage_values import RedisValue, get_redis_value_class, mark_process_dead_redis


__version__ = "0.1.0"
__all__ = [
    "RedisDict",
    "redis_key",
    "RedisValue",
    "get_redis_value_class",
    "mark_process_dead_redis",
    "RedisMultiProcessCollector",
    "RedisStorageClient",
    "RedisStorageDict",
    "RedisValueClass",
]

"""Redis Storage Client for Prometheus metrics.

This module provides a clean, testable interface for Redis-based storage
with proper separation of concerns and dependency injection.
"""

import logging
import threading
import time

from typing import Dict, Iterable, Optional, Protocol, Tuple, Union

from ...config import config


logger = logging.getLogger(__name__)


class RedisClientProtocol(Protocol):
    """Protocol for Redis client interface."""

    def ping(self) -> bool:
        """Test Redis connection."""
        raise NotImplementedError

    def hget(self, name: Union[str, bytes], key: str) -> Optional[Union[bytes, str]]:
        """Get hash field value."""
        raise NotImplementedError

    def hset(
        self,
        name: Union[str, bytes],
        key: str = None,
        value: str = None,
        mapping: Dict[str, object] = None,
    ) -> int:
        """Set hash field value."""
        raise NotImplementedError

    def hgetall(
        self, name: Union[str, bytes]
    ) -> Dict[Union[bytes, str], Union[bytes, str]]:
        """Get all hash fields."""
        raise NotImplementedError

    def keys(self, pattern: str) -> list[bytes]:
        """Get keys matching pattern."""
        raise NotImplementedError

    def scan_iter(self, match: str) -> Iterable[bytes]:
        """Iterate keys matching pattern (non-blocking)."""
        raise NotImplementedError

    def delete(self, *keys: Union[bytes, str]) -> int:
        """Delete keys."""
        raise NotImplementedError


class StorageDictProtocol(Protocol):
    """Protocol for storage dictionary interface."""

    def read_value(self, key: str, metric_type: str = "counter") -> Tuple[float, float]:
        """Read value and timestamp."""
        raise NotImplementedError

    def write_value(
        self, key: str, value: float, timestamp: float, metric_type: str = "counter"
    ) -> None:
        """Write value and timestamp."""
        raise NotImplementedError


class RedisStorageDict:
    """Redis-backed dictionary for storing metric values with thread safety."""

    def __init__(self, redis_client: RedisClientProtocol, key_prefix: str = None):
        """Initialize Redis storage dictionary.

        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for Redis keys (defaults to config.redis_key_prefix)
        """
        self._redis = redis_client
        self._key_prefix = key_prefix or config.redis_key_prefix
        self._lock = threading.Lock()
        logger.debug("Initialized Redis storage dict with prefix: %s", key_prefix)

    def read_value(self, key: str, metric_type: str = "counter") -> Tuple[float, float]:
        """Read value and timestamp for a metric key.

        Args:
            key: Metric key
            metric_type: Type of metric (counter, gauge, histogram, summary)

        Returns:
            Tuple of (value, timestamp)
        """
        metric_key = self._get_metric_key(key, metric_type)

        with self._lock:
            # Get value and timestamp
            value_data = self._redis.hget(metric_key, "value")
            timestamp_data = self._redis.hget(metric_key, "timestamp")

            if value_data is None or timestamp_data is None:
                # Initialize with default values (without acquiring lock again)
                self._init_value_unlocked(key, metric_type)
                return 0.0, 0.0

            if isinstance(value_data, (bytes, bytearray)):
                value_data = value_data.decode("utf-8")
            if isinstance(timestamp_data, (bytes, bytearray)):
                timestamp_data = timestamp_data.decode("utf-8")
            return float(value_data), float(timestamp_data)

    def write_value(
        self, key: str, value: float, timestamp: float, metric_type: str = "counter"
    ) -> None:
        """Write value and timestamp for a metric key.

        Args:
            key: Metric key
            value: Metric value
            timestamp: Metric timestamp
            metric_type: Type of metric (counter, gauge, histogram, summary)
        """
        metric_key = self._get_metric_key(key, metric_type)

        with self._lock:
            # Store value and timestamp in Redis hash
            self._redis.hset(
                metric_key,
                mapping={
                    "value": value,
                    "timestamp": timestamp,
                    "updated_at": time.time(),
                },
            )

            # Set TTL if not disabled
            if not config.redis_ttl_disabled:
                self._redis.expire(metric_key, config.redis_ttl_seconds)

            # Store metadata separately for easier querying
            metadata_key = self._get_metadata_key(key, metric_type)
            self._redis.hset(
                metadata_key, mapping={"original_key": key, "created_at": time.time()}
            )

            # Set TTL for metadata key as well
            if not config.redis_ttl_disabled:
                self._redis.expire(metadata_key, config.redis_ttl_seconds)

    def _get_metric_key(self, key: str, metric_type: str = "counter") -> str:
        """Get Redis key for metric data."""
        import os

        pid = os.getpid()
        return f"{self._key_prefix}:{metric_type}:{pid}:metric:{key}"

    def _get_metadata_key(self, key: str, metric_type: str = "counter") -> str:
        """Get Redis key for metadata."""
        import os

        pid = os.getpid()
        return f"{self._key_prefix}:{metric_type}:{pid}:meta:{key}"

    def _init_value(self, key: str, metric_type: str = "counter") -> None:
        """Initialize a value with defaults."""
        with self._lock:
            self._init_value_unlocked(key, metric_type)

    def _init_value_unlocked(self, key: str, metric_type: str = "counter") -> None:
        """Initialize a value with defaults (assumes lock is already held)."""
        metric_key = self._get_metric_key(key, metric_type)

        # Store value and timestamp in Redis hash
        self._redis.hset(
            metric_key,
            mapping={"value": 0.0, "timestamp": 0.0, "updated_at": time.time()},
        )

        # Set TTL for metric key if not disabled
        if not config.redis_ttl_disabled:
            self._redis.expire(metric_key, config.redis_ttl_seconds)

        # Store metadata separately for easier querying
        metadata_key = self._get_metadata_key(key, metric_type)
        self._redis.hset(
            metadata_key, mapping={"original_key": key, "created_at": time.time()}
        )

        # Set TTL for metadata key as well
        if not config.redis_ttl_disabled:
            self._redis.expire(metadata_key, config.redis_ttl_seconds)

    def _extract_original_key(self, metadata):
        """Extract original key from metadata, handling both bytes and string."""
        original_raw = metadata.get(b"original_key") or metadata.get("original_key")
        if isinstance(original_raw, (bytes, bytearray)):
            return original_raw.decode("utf-8")
        return str(original_raw or "")

    def _extract_metric_values(self, metric_key):
        """Extract value and timestamp from metric key."""
        value_data = self._redis.hget(metric_key, "value")
        timestamp_data = self._redis.hget(metric_key, "timestamp")

        if value_data is None or timestamp_data is None:
            return None, None

        if isinstance(value_data, (bytes, bytearray)):
            value_data = value_data.decode("utf-8")
        if isinstance(timestamp_data, (bytes, bytearray)):
            timestamp_data = timestamp_data.decode("utf-8")

        return float(value_data), float(timestamp_data)

    def read_all_values(self) -> Iterable[Tuple[str, float, float]]:
        """Yield (key, value, timestamp) for all metrics."""
        pattern = f"{self._key_prefix}:*:*:metric:*"

        with self._lock:
            for metric_key in self._redis.scan_iter(match=pattern):
                if isinstance(metric_key, (bytes, bytearray)):
                    metric_key = metric_key.decode("utf-8")

                # Get metadata and original key
                metadata_key = metric_key.replace(":metric:", ":meta:", 1)
                metadata = self._redis.hgetall(metadata_key)
                if not metadata:
                    continue

                original_key = self._extract_original_key(metadata)
                if not original_key:
                    continue

                # Get value and timestamp
                value, timestamp = self._extract_metric_values(metric_key)
                if value is not None and timestamp is not None:
                    yield original_key, value, timestamp

    @staticmethod
    def read_all_values_from_redis(redis_client, key_prefix: str = None):
        """Static method to read all values from Redis, similar to MmapedDict."""
        if key_prefix is None:
            key_prefix = config.redis_key_prefix
        redis_dict = RedisStorageDict(redis_client, key_prefix)
        return redis_dict.read_all_values()

    def close(self):
        """Close Redis connection if needed."""
        # Redis client is typically managed externally


class RedisValueClass:
    """Redis-backed value class for Prometheus metrics."""

    def __init__(self, redis_client: RedisClientProtocol, key_prefix: str = None):
        """Initialize Redis value class.

        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for Redis keys (defaults to config.redis_key_prefix)
        """
        self._redis_client = redis_client
        self._key_prefix = key_prefix or config.redis_key_prefix
        logger.debug("Initialized Redis value class with prefix: %s", key_prefix)

    def __call__(self, *args, **kwargs):
        """Create a RedisValue instance."""
        # Use dynamic import to avoid cyclic import
        import importlib

        values_module = importlib.import_module(".values", package=__package__)
        RedisValue = values_module.RedisValue
        kwargs.setdefault("redis_client", self._redis_client)
        kwargs.setdefault("redis_key_prefix", self._key_prefix)
        return RedisValue(*args, **kwargs)


class RedisStorageClient:
    """Main client for Redis-based storage operations."""

    def __init__(self, redis_client: RedisClientProtocol, key_prefix: str = None):
        """Initialize Redis storage client.

        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for Redis keys (defaults to config.redis_key_prefix)
        """
        self._redis_client = redis_client
        self._key_prefix = key_prefix or config.redis_key_prefix
        self._redis_dict = RedisStorageDict(redis_client, self._key_prefix)
        self._value_class = RedisValueClass(redis_client, self._key_prefix)
        logger.debug("Initialized Redis storage client with prefix: %s", key_prefix)

    def get_value_class(self):
        """Get the Redis value class."""
        return self._value_class

    def cleanup_process_keys(self, pid: int) -> None:
        """Clean up Redis keys for a dead process.

        Args:
            pid: Process ID to clean up
        """
        try:
            pattern = f"{self._key_prefix}:*:{pid}:*"
            # Use scan_iter with timeout to avoid blocking
            keys_to_delete = []
            try:
                # Limit scan to avoid blocking for too long
                for key in self._redis_client.scan_iter(match=pattern, count=100):
                    keys_to_delete.append(key)
                    # Limit to 1000 keys to avoid blocking
                    if len(keys_to_delete) >= 1000:
                        break
            except Exception as scan_error:
                logger.warning(
                    "Failed to scan Redis keys for process %d: %s", pid, scan_error
                )
                return

            if keys_to_delete:
                # Delete keys in batches to avoid blocking
                batch_size = 100
                for i in range(0, len(keys_to_delete), batch_size):
                    batch = keys_to_delete[i : i + batch_size]
                    try:
                        self._redis_client.delete(*batch)
                    except Exception as delete_error:
                        logger.warning(
                            "Failed to delete Redis key batch for process %d: %s",
                            pid,
                            delete_error,
                        )
                        # Continue with next batch even if this one fails

                logger.debug(
                    "Cleaned up %d Redis keys for process %d", len(keys_to_delete), pid
                )

        except Exception as e:
            logger.warning("Failed to cleanup Redis keys for process %d: %s", pid, e)

    def get_client(self) -> RedisClientProtocol:
        """Get the Redis client."""
        return self._redis_client

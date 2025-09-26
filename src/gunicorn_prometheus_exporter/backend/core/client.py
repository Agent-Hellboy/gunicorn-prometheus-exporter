"""Redis Storage Client for Prometheus metrics.

This module provides a clean, testable interface for Redis-based storage
with proper separation of concerns and dependency injection.
"""

import hashlib
import logging
import threading
import time

from typing import Dict, Iterable, Optional, Protocol, Tuple, Union

from ...config import get_config


logger = logging.getLogger(__name__)


def _safe_decode_bytes(data: Union[bytes, bytearray, str, None]) -> str:
    """Safely decode bytes/bytearray to string, handling None values.

    Args:
        data: Data that might be bytes, bytearray, string, or None

    Returns:
        Decoded string or empty string if None
    """
    if data is None:
        return ""
    if isinstance(data, (bytes, bytearray)):
        return data.decode("utf-8")
    return str(data)


def _safe_parse_float(
    data: Union[bytes, bytearray, str, None], default: float = 0.0
) -> float:
    """Safely parse bytes/string to float with error handling.

    Args:
        data: Data that might be bytes, bytearray, string, or None
        default: Default value to return if parsing fails

    Returns:
        Parsed float value or default if parsing fails
    """
    if data is None:
        return default

    try:
        str_data = _safe_decode_bytes(data)
        return float(str_data)
    except (ValueError, TypeError) as e:
        logger.warning("Failed to parse float from %r: %s", data, e)
        return default


def _should_set_ttl() -> bool:
    """Check if TTL should be set for Redis keys.

    Returns:
        True if TTL should be set (TTL is not disabled and seconds > 0)
    """
    return not get_config().redis_ttl_disabled and get_config().redis_ttl_seconds > 0


def _safe_extract_original_key(metadata: Dict) -> str:
    """Safely extract original key from metadata, handling both bytes and string keys.

    Args:
        metadata: Dictionary that might have bytes or string keys

    Returns:
        Extracted original key as string
    """
    original_raw = metadata.get(b"original_key") or metadata.get("original_key")
    return _safe_decode_bytes(original_raw)


class RedisClientProtocol(Protocol):
    """Protocol for Redis client interface."""

    def ping(self) -> bool:
        """Test Redis connection."""
        raise NotImplementedError

    def expire(self, name: Union[str, bytes], time: int) -> bool:
        """Set expiration time for a key in seconds."""
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

    def hsetnx(self, name: Union[str, bytes], key: str, value: str) -> bool:
        """Set hash field value only if field does not exist."""
        raise NotImplementedError

    def hgetall(
        self, name: Union[str, bytes]
    ) -> Dict[Union[bytes, str], Union[bytes, str]]:
        """Get all hash fields."""
        raise NotImplementedError

    def keys(self, pattern: str) -> list[bytes]:
        """Get keys matching pattern."""
        raise NotImplementedError

    def scan_iter(
        self, match: Union[str, bytes] = None, count: Optional[int] = None
    ) -> Iterable[bytes]:
        """Iterate keys matching pattern (non-blocking)."""
        raise NotImplementedError

    def delete(self, *keys: Union[bytes, str]) -> int:
        """Delete keys."""
        raise NotImplementedError

    def time(self) -> Tuple[int, int]:
        """Get Redis server time as (seconds, microseconds)."""
        raise NotImplementedError


class StorageDictProtocol(Protocol):
    """Protocol for storage dictionary interface."""

    def read_value(
        self, key: str, metric_type: str = "counter", multiprocess_mode: str = ""
    ) -> Tuple[float, float]:
        """Read value and timestamp."""
        raise NotImplementedError

    def write_value(
        self,
        key: str,
        value: float,
        timestamp: float,
        metric_type: str = "counter",
        multiprocess_mode: str = "",
    ) -> None:
        """Write value and timestamp."""
        raise NotImplementedError


class RedisStorageDict:
    """Redis-backed dictionary for storing metric values with thread safety."""

    def __init__(self, redis_client: RedisClientProtocol, key_prefix: str = None):
        """Initialize Redis storage dictionary.

        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for Redis keys
                (defaults to get_config().redis_key_prefix)
        """
        self._redis = redis_client
        self._key_prefix = key_prefix or get_config().redis_key_prefix
        self._lock = threading.Lock()
        logger.debug("Initialized Redis storage dict with prefix: %s", key_prefix)

    def _redis_now(self) -> float:
        """Get current timestamp using Redis server time for coherence.

        Falls back to local time if Redis time is not available.

        Returns:
            Current timestamp as float (seconds since epoch)
        """
        try:
            sec, usec = self._redis.time()  # returns (seconds, microseconds)
            return sec + usec / 1_000_000.0
        except Exception as e:
            logger.debug("Failed to get Redis time, falling back to local time: %s", e)
            return time.time()

    def _get_multiprocess_mode_from_metadata(self, key: str, metric_type: str) -> str:
        """Get multiprocess_mode from metadata if available."""
        try:
            # Try to get metadata key with current metric_type first
            metadata_key = self._get_metadata_key(key, metric_type)
            metadata = self._redis.hgetall(metadata_key)
            if metadata:
                mode = metadata.get(b"multiprocess_mode") or metadata.get(
                    "multiprocess_mode"
                )
                if mode:
                    return _safe_decode_bytes(mode)

            # If not found, try common gauge modes
            if metric_type == "gauge":
                for mode in ["all", "liveall", "live", "max", "min", "sum"]:
                    metadata_key = self._get_metadata_key(key, metric_type, mode)
                    metadata = self._redis.hgetall(metadata_key)
                    if metadata:
                        return mode
        except Exception:  # nosec B110 - Silently handle Redis lookup failures
            pass

        return ""  # Return empty string if not found

    def read_value(
        self, key: str, metric_type: str = "counter", multiprocess_mode: str = ""
    ) -> Tuple[float, float]:
        """Read value and timestamp for a metric key.

        Args:
            key: Metric key
            metric_type: Type of metric (counter, gauge, histogram, summary)
            multiprocess_mode: Multiprocess mode for gauge metrics

        Returns:
            Tuple of (value, timestamp)
        """
        # Use multiprocess_mode parameter if provided, otherwise try to get
        # from metadata
        if not multiprocess_mode:
            multiprocess_mode = self._get_multiprocess_mode_from_metadata(
                key, metric_type
            )
        metric_key = self._get_metric_key(key, metric_type, multiprocess_mode)

        with self._lock:
            # Get value and timestamp
            value_data = self._redis.hget(metric_key, "value")
            timestamp_data = self._redis.hget(metric_key, "timestamp")

            if value_data is None or timestamp_data is None:
                # Initialize with default values (without acquiring lock again)
                self._init_value_unlocked(key, metric_type)
                return 0.0, 0.0

            return _safe_parse_float(value_data), _safe_parse_float(timestamp_data)

    def write_value(
        self,
        key: str,
        value: float,
        timestamp: float,
        metric_type: str = "counter",
        multiprocess_mode: str = "",
    ) -> None:
        """Write value and timestamp for a metric key.

        Args:
            key: Metric key
            value: Metric value
            timestamp: Metric timestamp
            metric_type: Type of metric (counter, gauge, histogram, summary)
            multiprocess_mode: Multiprocess mode for gauge metrics
        """
        # Use multiprocess_mode parameter if provided, otherwise try to get
        # from metadata
        if not multiprocess_mode:
            multiprocess_mode = self._get_multiprocess_mode_from_metadata(
                key, metric_type
            )
        metric_key = self._get_metric_key(key, metric_type, multiprocess_mode)

        with self._lock:
            # Store value and timestamp in Redis hash
            self._redis.hset(
                metric_key,
                mapping={
                    "value": value,
                    "timestamp": timestamp,
                    "updated_at": self._redis_now(),
                },
            )

            # Set TTL if not disabled
            if _should_set_ttl():
                self._redis.expire(metric_key, get_config().redis_ttl_seconds)

            # Store metadata separately for easier querying
            metadata_key = self._get_metadata_key(key, metric_type, multiprocess_mode)
            # Set metadata only once - don't overwrite created_at on subsequent writes
            self._redis.hsetnx(metadata_key, "original_key", key)
            self._redis.hsetnx(metadata_key, "created_at", str(self._redis_now()))

            # Set TTL for metadata key as well
            if _should_set_ttl():
                self._redis.expire(metadata_key, get_config().redis_ttl_seconds)

    def _get_metric_key(
        self, key: str, metric_type: str = "counter", multiprocess_mode: str = ""
    ) -> str:
        """Get Redis key for metric data (hashed for stability)."""
        import os

        pid = os.getpid()
        key_hash = hashlib.md5(key.encode("utf-8"), usedforsecurity=False).hexdigest()

        # Include multiprocess mode in key structure for gauge metrics
        if metric_type == "gauge" and multiprocess_mode:
            type_with_mode = f"{metric_type}_{multiprocess_mode}"
        else:
            type_with_mode = metric_type

        return f"{self._key_prefix}:{type_with_mode}:{pid}:metric:{key_hash}"

    def _get_metadata_key(
        self, key: str, metric_type: str = "counter", multiprocess_mode: str = ""
    ) -> str:
        """Get Redis key for metadata (hashed for stability)."""
        import os

        pid = os.getpid()
        key_hash = hashlib.md5(key.encode("utf-8"), usedforsecurity=False).hexdigest()

        # Include multiprocess mode in key structure for gauge metrics
        if metric_type == "gauge" and multiprocess_mode:
            type_with_mode = f"{metric_type}_{multiprocess_mode}"
        else:
            type_with_mode = metric_type

        return f"{self._key_prefix}:{type_with_mode}:{pid}:meta:{key_hash}"

    def _init_value(self, key: str, metric_type: str = "counter") -> None:
        """Initialize a value with defaults."""
        with self._lock:
            self._init_value_unlocked(key, metric_type)

    def _init_value_unlocked(self, key: str, metric_type: str = "counter") -> None:
        """Initialize a value with defaults (assumes lock is already held)."""
        # Try to get multiprocess_mode from metadata
        multiprocess_mode = self._get_multiprocess_mode_from_metadata(key, metric_type)
        metric_key = self._get_metric_key(key, metric_type, multiprocess_mode)

        # Store value and timestamp in Redis hash
        self._redis.hset(
            metric_key,
            mapping={"value": 0.0, "timestamp": 0.0, "updated_at": self._redis_now()},
        )

        # Set TTL for metric key if not disabled
        if _should_set_ttl():
            self._redis.expire(metric_key, get_config().redis_ttl_seconds)

        # Store metadata separately for easier querying
        metadata_key = self._get_metadata_key(key, metric_type, multiprocess_mode)
        # Set metadata only once - don't overwrite created_at on subsequent writes
        self._redis.hsetnx(metadata_key, "original_key", key)
        self._redis.hsetnx(metadata_key, "created_at", str(self._redis_now()))

        # Set TTL for metadata key as well
        if _should_set_ttl():
            self._redis.expire(metadata_key, get_config().redis_ttl_seconds)

    def _extract_original_key(self, metadata):
        """Extract original key from metadata, handling both bytes and string."""
        return _safe_extract_original_key(metadata)

    def _extract_metric_values(self, metric_key):
        """Extract value and timestamp from metric key."""
        value_data = self._redis.hget(metric_key, "value")
        timestamp_data = self._redis.hget(metric_key, "timestamp")

        if value_data is None or timestamp_data is None:
            return None, None

        return _safe_parse_float(value_data), _safe_parse_float(timestamp_data)

    def read_all_values(self) -> Iterable[Tuple[str, float, float]]:
        """Yield (key, value, timestamp) for all metrics."""
        pattern = f"{self._key_prefix}:*:*:metric:*"

        for metric_key in self._redis.scan_iter(match=pattern, count=100):
            with self._lock:
                # Get the original key from metadata
                metadata_key = (
                    metric_key.replace(b":metric:", b":meta:", 1)
                    if isinstance(metric_key, (bytes, bytearray))
                    else metric_key.replace(":metric:", ":meta:", 1)
                )
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
            key_prefix = get_config().redis_key_prefix
        redis_dict = RedisStorageDict(redis_client, key_prefix)
        return redis_dict.read_all_values()

    def ensure_metadata(
        self, key: str, typ: str = "counter", multiprocess_mode: str = "all"
    ):
        """Ensure metadata exists for a metric key.

        Args:
            key: The metric key
            typ: Metric type (counter, gauge, histogram, summary)
            multiprocess_mode: Multiprocess mode (all, liveall, live, max, min, sum)
        """
        metadata_key = self._get_metadata_key(key, typ, multiprocess_mode)

        with self._lock:
            try:
                # Check if metadata already exists
                existing_metadata = self._redis.hgetall(metadata_key)
                if existing_metadata:
                    # Metadata already exists, no need to create
                    return

                # Create metadata if it doesn't exist
                metadata = {
                    "typ": typ,
                    "multiprocess_mode": multiprocess_mode,
                    "created_at": str(self._redis_now()),
                }

                self._redis.hset(metadata_key, mapping=metadata)

                # Set TTL if configured
                if _should_set_ttl():
                    self._redis.expire(metadata_key, get_config().redis_ttl_seconds)

                logger.debug(
                    "Created metadata for key %s: typ=%s, mode=%s",
                    key,
                    typ,
                    multiprocess_mode,
                )

            except Exception as e:
                logger.warning("Failed to ensure metadata for key %s: %s", key, e)

    def close(self):
        """Close Redis connection if needed."""
        # Redis client is typically managed externally


class RedisValueClass:
    """Redis-backed value class for Prometheus metrics."""

    def __init__(self, redis_client: RedisClientProtocol, key_prefix: str = None):
        """Initialize Redis value class.

        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for Redis keys
                (defaults to get_config().redis_key_prefix)
        """
        self._redis_client = redis_client
        self._key_prefix = key_prefix or get_config().redis_key_prefix
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
            key_prefix: Prefix for Redis keys
                (defaults to get_config().redis_key_prefix)
        """
        self._redis_client = redis_client
        self._key_prefix = key_prefix or get_config().redis_key_prefix
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
            deleted_count = 0
            batch_size = 100
            current_batch = []

            try:
                # Process keys in streaming fashion to avoid memory issues
                for key in self._redis_client.scan_iter(match=pattern, count=100):
                    current_batch.append(key)

                    # Delete when batch is full
                    if len(current_batch) >= batch_size:
                        try:
                            self._redis_client.delete(*current_batch)
                            deleted_count += len(current_batch)
                        except Exception as delete_error:
                            logger.warning(
                                "Failed to delete Redis key batch for process %d: %s",
                                pid,
                                delete_error,
                            )
                        current_batch = []

                        # Limit total cleanup to avoid blocking for too long
                        if deleted_count >= 1000:
                            logger.debug(
                                "Reached cleanup limit of 1000 keys for process %d", pid
                            )
                            break

            except Exception as scan_error:
                logger.warning(
                    "Failed to scan Redis keys for process %d: %s", pid, scan_error
                )
                return

            # Delete any remaining keys in the final batch
            if current_batch:
                try:
                    self._redis_client.delete(*current_batch)
                    deleted_count += len(current_batch)
                except Exception as delete_error:
                    logger.warning(
                        "Failed to delete final Redis key batch for process %d: %s",
                        pid,
                        delete_error,
                    )

            if deleted_count > 0:
                logger.debug(
                    "Cleaned up %d Redis keys for process %d", deleted_count, pid
                )

        except Exception as e:
            logger.warning("Failed to cleanup Redis keys for process %d: %s", pid, e)

    def get_client(self) -> RedisClientProtocol:
        """Get the Redis client."""
        return self._redis_client

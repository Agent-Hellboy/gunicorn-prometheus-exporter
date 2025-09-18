import hashlib
import json
import time

from threading import Lock
from typing import List, Tuple

from ...config import config


# Conditional Redis import - only import when needed
try:
    import redis  # pylint: disable=unused-import

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisDict:
    """A dict of doubles, backed by Redis.

    This replaces MmapedDict for storing metrics in Redis instead of files.
    Each metric is stored as a Redis hash with keys for value, timestamp, and metadata.
    """

    def __init__(self, redis_client, key_prefix: str = None):
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis is not available. Install redis package to use RedisDict."
            )

        self._redis = redis_client
        self._key_prefix = key_prefix or config.redis_key_prefix
        self._lock = Lock()

    def _get_metric_key(self, metric_key: str) -> str:
        """Convert internal metric key to Redis key."""
        key_hash = hashlib.sha256(metric_key.encode("utf-8")).hexdigest()
        return f"{self._key_prefix}:metric:{key_hash}"

    def _get_metadata_key(self, metric_key: str) -> str:
        """Get Redis key for metric metadata."""
        key_hash = hashlib.sha256(metric_key.encode("utf-8")).hexdigest()
        return f"{self._key_prefix}:meta:{key_hash}"

    def read_value(self, key: str) -> Tuple[float, float]:
        """Read value and timestamp for a metric key."""
        metric_key = self._get_metric_key(key)

        with self._lock:
            # Get value and timestamp
            value_data = self._redis.hget(metric_key, "value")
            timestamp_data = self._redis.hget(metric_key, "timestamp")

            if value_data is None or timestamp_data is None:
                # Initialize with default values (without acquiring lock again)
                self._init_value_unlocked(key)
                return 0.0, 0.0

            if isinstance(value_data, (bytes, bytearray)):
                value_data = value_data.decode("utf-8")
            if isinstance(timestamp_data, (bytes, bytearray)):
                timestamp_data = timestamp_data.decode("utf-8")
            return float(value_data), float(timestamp_data)

    def write_value(self, key: str, value: float, timestamp: float):
        """Write value and timestamp for a metric key."""
        metric_key = self._get_metric_key(key)

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

            # Store metadata separately for easier querying
            metadata_key = self._get_metadata_key(key)
            self._redis.hset(
                metadata_key, mapping={"original_key": key, "created_at": time.time()}
            )

    def _init_value(self, key: str):
        """Initialize a value with defaults."""
        with self._lock:
            self._init_value_unlocked(key)

    def _init_value_unlocked(self, key: str):
        """Initialize a value with defaults (assumes lock is already held)."""
        metric_key = self._get_metric_key(key)

        # Store value and timestamp in Redis hash
        self._redis.hset(
            metric_key,
            mapping={"value": 0.0, "timestamp": 0.0, "updated_at": time.time()},
        )

        # Store metadata separately for easier querying
        metadata_key = self._get_metadata_key(key)
        self._redis.hset(
            metadata_key, mapping={"original_key": key, "created_at": time.time()}
        )

    def read_all_values(self):
        """Yield (key, value, timestamp) for all metrics."""
        pattern = f"{self._key_prefix}:metric:*"

        with self._lock:
            for metric_key in self._redis.keys(pattern):
                # Get the original key from metadata
                metadata_key = metric_key.replace("metric:", "meta:")
                metadata = self._redis.hgetall(metadata_key)

                if not metadata:
                    continue

                original_key = metadata.get(b"original_key", b"").decode("utf-8")
                if not original_key:
                    continue

                # Get value and timestamp
                value_data = self._redis.hget(metric_key, "value")
                timestamp_data = self._redis.hget(metric_key, "timestamp")

                if value_data is not None and timestamp_data is not None:
                    yield original_key, float(value_data), float(timestamp_data)

    def close(self):
        """Close Redis connection if needed."""
        # Redis client is typically managed externally

    @staticmethod
    def read_all_values_from_redis(redis_client, key_prefix: str = None):
        """Static method to read all values from Redis, similar to MmapedDict."""
        if key_prefix is None:
            key_prefix = config.redis_key_prefix
        redis_dict = RedisDict(redis_client, key_prefix)
        return redis_dict.read_all_values()


def redis_key(
    metric_name: str,
    name: str,
    labelnames: List[str],
    labelvalues: List[str],
    help_text: str,
) -> str:
    """Format a key for use in Redis, similar to mmap_key."""
    # Ensure labels are in consistent order for identity
    labels = dict(zip(labelnames, labelvalues))
    return json.dumps([metric_name, name, labels, help_text], sort_keys=True)

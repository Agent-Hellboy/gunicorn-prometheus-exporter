import json
import time

from threading import Lock
from typing import List, Tuple

import redis


class RedisDict:
    """A dict of doubles, backed by Redis.

    This replaces MmapedDict for storing metrics in Redis instead of files.
    Each metric is stored as a Redis hash with keys for value, timestamp, and metadata.
    """

    def __init__(self, redis_client: redis.Redis, key_prefix: str = "prometheus"):
        self._redis = redis_client
        self._key_prefix = key_prefix
        self._lock = Lock()

    def _get_metric_key(self, metric_key: str) -> str:
        """Convert internal metric key to Redis key."""
        return f"{self._key_prefix}:metric:{hash(metric_key)}"

    def _get_metadata_key(self, metric_key: str) -> str:
        """Get Redis key for metric metadata."""
        return f"{self._key_prefix}:meta:{hash(metric_key)}"

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
    def read_all_values_from_redis(
        redis_client: redis.Redis, key_prefix: str = "prometheus"
    ):
        """Static method to read all values from Redis, similar to MmapedDict."""
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

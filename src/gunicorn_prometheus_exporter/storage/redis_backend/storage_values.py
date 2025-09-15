import os

import redis

from .storage_dict import RedisDict, redis_key


class RedisValue:
    """A float backed by Redis for multi-process mode.

    This replaces MmapedValue for storing metrics in Redis instead of files.
    """

    _multiprocess = True

    def __init__(
        self,
        typ,
        metric_name,
        name,
        labelnames,
        labelvalues,
        help_text,
        multiprocess_mode="",
        redis_client=None,
        redis_key_prefix="prometheus",
        **_kwargs,
    ):
        self._params = (
            typ,
            metric_name,
            name,
            labelnames,
            labelvalues,
            help_text,
            multiprocess_mode,
        )
        self._redis_client = redis_client or self._get_default_redis_client()
        self._redis_key_prefix = redis_key_prefix

        # Initialize Redis connection if not provided
        if self._redis_client is None:
            raise ValueError(
                "Redis client must be provided or PROMETHEUS_REDIS_URL must be set"
            )

        # Create RedisDict instance
        if typ == "gauge":
            file_prefix = typ + "_" + multiprocess_mode
        else:
            file_prefix = typ

        # Use process ID to create unique keys per process
        pid = os.getpid()
        self._redis_dict = RedisDict(
            self._redis_client, f"{self._redis_key_prefix}:{file_prefix}:{pid}"
        )

        self._key = redis_key(metric_name, name, labelnames, labelvalues, help_text)
        self._value, self._timestamp = self._redis_dict.read_value(self._key)

    def _get_default_redis_client(self):
        """Get default Redis client from environment variables."""
        redis_url = os.environ.get("PROMETHEUS_REDIS_URL")
        if redis_url:
            return redis.from_url(redis_url)

        # Try to connect to local Redis
        try:
            return redis.Redis(
                host="localhost", port=6379, db=0, decode_responses=False
            )
        except redis.ConnectionError:
            return None

    def inc(self, amount):
        """Increment the value by amount."""
        self._value += amount
        self._timestamp = 0.0
        self._redis_dict.write_value(self._key, self._value, self._timestamp)

    def set(self, value, timestamp=None):
        """Set the value and optional timestamp."""
        self._value = value
        self._timestamp = timestamp or 0.0
        self._redis_dict.write_value(self._key, self._value, self._timestamp)

    def set_exemplar(self, _exemplar):
        """Set exemplar (not implemented for Redis yet)."""
        # TODO: Implement exemplars for Redis mode
        return

    def get(self):
        """Get the current value."""
        return self._value

    def get_exemplar(self):
        """Get exemplar (not implemented for Redis yet)."""
        # TODO: Implement exemplars for Redis mode
        return None


def get_redis_value_class(redis_client=None, redis_key_prefix="prometheus"):
    """Returns a RedisValue class configured with Redis client."""

    class ConfiguredRedisValue(RedisValue):
        def __init__(
            self,
            typ,
            metric_name,
            name,
            labelnames,
            labelvalues,
            help_text,
            multiprocess_mode="",
            **kwargs,
        ):
            super().__init__(
                typ,
                metric_name,
                name,
                labelnames,
                labelvalues,
                help_text,
                multiprocess_mode,
                redis_client,
                redis_key_prefix,
                **kwargs,
            )

    return ConfiguredRedisValue


def mark_process_dead_redis(pid, redis_client=None, redis_key_prefix="prometheus"):
    """Do bookkeeping for when one process dies in a Redis multi-process setup."""
    if redis_client is None:
        redis_url = os.environ.get("PROMETHEUS_REDIS_URL")
        if redis_url:
            redis_client = redis.from_url(redis_url)
        else:
            redis_client = redis.Redis(host="localhost", port=6379, db=0)

    # Remove all keys for the dead process
    pattern = f"{redis_key_prefix}:*:*:{pid}"
    keys_to_delete = redis_client.keys(pattern)

    if keys_to_delete:
        redis_client.delete(*keys_to_delete)

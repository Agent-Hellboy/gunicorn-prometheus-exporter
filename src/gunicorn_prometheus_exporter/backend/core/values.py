from ...config import get_config
from .dict import redis_key


class RedisValue:
    """A float backed by Redis for multi-process mode.

    This replaces MmapedValue for storing metrics in Redis instead of files.
    """

    _multiprocess = True

    def __init__(
        self,
        typ=None,
        metric_name=None,
        name=None,
        labelnames=None,
        labelvalues=None,
        help_text=None,
        multiprocess_mode="",
        redis_client=None,
        redis_key_prefix=None,
        **_kwargs,
    ):
        """Initialize RedisValue with Redis client and key prefix.

        Args:
            typ: Metric type (counter, gauge, histogram, summary)
            metric_name: Name of the metric
            name: Sample name
            labelnames: Label names
            labelvalues: Label values
            help_text: Help text for the metric
            multiprocess_mode: Multiprocess mode for gauge metrics
            redis_client: Redis client instance
            redis_key_prefix: Prefix for Redis keys
        """
        if redis_client is None:
            raise ValueError("redis_client must be provided")

        # Create RedisStorageDict from client and prefix
        from .client import RedisStorageDict

        self._redis_dict = RedisStorageDict(
            redis_client, redis_key_prefix or get_config().redis_key_prefix
        )
        self._params = (
            typ,
            metric_name,
            name,
            labelnames,
            labelvalues,
            help_text,
            multiprocess_mode,
        )
        self._key = redis_key(metric_name, name, labelnames, labelvalues, help_text)
        # Ensure metadata is present for accurate merging later
        if hasattr(self._redis_dict, "ensure_metadata"):
            self._redis_dict.ensure_metadata(
                self._key,
                typ=typ or "counter",
                multiprocess_mode=multiprocess_mode or "all",
            )
        self._value, self._timestamp = self._redis_dict.read_value(
            self._key,
            self._params[0],
            self._params[6],  # Pass multiprocess_mode
        )

    def inc(self, amount=1):
        """Increment the value by amount."""
        self._value += amount
        self._timestamp = 0.0
        self._redis_dict.write_value(
            self._key,
            self._value,
            self._timestamp,
            self._params[0],
            self._params[6],  # Pass multiprocess_mode
        )

    def set(self, value, timestamp=None):
        """Set the value and optional timestamp."""
        import time

        self._value = value
        self._timestamp = time.time() if timestamp is None else float(timestamp)
        self._redis_dict.write_value(
            self._key,
            self._value,
            self._timestamp,
            self._params[0],
            self._params[6],  # Pass multiprocess_mode
        )

    def set_exemplar(self, _exemplar):
        """Set exemplar (not implemented for Redis yet)."""
        # TODO: Implement exemplars for Redis mode
        return

    def get(self):
        """Get the current value."""
        return self._value

    def get_timestamp(self):
        """Get the current timestamp."""
        return self._timestamp

    def get_exemplar(self):
        """Get exemplar (not implemented for Redis yet)."""
        # TODO: Implement exemplars for Redis mode
        return None


def get_redis_value_class(redis_client, redis_key_prefix=None):
    """Returns a RedisValue class configured with Redis client.

    Args:
        redis_client: Redis client instance
        redis_key_prefix: Prefix for Redis keys
            (defaults to get_config().redis_key_prefix)

    Returns:
        Configured RedisValue class
    """
    if redis_key_prefix is None:
        redis_key_prefix = get_config().redis_key_prefix

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
                typ=typ,
                metric_name=metric_name,
                name=name,
                labelnames=labelnames,
                labelvalues=labelvalues,
                help_text=help_text,
                multiprocess_mode=multiprocess_mode,
                redis_client=redis_client,
                redis_key_prefix=redis_key_prefix,
                **kwargs,
            )

    return ConfiguredRedisValue


def cleanup_process_keys_for_pid(
    pid: int, redis_client, redis_key_prefix: str = None
) -> None:
    """Clean up Redis keys for a specific process ID.

    Args:
        pid: Process ID to clean up
        redis_client: Redis client instance
        redis_key_prefix: Prefix for Redis keys
            (defaults to get_config().redis_key_prefix)
    """
    if redis_key_prefix is None:
        redis_key_prefix = get_config().redis_key_prefix
    from .client import RedisStorageClient

    storage_client = RedisStorageClient(redis_client, redis_key_prefix)
    storage_client.cleanup_process_keys(pid)


def mark_process_dead_redis(pid, redis_client, redis_key_prefix=None):
    """Do bookkeeping for when one process dies in a Redis multi-process setup.

    Args:
        pid: Process ID to clean up
        redis_client: Redis client instance
        redis_key_prefix: Prefix for Redis keys
            (defaults to get_config().redis_key_prefix)
    """
    if redis_key_prefix is None:
        redis_key_prefix = get_config().redis_key_prefix
    cleanup_process_keys_for_pid(pid, redis_client, redis_key_prefix)


class CleanupUtilsMixin:
    """Mixin class for cleanup utilities."""

    @staticmethod
    def cleanup_process_keys_for_pid(
        pid: int, redis_client, redis_key_prefix: str = None
    ) -> None:
        """Clean up Redis keys for a specific process ID.

        Args:
            pid: Process ID to clean up
            redis_client: Redis client instance
            redis_key_prefix: Prefix for Redis keys (defaults to config)
        """
        cleanup_process_keys_for_pid(pid, redis_client, redis_key_prefix)

    @staticmethod
    def mark_process_as_dead(
        pid: int, redis_client, redis_key_prefix: str = None
    ) -> None:
        """Mark a process as dead and clean up its keys.

        Args:
            pid: Process ID to mark as dead
            redis_client: Redis client instance
            redis_key_prefix: Prefix for Redis keys
        """
        mark_process_dead_redis(pid, redis_client, redis_key_prefix)

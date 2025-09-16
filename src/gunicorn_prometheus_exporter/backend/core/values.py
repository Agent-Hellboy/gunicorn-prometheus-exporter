import os

import redis

from .dict import RedisDict, redis_key


class RedisValue:
    """A float backed by Redis for multi-process mode.

    This replaces MmapedValue for storing metrics in Redis instead of files.
    """

    _multiprocess = True

    def __init__(
        self,
        redis_dict,
        typ=None,
        metric_name=None,
        name=None,
        labelnames=None,
        labelvalues=None,
        help_text=None,
        multiprocess_mode="",
        **_kwargs,
    ):
        """Initialize RedisValue with RedisStorageDict.
        
        Args:
            redis_dict: RedisStorageDict instance for storage operations
            typ: Metric type (counter, gauge, histogram, summary)
            metric_name: Name of the metric
            name: Sample name
            labelnames: Label names
            labelvalues: Label values
            help_text: Help text for the metric
            multiprocess_mode: Multiprocess mode for gauge metrics
        """
        if not hasattr(redis_dict, "read_value"):
            raise ValueError("redis_dict must be a RedisStorageDict instance")
            
        self._redis_dict = redis_dict
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
        self._value, self._timestamp = self._redis_dict.read_value(self._key)


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


def get_redis_value_class(redis_client, redis_key_prefix="prometheus"):
    """Returns a RedisValue class configured with Redis client.
    
    Args:
        redis_client: Redis client instance
        redis_key_prefix: Prefix for Redis keys
        
    Returns:
        Configured RedisValue class
    """
    from .client import RedisStorageClient
    
    storage_client = RedisStorageClient(redis_client, redis_key_prefix)
    redis_dict = storage_client._redis_dict

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
                redis_dict,
                typ,
                metric_name,
                name,
                labelnames,
                labelvalues,
                help_text,
                multiprocess_mode,
                **kwargs,
            )

    return ConfiguredRedisValue


def mark_process_dead_redis(pid, redis_client, redis_key_prefix="prometheus"):
    """Do bookkeeping for when one process dies in a Redis multi-process setup.
    
    Args:
        pid: Process ID to clean up
        redis_client: Redis client instance
        redis_key_prefix: Prefix for Redis keys
    """
    from .client import RedisStorageClient
    
    storage_client = RedisStorageClient(redis_client, redis_key_prefix)
    storage_client.cleanup_process_keys(pid)

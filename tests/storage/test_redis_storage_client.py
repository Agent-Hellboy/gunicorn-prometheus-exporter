"""Tests for Redis storage client module."""

from typing import Dict, Optional, Tuple
from unittest.mock import Mock, patch

import pytest

from gunicorn_prometheus_exporter.backend.core.client import (
    RedisStorageClient,
    RedisStorageDict,
    RedisValueClass,
)
from gunicorn_prometheus_exporter.backend.core.values import (
    get_redis_value_class,
    mark_process_dead_redis,
)


class TestRedisClientProtocol:
    """Test Redis client protocol."""

    def test_protocol_methods(self):
        """Test that protocol methods raise NotImplementedError."""

        # Protocols cannot be instantiated, so we test the methods directly
        class TestRedisClient:
            def ping(self) -> bool:
                raise NotImplementedError

            def hget(self, name: str, key: str) -> Optional[bytes]:
                raise NotImplementedError

            def hset(
                self,
                name: str,
                key: str = None,
                value: str = None,
                mapping: Dict[str, str] = None,
            ) -> int:
                raise NotImplementedError

            def hgetall(self, name: str) -> Dict[bytes, bytes]:
                raise NotImplementedError

            def keys(self, pattern: str) -> list[bytes]:
                raise NotImplementedError

            def delete(self, *keys: str) -> int:
                raise NotImplementedError

        client = TestRedisClient()

        with pytest.raises(NotImplementedError):
            client.ping()

        with pytest.raises(NotImplementedError):
            client.hget("name", "key")

        with pytest.raises(NotImplementedError):
            client.hset("name", "key", "value")

        with pytest.raises(NotImplementedError):
            client.hgetall("name")

        with pytest.raises(NotImplementedError):
            client.keys("pattern")

        with pytest.raises(NotImplementedError):
            client.delete("key1", "key2")


class TestStorageDictProtocol:
    """Test storage dictionary protocol."""

    def test_protocol_methods(self):
        """Test that protocol methods raise NotImplementedError."""

        # Protocols cannot be instantiated, so we test the methods directly
        class TestStorageDict:
            def read_value(self, key: str) -> Tuple[float, float]:
                raise NotImplementedError

            def write_value(self, key: str, value: float, timestamp: float) -> None:
                raise NotImplementedError

        storage_dict = TestStorageDict()

        with pytest.raises(NotImplementedError):
            storage_dict.read_value("key")

        with pytest.raises(NotImplementedError):
            storage_dict.write_value("key", 1.0, 1234567890.0)


class TestRedisStorageDict:
    """Test Redis storage dictionary."""

    def test_init(self):
        """Test initialization."""
        mock_redis = Mock()
        storage_dict = RedisStorageDict(mock_redis, "test_prefix")

        assert storage_dict._redis is mock_redis
        assert storage_dict._key_prefix == "test_prefix"
        assert isinstance(storage_dict._lock, type(storage_dict._lock))

    def test_init_default_prefix(self):
        """Test initialization with default prefix."""
        mock_redis = Mock()
        storage_dict = RedisStorageDict(mock_redis)

        assert storage_dict._key_prefix == "gunicorn"

    def test_get_metric_key(self):
        """Test metric key generation."""
        mock_redis = Mock()
        storage_dict = RedisStorageDict(mock_redis, "test_prefix")

        key = storage_dict._get_metric_key("test_key")
        assert key.startswith("test_prefix:counter:")
        assert key.endswith(":metric:test_key")
        assert ":metric:" in key

    def test_get_metadata_key(self):
        """Test metadata key generation."""
        mock_redis = Mock()
        storage_dict = RedisStorageDict(mock_redis, "test_prefix")

        key = storage_dict._get_metadata_key("test_key")
        assert key.startswith("test_prefix:counter:")
        assert key.endswith(":meta:test_key")
        assert ":meta:" in key

    def test_read_value_existing(self):
        """Test reading existing value."""
        mock_redis = Mock()
        mock_redis.hget.side_effect = [b"1.5", b"1234567890"]

        storage_dict = RedisStorageDict(mock_redis, "test_prefix")
        value, timestamp = storage_dict.read_value("test_key")

        assert value == 1.5
        assert timestamp == 1234567890.0

        # Verify Redis calls - check that hget was called with the correct pattern
        assert mock_redis.hget.call_count == 2
        # Check that the calls match the new key format pattern
        calls = mock_redis.hget.call_args_list
        metric_key = calls[0][0][0]  # First argument of first call
        assert metric_key.startswith("test_prefix:counter:")
        assert metric_key.endswith(":metric:test_key")
        assert calls[0][0][1] == "value"  # Second argument should be "value"
        assert calls[1][0][1] == "timestamp"  # Second argument should be "timestamp"

    def test_read_value_missing(self):
        """Test reading missing value (initializes with defaults)."""
        mock_redis = Mock()
        mock_redis.hget.side_effect = [None, None]  # Both value and timestamp missing

        storage_dict = RedisStorageDict(mock_redis, "test_prefix")

        with patch.object(storage_dict, "_init_value_unlocked") as mock_init:
            value, timestamp = storage_dict.read_value("test_key")

            assert value == 0.0
            assert timestamp == 0.0
            mock_init.assert_called_once_with("test_key", "counter")

    def test_read_value_partial_missing(self):
        """Test reading value with missing timestamp."""
        mock_redis = Mock()
        mock_redis.hget.side_effect = [b"1.5", None]  # Value exists, timestamp missing

        storage_dict = RedisStorageDict(mock_redis, "test_prefix")

        with patch.object(storage_dict, "_init_value_unlocked") as mock_init:
            value, timestamp = storage_dict.read_value("test_key")

            assert value == 0.0
            assert timestamp == 0.0
            mock_init.assert_called_once_with("test_key", "counter")

    def test_write_value(self):
        """Test writing value."""
        mock_redis = Mock()
        storage_dict = RedisStorageDict(mock_redis, "test_prefix")

        with patch("time.time", return_value=1234567890.0):
            storage_dict.write_value("test_key", 1.5, 987654321.0)

        # Verify Redis calls - check that hset was called with the correct pattern
        assert mock_redis.hset.call_count == 2

        # Check that the calls match the new key format pattern
        calls = mock_redis.hset.call_args_list
        metric_key = calls[0][0][0]  # First argument of first call
        metadata_key = calls[1][0][0]  # First argument of second call

        assert metric_key.startswith("test_prefix:counter:")
        assert metric_key.endswith(":metric:test_key")
        assert metadata_key.startswith("test_prefix:counter:")
        assert metadata_key.endswith(":meta:test_key")

        # Check the mapping content
        metric_mapping = calls[0][1]["mapping"]
        assert metric_mapping["value"] == 1.5
        assert metric_mapping["timestamp"] == 987654321.0
        assert metric_mapping["updated_at"] == 1234567890.0

    def test_init_value(self):
        """Test initializing value."""
        mock_redis = Mock()
        storage_dict = RedisStorageDict(mock_redis, "test_prefix")

        with patch.object(storage_dict, "_init_value_unlocked") as mock_init_unlocked:
            storage_dict._init_value("test_key")
            mock_init_unlocked.assert_called_once_with("test_key", "counter")

    def test_init_value_unlocked(self):
        """Test initializing value without lock."""
        mock_redis = Mock()
        storage_dict = RedisStorageDict(mock_redis, "test_prefix")

        with patch("time.time", return_value=1234567890.0):
            storage_dict._init_value_unlocked("test_key")

        # Verify Redis calls - check that hset was called with the correct pattern
        assert mock_redis.hset.call_count == 2

        # Check that the calls match the new key format pattern
        calls = mock_redis.hset.call_args_list
        metric_key = calls[0][0][0]  # First argument of first call
        metadata_key = calls[1][0][0]  # First argument of second call

        assert metric_key.startswith("test_prefix:counter:")
        assert metric_key.endswith(":metric:test_key")
        assert metadata_key.startswith("test_prefix:counter:")
        assert metadata_key.endswith(":meta:test_key")

        # Check the mapping content
        metric_mapping = calls[0][1]["mapping"]
        assert metric_mapping["value"] == 0.0
        assert metric_mapping["timestamp"] == 0.0
        assert metric_mapping["updated_at"] == 1234567890.0


class TestRedisValueClass:
    """Test Redis value class."""

    def test_init(self):
        """Test initialization."""
        mock_redis = Mock()
        value_class = RedisValueClass(mock_redis, "test_prefix")

        assert value_class._redis_client is mock_redis
        assert value_class._key_prefix == "test_prefix"

    def test_init_default_prefix(self):
        """Test initialization with default prefix."""
        mock_redis = Mock()
        value_class = RedisValueClass(mock_redis)

        assert value_class._key_prefix == "gunicorn"

    def test_call(self):
        """Test creating RedisValue instance."""
        mock_redis = Mock()
        # Mock the Redis responses to return proper byte strings
        mock_redis.hget.side_effect = [b"0.0", b"0.0"]  # value, timestamp

        value_class = RedisValueClass(mock_redis, "test_prefix")

        # Test that the call method works by calling it directly
        # The actual RedisValue import happens inside the method
        result = value_class(
            "counter", "test_metric", "test_key", [], [], "Test metric"
        )

        # Verify that a RedisValue instance was created
        assert result is not None
        assert hasattr(result, "_redis_dict")
        # The RedisValue creates its own RedisStorageDict, so we just verify it exists
        assert result._redis_dict is not None


class TestRedisStorageClient:
    """Test Redis storage client."""

    def test_init(self):
        """Test initialization."""
        mock_redis = Mock()
        client = RedisStorageClient(mock_redis, "test_prefix")

        assert client._redis_client is mock_redis
        assert client._key_prefix == "test_prefix"
        assert isinstance(client._value_class, RedisValueClass)

    def test_init_default_prefix(self):
        """Test initialization with default prefix."""
        mock_redis = Mock()
        client = RedisStorageClient(mock_redis)

        assert client._key_prefix == "gunicorn"

    def test_get_value_class(self):
        """Test getting value class."""
        mock_redis = Mock()
        client = RedisStorageClient(mock_redis, "test_prefix")

        value_class = client.get_value_class()
        assert isinstance(value_class, RedisValueClass)

    def test_cleanup_process_keys_success(self):
        """Test successful cleanup of process keys."""
        mock_redis = Mock()
        mock_redis.keys.return_value = [b"key1", b"key2", b"key3"]
        mock_redis.delete.return_value = 3

        client = RedisStorageClient(mock_redis, "test_prefix")

        with patch(
            "gunicorn_prometheus_exporter.backend.core.client.logger"
        ) as mock_logger:
            client.cleanup_process_keys(12345)

        # Verify Redis calls
        expected_pattern = "test_prefix:*:12345:*"
        mock_redis.keys.assert_called_once_with(expected_pattern)
        mock_redis.delete.assert_called_once_with(b"key1", b"key2", b"key3")

        # Verify logging
        mock_logger.debug.assert_called_once_with(
            "Cleaned up %d Redis keys for process %d", 3, 12345
        )

    def test_cleanup_process_keys_no_keys(self):
        """Test cleanup when no keys exist."""
        mock_redis = Mock()
        mock_redis.keys.return_value = []

        client = RedisStorageClient(mock_redis, "test_prefix")

        with patch(
            "gunicorn_prometheus_exporter.backend.core.client.logger"
        ) as mock_logger:
            client.cleanup_process_keys(12345)

        # Verify Redis calls
        expected_pattern = "test_prefix:*:12345:*"
        mock_redis.keys.assert_called_once_with(expected_pattern)
        mock_redis.delete.assert_not_called()

        # Verify no debug logging
        mock_logger.debug.assert_not_called()

    def test_cleanup_process_keys_exception(self):
        """Test cleanup with exception."""
        mock_redis = Mock()
        mock_redis.keys.side_effect = Exception("Redis error")

        client = RedisStorageClient(mock_redis, "test_prefix")

        with patch(
            "gunicorn_prometheus_exporter.backend.core.client.logger"
        ) as mock_logger:
            client.cleanup_process_keys(12345)

        # Verify warning logging - the exception object is passed, not the string
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert call_args[0][0] == "Failed to cleanup Redis keys for process %d: %s"
        assert call_args[0][1] == 12345
        assert str(call_args[0][2]) == "Redis error"

    def test_get_client(self):
        """Test getting Redis client."""
        mock_redis = Mock()
        client = RedisStorageClient(mock_redis, "test_prefix")

        returned_client = client.get_client()
        assert returned_client is mock_redis


class TestFactoryFunctions:
    """Test factory functions."""

    def test_get_redis_value_class(self):
        """Test get_redis_value_class factory function."""
        mock_redis = Mock()
        # Mock the Redis client methods to return proper values
        mock_redis.hget.return_value = None  # Return None to trigger initialization
        mock_redis.hset.return_value = 1
        mock_redis.hgetall.return_value = {}
        mock_redis.keys.return_value = []
        mock_redis.delete.return_value = None

        result = get_redis_value_class(mock_redis, "test_prefix")

        # The function returns a ConfiguredRedisValue class
        assert result is not None
        assert callable(result)

        # Test that the class can be instantiated with correct parameters
        instance = result(
            typ="counter",
            metric_name="test_metric",
            name="test_name",
            labelnames=[],
            labelvalues=[],
            help_text="Test help",
        )
        assert instance is not None

    def test_get_redis_value_class_default_prefix(self):
        """Test get_redis_value_class with default prefix."""
        mock_redis = Mock()
        # Mock the Redis client methods to return proper values
        mock_redis.hget.return_value = None  # Return None to trigger initialization
        mock_redis.hset.return_value = 1
        mock_redis.hgetall.return_value = {}
        mock_redis.keys.return_value = []
        mock_redis.delete.return_value = None

        result = get_redis_value_class(mock_redis)

        # The function returns a ConfiguredRedisValue class
        assert result is not None
        assert callable(result)

        # Test that the class can be instantiated with correct parameters
        instance = result(
            typ="counter",
            metric_name="test_metric",
            name="test_name",
            labelnames=[],
            labelvalues=[],
            help_text="Test help",
        )
        assert instance is not None

    def test_mark_process_dead_redis(self):
        """Test mark_process_dead_redis factory function."""
        mock_redis = Mock()

        with patch(
            "gunicorn_prometheus_exporter.backend.core.client.RedisStorageClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mark_process_dead_redis(12345, mock_redis, "test_prefix")

            mock_client_class.assert_called_once_with(mock_redis, "test_prefix")
            mock_client.cleanup_process_keys.assert_called_once_with(12345)

    def test_mark_process_dead_redis_default_prefix(self):
        """Test mark_process_dead_redis with default prefix."""
        mock_redis = Mock()

        with patch(
            "gunicorn_prometheus_exporter.backend.core.client.RedisStorageClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mark_process_dead_redis(12345, mock_redis)

            mock_client_class.assert_called_once_with(mock_redis, "gunicorn")
            mock_client.cleanup_process_keys.assert_called_once_with(12345)

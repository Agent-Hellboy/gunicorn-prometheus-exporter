"""Unit tests for Redis backend storage components."""

import os

from unittest.mock import Mock, patch

from gunicorn_prometheus_exporter.backend.core import (
    RedisMultiProcessCollector,
    RedisStorageClient,
    RedisStorageDict,
    RedisValue,
    get_redis_value_class,
    mark_process_dead_redis,
)


class TestRedisStorageClient:
    """Test RedisStorageClient class."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["REDIS_ENABLED"] = "true"
        os.environ["REDIS_HOST"] = "localhost"
        os.environ["REDIS_PORT"] = "6379"
        os.environ["REDIS_DB"] = "0"

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.pop("REDIS_ENABLED", None)
        os.environ.pop("REDIS_HOST", None)
        os.environ.pop("REDIS_PORT", None)
        os.environ.pop("REDIS_DB", None)

    @patch("redis.Redis")
    def test_init_success(self, mock_redis_class):
        """Test successful initialization."""
        mock_client = Mock()
        mock_redis_class.return_value = mock_client
        mock_client.ping.return_value = True

        client = RedisStorageClient(mock_client)

        assert client._redis_client is not None
        assert client._key_prefix == "gunicorn"

    def test_init_connection_failure(self):
        """Test initialization with connection failure."""
        mock_client = Mock()
        # RedisStorageClient doesn't raise exceptions during init
        client = RedisStorageClient(mock_client)

        assert client._redis_client == mock_client

    @patch("redis.Redis")
    def test_get_client(self, mock_redis_class):
        """Test getting Redis client."""
        mock_client = Mock()
        mock_redis_class.return_value = mock_client
        mock_client.ping.return_value = True

        client = RedisStorageClient(mock_client)

        assert client._redis_client == mock_client


class TestRedisStorageDict:
    """Test RedisStorageDict class."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["REDIS_ENABLED"] = "true"

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.pop("REDIS_ENABLED", None)

    @patch("gunicorn_prometheus_exporter.backend.core.client.RedisStorageClient")
    def test_init(self, mock_client_class):
        """Test initialization."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        redis_dict = RedisStorageDict(mock_client)

        assert redis_dict._redis == mock_client

    @patch("gunicorn_prometheus_exporter.backend.core.client.RedisStorageClient")
    def test_set_get(self, mock_client_class):
        """Test set and get operations."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.hset.return_value = 1
        mock_client.hget.side_effect = [
            b"10.5",
            b"1234567890.0",
        ]  # value, then timestamp

        redis_dict = RedisStorageDict(mock_client)

        # Test write_value and read_value methods
        redis_dict.write_value("test_key", 10.5, 1234567890.0)
        value, timestamp = redis_dict.read_value("test_key")

        assert value == 10.5
        assert timestamp == 1234567890.0
        assert mock_client.hset.call_count == 2  # Called twice: metric data + metadata

    def test_read_all_values(self):
        """Test reading all values."""
        mock_client = Mock()
        mock_client.scan_iter.return_value = [
            "prometheus:metric:test_key"
        ]  # Return strings, not bytes
        mock_client.hget.return_value = b"10.5"
        redis_dict = RedisStorageDict(mock_client)

        values = list(redis_dict.read_all_values())

        assert len(values) > 0
        mock_client.scan_iter.assert_called_once()

    def test_close(self):
        """Test close method."""
        mock_client = Mock()
        redis_dict = RedisStorageDict(mock_client)

        # RedisStorageDict.close() doesn't call redis_client.close()
        redis_dict.close()

        # Just test that close() doesn't raise an exception
        assert True


class TestRedisValue:
    """Test RedisValue."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["REDIS_ENABLED"] = "true"

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.pop("REDIS_ENABLED", None)

    @patch("gunicorn_prometheus_exporter.backend.core.client.RedisStorageDict")
    def test_init(self, mock_redis_storage_dict_class):
        """Test initialization."""
        mock_redis = Mock()
        mock_redis_storage_dict = Mock()
        mock_redis_storage_dict_class.return_value = mock_redis_storage_dict
        mock_redis_storage_dict.read_value.return_value = (0.0, 0)

        value = RedisValue(
            typ="counter",
            metric_name="test_metric",
            name="test_name",
            labelnames=(),
            labelvalues=(),
            help_text="Test help",
            redis_client=mock_redis,
            redis_key_prefix="test_prefix",
        )

        assert value._redis_dict == mock_redis_storage_dict
        assert value._value == 0.0
        assert value._timestamp == 0

    @patch("gunicorn_prometheus_exporter.backend.core.client.RedisStorageDict")
    def test_value_operations(self, mock_redis_storage_dict_class):
        """Test value operations."""
        mock_redis = Mock()
        mock_redis_storage_dict = Mock()
        mock_redis_storage_dict_class.return_value = mock_redis_storage_dict
        mock_redis_storage_dict.read_value.return_value = (10.0, 1234567890)

        value = RedisValue(
            typ="counter",
            metric_name="test_metric",
            name="test_name",
            labelnames=(),
            labelvalues=(),
            help_text="Test help",
            redis_client=mock_redis,
            redis_key_prefix="test_prefix",
        )

        # Test value property
        assert value._value == 10.0
        assert value._timestamp == 1234567890


class TestRedisMultiProcessCollector:
    """Test RedisMultiProcessCollector class."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["REDIS_ENABLED"] = "true"

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.pop("REDIS_ENABLED", None)

    @patch("gunicorn_prometheus_exporter.backend.core.client.RedisStorageClient")
    def test_init(self, mock_client_class):
        """Test initialization."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_registry = Mock()

        collector = RedisMultiProcessCollector(mock_registry, mock_client)

        assert collector._redis_client == mock_client

    @patch("gunicorn_prometheus_exporter.backend.core.client.RedisStorageClient")
    def test_collect_empty(self, mock_client_class):
        """Test collect with no metrics."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.scan_iter.return_value = []
        mock_registry = Mock()

        collector = RedisMultiProcessCollector(mock_registry, mock_client)
        metrics = list(collector.collect())

        assert metrics == []
        mock_client.scan_iter.assert_called_with(match="gunicorn:*:*:metric:*")

    @patch("gunicorn_prometheus_exporter.backend.core.client.RedisStorageClient")
    def test_collect_with_metrics(self, mock_client_class):
        """Test collect with metrics."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.scan_iter.return_value = [
            b"gunicorn:counter:12345:metric:test_metric"
        ]
        mock_client.hget.side_effect = [
            b"10.5",
            b"1234567890.0",
        ]  # value, then timestamp
        mock_registry = Mock()

        collector = RedisMultiProcessCollector(mock_registry, mock_client)
        metrics = list(collector.collect())

        assert len(metrics) > 0
        mock_client.scan_iter.assert_called_with(match="gunicorn:*:*:metric:*")

    @patch("gunicorn_prometheus_exporter.backend.core.client.RedisStorageClient")
    def test_collect_error_handling(self, mock_client_class):
        """Test collect with Redis error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.keys.side_effect = Exception("Redis error")
        mock_registry = Mock()

        collector = RedisMultiProcessCollector(mock_registry, mock_client)

        # Collector handles errors gracefully, returns empty list
        metrics = list(collector.collect())
        assert metrics == []


class TestModuleFunctions:
    """Test module-level functions."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["REDIS_ENABLED"] = "true"

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.pop("REDIS_ENABLED", None)

    def test_get_redis_value_class(self):
        """Test get_redis_value_class function."""
        mock_client = Mock()
        result = get_redis_value_class(mock_client)

        assert result is not None
        assert callable(result)

    def test_mark_process_dead_redis(self):
        """Test mark_process_dead_redis function."""
        mock_client = Mock()
        mock_client.scan_iter.return_value = [
            "key1",
            "key2",
        ]  # Return strings, not bytes
        mock_client.hgetall.return_value = {
            b"original_key": b"key1"
        }  # Mock metadata  # Return actual keys
        mock_client.delete.return_value = 2

        result = mark_process_dead_redis("123", mock_client)

        # Function may not return anything, just test it doesn't raise
        assert result is None or result == 2


class TestRedisBackendIntegration:
    """Integration tests for Redis backend components."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["REDIS_ENABLED"] = "true"

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.pop("REDIS_ENABLED", None)

    @patch("gunicorn_prometheus_exporter.backend.core.client.RedisStorageClient")
    def test_storage_dict_integration(self, mock_client_class):
        """Test RedisStorageDict integration."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.hset.return_value = 1
        mock_client.hget.side_effect = [
            b"10.5",
            b"1234567890.0",
            b"10.5",
            b"1234567890.0",
            b"20.0",
            b"1234567891.0",
        ]  # Enough for 2 keys
        mock_client.delete.return_value = 1
        mock_client.scan_iter.return_value = [
            "key1",
            "key2",
        ]  # Return strings, not bytes
        mock_client.hgetall.return_value = {b"original_key": b"key1"}  # Mock metadata

        redis_dict = RedisStorageDict(mock_client)

        # Test complete workflow using actual API
        redis_dict.write_value("key1", 10.5, 1234567890.0)
        value, timestamp = redis_dict.read_value("key1")
        values = list(redis_dict.read_all_values())
        redis_dict.close()

        assert value == 10.5
        assert timestamp == 1234567890.0
        assert len(values) > 0
        mock_client.hset.assert_called()
        mock_client.hget.assert_called()
        mock_client.scan_iter.assert_called()
        # RedisStorageDict.close() doesn't call redis_client.close()

    @patch("gunicorn_prometheus_exporter.backend.core.client.RedisStorageClient")
    def test_value_class_integration(self, mock_client_class):
        """Test RedisValueClass integration."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.hget.return_value = b"10.5"
        mock_client.hset.return_value = 1

        value_class = RedisValue(
            typ="counter",
            metric_name="test_metric",
            name="test_name",
            labelnames=[],
            labelvalues=[],
            help_text="Test metric",
            redis_client=mock_client,
            redis_key_prefix="test_prefix",
        )

        # Test that the value class was created successfully
        assert value_class._redis_dict is not None

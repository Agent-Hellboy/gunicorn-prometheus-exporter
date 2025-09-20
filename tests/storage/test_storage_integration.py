"""Unit tests for storage module integration."""

import os

from unittest.mock import Mock, patch

from gunicorn_prometheus_exporter.backend import (
    RedisStorageClient,
    RedisStorageDict,
    RedisStorageManager,
    RedisValueClass,
    cleanup_redis_keys,
    get_redis_client,
    get_redis_collector,
    get_redis_storage_manager,
    is_redis_enabled,
    setup_redis_metrics,
    teardown_redis_metrics,
)
from gunicorn_prometheus_exporter.backend.core.values import (
    get_redis_value_class,
    mark_process_dead_redis,
)


class TestStorageModuleIntegration:
    """Integration tests for the entire storage module."""

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

    @patch("gunicorn_prometheus_exporter.backend.service.manager.redis")
    def test_redis_storage_manager_integration(self, mock_redis):
        """Test RedisStorageManager integration."""
        mock_client = Mock()
        mock_redis.from_url.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.keys.return_value = []

        # Test manager creation
        manager = RedisStorageManager()
        assert manager is not None

        # Test setup
        result = manager.setup()
        assert result is True
        assert manager.is_enabled() is True

        # Test teardown
        manager.teardown()
        assert manager.is_enabled() is False

    def test_module_functions_integration(self):
        """Test module-level functions integration."""
        # Test setup function
        with patch(
            "gunicorn_prometheus_exporter.backend.service.manager.redis"
        ) as mock_redis:
            mock_client = Mock()
            mock_redis.from_url.return_value = mock_client
            mock_client.ping.return_value = True

            result = setup_redis_metrics()
            assert result is True

            # Test teardown
            teardown_redis_metrics()

            # Test is_enabled
            enabled = is_redis_enabled()
            assert isinstance(enabled, bool)

    def test_redis_backend_integration(self):
        """Test Redis backend integration."""
        with patch("redis.Redis") as mock_redis:
            mock_client = Mock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            mock_client.hget.return_value = None
            mock_client.hset.return_value = True
            mock_client.keys.return_value = []

            # Test RedisStorageDict
            redis_dict = RedisStorageDict(mock_client, "test")
            assert redis_dict is not None

            # Test RedisStorageClient
            storage_client = RedisStorageClient(mock_client, "test")
            assert storage_client is not None

            # Test RedisValueClass
            value_class = RedisValueClass(mock_client, "test")
            assert value_class is not None

    def test_error_handling_integration(self):
        """Test error handling across the storage module."""
        # Test Redis connection failure
        with patch(
            "gunicorn_prometheus_exporter.backend.service.manager.redis"
        ) as mock_redis:
            mock_redis.from_url.side_effect = Exception("Connection failed")

            manager = RedisStorageManager()
            # RedisStorageManager handles connection failures gracefully
            assert manager is not None

    def test_module_imports(self):
        """Test that all module imports work correctly."""
        # Test that all classes can be imported
        assert RedisStorageManager is not None
        assert RedisStorageClient is not None
        assert RedisStorageDict is not None
        assert RedisValueClass is not None

        # Test that all functions can be imported
        assert setup_redis_metrics is not None
        assert teardown_redis_metrics is not None
        assert is_redis_enabled is not None
        assert get_redis_storage_manager is not None
        assert get_redis_client is not None
        assert get_redis_collector is not None
        assert get_redis_value_class is not None
        assert cleanup_redis_keys is not None
        assert mark_process_dead_redis is not None

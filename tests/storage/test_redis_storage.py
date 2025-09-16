"""Tests for Redis storage module."""

from unittest.mock import Mock, patch

from gunicorn_prometheus_exporter.backend.service import RedisStorageManager


class TestRedisStorageManager:
    """Test Redis storage manager."""

    def setup_method(self):
        """Set up test environment."""
        self.manager = RedisStorageManager()

    def teardown_method(self):
        """Clean up test environment."""
        if self.manager.is_enabled():
            self.manager.teardown()

    @patch("gunicorn_prometheus_exporter.backend.service.manager.config")
    def test_setup_redis_metrics_disabled(self, mock_config):
        """Test setup when Redis is disabled."""
        mock_config.redis_enabled = False

        with patch(
            "gunicorn_prometheus_exporter.backend.service.manager.logger"
        ) as mock_logger:
            result = self.manager.setup()

            assert result is False
            mock_logger.debug.assert_called_once_with(
                "Redis is not enabled, skipping Redis metrics setup"
            )

    @patch("gunicorn_prometheus_exporter.backend.service.manager.config")
    @patch("redis.from_url")
    @patch("prometheus_client.values")
    def test_setup_redis_metrics_success(
        self, mock_values, mock_redis_from_url, mock_config
    ):
        """Test successful Redis setup."""
        # Configure mocks
        mock_config.redis_enabled = True
        mock_config.redis_host = "localhost"
        mock_config.redis_port = 6379
        mock_config.redis_db = 0
        mock_config.redis_password = None

        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis_from_url.return_value = mock_client

        mock_value_class = Mock()
        self.manager._value_class_factory = Mock(return_value=mock_value_class)

        mock_original_value_class = Mock()
        mock_values.ValueClass = mock_original_value_class

        with patch(
            "gunicorn_prometheus_exporter.backend.service.manager.logger"
        ) as mock_logger:
            result = self.manager.setup()

            assert result is True
            assert self.manager.is_enabled() is True
            assert self.manager.get_client() is mock_client

            # Verify Redis client was created
            mock_redis_from_url.assert_called_once()
            mock_client.ping.assert_called_once()

            # Verify value class was replaced
            self.manager._value_class_factory.assert_called_once_with(
                mock_client, "gunicorn"
            )
            assert mock_values.ValueClass is mock_value_class

            # Verify logging
            mock_logger.info.assert_called_with(
                "Redis metrics storage enabled - using Redis instead of files"
            )

    @patch("gunicorn_prometheus_exporter.backend.service.manager.config")
    @patch("redis.from_url")
    def test_setup_redis_metrics_connection_error(
        self, mock_redis_from_url, mock_config
    ):
        """Test Redis setup with connection error."""
        mock_config.redis_enabled = True
        mock_config.redis_host = "localhost"
        mock_config.redis_port = 6379
        mock_config.redis_db = 0
        mock_config.redis_password = None

        mock_client = Mock()
        mock_client.ping.side_effect = Exception("Connection failed")
        mock_redis_from_url.return_value = mock_client

        with patch(
            "gunicorn_prometheus_exporter.backend.service.manager.logger"
        ) as mock_logger:
            result = self.manager.setup()

            assert result is False
            assert self.manager.is_enabled() is False
            mock_logger.error.assert_called_once_with(
                "Failed to setup Redis metrics: %s", mock_client.ping.side_effect
            )

    def test_teardown_when_not_initialized(self):
        """Test teardown when not initialized."""
        with patch("gunicorn_prometheus_exporter.backend.service.manager.logger"):
            self.manager.teardown()
            # Should not log anything when not initialized

    @patch("prometheus_client.values")
    def test_teardown_success(self, mock_values):
        """Test successful teardown."""
        # Setup manager state
        self.manager._is_initialized = True
        self.manager._redis_client = Mock()
        original_value_class = Mock()
        self.manager._original_value_class = original_value_class
        mock_values.ValueClass = Mock()

        with patch(
            "gunicorn_prometheus_exporter.backend.service.manager.logger"
        ) as mock_logger:
            self.manager.teardown()

            assert self.manager.is_enabled() is False
            assert self.manager._redis_client is None
            assert self.manager._original_value_class is None

            # Verify original value class was restored
            assert mock_values.ValueClass is original_value_class

            mock_logger.info.assert_called_with("Redis storage teardown completed")

    def test_is_enabled(self):
        """Test is_enabled method."""
        assert self.manager.is_enabled() is False

        self.manager._is_initialized = True
        self.manager._redis_client = Mock()
        assert self.manager.is_enabled() is True

    def test_get_client(self):
        """Test get_client method."""
        assert self.manager.get_client() is None

        mock_client = Mock()
        self.manager._redis_client = mock_client
        assert self.manager.get_client() is mock_client

    @patch("gunicorn_prometheus_exporter.backend.core.mark_process_dead_redis")
    def test_cleanup_keys(self, mock_mark_dead):
        """Test cleanup_keys method."""
        mock_client = Mock()
        self.manager._redis_client = mock_client

        with patch("os.getpid", return_value=12345):
            with patch(
                "gunicorn_prometheus_exporter.backend.service.manager.logger"
            ) as mock_logger:
                self.manager.cleanup_keys()

                mock_mark_dead.assert_called_once_with(12345, mock_client, "gunicorn")
                mock_logger.debug.assert_called_once_with(
                    "Cleaned up Redis keys for process %d", 12345
                )

    def test_cleanup_keys_no_client(self):
        """Test cleanup_keys when no client."""
        with patch("gunicorn_prometheus_exporter.backend.service.manager.logger"):
            self.manager.cleanup_keys()
            # Should not do anything when no client

    @patch("gunicorn_prometheus_exporter.backend.core.RedisMultiProcessCollector")
    @patch("gunicorn_prometheus_exporter.metrics.get_shared_registry")
    def test_get_collector_success(self, mock_get_registry, mock_collector_class):
        """Test successful collector creation."""
        mock_client = Mock()
        self.manager._redis_client = mock_client
        self.manager._is_initialized = True

        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry
        mock_collector = Mock()
        mock_collector_class.return_value = mock_collector

        result = self.manager.get_collector()

        assert result is mock_collector
        mock_collector_class.assert_called_once_with(
            mock_registry, mock_client, "gunicorn"
        )

    def test_get_collector_not_enabled(self):
        """Test get_collector when not enabled."""
        result = self.manager.get_collector()
        assert result is None

    @patch("gunicorn_prometheus_exporter.backend.core.RedisMultiProcessCollector")
    @patch("gunicorn_prometheus_exporter.metrics.get_shared_registry")
    def test_get_collector_error(self, mock_get_registry, mock_collector_class):
        """Test collector creation with error."""
        mock_client = Mock()
        self.manager._redis_client = mock_client
        self.manager._is_initialized = True

        mock_get_registry.side_effect = Exception("Registry error")

        with patch(
            "gunicorn_prometheus_exporter.backend.service.manager.logger"
        ) as mock_logger:
            result = self.manager.get_collector()

            assert result is None
            mock_logger.error.assert_called_once_with(
                "Failed to create Redis collector: %s", mock_get_registry.side_effect
            )

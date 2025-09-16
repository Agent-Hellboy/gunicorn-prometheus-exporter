"""Tests for Redis storage module."""

from unittest.mock import Mock, patch

from gunicorn_prometheus_exporter.storage.redis_manager import redis_storage


class TestRedisStorageSetup:
    """Test Redis storage setup functions."""

    def setup_method(self):
        """Set up test environment."""
        # Reset global variables
        redis_storage._redis_client = None
        redis_storage._redis_value_class = None
        redis_storage._original_value_class = None

    def teardown_method(self):
        """Clean up test environment."""
        # Reset global variables
        redis_storage._redis_client = None
        redis_storage._redis_value_class = None
        redis_storage._original_value_class = None

    @patch("gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.config")
    def test_setup_redis_metrics_disabled(self, mock_config):
        """Test setup when Redis is disabled."""
        mock_config.redis_enabled = False

        with patch(
            "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
        ) as mock_logger:
            result = redis_storage.setup_redis_metrics()

            assert result is False
            mock_logger.debug.assert_called_once_with(
                "Redis is not enabled, skipping Redis metrics setup"
            )

    @patch("gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.config")
    @patch("redis.from_url")
    @patch(
        "gunicorn_prometheus_exporter.storage.redis_backend.redis_storage_client.get_redis_value_class"
    )
    @patch("prometheus_client.values")
    def test_setup_redis_metrics_success(
        self, mock_values, mock_get_value_class, mock_redis_from_url, mock_config
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
        mock_get_value_class.return_value = mock_value_class

        mock_original_value_class = Mock()
        mock_values.ValueClass = mock_original_value_class

        with patch(
            "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
        ) as mock_logger:
            result = redis_storage.setup_redis_metrics()

            assert result is True
            assert redis_storage._redis_client is mock_client
            assert redis_storage._redis_value_class is mock_value_class
            assert redis_storage._original_value_class is mock_original_value_class

            # Verify Redis client creation
            mock_redis_from_url.assert_called_once_with(
                "redis://localhost:6379/0", decode_responses=False
            )
            mock_client.ping.assert_called_once()

            # Verify value class setup
            mock_get_value_class.assert_called_once_with(mock_client, "gunicorn")
            assert mock_values.ValueClass is mock_value_class

            # Verify logging
            mock_logger.info.assert_any_call(
                "Connected to Redis at %s:%s", "localhost", 6379
            )
            mock_logger.info.assert_any_call(
                "Redis metrics storage enabled - using Redis instead of files"
            )

    @patch("gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.config")
    @patch("redis.from_url")
    def test_setup_redis_metrics_with_password(self, mock_redis_from_url, mock_config):
        """Test Redis setup with password."""
        # Configure mocks
        mock_config.redis_enabled = True
        mock_config.redis_host = "localhost"
        mock_config.redis_port = 6379
        mock_config.redis_db = 0
        mock_config.redis_password = "secret"

        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis_from_url.return_value = mock_client

        with (
            patch(
                "gunicorn_prometheus_exporter.storage.redis_backend.redis_storage_client.get_redis_value_class"
            ) as mock_get_value_class,
            patch("prometheus_client.values") as mock_values,
            patch(
                "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
            ),
        ):
            mock_value_class = Mock()
            mock_get_value_class.return_value = mock_value_class
            mock_values.ValueClass = Mock()

            result = redis_storage.setup_redis_metrics()

            assert result is True
            # Verify Redis URL with password
            expected_url = "redis://:secret@localhost:6379/0"
            mock_redis_from_url.assert_called_once_with(
                expected_url, decode_responses=False
            )

    @patch("gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.config")
    def test_setup_redis_metrics_import_error(self, mock_config):
        """Test setup with import error."""
        mock_config.redis_enabled = True

        with patch(
            "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
        ) as mock_logger:
            with patch(
                "redis.from_url", side_effect=ImportError("redis not available")
            ):
                result = redis_storage.setup_redis_metrics()

                assert result is False
                mock_logger.error.assert_called_once_with(
                    "prometheus-redis-client not installed. Install with: "
                    "pip install prometheus-redis-client"
                )

    @patch("gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.config")
    @patch("redis.from_url")
    def test_setup_redis_metrics_connection_error(
        self, mock_redis_from_url, mock_config
    ):
        """Test setup with connection error."""
        mock_config.redis_enabled = True
        mock_config.redis_host = "localhost"
        mock_config.redis_port = 6379
        mock_config.redis_db = 0
        mock_config.redis_password = None

        mock_client = Mock()
        mock_client.ping.side_effect = Exception("Connection failed")
        mock_redis_from_url.return_value = mock_client

        with patch(
            "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
        ) as mock_logger:
            result = redis_storage.setup_redis_metrics()

            assert result is False
            # The actual error message will be about connection failure
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Failed to setup Redis metrics" in call_args[0][0]

    def test_teardown_redis_metrics_no_setup(self):
        """Test teardown when nothing was set up."""
        with patch(
            "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
        ) as mock_logger:
            redis_storage.teardown_redis_metrics()

            # Should not log anything when nothing was set up
            mock_logger.info.assert_not_called()
            mock_logger.warning.assert_not_called()

    def test_teardown_redis_metrics_with_setup(self):
        """Test teardown with proper setup."""
        # Set up mock state
        mock_client = Mock()
        mock_value_class = Mock()
        mock_original_value_class = Mock()

        redis_storage._redis_client = mock_client
        redis_storage._redis_value_class = mock_value_class
        redis_storage._original_value_class = mock_original_value_class

        with (
            patch("prometheus_client.values") as mock_values,
            patch(
                "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
            ) as mock_logger,
        ):
            redis_storage.teardown_redis_metrics()

            # Verify value class restoration
            assert mock_values.ValueClass is mock_original_value_class
            mock_logger.info.assert_any_call("Restored original Prometheus value class")

            # Verify Redis client cleanup
            mock_client.close.assert_called_once()
            mock_logger.info.assert_any_call("Disconnected from Redis")

            # Verify state reset
            assert redis_storage._redis_client is None
            assert redis_storage._redis_value_class is None
            assert redis_storage._original_value_class is None

    def test_teardown_redis_metrics_close_error(self):
        """Test teardown with Redis close error."""
        # Set up mock state
        mock_client = Mock()
        mock_client.close.side_effect = Exception("Close failed")
        redis_storage._redis_client = mock_client
        redis_storage._original_value_class = Mock()

        with (
            patch("prometheus_client.values"),
            patch(
                "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
            ) as mock_logger,
        ):
            redis_storage.teardown_redis_metrics()

            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args[0][0] == "Error disconnecting from Redis: %s"
            assert str(call_args[0][1]) == "Close failed"

    def test_is_redis_enabled_false(self):
        """Test is_redis_enabled when disabled."""
        assert redis_storage.is_redis_enabled() is False

    def test_is_redis_enabled_true(self):
        """Test is_redis_enabled when enabled."""
        redis_storage._redis_client = Mock()
        redis_storage._redis_value_class = Mock()

        assert redis_storage.is_redis_enabled() is True

    def test_get_redis_client_none(self):
        """Test get_redis_client when not set."""
        assert redis_storage.get_redis_client() is None

    def test_get_redis_client_set(self):
        """Test get_redis_client when set."""
        mock_client = Mock()
        redis_storage._redis_client = mock_client

        assert redis_storage.get_redis_client() is mock_client

    def test_cleanup_redis_keys_no_client(self):
        """Test cleanup when no Redis client."""
        with patch(
            "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
        ) as mock_logger:
            redis_storage.cleanup_redis_keys()

            # Should not log anything when no client
            mock_logger.debug.assert_not_called()
            mock_logger.warning.assert_not_called()

    @patch("os.getpid")
    def test_cleanup_redis_keys_success(self, mock_getpid):
        """Test successful cleanup."""
        mock_getpid.return_value = 12345
        redis_storage._redis_client = Mock()

        with (
            patch(
                "gunicorn_prometheus_exporter.storage.redis_backend.redis_storage_client.mark_process_dead_redis"
            ) as mock_cleanup,
            patch(
                "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
            ) as mock_logger,
        ):
            redis_storage.cleanup_redis_keys()

            mock_cleanup.assert_called_once_with(
                12345, redis_storage._redis_client, "gunicorn"
            )
            mock_logger.debug.assert_called_once_with(
                "Cleaned up Redis keys for process %d", 12345
            )

    @patch("os.getpid")
    def test_cleanup_redis_keys_error(self, mock_getpid):
        """Test cleanup with error."""
        mock_getpid.return_value = 12345
        redis_storage._redis_client = Mock()

        with (
            patch(
                "gunicorn_prometheus_exporter.storage.redis_backend.redis_storage_client.mark_process_dead_redis",
                side_effect=Exception("Cleanup failed"),
            ),
            patch(
                "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
            ) as mock_logger,
        ):
            redis_storage.cleanup_redis_keys()

            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args[0][0] == "Failed to cleanup Redis keys: %s"
            assert str(call_args[0][1]) == "Cleanup failed"

    def test_get_redis_collector_disabled(self):
        """Test get_redis_collector when Redis is disabled."""
        with patch(
            "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.is_redis_enabled",
            return_value=False,
        ):
            result = redis_storage.get_redis_collector()
            assert result is None

    def test_get_redis_collector_success(self):
        """Test successful collector creation."""
        redis_storage._redis_client = Mock()

        with (
            patch(
                "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.is_redis_enabled",
                return_value=True,
            ),
            patch(
                "gunicorn_prometheus_exporter.metrics.get_shared_registry"
            ) as mock_get_registry,
            patch(
                "gunicorn_prometheus_exporter.storage.redis_backend.storage_collector.RedisMultiProcessCollector"
            ) as mock_collector_class,
        ):
            mock_registry = Mock()
            mock_get_registry.return_value = mock_registry
            mock_collector = Mock()
            mock_collector_class.return_value = mock_collector

            result = redis_storage.get_redis_collector()

            assert result is mock_collector
            mock_collector_class.assert_called_once_with(
                mock_registry, redis_storage._redis_client, "gunicorn"
            )

    def test_get_redis_collector_error(self):
        """Test collector creation with error."""
        redis_storage._redis_client = Mock()

        with (
            patch(
                "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.is_redis_enabled",
                return_value=True,
            ),
            patch(
                "gunicorn_prometheus_exporter.metrics.get_shared_registry",
                side_effect=Exception("Registry error"),
            ),
            patch(
                "gunicorn_prometheus_exporter.storage.redis_manager.redis_storage.logger"
            ) as mock_logger,
        ):
            result = redis_storage.get_redis_collector()

            assert result is None
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "Failed to create Redis collector: %s"
            assert str(call_args[0][1]) == "Registry error"

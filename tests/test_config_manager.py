"""
Tests for Gunicorn Prometheus Exporter configuration manager.
"""

import os
import tempfile
import threading

from unittest.mock import MagicMock, patch

import pytest

from gunicorn_prometheus_exporter.config import (
    ConfigManager,
    ConfigState,
    cleanup_config,
    get_config,
    get_config_manager,
    initialize_config,
)


class TestConfigManager:
    """Test ConfigManager class."""

    def test_initial_state(self):
        """Test initial state of ConfigManager."""
        manager = ConfigManager()

        assert manager.state == ConfigState.UNINITIALIZED
        assert not manager.is_initialized
        assert manager.validation_errors == []

    def test_initialize_success(self):
        """Test successful configuration initialization."""
        manager = ConfigManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            manager.initialize(
                PROMETHEUS_METRICS_PORT="9091",
                PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                GUNICORN_WORKERS="2",
                PROMETHEUS_MULTIPROC_DIR=temp_dir,
            )

            assert manager.state == ConfigState.INITIALIZED
            assert manager.is_initialized
            assert manager.validation_errors == []

            config = manager.get_config()
            assert config.prometheus_metrics_port == 9091
            assert config.prometheus_bind_address == "0.0.0.0"
            assert config.gunicorn_workers == 2

    def test_initialize_already_initialized(self):
        """Test initialization when already initialized."""
        manager = ConfigManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            manager.initialize(
                PROMETHEUS_METRICS_PORT="9091",
                PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                GUNICORN_WORKERS="2",
                PROMETHEUS_MULTIPROC_DIR=temp_dir,
            )

            # Try to initialize again
            with pytest.raises(RuntimeError, match="Configuration already initialized"):
                manager.initialize(PROMETHEUS_METRICS_PORT="9092")

    def test_initialize_validation_failure(self):
        """Test initialization with validation failure."""
        manager = ConfigManager()

        # Test with missing required settings
        with pytest.raises(ValueError, match="Configuration validation failed"):
            manager.initialize(
                PROMETHEUS_METRICS_PORT="",  # Empty port should fail
                PROMETHEUS_BIND_ADDRESS="",  # Empty address should fail
                GUNICORN_WORKERS="",  # Empty workers should fail
            )

    def test_get_config_not_initialized(self):
        """Test getting config when not initialized."""
        manager = ConfigManager()

        with pytest.raises(RuntimeError, match="Configuration not initialized"):
            manager.get_config()

    def test_get_config_wrong_state(self):
        """Test getting config in wrong state."""
        manager = ConfigManager()

        # Manually set state to error
        manager._state = ConfigState.ERROR

        with pytest.raises(RuntimeError, match="Configuration not initialized"):
            manager.get_config()

    def test_update_config_success(self):
        """Test successful configuration update."""
        manager = ConfigManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            manager.initialize(
                PROMETHEUS_METRICS_PORT="9091",
                PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                GUNICORN_WORKERS="2",
                PROMETHEUS_MULTIPROC_DIR=temp_dir,
            )

            # Update configuration
            manager.update_config(PROMETHEUS_METRICS_PORT="9092")

            assert manager.state == ConfigState.INITIALIZED
            config = manager.get_config()
            assert config.prometheus_metrics_port == 9092

    def test_update_config_not_initialized(self):
        """Test updating config when not initialized."""
        manager = ConfigManager()

        with pytest.raises(RuntimeError, match="Configuration not initialized"):
            manager.update_config(PROMETHEUS_METRICS_PORT="9092")

    def test_reload_config_success(self):
        """Test successful configuration reload."""
        manager = ConfigManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            manager.initialize(
                PROMETHEUS_METRICS_PORT="9091",
                PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                GUNICORN_WORKERS="2",
                PROMETHEUS_MULTIPROC_DIR=temp_dir,
            )

            # Change environment variable
            os.environ["PROMETHEUS_METRICS_PORT"] = "9093"

            # Reload configuration
            manager.reload_config()

            assert manager.state == ConfigState.INITIALIZED
            config = manager.get_config()
            assert config.prometheus_metrics_port == 9093

    def test_cleanup(self):
        """Test configuration cleanup."""
        manager = ConfigManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            manager.initialize(
                PROMETHEUS_METRICS_PORT="9091",
                PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                GUNICORN_WORKERS="2",
                PROMETHEUS_MULTIPROC_DIR=temp_dir,
            )

            assert manager.is_initialized

            # Cleanup
            manager.cleanup()

            assert manager.state == ConfigState.UNINITIALIZED
            assert not manager.is_initialized
            assert manager._config is None

    def test_reset(self):
        """Test configuration reset."""
        manager = ConfigManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            manager.initialize(
                PROMETHEUS_METRICS_PORT="9091",
                PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                GUNICORN_WORKERS="2",
                PROMETHEUS_MULTIPROC_DIR=temp_dir,
            )

            # Reset
            manager.reset()

            assert manager.state == ConfigState.UNINITIALIZED
            assert not manager.is_initialized

    def test_get_config_summary(self):
        """Test getting configuration summary."""
        manager = ConfigManager()

        # Test uninitialized state
        summary = manager.get_config_summary()
        assert summary["state"] == ConfigState.UNINITIALIZED.value
        assert not summary["initialized"]

        # Test initialized state
        with tempfile.TemporaryDirectory() as temp_dir:
            manager.initialize(
                PROMETHEUS_METRICS_PORT="9091",
                PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                GUNICORN_WORKERS="2",
                PROMETHEUS_MULTIPROC_DIR=temp_dir,
            )

            summary = manager.get_config_summary()
            assert summary["state"] == ConfigState.INITIALIZED.value
            assert summary["initialized"]
            assert summary["prometheus_port"] == 9091
            assert summary["gunicorn_workers"] == 2

    def test_health_check_healthy(self):
        """Test health check when healthy."""
        manager = ConfigManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            manager.initialize(
                PROMETHEUS_METRICS_PORT="9091",
                PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                GUNICORN_WORKERS="2",
                PROMETHEUS_MULTIPROC_DIR=temp_dir,
            )

            health = manager.health_check()
            assert health["healthy"]
            assert health["state"] == ConfigState.INITIALIZED.value
            assert health["errors"] == []

    def test_health_check_unhealthy(self):
        """Test health check when unhealthy."""
        manager = ConfigManager()

        # Test not initialized
        health = manager.health_check()
        assert not health["healthy"]
        assert "Configuration not initialized" in health["errors"]

    def test_redis_validation_success(self):
        """Test Redis validation when Redis is enabled and working."""
        manager = ConfigManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("redis.Redis") as mock_redis:
                mock_client = MagicMock()
                mock_client.ping.return_value = True
                mock_redis.return_value = mock_client

                manager.initialize(
                    PROMETHEUS_METRICS_PORT="9091",
                    PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                    GUNICORN_WORKERS="2",
                    PROMETHEUS_MULTIPROC_DIR=temp_dir,
                    REDIS_ENABLED="true",
                    REDIS_HOST="localhost",
                    REDIS_PORT="6379",
                )

                assert manager.state == ConfigState.INITIALIZED
                mock_redis.assert_called_once()
                mock_client.ping.assert_called_once()

    def test_redis_validation_failure(self):
        """Test Redis validation when Redis connection fails."""
        manager = ConfigManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("redis.Redis") as mock_redis:
                mock_client = MagicMock()
                mock_client.ping.side_effect = Exception("Connection failed")
                mock_redis.return_value = mock_client

                with pytest.raises(ValueError, match="Cannot connect to Redis"):
                    manager.initialize(
                        PROMETHEUS_METRICS_PORT="9091",
                        PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                        GUNICORN_WORKERS="2",
                        PROMETHEUS_MULTIPROC_DIR=temp_dir,
                        REDIS_ENABLED="true",
                        REDIS_HOST="localhost",
                        REDIS_PORT="6379",
                    )

    def test_thread_safety(self):
        """Test thread safety of ConfigManager."""
        manager = ConfigManager()
        results = []
        errors = []

        def worker():
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    manager.initialize(
                        PROMETHEUS_METRICS_PORT="9091",
                        PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                        GUNICORN_WORKERS="2",
                        PROMETHEUS_MULTIPROC_DIR=temp_dir,
                    )
                    config = manager.get_config()
                    results.append(config.prometheus_metrics_port)
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should have some results and some errors (due to double initialization)
        assert len(results) > 0
        assert len(errors) > 0
        assert all(result == 9091 for result in results)


class TestGlobalConfigManager:
    """Test global configuration manager functions."""

    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns singleton."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()

        assert manager1 is manager2

    def test_initialize_config(self):
        """Test global initialize_config function."""
        # Clean up first
        cleanup_config()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                initialize_config(
                    PROMETHEUS_METRICS_PORT="9091",
                    PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                    GUNICORN_WORKERS="2",
                    PROMETHEUS_MULTIPROC_DIR=temp_dir,
                )

                manager = get_config_manager()
                assert manager.is_initialized
        finally:
            # Always cleanup to prevent leaving singleton pointing at deleted temp dir
            cleanup_config()
            # Re-initialize with session-scoped temp dir for other tests
            try:
                initialize_config(
                    PROMETHEUS_METRICS_PORT="9091",
                    PROMETHEUS_BIND_ADDRESS="127.0.0.1",
                    GUNICORN_WORKERS="2",
                    PROMETHEUS_MULTIPROC_DIR=os.environ.get("PROMETHEUS_MULTIPROC_DIR"),
                )
            except RuntimeError as e:
                if "Configuration already initialized" in str(e):
                    # Config is already initialized, that's fine
                    pass
                else:
                    raise

    def test_get_config_global(self):
        """Test global get_config function."""
        # Clean up first
        cleanup_config()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                initialize_config(
                    PROMETHEUS_METRICS_PORT="9091",
                    PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                    GUNICORN_WORKERS="2",
                    PROMETHEUS_MULTIPROC_DIR=temp_dir,
                )

                config = get_config()
                assert config.prometheus_metrics_port == 9091
        finally:
            # Always cleanup to prevent leaving singleton pointing at deleted temp dir
            cleanup_config()
            # Re-initialize with session-scoped temp dir for other tests
            try:
                initialize_config(
                    PROMETHEUS_METRICS_PORT="9091",
                    PROMETHEUS_BIND_ADDRESS="127.0.0.1",
                    GUNICORN_WORKERS="2",
                    PROMETHEUS_MULTIPROC_DIR=os.environ.get("PROMETHEUS_MULTIPROC_DIR"),
                )
            except RuntimeError as e:
                if "Configuration already initialized" in str(e):
                    # Config is already initialized, that's fine
                    pass
                else:
                    raise

    def test_cleanup_config(self):
        """Test global cleanup_config function."""
        # Clean up first
        cleanup_config()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                initialize_config(
                    PROMETHEUS_METRICS_PORT="9091",
                    PROMETHEUS_BIND_ADDRESS="0.0.0.0",
                    GUNICORN_WORKERS="2",
                    PROMETHEUS_MULTIPROC_DIR=temp_dir,
                )

                manager = get_config_manager()
                assert manager.is_initialized

                cleanup_config()

                # Get new manager instance
                manager = get_config_manager()
                assert not manager.is_initialized
        finally:
            # Always cleanup to prevent leaving singleton pointing at deleted temp dir
            cleanup_config()
            # Re-initialize with session-scoped temp dir for other tests
            try:
                initialize_config(
                    PROMETHEUS_METRICS_PORT="9091",
                    PROMETHEUS_BIND_ADDRESS="127.0.0.1",
                    GUNICORN_WORKERS="2",
                    PROMETHEUS_MULTIPROC_DIR=os.environ.get("PROMETHEUS_MULTIPROC_DIR"),
                )
            except RuntimeError as e:
                if "Configuration already initialized" in str(e):
                    # Config is already initialized, that's fine
                    pass
                else:
                    raise

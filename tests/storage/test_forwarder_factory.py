"""Unit tests for forwarder factory components."""

import os

from unittest.mock import Mock, patch

from gunicorn_prometheus_exporter.storage.redis_manager import (
    ForwarderConfig,
    ForwarderFactory,
    ForwarderManager,
    create_redis_forwarder,
    get_forwarder_manager,
)


class TestForwarderConfig:
    """Test ForwarderConfig class."""

    def test_init_default(self):
        """Test initialization with default values."""
        config = ForwarderConfig(name="test", forwarder_type="redis")

        assert config.name == "test"
        assert config.forwarder_type == "redis"
        assert config.enabled is True
        assert config.config == {}

    def test_init_custom(self):
        """Test initialization with custom values."""
        config = ForwarderConfig(
            name="custom",
            forwarder_type="custom",
            enabled=False,
            config={"host": "redis.example.com", "port": 6380},
        )

        assert config.name == "custom"
        assert config.forwarder_type == "custom"
        assert config.enabled is False
        assert config.config["host"] == "redis.example.com"
        assert config.config["port"] == 6380

    def test_config_validation(self):
        """Test configuration validation."""
        config = ForwarderConfig(name="test", forwarder_type="redis")

        # Test that config is properly initialized
        assert config.config is not None
        assert isinstance(config.config, dict)


class TestForwarderFactory:
    """Test ForwarderFactory class."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["REDIS_ENABLED"] = "true"

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.pop("REDIS_ENABLED", None)

    def test_init(self):
        """Test initialization."""
        factory = ForwarderFactory()

        # ForwarderFactory automatically registers Redis forwarder
        assert "redis" in factory._forwarder_types
        assert isinstance(factory._forwarder_types, dict)

    def test_register_forwarder_type(self):
        """Test registering a forwarder type."""
        factory = ForwarderFactory()
        mock_forwarder_class = Mock()

        factory.register_forwarder_type("test", mock_forwarder_class)

        assert "test" in factory._forwarder_types
        assert factory._forwarder_types["test"] == mock_forwarder_class

    def test_get_forwarder_type(self):
        """Test getting a forwarder type."""
        factory = ForwarderFactory()

        result = factory._forwarder_types.get("redis")

        assert result is not None

    def test_get_forwarder_type_not_found(self):
        """Test getting non-existent forwarder type."""
        factory = ForwarderFactory()

        result = factory._forwarder_types.get("nonexistent")

        assert result is None

    @patch(
        "gunicorn_prometheus_exporter.storage.metrics_forwarder.redis_forwarder.RedisForwarder"
    )
    def test_create_forwarder_success(self, mock_redis_forwarder):
        """Test successful forwarder creation."""
        mock_instance = Mock()
        mock_redis_forwarder.return_value = mock_instance

        factory = ForwarderFactory()
        factory.register_forwarder_type("redis", mock_redis_forwarder)

        config = ForwarderConfig(name="redis", forwarder_type="redis")
        result = factory.create_forwarder(config)

        assert result == mock_instance
        mock_redis_forwarder.assert_called_once()

    def test_create_forwarder_type_not_found(self):
        """Test creating forwarder with unknown type."""
        factory = ForwarderFactory()
        config = ForwarderConfig(name="test", forwarder_type="unknown")

        result = factory.create_forwarder(config)

        assert result is None

    @patch(
        "gunicorn_prometheus_exporter.storage.metrics_forwarder.redis_forwarder.RedisForwarder"
    )
    def test_create_forwarder_multiple_calls(self, mock_redis_forwarder):
        """Test creating multiple forwarders."""
        mock_instance = Mock()
        mock_redis_forwarder.return_value = mock_instance

        factory = ForwarderFactory()
        factory.register_forwarder_type("redis", mock_redis_forwarder)

        config = ForwarderConfig(name="redis", forwarder_type="redis")

        # Create first instance
        result1 = factory.create_forwarder(config)

        # Create second instance (creates new instance)
        result2 = factory.create_forwarder(config)

        assert result1 is not None
        assert result2 is not None
        # Each call creates a new instance
        assert mock_redis_forwarder.call_count == 2

    @patch(
        "gunicorn_prometheus_exporter.storage.metrics_forwarder.redis_forwarder.RedisForwarder"
    )
    def test_create_forwarder_error(self, mock_redis_forwarder):
        """Test forwarder creation with error."""
        mock_redis_forwarder.side_effect = Exception("Creation failed")

        factory = ForwarderFactory()
        factory.register_forwarder_type("redis", mock_redis_forwarder)

        config = ForwarderConfig(name="redis", forwarder_type="redis")

        result = factory.create_forwarder(config)

        assert result is None

    def test_get_available_types(self):
        """Test getting available forwarder types."""
        factory = ForwarderFactory()

        types = factory.get_available_types()

        assert "redis" in types
        assert isinstance(types, list)


class TestForwarderManager:
    """Test ForwarderManager class."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["REDIS_ENABLED"] = "true"

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.pop("REDIS_ENABLED", None)

    def test_init(self):
        """Test initialization."""
        manager = ForwarderManager()

        assert manager._factory is not None
        assert manager._forwarders == {}

    def test_add_forwarder(self):
        """Test adding a forwarder."""
        manager = ForwarderManager()
        mock_forwarder = Mock()

        manager.add_forwarder("test", mock_forwarder)

        assert "test" in manager._forwarders
        assert manager._forwarders["test"] == mock_forwarder

    def test_remove_forwarder(self):
        """Test removing a forwarder."""
        manager = ForwarderManager()
        mock_forwarder = Mock()
        manager._forwarders["test"] = mock_forwarder

        manager.remove_forwarder("test")

        assert "test" not in manager._forwarders

    def test_get_forwarder(self):
        """Test getting a forwarder."""
        manager = ForwarderManager()
        mock_forwarder = Mock()
        manager._forwarders["test"] = mock_forwarder

        result = manager.get_forwarder("test")

        assert result == mock_forwarder

    def test_get_forwarder_not_found(self):
        """Test getting non-existent forwarder."""
        manager = ForwarderManager()

        result = manager.get_forwarder("nonexistent")

        assert result is None

    def test_start_all(self):
        """Test starting all forwarders."""
        manager = ForwarderManager()
        mock_forwarder1 = Mock()
        mock_forwarder1.start.return_value = True
        mock_forwarder2 = Mock()
        mock_forwarder2.start.return_value = True
        manager._forwarders["test1"] = mock_forwarder1
        manager._forwarders["test2"] = mock_forwarder2

        result = manager.start_all()

        assert result is True
        mock_forwarder1.start.assert_called_once()
        mock_forwarder2.start.assert_called_once()

    def test_stop_all(self):
        """Test stopping all forwarders."""
        manager = ForwarderManager()
        mock_forwarder1 = Mock()
        mock_forwarder2 = Mock()
        manager._forwarders["test1"] = mock_forwarder1
        manager._forwarders["test2"] = mock_forwarder2

        manager.stop_all()

        mock_forwarder1.stop.assert_called_once()
        mock_forwarder2.stop.assert_called_once()

    @patch("gunicorn_prometheus_exporter.storage.redis_manager.ForwarderFactory")
    def test_create_from_config(self, mock_factory_class):
        """Test creating forwarder from config."""
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_forwarder = Mock()
        mock_factory.create_forwarder.return_value = mock_forwarder

        manager = ForwarderManager()
        config = ForwarderConfig(name="redis", forwarder_type="redis")

        result = manager.create_forwarder(config)

        assert result is True


class TestModuleFunctions:
    """Test module-level functions."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["REDIS_ENABLED"] = "true"

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.pop("REDIS_ENABLED", None)

    def test_get_forwarder_manager(self):
        """Test get_forwarder_manager function."""
        result = get_forwarder_manager()

        assert isinstance(result, ForwarderManager)
        assert result._factory is not None

    @patch("gunicorn_prometheus_exporter.storage.redis_manager.ForwarderFactory")
    @patch(
        "gunicorn_prometheus_exporter.storage.metrics_forwarder.redis_forwarder.RedisForwarder"
    )
    def test_create_redis_forwarder(self, mock_redis_forwarder, mock_factory_class):
        """Test create_redis_forwarder function."""
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_instance = Mock()
        mock_factory.create_forwarder.return_value = mock_instance

        result = create_redis_forwarder()

        assert result is True


class TestForwarderFactoryIntegration:
    """Integration tests for forwarder factory components."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["REDIS_ENABLED"] = "true"

    def teardown_method(self):
        """Clean up test environment."""
        os.environ.pop("REDIS_ENABLED", None)

    @patch(
        "gunicorn_prometheus_exporter.storage.metrics_forwarder.redis_forwarder.RedisForwarder"
    )
    def test_factory_lifecycle(self, mock_redis_forwarder):
        """Test ForwarderFactory complete lifecycle."""
        mock_instance = Mock()
        mock_redis_forwarder.return_value = mock_instance

        factory = ForwarderFactory()
        factory.register_forwarder_type("redis", mock_redis_forwarder)

        # Test configuration
        config = ForwarderConfig(name="redis", forwarder_type="redis")

        # Test creation
        result = factory.create_forwarder(config)
        assert result == mock_instance

        # Test caching
        result2 = factory.create_forwarder(config)
        assert result == result2

        # Test supported types
        types = factory.get_available_types()
        assert "redis" in types

    def test_manager_integration(self):
        """Test ForwarderManager integration."""
        manager = ForwarderManager()
        mock_forwarder1 = Mock()
        mock_forwarder1.forward.return_value = True
        mock_forwarder2 = Mock()
        mock_forwarder2.forward.return_value = True

        # Test adding forwarders
        manager.add_forwarder("test1", mock_forwarder1)
        manager.add_forwarder("test2", mock_forwarder2)

        # Test start all
        manager.start_all()

        # Test stop all
        manager.stop_all()

        # Test removal
        manager.remove_forwarder("test1")
        assert "test1" not in manager._forwarders

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        # Test that ForwarderConfig can be created with environment-based values
        config = ForwarderConfig(
            name="env_test",
            forwarder_type="redis",
            config={"host": "localhost", "port": 6379},
        )

        assert config.name == "env_test"
        assert config.forwarder_type == "redis"
        assert config.config["host"] == "localhost"

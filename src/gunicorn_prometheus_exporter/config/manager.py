"""Configuration manager for Gunicorn Prometheus Exporter with lifecycle management."""

import logging
import os
import threading
import time

from enum import Enum
from typing import Any, Dict, List, Optional

from .settings import ExporterConfig


logger = logging.getLogger(__name__)


class ConfigState(Enum):
    """Configuration lifecycle states."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    VALIDATING = "validating"
    UPDATING = "updating"
    CLEANUP = "cleanup"
    ERROR = "error"


class ConfigManager:
    """Manages configuration lifecycle with proper state management and validation."""

    def __init__(self):
        """Initialize the configuration manager."""
        self._config: Optional[ExporterConfig] = None
        self._state = ConfigState.UNINITIALIZED
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._validation_errors: List[str] = []
        self._initialization_time: Optional[float] = None

    @property
    def state(self) -> ConfigState:
        """Get current configuration state."""
        return self._state

    @property
    def is_initialized(self) -> bool:
        """Check if configuration is initialized."""
        return self._state == ConfigState.INITIALIZED

    @property
    def validation_errors(self) -> List[str]:
        """Get list of validation errors."""
        return self._validation_errors.copy()

    def initialize(self, config_file: Optional[str] = None, **kwargs) -> None:
        """Initialize configuration with proper lifecycle management.

        Args:
            config_file: Optional path to YAML configuration file
            **kwargs: Environment variable overrides
        """
        with self._lock:
            if self._state == ConfigState.INITIALIZED:
                raise RuntimeError("Configuration already initialized")

            if self._state == ConfigState.INITIALIZING:
                raise RuntimeError("Configuration initialization in progress")

            try:
                self._state = ConfigState.INITIALIZING
                logger.info("Initializing configuration...")

                # Load YAML configuration first if provided
                if config_file:
                    from .loader import load_yaml_config

                    load_yaml_config(config_file)
                    logger.info("YAML configuration loaded from: %s", config_file)

                # Set environment variables if provided (these override YAML values)
                for key, value in kwargs.items():
                    if value is None:
                        continue
                    os.environ[key] = str(value)

                # Create configuration instance
                self._config = ExporterConfig()
                self._initialization_time = time.time()

                # Validate configuration
                self._validate_config()

                self._state = ConfigState.INITIALIZED
                logger.info("Configuration initialized successfully")

            except Exception as e:
                self._state = ConfigState.ERROR
                logger.error("Configuration initialization failed: %s", e)
                self._cleanup()
                raise

    def _validate_config(self) -> None:
        """Validate configuration state and requirements."""
        with self._lock:
            if not self._config:
                raise RuntimeError("Configuration not initialized")

            self._state = ConfigState.VALIDATING
            self._validation_errors.clear()

            try:
                # Validate required settings
                self._validate_required_settings()

                # Validate Redis settings if enabled
                if self._config.redis_enabled:
                    self._validate_redis_settings()

                # Validate SSL settings if configured
                self._validate_ssl_settings()

                if self._validation_errors:
                    errors = ", ".join(self._validation_errors)
                    raise ValueError(f"Configuration validation failed: {errors}")

            except Exception:
                self._state = ConfigState.ERROR
                raise

    def _validate_required_settings(self) -> None:
        """Validate required configuration settings (delegates to ExporterConfig)."""
        config = self._config
        # Keep directory readiness check
        try:
            os.makedirs(config.prometheus_multiproc_dir, exist_ok=True)
        except Exception as e:
            self._validation_errors.append(f"Cannot create multiprocess directory: {e}")
            return
        # Delegate full validation (port ranges, workers, timeouts, etc.)
        if not config.validate():
            self._validation_errors.append(
                "Base exporter configuration invalid (see logs)"
            )

    def _validate_redis_settings(self) -> None:
        """Validate Redis configuration settings."""
        config = self._config

        if not config.redis_host:
            self._validation_errors.append(
                "REDIS_HOST must be set when Redis is enabled"
            )

        if not config.redis_port:
            self._validation_errors.append(
                "REDIS_PORT must be set when Redis is enabled"
            )

        # Test Redis connection if possible
        try:
            import redis

            client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                password=config.redis_password,
                socket_timeout=5.0,
            )
            client.ping()
        except ImportError:
            self._validation_errors.append("Redis client not available")
        except Exception as e:
            self._validation_errors.append(f"Cannot connect to Redis: {e}")

    def _validate_ssl_settings(self) -> None:
        """Validate SSL configuration settings."""
        # Check if SSL is configured
        ssl_cert = os.environ.get("PROMETHEUS_SSL_CERTFILE")
        ssl_key = os.environ.get("PROMETHEUS_SSL_KEYFILE")

        if ssl_cert and not ssl_key:
            self._validation_errors.append(
                "SSL key file required when certificate is provided"
            )

        if ssl_key and not ssl_cert:
            self._validation_errors.append(
                "SSL certificate file required when key is provided"
            )

        # Validate SSL files exist
        if ssl_cert and not os.path.exists(ssl_cert):
            self._validation_errors.append(
                f"SSL certificate file not found: {ssl_cert}"
            )

        if ssl_key and not os.path.exists(ssl_key):
            self._validation_errors.append(f"SSL key file not found: {ssl_key}")

    def get_config(self) -> ExporterConfig:
        """Get the configuration instance with state validation."""
        with self._lock:
            if not self._config:
                raise RuntimeError("Configuration not initialized")

            if self._state != ConfigState.INITIALIZED:
                raise RuntimeError(
                    f"Configuration not ready (state: {self._state.value})"
                )

            return self._config

    def update_config(self, **kwargs) -> None:
        """Update configuration with validation."""
        with self._lock:
            if not self._config:
                raise RuntimeError("Configuration not initialized")

            if self._state != ConfigState.INITIALIZED:
                raise RuntimeError(
                    f"Cannot update configuration (state: {self._state.value})"
                )

            try:
                self._state = ConfigState.UPDATING
                logger.info("Updating configuration...")

                # Update environment variables
                for key, value in kwargs.items():
                    if value is None:
                        continue
                    os.environ[key] = str(value)
                    logger.debug("Updated environment variable: %s", key)

                # Revalidate configuration
                self._validate_config()

                self._state = ConfigState.INITIALIZED
                logger.info("Configuration updated successfully")

            except Exception as e:
                self._state = ConfigState.ERROR
                logger.error("Configuration update failed: %s", e)
                raise

    def reload_config(self) -> None:
        """Reload configuration from environment variables."""
        with self._lock:
            if not self._config:
                raise RuntimeError("Configuration not initialized")

            try:
                self._state = ConfigState.UPDATING
                logger.info("Reloading configuration...")

                # Create new configuration instance
                self._config = ExporterConfig()

                # Revalidate
                self._validate_config()

                self._state = ConfigState.INITIALIZED
                logger.info("Configuration reloaded successfully")

            except Exception as e:
                self._state = ConfigState.ERROR
                logger.error("Configuration reload failed: %s", e)
                raise

    def cleanup(self) -> None:
        """Clean up configuration resources."""
        with self._lock:
            if self._state == ConfigState.UNINITIALIZED:
                return

            try:
                self._state = ConfigState.CLEANUP
                logger.info("Cleaning up configuration...")

                self._cleanup()

                logger.info("Configuration cleanup completed")

            except Exception as e:
                logger.error("Configuration cleanup failed: %s", e)
                self._state = ConfigState.ERROR
                raise

    def _cleanup(self) -> None:
        """Internal cleanup method."""
        self._config = None
        self._validation_errors.clear()
        self._initialization_time = None
        self._state = ConfigState.UNINITIALIZED

    def reset(self) -> None:
        """Reset configuration manager to initial state."""
        with self._lock:
            self._cleanup()
            logger.info("Configuration manager reset")

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging."""
        with self._lock:
            if not self._config:
                return {"state": self._state.value, "initialized": False}

            return {
                "state": self._state.value,
                "initialized": True,
                "initialization_time": self._initialization_time,
                "validation_errors": self._validation_errors,
                "prometheus_port": self._config.prometheus_metrics_port,
                "redis_enabled": self._config.redis_enabled,
                "gunicorn_workers": self._config.gunicorn_workers,
            }

    def health_check(self) -> Dict[str, Any]:
        """Perform configuration health check."""
        with self._lock:
            health = {"healthy": False, "state": self._state.value, "errors": []}

            try:
                if not self._config:
                    health["errors"].append("Configuration not initialized")
                    return health

                if self._state != ConfigState.INITIALIZED:
                    health["errors"].append(
                        f"Configuration not ready (state: {self._state.value})"
                    )
                    return health

                # Test multiprocess directory
                try:
                    os.makedirs(self._config.prometheus_multiproc_dir, exist_ok=True)
                except Exception as e:
                    health["errors"].append(f"Multiprocess directory error: {e}")

                # Test Redis connection if enabled
                if self._config.redis_enabled:
                    try:
                        import redis

                        client = redis.Redis(
                            host=self._config.redis_host,
                            port=self._config.redis_port,
                            password=self._config.redis_password,
                            socket_timeout=5.0,
                        )
                        client.ping()
                    except Exception as e:
                        health["errors"].append(f"Redis connection error: {e}")

                health["healthy"] = len(health["errors"]) == 0

            except Exception as e:
                health["errors"].append(f"Health check failed: {e}")

            return health


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None
_manager_lock = threading.Lock()


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager

    with _manager_lock:
        if _config_manager is None:
            _config_manager = ConfigManager()
        return _config_manager


def initialize_config(config_file: Optional[str] = None, **kwargs) -> None:
    """Initialize the global configuration.

    Args:
        config_file: Optional path to YAML configuration file
        **kwargs: Environment variable overrides
    """
    manager = get_config_manager()
    manager.initialize(config_file=config_file, **kwargs)


def get_config() -> ExporterConfig:
    """Get the global configuration instance."""
    manager = get_config_manager()
    return manager.get_config()


def cleanup_config() -> None:
    """Clean up the global configuration."""
    global _config_manager

    with _manager_lock:
        if _config_manager:
            _config_manager.cleanup()
            _config_manager = None

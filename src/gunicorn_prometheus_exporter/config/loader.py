"""YAML configuration loader for Gunicorn Prometheus Exporter."""

import logging
import os

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


logger = logging.getLogger(__name__)


class YamlConfigLoader:
    """Loads and validates YAML configuration files."""

    def __init__(self):
        """Initialize the YAML configuration loader."""
        self.logger = logging.getLogger(__name__)

    def load_config_file(self, config_file_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Args:
            config_file_path: Path to the YAML configuration file

        Returns:
            Dictionary containing the configuration

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the configuration structure is invalid
        """
        config_path = Path(config_file_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file_path}")

        if not config_path.is_file():
            raise ValueError(f"Path is not a file: {config_file_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config_data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in configuration file: {e}") from e

        if not isinstance(config_data, dict):
            raise ValueError(
                "Configuration file must contain a dictionary at the root level"
            )

        # Validate and normalize the configuration structure
        return self._validate_and_normalize_config(config_data)

    def _validate_and_normalize_config(
        self, config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and normalize configuration structure.

        Args:
            config_data: Raw configuration data from YAML

        Returns:
            Normalized configuration dictionary

        Raises:
            ValueError: If the configuration structure is invalid
        """
        self._validate_exporter_section(config_data)
        exporter_config = config_data["exporter"]

        self._validate_prometheus_section(exporter_config)
        self._validate_gunicorn_section(exporter_config)
        self._validate_optional_sections(exporter_config)

        return config_data

    def _validate_exporter_section(self, config_data: Dict[str, Any]) -> None:
        """Validate the main exporter section."""
        if "exporter" not in config_data:
            raise ValueError("Configuration must contain 'exporter' section")

        exporter_config = config_data["exporter"]
        if not isinstance(exporter_config, dict):
            raise ValueError("'exporter' section must be a dictionary")

        # Validate required sections
        required_sections = ["prometheus", "gunicorn"]
        for section in required_sections:
            if section not in exporter_config:
                raise ValueError(f"Missing required section: exporter.{section}")

    def _validate_prometheus_section(self, exporter_config: Dict[str, Any]) -> None:
        """Validate the prometheus section."""
        prometheus_config = exporter_config["prometheus"]
        if not isinstance(prometheus_config, dict):
            raise ValueError("'exporter.prometheus' must be a dictionary")

        required_prometheus_fields = ["metrics_port", "bind_address"]
        for field in required_prometheus_fields:
            if field not in prometheus_config:
                raise ValueError(f"Missing required field: exporter.prometheus.{field}")

        # Validate SSL section if present
        if "ssl" in prometheus_config:
            ssl_config = prometheus_config["ssl"]
            if not isinstance(ssl_config, dict):
                raise ValueError("'exporter.prometheus.ssl' must be a dictionary")

    def _validate_gunicorn_section(self, exporter_config: Dict[str, Any]) -> None:
        """Validate the gunicorn section."""
        gunicorn_config = exporter_config["gunicorn"]
        if not isinstance(gunicorn_config, dict):
            raise ValueError("'exporter.gunicorn' must be a dictionary")

    def _validate_optional_sections(self, exporter_config: Dict[str, Any]) -> None:
        """Validate optional sections like Redis."""
        # Validate Redis section if present
        if "redis" in exporter_config:
            redis_config = exporter_config["redis"]
            if not isinstance(redis_config, dict):
                raise ValueError("'exporter.redis' must be a dictionary")

    def convert_to_environment_variables(
        self, config_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Convert YAML configuration to environment variable format.

        Args:
            config_data: Validated configuration data

        Returns:
            Dictionary of environment variable key-value pairs
        """
        env_vars = {}
        exporter_config = config_data["exporter"]

        self._convert_prometheus_config(exporter_config["prometheus"], env_vars)
        self._convert_gunicorn_config(exporter_config["gunicorn"], env_vars)
        self._convert_redis_config(exporter_config, env_vars)
        self._convert_cleanup_config(exporter_config, env_vars)

        return env_vars

    def _convert_prometheus_config(
        self, prometheus_config: Dict[str, Any], env_vars: Dict[str, str]
    ) -> None:
        """Convert prometheus configuration to environment variables."""
        if prometheus_config["metrics_port"] is not None:
            env_vars["PROMETHEUS_METRICS_PORT"] = str(prometheus_config["metrics_port"])
        if prometheus_config["bind_address"] is not None:
            env_vars["PROMETHEUS_BIND_ADDRESS"] = str(prometheus_config["bind_address"])

        if (
            "multiproc_dir" in prometheus_config
            and prometheus_config["multiproc_dir"] is not None
        ):
            env_vars["PROMETHEUS_MULTIPROC_DIR"] = str(
                prometheus_config["multiproc_dir"]
            )

        # SSL configuration
        if "ssl" in prometheus_config:
            self._convert_ssl_config(prometheus_config["ssl"], env_vars)

    def _convert_ssl_config(
        self, ssl_config: Dict[str, Any], env_vars: Dict[str, str]
    ) -> None:
        """Convert SSL configuration to environment variables."""
        if not ssl_config.get("enabled", False):
            return

        ssl_mappings = {
            "certfile": "PROMETHEUS_SSL_CERTFILE",
            "keyfile": "PROMETHEUS_SSL_KEYFILE",
            "client_cafile": "PROMETHEUS_SSL_CLIENT_CAFILE",
            "client_capath": "PROMETHEUS_SSL_CLIENT_CAPATH",
        }

        for ssl_key, env_key in ssl_mappings.items():
            if ssl_key in ssl_config and ssl_config[ssl_key] is not None:
                env_vars[env_key] = str(ssl_config[ssl_key])

        if (
            "client_auth_required" in ssl_config
            and ssl_config["client_auth_required"] is not None
        ):
            env_vars["PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED"] = str(
                ssl_config["client_auth_required"]
            ).lower()

    def _convert_gunicorn_config(
        self, gunicorn_config: Dict[str, Any], env_vars: Dict[str, str]
    ) -> None:
        """Convert gunicorn configuration to environment variables."""
        gunicorn_mappings = {
            "workers": "GUNICORN_WORKERS",
            "timeout": "GUNICORN_TIMEOUT",
            "keepalive": "GUNICORN_KEEPALIVE",
        }

        for gunicorn_key, env_key in gunicorn_mappings.items():
            if (
                gunicorn_key in gunicorn_config
                and gunicorn_config[gunicorn_key] is not None
            ):
                env_vars[env_key] = str(gunicorn_config[gunicorn_key])

    def _convert_redis_config(
        self, exporter_config: Dict[str, Any], env_vars: Dict[str, str]
    ) -> None:
        """Convert Redis configuration to environment variables."""
        if "redis" not in exporter_config:
            return

        redis_config = exporter_config["redis"]
        if not redis_config.get("enabled", False):
            return

        env_vars["REDIS_ENABLED"] = "true"

        redis_mappings = {
            "host": "REDIS_HOST",
            "port": "REDIS_PORT",
            "db": "REDIS_DB",
            "key_prefix": "REDIS_KEY_PREFIX",
            "ttl_seconds": "REDIS_TTL_SECONDS",
        }

        for redis_key, env_key in redis_mappings.items():
            if redis_key in redis_config and redis_config[redis_key] is not None:
                env_vars[env_key] = str(redis_config[redis_key])

        # Handle password separately (only if not empty and not None)
        if "password" in redis_config and redis_config["password"] is not None:
            env_vars["REDIS_PASSWORD"] = str(redis_config["password"])

        # Handle ttl_disabled separately (convert to lowercase)
        if "ttl_disabled" in redis_config and redis_config["ttl_disabled"] is not None:
            env_vars["REDIS_TTL_DISABLED"] = str(redis_config["ttl_disabled"]).lower()

    def _convert_cleanup_config(
        self, exporter_config: Dict[str, Any], env_vars: Dict[str, str]
    ) -> None:
        """Convert cleanup configuration to environment variables."""
        if "cleanup" not in exporter_config:
            return

        cleanup_config = exporter_config["cleanup"]
        if "db_files" in cleanup_config and cleanup_config["db_files"] is not None:
            env_vars["CLEANUP_DB_FILES"] = str(cleanup_config["db_files"]).lower()

    def load_and_apply_config(self, config_file_path: str) -> None:
        """Load YAML configuration and apply it to environment variables.

        Args:
            config_file_path: Path to the YAML configuration file

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the configuration structure is invalid
        """
        self.logger.info("Loading configuration from YAML file: %s", config_file_path)

        # Load and validate configuration
        config_data = self.load_config_file(config_file_path)

        # Convert to environment variables
        env_vars = self.convert_to_environment_variables(config_data)

        # Apply environment variables (only if not already set)
        for key, value in env_vars.items():
            if key not in os.environ:
                os.environ[key] = value
                self.logger.debug("Set environment variable: %s=%s", key, value)
            else:
                self.logger.debug("Environment variable already set, skipping: %s", key)

        self.logger.info("Configuration loaded successfully from YAML file")


# Global YAML loader instance
_yaml_loader: Optional[YamlConfigLoader] = None


def get_yaml_loader() -> YamlConfigLoader:
    """Get the global YAML configuration loader instance."""
    global _yaml_loader
    if _yaml_loader is None:
        _yaml_loader = YamlConfigLoader()
    return _yaml_loader


def load_yaml_config(config_file_path: str) -> None:
    """Load configuration from YAML file and apply to environment variables.

    This is the main public API for loading YAML configuration files.

    Args:
        config_file_path: Path to the YAML configuration file

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the YAML file is invalid
        ValueError: If the configuration structure is invalid

    Example:
        >>> from gunicorn_prometheus_exporter.config.loader import load_yaml_config
        >>> load_yaml_config("config.yml")
    """
    loader = get_yaml_loader()
    loader.load_and_apply_config(config_file_path)

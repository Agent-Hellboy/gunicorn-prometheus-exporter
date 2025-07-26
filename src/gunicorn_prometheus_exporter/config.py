"""Configuration management for Gunicorn Prometheus Exporter."""

import logging
import os


logger = logging.getLogger(__name__)


class ExporterConfig:
    """Configuration class for Gunicorn Prometheus Exporter."""

    # Default values (only for development/testing)
    _default_prometheus_dir = os.path.join(
        os.path.expanduser("~"), ".gunicorn_prometheus"
    )
    PROMETHEUS_MULTIPROC_DIR = os.environ.get(
        "PROMETHEUS_MULTIPROC_DIR", _default_prometheus_dir
    )
    # Production settings - no defaults, must be set by user
    PROMETHEUS_METRICS_PORT = None  # Must be set by user in production
    PROMETHEUS_BIND_ADDRESS = None  # Must be set by user in production
    GUNICORN_WORKERS = None  # Must be set by user in production
    GUNICORN_TIMEOUT = os.environ.get("GUNICORN_TIMEOUT", 30)
    GUNICORN_KEEPALIVE = os.environ.get("GUNICORN_KEEPALIVE", 2)

    # Environment variable names
    ENV_PROMETHEUS_MULTIPROC_DIR = "PROMETHEUS_MULTIPROC_DIR"
    ENV_PROMETHEUS_METRICS_PORT = "PROMETHEUS_METRICS_PORT"
    ENV_PROMETHEUS_BIND_ADDRESS = "PROMETHEUS_BIND_ADDRESS"
    ENV_GUNICORN_WORKERS = "GUNICORN_WORKERS"
    ENV_GUNICORN_TIMEOUT = "GUNICORN_TIMEOUT"
    ENV_GUNICORN_KEEPALIVE = "GUNICORN_KEEPALIVE"

    # Redis environment variables
    ENV_REDIS_ENABLED = "REDIS_ENABLED"
    ENV_REDIS_HOST = "REDIS_HOST"
    ENV_REDIS_PORT = "REDIS_PORT"
    ENV_REDIS_DB = "REDIS_DB"
    ENV_REDIS_PASSWORD = "REDIS_PASSWORD"  # nosec - environment variable name
    ENV_REDIS_KEY_PREFIX = "REDIS_KEY_PREFIX"
    ENV_REDIS_FORWARD_INTERVAL = "REDIS_FORWARD_INTERVAL"

    # Cleanup environment variables
    ENV_CLEANUP_DB_FILES = "CLEANUP_DB_FILES"

    def __init__(self):
        """Initialize configuration with environment variables and defaults.

        Note: This modifies os.environ during initialization to set up
        the multiprocess directory if not already set. If you need to
        set environment variables after importing this module, do so
        before creating an ExporterConfig instance.
        """
        self._setup_multiproc_dir()

    def _setup_multiproc_dir(self):
        """Set up the Prometheus multiprocess directory."""
        if not os.environ.get(self.ENV_PROMETHEUS_MULTIPROC_DIR):
            os.environ[
                self.ENV_PROMETHEUS_MULTIPROC_DIR
            ] = self.PROMETHEUS_MULTIPROC_DIR

    @property
    def prometheus_multiproc_dir(self) -> str:
        """Get the Prometheus multiprocess directory path."""
        return os.environ.get(
            self.ENV_PROMETHEUS_MULTIPROC_DIR, self.PROMETHEUS_MULTIPROC_DIR
        )

    @property
    def prometheus_metrics_port(self) -> int:
        """Get the Prometheus metrics server port."""
        value = os.environ.get(
            self.ENV_PROMETHEUS_METRICS_PORT, self.PROMETHEUS_METRICS_PORT
        )
        if value is None:
            raise ValueError(
                f"Environment variable {self.ENV_PROMETHEUS_METRICS_PORT} "
                f"must be set in production. "
                f"Example: export {self.ENV_PROMETHEUS_METRICS_PORT}=9091"
            )
        return int(value)

    @property
    def prometheus_bind_address(self) -> str:
        """Get the Prometheus metrics server bind address."""
        value = os.environ.get(
            self.ENV_PROMETHEUS_BIND_ADDRESS, self.PROMETHEUS_BIND_ADDRESS
        )
        if value is None:
            raise ValueError(
                f"Environment variable {self.ENV_PROMETHEUS_BIND_ADDRESS} "
                f"must be set in production. "
                f"Example: export {self.ENV_PROMETHEUS_BIND_ADDRESS}=0.0.0.0"
            )
        return value

    @property
    def gunicorn_workers(self) -> int:
        """Get the number of Gunicorn workers."""
        value = os.environ.get(self.ENV_GUNICORN_WORKERS, self.GUNICORN_WORKERS)
        if value is None:
            raise ValueError(
                f"Environment variable {self.ENV_GUNICORN_WORKERS} "
                f"must be set in production. "
                f"Example: export {self.ENV_GUNICORN_WORKERS}=4"
            )
        return int(value)

    @property
    def gunicorn_timeout(self) -> int:
        """Get the Gunicorn worker timeout."""
        return int(
            os.environ.get(self.ENV_GUNICORN_TIMEOUT, str(self.GUNICORN_TIMEOUT))
        )

    @property
    def gunicorn_keepalive(self) -> int:
        """Get the Gunicorn keepalive setting."""
        return int(
            os.environ.get(self.ENV_GUNICORN_KEEPALIVE, str(self.GUNICORN_KEEPALIVE))
        )

    # Redis properties
    @property
    def redis_enabled(self) -> bool:
        """Check if Redis forwarding is enabled."""
        return os.environ.get(self.ENV_REDIS_ENABLED, "").lower() in (
            "true",
            "1",
            "yes",
            "on",
        )

    @property
    def redis_host(self) -> str:
        """Get Redis host."""
        return os.environ.get(self.ENV_REDIS_HOST, "localhost")

    @property
    def redis_port(self) -> int:
        """Get Redis port."""
        return int(os.environ.get(self.ENV_REDIS_PORT, "6379"))

    @property
    def redis_db(self) -> int:
        """Get Redis database number."""
        return int(os.environ.get(self.ENV_REDIS_DB, "0"))

    @property
    def redis_password(self) -> str:
        """Get Redis password."""
        return os.environ.get(self.ENV_REDIS_PASSWORD)

    @property
    def redis_key_prefix(self) -> str:
        """Get Redis key prefix."""
        return os.environ.get(self.ENV_REDIS_KEY_PREFIX, "gunicorn:metrics:")

    @property
    def redis_forward_interval(self) -> int:
        """Get Redis forward interval in seconds."""
        return int(os.environ.get(self.ENV_REDIS_FORWARD_INTERVAL, "30"))

    @property
    def cleanup_db_files(self) -> bool:
        """Check if DB file cleanup is enabled."""
        return os.environ.get(self.ENV_CLEANUP_DB_FILES, "true").lower() in (
            "true",
            "1",
            "yes",
            "on",
        )

    def get_gunicorn_config(self) -> dict:
        """Get Gunicorn configuration dictionary."""
        return {
            "bind": "127.0.0.1:8084",
            "workers": self.gunicorn_workers,
            "threads": 1,
            "timeout": self.gunicorn_timeout,
            "keepalive": self.gunicorn_keepalive,
            "worker_class": "gunicorn_prometheus_exporter.plugin.PrometheusWorker",
            "accesslog": "-",
            "errorlog": "-",
            "loglevel": "info",
            "proc_name": "gunicorn-prometheus-exporter",
        }

    def get_prometheus_config(self) -> dict:
        """Get Prometheus metrics server configuration dictionary."""
        return {
            "bind_address": self.prometheus_bind_address,
            "port": self.prometheus_metrics_port,
            "multiproc_dir": self.prometheus_multiproc_dir,
        }

    def validate(self) -> bool:
        """Validate the configuration."""
        try:
            # Check required environment variables for production
            required_vars = [
                (self.ENV_PROMETHEUS_BIND_ADDRESS, "Bind address for metrics server"),
                (self.ENV_PROMETHEUS_METRICS_PORT, "Port for metrics server"),
                (self.ENV_GUNICORN_WORKERS, "Number of Gunicorn workers"),
            ]

            missing_vars = []
            for var_name, description in required_vars:
                if not os.environ.get(var_name):
                    missing_vars.append(f"{var_name} ({description})")

            if missing_vars:
                logger.error("Required environment variables not set:")
                for var in missing_vars:
                    logger.error("   - %s", var)
                logger.error("\n Set these variables before running in production:")
                logger.error("   export %s=0.0.0.0", self.ENV_PROMETHEUS_BIND_ADDRESS)
                logger.error("   export %s=9091", self.ENV_PROMETHEUS_METRICS_PORT)
                logger.error("   export %s=4", self.ENV_GUNICORN_WORKERS)
                return False

            # Validate multiprocess directory
            if not os.path.exists(self.prometheus_multiproc_dir):
                os.makedirs(self.prometheus_multiproc_dir, exist_ok=True)

            # Validate port range
            if not (1024 <= self.prometheus_metrics_port <= 65535):
                raise ValueError(
                    f"Port {self.prometheus_metrics_port} is not in valid range "
                    f"(1024-65535)"
                )

            # Validate worker count
            if self.gunicorn_workers < 1:
                raise ValueError(
                    f"Worker count {self.gunicorn_workers} must be at least 1"
                )

            # Validate timeout
            if self.gunicorn_timeout < 1:
                raise ValueError(
                    f"Timeout {self.gunicorn_timeout} must be at least 1 second"
                )

            return True

        except Exception as e:
            logger.error("Configuration validation failed: %s", e)
            return False

    def print_config(self):
        """Log the current configuration."""
        logger.info("Gunicorn Prometheus Exporter Configuration:")
        logger.info("=" * 50)
        logger.info("Prometheus Multiproc Dir: %s", self.prometheus_multiproc_dir)
        logger.info("Prometheus Metrics Port: %s", self.prometheus_metrics_port)
        logger.info("Prometheus Bind Address: %s", self.prometheus_bind_address)
        logger.info("Gunicorn Workers: %s", self.gunicorn_workers)
        logger.info("Gunicorn Timeout: %s", self.gunicorn_timeout)
        logger.info("Gunicorn Keepalive: %s", self.gunicorn_keepalive)
        logger.info("=" * 50)


# Global configuration instance
config = ExporterConfig()


def get_config() -> ExporterConfig:
    """Get the global configuration instance."""
    return config

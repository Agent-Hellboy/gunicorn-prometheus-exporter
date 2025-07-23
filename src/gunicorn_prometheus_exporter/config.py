"""Configuration management for Gunicorn Prometheus Exporter."""

import os


class ExporterConfig:
    """Configuration class for Gunicorn Prometheus Exporter."""

    # Default values (only for development/testing)
    PROMETHEUS_MULTIPROC_DIR = os.environ.get(
        "PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus"
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

    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        self._setup_multiproc_dir()

    def _setup_multiproc_dir(self):
        """Set up the Prometheus multiprocess directory."""
        if not os.environ.get(self.ENV_PROMETHEUS_MULTIPROC_DIR):
            os.environ[self.ENV_PROMETHEUS_MULTIPROC_DIR] = (
                self.PROMETHEUS_MULTIPROC_DIR
            )

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
            # Default to 9091 for development/testing
            return 9091
        return int(value)

    @property
    def prometheus_bind_address(self) -> str:
        """Get the Prometheus metrics server bind address."""
        value = os.environ.get(
            self.ENV_PROMETHEUS_BIND_ADDRESS, self.PROMETHEUS_BIND_ADDRESS
        )
        if value is None:
            # Default to 127.0.0.1 for development/testing
            return "127.0.0.1"
        return value

    @property
    def gunicorn_workers(self) -> int:
        """Get the number of Gunicorn workers."""
        value = os.environ.get(self.ENV_GUNICORN_WORKERS, self.GUNICORN_WORKERS)
        if value is None:
            # Default to 2 for development/testing
            return 2
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

            # For testing/development, allow missing environment variables
            if missing_vars and os.environ.get("ENVIRONMENT") == "production":
                print("Required environment variables not set:")
                for var in missing_vars:
                    print(f"   - {var}")
                print("\n Set these variables before running in production:")
                print(f"   export {self.ENV_PROMETHEUS_BIND_ADDRESS}=0.0.0.0")
                print(f"   export {self.ENV_PROMETHEUS_METRICS_PORT}=9091")
                print(f"   export {self.ENV_GUNICORN_WORKERS}=4")
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
            print(f"Configuration validation failed: {e}")
            return False

    def print_config(self):
        """Print current configuration."""
        print("Gunicorn Prometheus Exporter Configuration:")
        print("=" * 50)
        print(f"Prometheus Multiproc Dir: {self.prometheus_multiproc_dir}")
        print(f"Prometheus Metrics Port: {self.prometheus_metrics_port}")
        print(f"Prometheus Bind Address: {self.prometheus_bind_address}")
        print(f"Gunicorn Workers: {self.gunicorn_workers}")
        print(f"Gunicorn Timeout: {self.gunicorn_timeout}")
        print(f"Gunicorn Keepalive: {self.gunicorn_keepalive}")
        print("=" * 50)


# Global configuration instance
config = ExporterConfig()


def get_config() -> ExporterConfig:
    """Get the global configuration instance."""
    return config

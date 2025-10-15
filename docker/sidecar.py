#!/usr/bin/env python3
"""
Gunicorn Prometheus Exporter Sidecar

This script runs the Prometheus metrics server as a sidecar container.

Architecture:
- Redis mode: Collects metrics from Redis storage (Kubernetes deployments)
- Multiprocess mode: Collects metrics from shared files (Docker Compose/local development)

Kubernetes deployments MUST use Redis mode - multiprocess files are incompatible
with containerized, multi-pod architectures due to read-only filesystems and
lack of shared storage between pods.

Usage:
    python sidecar.py [--port PORT] [--bind ADDRESS] [--multiproc-dir DIR]

Environment Variables:
    PROMETHEUS_METRICS_PORT: Port for metrics endpoint (default: 9091)
    PROMETHEUS_BIND_ADDRESS: Bind address (default: 0.0.0.0)
    PROMETHEUS_MULTIPROC_DIR: Directory with multiprocess files (default: /tmp/prometheus_multiproc)
    REDIS_ENABLED: Enable Redis storage (default: false)
    REDIS_HOST: Redis host (default: localhost)
    REDIS_PORT: Redis port (default: 6379)
    REDIS_DB: Redis database (default: 0)
    REDIS_PASSWORD: Redis password (optional)
    REDIS_KEY_PREFIX: Redis key prefix (default: gunicorn)
"""

import argparse
import logging
import os
import signal
import sys
import time

from pathlib import Path


# Set sidecar mode environment variable BEFORE importing gunicorn_prometheus_exporter
# This ensures the configuration manager knows we're in sidecar mode
os.environ["SIDECAR_MODE"] = "true"

# Set required environment variables for sidecar mode BEFORE any imports
os.environ["PROMETHEUS_BIND_ADDRESS"] = "0.0.0.0"  # nosec B104
os.environ["PROMETHEUS_METRICS_PORT"] = "9091"
os.environ["GUNICORN_WORKERS"] = "1"  # Dummy value for sidecar mode
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prometheus_multiproc"  # nosec B108

from prometheus_client import CollectorRegistry, Gauge, start_http_server  # noqa: E402
from prometheus_client.multiprocess import MultiProcessCollector  # noqa: E402

from gunicorn_prometheus_exporter.config.settings import ExporterConfig  # noqa: E402


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import our modules
try:
    from gunicorn_prometheus_exporter.backend import (
        get_redis_storage_manager,
        setup_redis_metrics,
        teardown_redis_metrics,
    )
except ImportError as e:
    logger.error("Failed to import gunicorn_prometheus_exporter package: %s", e)
    logger.error(
        "Ensure the package is installed: pip install gunicorn-prometheus-exporter"
    )
    sys.exit(1)


class SidecarMetrics:
    """Additional metrics specific to the sidecar container."""

    def __init__(self, registry: CollectorRegistry):
        self.registry = registry

        # Sidecar-specific metrics
        self.sidecar_uptime = Gauge(
            "gunicorn_sidecar_uptime_seconds",
            "Sidecar container uptime in seconds",
            registry=registry,
        )

        self.sidecar_start_time = time.time()

        # File system metrics
        self.multiproc_dir_size = Gauge(
            "gunicorn_sidecar_multiproc_dir_size_bytes",
            "Size of multiprocess directory in bytes",
            registry=registry,
        )

        self.multiproc_files_count = Gauge(
            "gunicorn_sidecar_multiproc_files_count",
            "Number of files in multiprocess directory",
            registry=registry,
        )

        # Redis connection metrics (if enabled)
        redis_enabled_init = os.getenv("REDIS_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        if redis_enabled_init:
            self.redis_connected = Gauge(
                "gunicorn_sidecar_redis_connected",
                "Redis connection status (1=connected, 0=disconnected)",
                registry=registry,
            )

    def update_metrics(self, multiproc_dir: str):
        """Update sidecar-specific metrics."""
        # Update uptime
        self.sidecar_uptime.set(time.time() - self.sidecar_start_time)

        # File system metrics only relevant for multiprocess mode (non-Kubernetes)
        # In Kubernetes Redis mode, these metrics are irrelevant
        redis_enabled_check = os.getenv("REDIS_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        if not redis_enabled_check:
            try:
                multiproc_path = Path(multiproc_dir)
                if multiproc_path.exists():
                    total_size = sum(
                        f.stat().st_size
                        for f in multiproc_path.rglob("*")
                        if f.is_file()
                    )
                    file_count = len(list(multiproc_path.rglob("*")))

                    self.multiproc_dir_size.set(total_size)
                    self.multiproc_files_count.set(file_count)
                else:
                    self.multiproc_dir_size.set(0)
                    self.multiproc_files_count.set(0)
            except Exception as e:
                logger.warning(f"Failed to update filesystem metrics: {e}")
        else:
            # Kubernetes Redis mode - multiprocess files not applicable
            self.multiproc_dir_size.set(0)
            self.multiproc_files_count.set(0)

        # Update Redis metrics if enabled
        if redis_enabled_check and hasattr(self, "redis_connected"):
            try:
                redis_manager = get_redis_storage_manager()
                if redis_manager and redis_manager.is_connected():
                    self.redis_connected.set(1)
                else:
                    self.redis_connected.set(0)
            except Exception as e:
                logger.warning(f"Failed to update Redis metrics: {e}")
                self.redis_connected.set(0)


def setup_metrics_server(
    port: int, bind_address: str, multiproc_dir: str
) -> CollectorRegistry:
    """Set up the Prometheus metrics server."""
    logger.info(f"Setting up metrics server on {bind_address}:{port}")

    # Create registry
    registry = CollectorRegistry()

    # Disable multiprocess mode when using Redis
    redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() in ("true", "1", "yes")
    if redis_enabled:
        try:
            from prometheus_client import disable_created_metrics

            disable_created_metrics()
            logger.info("Disabled multiprocess metrics creation for Redis mode")
        except Exception as e:
            logger.warning(f"Failed to disable multiprocess metrics: {e}")

    # Choose appropriate collector based on storage backend
    redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() in ("true", "1", "yes")
    if redis_enabled:
        # Use Redis-backed multiprocess collector for Kubernetes deployments
        try:
            from gunicorn_prometheus_exporter.backend import (
                RedisMultiProcessCollector,
                get_redis_client,
            )

            redis_client = get_redis_client()
            if redis_client:
                RedisMultiProcessCollector(registry, redis_client=redis_client)
                logger.info(
                    "Redis multiprocess collector initialized with configured client"
                )
            else:
                logger.warning(
                    "Redis client not available, skipping Redis multiprocess collector"
                )
        except Exception as e:
            logger.error(f"Failed to initialize Redis multiprocess collector: {e}")
            # Continue without collector
    else:
        # Use traditional multiprocess collector for local/docker deployments
        try:
            MultiProcessCollector(registry, multiproc_dir)
            logger.info(
                f"Multiprocess collector initialized with directory: {multiproc_dir}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize multiprocess collector: {e}")
            # Continue without multiprocess collector

    # Set up Redis if enabled
    if redis_enabled:
        try:
            setup_redis_metrics()
            logger.info("Redis metrics setup completed")

            # Add Redis collector to registry for reading stored metrics
            from gunicorn_prometheus_exporter.backend import get_redis_collector

            redis_collector = get_redis_collector()
            if redis_collector:
                registry.register(redis_collector)
                logger.info("Redis collector registered")
            else:
                logger.warning("Redis collector not available")
        except Exception as e:
            logger.error(f"Failed to setup Redis metrics: {e}")
    else:
        logger.info("Redis not enabled, skipping Redis metrics setup")

    # Add sidecar-specific metrics
    sidecar_metrics = SidecarMetrics(registry)

    # Start HTTP server (daemon thread, no cleanup needed)
    start_http_server(port, addr=bind_address, registry=registry)
    logger.info(f"Metrics server started on {bind_address}:{port}")

    return registry, sidecar_metrics


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")

    # Cleanup Redis if enabled
    redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() in ("true", "1", "yes")
    if redis_enabled:
        try:
            teardown_redis_metrics()
            logger.info("Redis metrics teardown completed")
        except Exception as e:
            logger.error(f"Failed to teardown Redis metrics: {e}")

    # HTTP server is a daemon thread and will stop automatically
    sys.exit(0)


def run_sidecar_mode(args: argparse.Namespace):
    """Run the sidecar mode."""
    # Environment variables are already set at module level
    # Update with command line arguments if provided
    if args.bind != "0.0.0.0":  # nosec B104
        os.environ["PROMETHEUS_BIND_ADDRESS"] = args.bind
    if args.port != 9091:
        os.environ["PROMETHEUS_METRICS_PORT"] = str(args.port)

    # Check if Redis is enabled (for Kubernetes mode)
    redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() in ("true", "1", "yes")

    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Create multiprocess directory only if Redis is not enabled
    if not redis_enabled:
        multiproc_path = Path(args.multiproc_dir)
        if not multiproc_path.exists():
            logger.info(f"Creating multiprocess directory: {args.multiproc_dir}")
            multiproc_path.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(f"Multiprocess directory exists: {args.multiproc_dir}")
    else:
        logger.info(
            "Kubernetes Redis mode - skipping multiprocess directory creation for security"
        )

    # Set up metrics server
    try:
        registry, sidecar_metrics = setup_metrics_server(
            args.port, args.bind, args.multiproc_dir
        )
        logger.info("Sidecar started successfully")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        sys.exit(1)

    # Main loop
    logger.info(
        "Sidecar running, updating metrics every {} seconds".format(
            args.update_interval
        )
    )
    try:
        while True:
            # Update sidecar-specific metrics
            sidecar_metrics.update_metrics(args.multiproc_dir)

            # Sleep until next update
            time.sleep(args.update_interval)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        sys.exit(1)
    finally:
        signal_handler(signal.SIGTERM, None)


def run_standalone_mode(args: argparse.Namespace):
    """Run the standalone mode."""
    # Set sidecar mode environment variable
    os.environ[ExporterConfig.ENV_SIDECAR_MODE] = "false"

    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Set up metrics server
    try:
        registry, sidecar_metrics = setup_metrics_server(
            args.port, args.bind, args.multiproc_dir
        )
        logger.info("Standalone metrics server started successfully")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        sys.exit(1)

    # Main loop
    logger.info(
        "Standalone metrics server running, updating metrics every {} seconds".format(
            args.update_interval
        )
    )
    try:
        while True:
            # Update sidecar-specific metrics (if any, though not applicable here)
            # sidecar_metrics.update_metrics(args.multiproc_dir) # No multiproc_dir in standalone

            # Sleep until next update
            time.sleep(args.update_interval)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        sys.exit(1)
    finally:
        signal_handler(signal.SIGTERM, None)


def run_health_mode(args: argparse.Namespace):
    """Run the health check mode."""
    # Set sidecar mode environment variable to true for health check
    os.environ[ExporterConfig.ENV_SIDECAR_MODE] = "true"

    # Set required environment variables for health check
    os.environ["PROMETHEUS_BIND_ADDRESS"] = "0.0.0.0"  # nosec B104
    os.environ["PROMETHEUS_METRICS_PORT"] = str(args.port)
    os.environ["GUNICORN_WORKERS"] = "1"  # Dummy value
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prometheus_multiproc"  # nosec B108

    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Create dummy multiprocess directory for health check
    multiproc_path = Path("/tmp/prometheus_multiproc")  # nosec B108
    multiproc_path.mkdir(parents=True, exist_ok=True)

    # Set up metrics server
    try:
        registry, sidecar_metrics = setup_metrics_server(
            args.port,
            "0.0.0.0",
            "/tmp/prometheus_multiproc",  # nosec B104, B108
        )
        logger.info("Health check completed successfully")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        sys.exit(1)

    # Main loop
    logger.info(
        "Health check running, metrics server available on {}:{}".format(
            "0.0.0.0",
            args.port,  # nosec B104
        )
    )
    try:
        while True:
            # No metrics to update in health check mode
            time.sleep(1)  # Keep it alive

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        sys.exit(1)
    finally:
        signal_handler(signal.SIGTERM, None)


def main():
    """Main sidecar function."""
    parser = argparse.ArgumentParser(description="Gunicorn Prometheus Exporter Sidecar")

    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")

    # Sidecar mode parser
    sidecar_parser = subparsers.add_parser(
        "sidecar", help="Run as sidecar container (default)"
    )
    sidecar_parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PROMETHEUS_METRICS_PORT", 9091)),
        help="Port for metrics endpoint",
    )
    sidecar_parser.add_argument(
        "--bind",
        default=os.getenv("PROMETHEUS_BIND_ADDRESS", "0.0.0.0"),  # nosec B104
        help="Bind address for metrics server",
    )
    sidecar_parser.add_argument(
        "--multiproc-dir",
        default=os.getenv("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc"),  # nosec B108
        help="Directory containing multiprocess files",
    )
    sidecar_parser.add_argument(
        "--update-interval",
        type=int,
        default=int(os.getenv("SIDECAR_UPDATE_INTERVAL", 30)),
        help="Interval for updating sidecar metrics (seconds)",
    )

    # Standalone mode parser
    standalone_parser = subparsers.add_parser(
        "standalone", help="Run standalone metrics server"
    )
    standalone_parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PROMETHEUS_METRICS_PORT", 9091)),
        help="Port for metrics endpoint",
    )
    standalone_parser.add_argument(
        "--bind",
        default=os.getenv("PROMETHEUS_BIND_ADDRESS", "0.0.0.0"),  # nosec B104
        help="Bind address for metrics server",
    )
    standalone_parser.add_argument(
        "--multiproc-dir",
        default=os.getenv("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc"),  # nosec B108
        help="Directory containing multiprocess files",
    )
    standalone_parser.add_argument(
        "--update-interval",
        type=int,
        default=int(os.getenv("SIDECAR_UPDATE_INTERVAL", 10)),
        help="Interval for updating metrics (seconds)",
    )

    # Health check parser
    health_parser = subparsers.add_parser("health", help="Run health check")
    health_parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PROMETHEUS_METRICS_PORT", 9091)),
        help="Port for metrics endpoint",
    )

    args = parser.parse_args()

    if args.mode == "sidecar":
        run_sidecar_mode(args)
    elif args.mode == "standalone":
        run_standalone_mode(args)
    elif args.mode == "health":
        run_health_mode(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

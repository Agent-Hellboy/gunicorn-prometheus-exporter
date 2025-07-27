"""Pre-built Gunicorn hooks for gunicorn-prometheus-exporter.

This module provides ready-to-use hook functions that can be imported
and assigned to Gunicorn configuration variables.

Available hooks:
- default_on_starting: Initialize master metrics
- default_when_ready: Start Prometheus metrics server
- default_worker_int: Handle worker interrupts
- default_on_exit: Cleanup on server exit
- redis_when_ready: Start Prometheus metrics server with Redis forwarding
"""

import logging
import time

from typing import Any, Union

from prometheus_client import start_http_server
from prometheus_client.multiprocess import MultiProcessCollector

from .config import config


def default_on_starting(_server: Any) -> None:
    """Default on_starting hook to initialize master metrics.

    This function:
    1. Ensures the multiprocess directory exists
    2. Initializes master metrics
    3. Logs initialization status

    Args:
        _server: Gunicorn server instance (unused)
    """
    from .utils import ensure_multiprocess_dir, get_multiprocess_dir

    mp_dir = get_multiprocess_dir()
    if not mp_dir:
        logging.warning(
            "PROMETHEUS_MULTIPROC_DIR not set; skipping master metrics initialization"
        )
        return

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Master starting - initializing PrometheusMaster metrics")

    # Ensure the multiprocess directory exists
    ensure_multiprocess_dir(mp_dir)
    logger.info(" Multiprocess directory ready: %s", mp_dir)

    logger.info(" Master metrics initialized")


def _setup_prometheus_server(logger: logging.Logger) -> Union[tuple[int, Any], None]:
    """Set up Prometheus multiprocess metrics server.

    This function:
    1. Validates multiprocess directory configuration
    2. Initializes MultiProcessCollector
    3. Returns port and registry for server startup

    Args:
        logger: Logger instance for status messages

    Returns:
        Tuple of (port, registry) if successful, None if failed
    """
    from .metrics import registry
    from .utils import get_multiprocess_dir

    mp_dir = get_multiprocess_dir()
    if not mp_dir:
        logger.warning("PROMETHEUS_MULTIPROC_DIR not set; skipping metrics server")
        return None

    port = config.prometheus_metrics_port

    # Initialize MultiProcessCollector
    try:
        MultiProcessCollector(registry)
        logger.info("Successfully initialized MultiProcessCollector")
    except Exception as e:
        logger.error("Failed to initialize MultiProcessCollector: %s", e)
        return None

    return port, registry


def default_when_ready(_server: Any) -> None:
    """Default when_ready hook with Prometheus metrics.

    This function:
    1. Sets up Prometheus multiprocess metrics collection
    2. Starts the Prometheus metrics HTTP server with retry logic
    3. Logs status information

    Args:
        _server: Gunicorn server instance (unused)
    """
    # Use configuration for port and logging
    logging.basicConfig(
        level=getattr(
            logging, config.get_gunicorn_config().get("loglevel", "INFO").upper()
        )
    )
    logger = logging.getLogger(__name__)

    result = _setup_prometheus_server(logger)
    if not result:
        return
    port, registry = result

    logger.info("Starting Prometheus multiprocess metrics server on :%s", port)

    # Start HTTP server for metrics with retry logic for USR2 upgrades
    max_retries = 3
    for attempt in range(max_retries):
        try:
            start_http_server(port, registry=registry)
            logger.info(
                "Using PrometheusMaster for signal handling and worker restart tracking"
            )
            logger.info(
                "Metrics server started successfully - includes both worker and master "
                "metrics"
            )
            break
        except OSError as e:
            if e.errno == 98 and attempt < max_retries - 1:  # Address already in use
                logger.warning(
                    "Port %s in use (attempt %s/%s), retrying in 1 second...",
                    port,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(1)
                continue
            logger.error(
                "Failed to start metrics server after %s attempts: %s", max_retries, e
            )
            break
        except Exception as e:
            logger.error("Failed to start metrics server: %s", e)
            break


def default_worker_int(_worker: Any) -> None:
    """Default worker interrupt handler.

    Args:
        _worker: Gunicorn worker instance (unused)
    """
    logger = logging.getLogger(__name__)
    logger.info("Worker received interrupt signal")


def default_on_exit(_server: Any) -> None:
    """Default on_exit hook for cleanup.

    Args:
        _server: Gunicorn server instance (unused)
    """
    logger = logging.getLogger(__name__)
    logger.info("Server shutting down")


def redis_when_ready(_server: Any) -> None:
    """Redis-enabled when_ready hook with Prometheus metrics and Redis forwarding.

    This function:
    1. Sets up Prometheus multiprocess metrics collection
    2. Starts the Prometheus metrics HTTP server with retry logic
    3. Initializes Redis forwarding for metrics
    4. Logs status information

    Args:
        _server: Gunicorn server instance (unused)
    """
    from . import start_redis_forwarder

    # Use configuration for port and logging
    logging.basicConfig(
        level=getattr(
            logging, config.get_gunicorn_config().get("loglevel", "INFO").upper()
        )
    )
    logger = logging.getLogger(__name__)

    result = _setup_prometheus_server(logger)
    if not result:
        return
    port, registry = result

    logger.info("Starting Prometheus multiprocess metrics server on :%s", port)

    # Start HTTP server with same retry logic as default_when_ready
    max_retries = 3
    for attempt in range(max_retries):
        try:
            start_http_server(port, registry=registry)
            logger.info("Metrics server started successfully")
            break
        except OSError as e:
            if e.errno == 98 and attempt < max_retries - 1:
                logger.warning(
                    "Port %s in use (attempt %s/%s), retrying in 1 second...",
                    port,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(1)
                continue
            logger.error(
                "Failed to start metrics server after %s attempts: %s", max_retries, e
            )
            return
        except Exception as e:
            logger.error("Failed to start metrics server: %s", e)
            return

    # Start Redis forwarder if enabled
    if config.redis_enabled:
        try:
            start_redis_forwarder()
            logger.info("Redis forwarder started successfully")
        except Exception as e:
            logger.error("Failed to start Redis forwarder: %s", e)
    else:
        logger.info("Redis forwarding disabled")


# Convenient aliases for easy import
on_starting = default_on_starting
when_ready = default_when_ready
worker_int = default_worker_int
on_exit = default_on_exit

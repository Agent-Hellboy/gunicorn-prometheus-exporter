"""Pre-built Gunicorn hooks for gunicorn-prometheus-exporter.

This module provides ready-to-use hook functions that can be imported
and assigned to Gunicorn configuration variables.

Available hooks:
- default_on_starting: Initialize master metrics
- default_when_ready: Start Prometheus metrics server
- default_worker_int: Handle worker interrupts
- default_on_exit: Cleanup on server exit
- default_post_fork: Configure CLI options after worker fork
- redis_when_ready: Start Prometheus metrics server with Redis forwarding
"""

import logging
import signal
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


def _update_workers_env(cfg: Any, logger: logging.Logger) -> None:
    """Update GUNICORN_WORKERS environment variable from CLI.

    Args:
        cfg: Gunicorn configuration object
        logger: Logger instance
    """
    import os

    if hasattr(cfg, "workers") and cfg.workers and cfg.workers != 1:
        os.environ["GUNICORN_WORKERS"] = str(cfg.workers)
        logger.info("Updated GUNICORN_WORKERS from CLI: %s", cfg.workers)


def _update_bind_env(cfg: Any, logger: logging.Logger) -> None:
    """Update GUNICORN_BIND environment variable from CLI.

    Args:
        cfg: Gunicorn configuration object
        logger: Logger instance
    """
    import os

    if hasattr(cfg, "bind") and cfg.bind and cfg.bind != ["127.0.0.1:8000"]:
        os.environ["GUNICORN_BIND"] = str(cfg.bind)
        logger.info("Updated GUNICORN_BIND from CLI: %s", cfg.bind)


def _update_worker_class_env(cfg: Any, logger: logging.Logger) -> None:
    """Update GUNICORN_WORKER_CLASS environment variable from CLI.

    Args:
        cfg: Gunicorn configuration object
        logger: Logger instance
    """
    import os

    if hasattr(cfg, "worker_class") and cfg.worker_class and cfg.worker_class != "sync":
        os.environ["GUNICORN_WORKER_CLASS"] = str(cfg.worker_class)
        logger.info("Updated GUNICORN_WORKER_CLASS from CLI: %s", cfg.worker_class)


def _update_env_from_cli(cfg: Any, logger: logging.Logger) -> None:
    """Update environment variables from CLI options.

    Args:
        cfg: Gunicorn configuration object
        logger: Logger instance
    """
    _update_workers_env(cfg, logger)
    _update_bind_env(cfg, logger)
    _update_worker_class_env(cfg, logger)


def default_post_fork(server: Any, worker: Any) -> None:
    """Default post_fork hook to configure CLI options after worker fork.

    This function:
    1. Runs after each worker process is forked
    2. Can access and configure Gunicorn CLI options
    3. Logs worker-specific configuration
    4. Can override environment-based settings with CLI options

    Args:
        server: Gunicorn server instance
        worker: Gunicorn worker instance
    """
    logger = logging.getLogger(__name__)

    # Access Gunicorn configuration
    cfg = server.cfg
    logger.info("Gunicorn configuration: %s", cfg)

    # Print the actual configuration being used
    logger.info("=== Gunicorn Configuration ===")
    logger.info(str(cfg))
    logger.info("=== End Configuration ===")

    # Update environment variables from CLI options
    _update_env_from_cli(cfg, logger)

    logger.info("Worker %s post-fork configuration complete", worker.pid)


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


def _start_metrics_server_single_attempt(
    port: int, registry: Any, logger: logging.Logger
) -> bool:
    """Start metrics server in a single attempt.

    Args:
        port: Port to start the server on
        registry: Prometheus registry
        logger: Logger instance

    Returns:
        True if successful, False otherwise
    """
    try:
        start_http_server(port, registry=registry)
        logger.info(
            "Using PrometheusMaster for signal handling and worker restart tracking"
        )
        logger.info(
            "Metrics server started successfully - includes both worker and master "
            "metrics"
        )
        return True
    except OSError as e:
        if e.errno == 98:  # Address already in use
            raise
        logger.error("Failed to start metrics server: %s", e)
        return False
    except Exception as e:
        logger.error("Failed to start metrics server: %s", e)
        return False


def _start_metrics_server_with_retry(
    port: int, registry: Any, logger: logging.Logger
) -> bool:
    """Start Prometheus metrics server with retry logic.

    Args:
        port: Port to start the server on
        registry: Prometheus registry
        logger: Logger instance

    Returns:
        True if server started successfully, False otherwise
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return _start_metrics_server_single_attempt(port, registry, logger)
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
            return False
    return False


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

    # Start HTTP server for metrics with retry logic
    _start_metrics_server_with_retry(port, registry, logger)


def _update_worker_metrics(worker: Any, logger: logging.Logger) -> None:
    """Update worker metrics before shutdown.

    Args:
        worker: Gunicorn worker instance
        logger: Logger instance
    """
    if hasattr(worker, "update_worker_metrics"):
        try:
            worker.update_worker_metrics()
            logger.debug("Updated worker metrics for %s", worker.worker_id)
        except Exception as e:
            logger.error("Failed to update worker metrics: %s", e)


def _handle_worker_shutdown(worker: Any, logger: logging.Logger) -> None:
    """Handle worker shutdown gracefully.

    Args:
        worker: Gunicorn worker instance
        logger: Logger instance
    """
    if hasattr(worker, "handle_quit"):
        try:
            # Call handle_quit to properly shut down the worker
            worker.handle_quit(signal.SIGINT, None)
        except Exception as e:
            logger.error("Failed to call parent handle_quit: %s", e)
            # Fallback: set alive to False to stop the worker
            worker.alive = False
    elif hasattr(worker, "alive"):
        # Direct fallback if handle_quit is not available
        worker.alive = False
        logger.info("Set worker.alive = False for graceful shutdown")


def default_worker_int(worker: Any) -> None:
    """Default worker_int hook for signal handling.

    This function:
    1. Handles interrupt signals (Ctrl+C) gracefully
    2. Updates worker metrics before shutdown
    3. Calls parent signal handling methods
    4. Ensures proper worker shutdown

    Args:
        worker: Gunicorn worker instance
    """
    logger = logging.getLogger(__name__)
    logger.info("Worker received interrupt signal")

    # Update worker metrics if the worker has the method
    _update_worker_metrics(worker, logger)

    # Handle worker shutdown
    _handle_worker_shutdown(worker, logger)


def default_on_exit(_server: Any) -> None:
    """Default on_exit hook for cleanup.

    This function:
    1. Logs server shutdown
    2. Ensures proper cleanup of metrics server
    3. Handles graceful shutdown

    Args:
        _server: Gunicorn server instance (unused)
    """
    logger = logging.getLogger(__name__)
    logger.info("Server shutting down - cleaning up Prometheus metrics server")

    # Force cleanup of any remaining processes
    import psutil

    try:
        # Get current process
        current_process = psutil.Process()

        # Find and terminate any child processes that might be hanging
        children = current_process.children(recursive=True)
        for child in children:
            try:
                logger.info(
                    "Terminating child process: %s (PID: %s)", child.name(), child.pid
                )
                child.terminate()
                child.wait(timeout=5)  # Wait up to 5 seconds
            except psutil.TimeoutExpired:
                logger.warning(
                    "Force killing child process: %s (PID: %s)", child.name(), child.pid
                )
                child.kill()
            except Exception as e:
                logger.error("Error terminating child process %s: %s", child.pid, e)
    except Exception as e:
        logger.error("Error during cleanup: %s", e)

    logger.info("Server shutdown complete")


def _start_redis_forwarder_if_enabled(logger: logging.Logger) -> None:
    """Start Redis forwarder if enabled.

    Args:
        logger: Logger instance
    """
    from . import start_redis_forwarder

    if config.redis_enabled:
        try:
            start_redis_forwarder()
            logger.info("Redis forwarder started successfully")
        except Exception as e:
            logger.error("Failed to start Redis forwarder: %s", e)
    else:
        logger.info("Redis forwarding disabled")


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

    # Start HTTP server with retry logic
    if _start_metrics_server_with_retry(port, registry, logger):
        # Start Redis forwarder if enabled
        _start_redis_forwarder_if_enabled(logger)


# Convenient aliases for easy import
on_starting = default_on_starting
when_ready = default_when_ready
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork

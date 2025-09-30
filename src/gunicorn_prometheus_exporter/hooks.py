"""Pre-built Gunicorn hooks for gunicorn-prometheus-exporter.

This module provides ready-to-use hook functions that can be imported
and assigned to Gunicorn configuration variables.

Available hooks:
- default_on_starting: Initialize master metrics
- default_when_ready: Start Prometheus metrics server
- default_worker_int: Handle worker interrupts
- default_on_exit: Cleanup on server exit
- default_post_fork: Configure CLI options after worker fork
- redis_when_ready: Start Prometheus metrics server with Redis storage
"""

import logging
import os
import time

from dataclasses import dataclass
from typing import Any, Optional

import psutil

from prometheus_client.multiprocess import MultiProcessCollector

from .config import get_config


@dataclass
class HookContext:
    """Context object for hook execution with configuration and state."""

    server: Any
    worker: Optional[Any] = None
    logger: Optional[logging.Logger] = None

    def __post_init__(self):
        if self.logger is None:
            self.logger = logging.getLogger(__name__)


class HookManager:
    """Manages hook execution and provides common utilities."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        try:
            # Try to get loglevel from config, fallback to INFO
            loglevel = "INFO"
            try:
                from .config import get_config

                loglevel = (
                    get_config().get_gunicorn_config().get("loglevel", "INFO").upper()
                )
            except (ValueError, AttributeError):
                # Config not available (e.g., during testing), use default
                pass

            logging.basicConfig(level=getattr(logging, loglevel))
        except Exception:
            # Fallback to basic logging setup
            logging.basicConfig(level=logging.INFO)

    def get_logger(self) -> logging.Logger:
        """Get configured logger instance."""
        return self.logger

    def safe_execute(self, func, *args, **kwargs) -> bool:
        """Safely execute a function with error handling."""
        try:
            func(*args, **kwargs)
            return True
        except Exception as e:
            self.logger.error("Hook execution failed: %s", e)
            return False


class EnvironmentManager:
    """Manages environment variable updates from CLI options."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._defaults = {
            "workers": 1,
            "bind": ["127.0.0.1:8000"],
            "worker_class": "sync",
        }

    def update_from_cli(self, cfg: Any) -> None:
        """Update environment variables from CLI configuration."""
        self._update_workers_env(cfg)
        self._update_bind_env(cfg)
        self._update_worker_class_env(cfg)

    def _update_workers_env(self, cfg: Any) -> None:
        """Update GUNICORN_WORKERS environment variable from CLI."""
        if (
            hasattr(cfg, "workers")
            and cfg.workers
            and cfg.workers != self._defaults["workers"]
        ):
            os.environ["GUNICORN_WORKERS"] = str(cfg.workers)
            self.logger.debug("Updated GUNICORN_WORKERS from CLI: %s", cfg.workers)

    def _update_bind_env(self, cfg: Any) -> None:
        """Update GUNICORN_BIND environment variable from CLI."""
        if hasattr(cfg, "bind") and cfg.bind and cfg.bind != self._defaults["bind"]:
            os.environ["GUNICORN_BIND"] = str(cfg.bind)
            self.logger.debug("Updated GUNICORN_BIND from CLI: %s", cfg.bind)

    def _update_worker_class_env(self, cfg: Any) -> None:
        """Update GUNICORN_WORKER_CLASS environment variable from CLI."""
        if (
            hasattr(cfg, "worker_class")
            and cfg.worker_class
            and cfg.worker_class != self._defaults["worker_class"]
        ):
            os.environ["GUNICORN_WORKER_CLASS"] = str(cfg.worker_class)
            self.logger.info(
                "Updated GUNICORN_WORKER_CLASS from CLI: %s", cfg.worker_class
            )


class MetricsServerManager:
    """Manages Prometheus metrics server lifecycle."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.max_retries = 5  # Increased retries for restart scenarios
        self.retry_delay = 2  # Increased delay for port release
        self._server_thread = None  # Store the server thread
        self._httpd = None  # Store the HTTP server instance

    def setup_server(self) -> Optional[tuple[int, Any]]:
        """Setup Prometheus metrics server."""
        from .config import initialize_config
        from .metrics import get_shared_registry
        from .utils import get_multiprocess_dir

        # Initialize configuration if not already done
        try:
            initialize_config()
        except RuntimeError:
            # Configuration already initialized, that's fine
            pass

        port = get_config().prometheus_metrics_port
        registry = get_shared_registry()

        # Try Redis collector first if Redis is enabled
        if get_config().redis_enabled:
            try:
                from .backend import get_redis_storage_manager

                manager = get_redis_storage_manager()
                redis_collector = manager.get_collector()
                if redis_collector:
                    self.logger.debug("Successfully initialized Redis-based collector")
                    return port, registry
            except Exception as e:
                self.logger.warning("Failed to initialize Redis collector: %s", e)

        # Fallback to file-based multiprocess collector
        mp_dir = get_multiprocess_dir()
        if not mp_dir:
            self.logger.warning(
                "PROMETHEUS_MULTIPROC_DIR not set; skipping metrics server"
            )
            return None

        try:
            MultiProcessCollector(registry)
            self.logger.debug("Successfully initialized MultiProcessCollector")
            return port, registry
        except Exception as e:
            self.logger.error("Failed to initialize MultiProcessCollector: %s", e)
            return None

    def start_server(self, port: int, registry: Any) -> bool:
        """Start metrics server with retry logic."""
        for attempt in range(self.max_retries):
            if self._start_single_attempt(port, registry):
                return True

            if attempt < self.max_retries - 1:
                self.logger.warning(
                    "Port %s in use (attempt %s/%s), retrying in %s second...",
                    port,
                    attempt + 1,
                    self.max_retries,
                    self.retry_delay,
                )
                # Wait longer for port to be released during restart scenarios
                wait_time = self.retry_delay * (attempt + 1)  # Progressive backoff
                time.sleep(wait_time)

        self.logger.error(
            "Failed to start metrics server after %s attempts", self.max_retries
        )
        return False

    def stop_server(self) -> None:
        """Stop the metrics server."""
        if self._server_thread is not None:
            try:
                # The prometheus_client start_http_server runs in a daemon thread
                # which should automatically terminate when the main process exits
                self.logger.debug("Metrics server will be stopped when process exits")
            except Exception as e:
                self.logger.error("Failed to stop metrics server: %s", e)
            finally:
                self._server_thread = None

    def _start_single_attempt(self, port: int, registry: Any) -> bool:
        """Start metrics server in a single attempt."""
        from .config import initialize_config

        # Initialize configuration if not already done
        try:
            initialize_config()
        except RuntimeError:
            # Configuration already initialized, that's fine
            pass

        try:
            # Get the bind address from configuration
            bind_address = get_config().prometheus_bind_address

            # Check if SSL/TLS is enabled
            if get_config().prometheus_ssl_enabled:
                self._start_https_server(port, registry, bind_address)
            else:
                self._start_http_server(port, registry)

            return True
        except OSError as e:
            if e.errno == 98:  # Address already in use
                self.logger.warning(
                    "Port %s already in use, metrics server may already be running",
                    port,
                )
                return False
            self.logger.error("Failed to start metrics server: %s", e)
            return False
        except Exception as e:
            self.logger.error("Failed to start metrics server: %s", e)
            return False

    def _start_https_server(self, port: int, registry: Any, bind_address: str) -> None:
        """Start HTTPS server with SSL/TLS."""
        from prometheus_client.exposition import start_http_server

        # Start HTTPS server with SSL/TLS using start_http_server
        # which supports SSL parameters unlike start_wsgi_server
        start_http_server(
            port=port,
            addr=bind_address,
            registry=registry,
            certfile=get_config().prometheus_ssl_certfile,
            keyfile=get_config().prometheus_ssl_keyfile,
        )
        self.logger.debug(
            "HTTPS metrics server started successfully on %s:%s",
            bind_address,
            port,
        )

    def _start_http_server(self, port: int, registry: Any) -> None:
        """Start HTTP server (default)."""
        from prometheus_client.exposition import start_http_server

        # Start HTTP server (default) without addr to preserve test expectations
        start_http_server(port, registry=registry)
        self.logger.debug("HTTP metrics server started successfully on :%s", port)


class ProcessManager:
    """Manages process cleanup and termination."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timeout = 5

    def cleanup_processes(self) -> None:
        """Clean up child processes on exit."""

        try:
            current_process = psutil.Process()
            children = current_process.children(recursive=True)

            for child in children:
                self._terminate_child(child)

        except Exception as e:
            self.logger.error("Error during cleanup: %s", e)

    def _terminate_child(self, child) -> None:
        """Terminate a child process with timeout."""
        try:
            self.logger.info(
                "Terminating child process: %s (PID: %s)", child.name(), child.pid
            )
            child.terminate()
            child.wait(timeout=self.timeout)
        except psutil.TimeoutExpired:
            self.logger.warning(
                "Force killing child process: %s (PID: %s)", child.name(), child.pid
            )
            child.kill()
        except Exception as e:
            self.logger.error("Error terminating child process %s: %s", child.pid, e)


# Global instances - lazy initialized
_hook_manager = None
_metrics_manager = None
_worker_manager = None
_process_manager = None


def _get_hook_manager() -> "HookManager":
    """Get or create the global hook manager instance."""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
    return _hook_manager


def _get_metrics_manager() -> "MetricsServerManager":
    """Get or create the global metrics manager instance."""
    global _metrics_manager
    if _metrics_manager is None:
        _metrics_manager = MetricsServerManager(_get_hook_manager().get_logger())
    return _metrics_manager


def _get_process_manager() -> "ProcessManager":
    """Get or create the global process manager instance."""
    global _process_manager
    if _process_manager is None:
        _process_manager = ProcessManager(_get_hook_manager().get_logger())
    return _process_manager


def default_on_starting(_server: Any) -> None:
    """Default on_starting hook to initialize master metrics."""
    from .utils import ensure_multiprocess_dir, get_multiprocess_dir

    mp_dir = get_multiprocess_dir()
    if not mp_dir:
        _get_hook_manager().logger.warning(
            "PROMETHEUS_MULTIPROC_DIR not set; skipping master metrics initialization"
        )
        return

    _get_hook_manager().logger.info(
        "Master starting - initializing PrometheusMaster metrics"
    )

    # Ensure the multiprocess directory exists
    ensure_multiprocess_dir(mp_dir)
    _get_hook_manager().logger.info("Multiprocess directory ready: %s", mp_dir)
    _get_hook_manager().logger.info("Master metrics initialized")


def default_post_fork(server: Any, worker: Any) -> None:
    """Default post_fork hook to configure CLI options after worker fork."""
    context = HookContext(
        server=server, worker=worker, logger=_get_hook_manager().get_logger()
    )

    # Log configuration
    context.logger.info("Gunicorn configuration: %s", server.cfg)
    context.logger.info("=== Gunicorn Configuration ===")
    context.logger.info(str(server.cfg))
    context.logger.info("=== End Configuration ===")

    # Update environment variables from CLI options
    env_manager = EnvironmentManager(context.logger)
    env_manager.update_from_cli(server.cfg)


def default_when_ready(_server: Any) -> None:
    """Default when_ready hook with Prometheus metrics."""
    context = HookContext(server=_server, logger=_get_hook_manager().get_logger())

    # Setup metrics server
    result = _get_metrics_manager().setup_server()
    if not result:
        return

    port, registry = result
    context.logger.info("Starting Prometheus multiprocess metrics server on :%s", port)

    # Start HTTP server for metrics with retry logic
    if not _get_metrics_manager().start_server(port, registry):
        context.logger.error("Failed to start metrics server")


def default_worker_int(worker: Any) -> None:
    """Default worker interrupt handler.

    Args:
        worker: Gunicorn worker instance
    """
    logger = logging.getLogger(__name__)
    logger.debug("Worker received interrupt signal")

    # Update worker metrics if the worker has the method
    if hasattr(worker, "update_worker_metrics"):
        try:
            worker.update_worker_metrics()
            logger.debug("Updated worker metrics for %s", worker.worker_id)
        except Exception as e:
            logger.error("Failed to update worker metrics: %s", e)


def default_on_exit(_server: Any) -> None:
    """Default on_exit hook - minimal cleanup only."""
    context = HookContext(server=_server, logger=_get_hook_manager().get_logger())

    context.logger.info("Server shutting down")

    # No metrics cleanup needed:
    # - Redis TTL handles automatic cleanup
    # - Metrics should persist for Prometheus scraping
    # - File-based metrics are cleaned up by OS on process exit

    # No process cleanup needed:
    # - OS will clean up child processes when parent exits
    # - Avoids blocking signal handling

    context.logger.info(
        "Server shutdown complete - Redis TTL handles automatic cleanup"
    )


def redis_when_ready(_server: Any) -> None:
    """Redis-enabled when_ready hook with Prometheus metrics and Redis storage."""
    from .config import initialize_config

    # Initialize configuration if not already done
    try:
        initialize_config()
    except RuntimeError:
        # Configuration already initialized, that's fine
        pass

    context = HookContext(server=_server, logger=_get_hook_manager().get_logger())

    # Setup Redis metrics storage if enabled
    if get_config().redis_enabled:
        from .backend import get_redis_storage_manager

        manager = get_redis_storage_manager()
        if manager.setup():
            context.logger.info(
                "Redis metrics storage enabled - using Redis instead of files"
            )
        else:
            context.logger.warning(
                "Failed to setup Redis metrics, falling back to file-based storage"
            )

    # Setup metrics server
    result = _get_metrics_manager().setup_server()
    if not result:
        return

    port, registry = result
    context.logger.info("Starting Prometheus multiprocess metrics server on :%s", port)

    # Start HTTP server for metrics with retry logic
    if not _get_metrics_manager().start_server(port, registry):
        context.logger.error("Failed to start metrics server")
        return

    # Setup Redis storage if enabled
    _setup_redis_storage_if_enabled(context.logger)


def _setup_redis_storage_if_enabled(logger: logging.Logger) -> None:
    """Setup Redis storage if enabled in configuration."""
    from .config import initialize_config

    # Initialize configuration if not already done
    try:
        initialize_config()
    except RuntimeError:
        # Configuration already initialized, that's fine
        pass

    if not get_config().redis_enabled:
        logger.debug("Redis storage disabled")
        return

    try:
        from .backend import setup_redis_metrics

        if setup_redis_metrics():
            logger.debug("Redis storage enabled - using Redis instead of files")
        else:
            logger.warning(
                "Failed to setup Redis storage, falling back to file storage"
            )
    except Exception as e:
        logger.error("Failed to setup Redis storage: %s", e)


def load_yaml_config(config_file_path: str) -> None:
    """Load configuration from YAML file and apply to environment variables.

    This is the main public API for loading YAML configuration files.
    It should be called before any other configuration or hook functions.

    Args:
        config_file_path: Path to the YAML configuration file

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the YAML file is invalid
        ValueError: If the configuration structure is invalid

    Example:
        >>> from gunicorn_prometheus_exporter.hooks import load_yaml_config
        >>> load_yaml_config("config.yml")
        >>> # Now use other hooks or initialize config
        >>> from gunicorn_prometheus_exporter.config import initialize_config
        >>> initialize_config()
    """
    from .config.loader import load_yaml_config as _load_yaml_config

    _load_yaml_config(config_file_path)

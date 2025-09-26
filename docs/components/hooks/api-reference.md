# Hooks API Reference

This document provides detailed API reference for the hooks component.

## Core Classes

### HookManager

Centralized logging and execution management for all hooks.

```python
class HookManager:
    """Manages hook execution and provides common utilities."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
```

**Methods:**

- `get_logger()` - Get configured logger instance
- `safe_execute(func, *args, **kwargs)` - Safely execute a function with error handling
- `_setup_logging()` - Setup logging configuration

### EnvironmentManager

Handles CLI-to-environment variable mapping and configuration updates.

```python
class EnvironmentManager:
    """Manages environment variable updates from CLI options."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._defaults = {
            "workers": 1,
            "bind": ["127.0.0.1:8000"],
            "worker_class": "sync",
        }
```

**Methods:**

- `update_from_cli(cfg)` - Update environment variables from CLI configuration
- `_update_workers_env(cfg)` - Update GUNICORN_WORKERS environment variable
- `_update_bind_env(cfg)` - Update GUNICORN_BIND environment variable
- `_update_worker_class_env(cfg)` - Update GUNICORN_WORKER_CLASS environment variable

### MetricsServerManager

Manages Prometheus metrics server lifecycle with retry logic and error handling.

```python
class MetricsServerManager:
    """Manages Prometheus metrics server lifecycle."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.max_retries = 5
        self.retry_delay = 2
        self._server_thread = None
```

**Methods:**

- `setup_server()` - Setup Prometheus metrics server
- `start_server(port, registry)` - Start metrics server with retry logic
- `stop_server()` - Stop the metrics server
- `_start_single_attempt(port, registry)` - Start metrics server in a single attempt

### ProcessManager

Manages process cleanup and termination with timeout handling.

```python
class ProcessManager:
    """Manages process cleanup and termination."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timeout = 5
```

**Methods:**

- `cleanup_processes()` - Clean up child processes on exit
- `_terminate_child(child)` - Terminate a child process with timeout

## Hook Functions

### Default Hooks

#### `default_on_starting(server)`

Called when the server is starting up. Initializes master metrics and multiprocess directory.

```python
def default_on_starting(_server: Any) -> None:
    """Default on_starting hook to initialize master metrics."""
```

**What it does:**

- Sets up logging with proper configuration
- Initializes PrometheusMaster metrics
- Ensures multiprocess directory exists
- Handles missing configuration gracefully

#### `default_when_ready(server)`

Called when the server is ready to accept connections. Sets up the Prometheus metrics server.

```python
def default_when_ready(_server: Any) -> None:
    """Default when_ready hook with Prometheus metrics."""
```

**What it does:**

- Initializes MultiProcessCollector
- Starts HTTP server for metrics endpoint
- Implements retry logic for port conflicts
- Handles server startup failures gracefully

#### `default_worker_int(worker)`

Called when a worker receives an interrupt signal (e.g., SIGINT from Ctrl+C).

```python
def default_worker_int(worker: Any) -> None:
    """Default worker interrupt handler."""
```

**What it does:**

- Updates worker metrics before shutdown
- Calls `worker.handle_quit()` for graceful shutdown
- Falls back to `worker.alive = False` if needed
- Handles exceptions during shutdown process

#### `default_on_exit(server)`

Called when the server is shutting down. Performs cleanup operations.

```python
def default_on_exit(_server: Any) -> None:
    """Default on_exit hook - minimal cleanup only."""
```

**What it does:**

- Cleans up Prometheus metrics server
- Terminates any remaining child processes
- Uses psutil for comprehensive process cleanup
- Handles cleanup failures gracefully

#### `default_post_fork(server, worker)`

Called after each worker process is forked. Configures CLI options and environment variables.

```python
def default_post_fork(server: Any, worker: Any) -> None:
    """Default post_fork hook to configure CLI options after worker fork."""
```

**What it does:**

- Accesses Gunicorn configuration (`server.cfg`)
- Logs detailed worker-specific configuration
- Updates environment variables with CLI values
- Ensures consistency between CLI and environment-based configuration

**Supported CLI options:**

- `--workers`: Number of worker processes
- `--bind`: Bind address and port
- `--worker-class`: Worker class to use

### Redis Hooks

#### `redis_when_ready(server)`

Sets up Redis storage when the server is ready.

```python
def redis_when_ready(_server: Any) -> None:
    """Redis-enabled when_ready hook with Prometheus metrics and Redis storage."""
```

**What it does:**

- Sets up Prometheus metrics server (same as `default_when_ready`)
- Initializes Redis storage if enabled
- Handles Redis connection failures gracefully
- Provides detailed logging for debugging

## HookContext

Structured context object for hook execution.

```python
@dataclass
class HookContext:
    """Context object for hook execution with configuration and state."""

    server: Any
    worker: Optional[Any] = None
    logger: Optional[logging.Logger] = None
```

**Properties:**

- `server` - Gunicorn server instance
- `worker` - Gunicorn worker instance (if applicable)
- `logger` - Configured logger instance

## Global Manager Functions

### `_get_hook_manager()`

Get or create the global hook manager instance.

```python
def _get_hook_manager() -> "HookManager":
    """Get or create the global hook manager instance."""
```

### `_get_metrics_manager()`

Get or create the global metrics manager instance.

```python
def _get_metrics_manager() -> "MetricsServerManager":
    """Get or create the global metrics manager instance."""
```

### `_get_process_manager()`

Get or create the global process manager instance.

```python
def _get_process_manager() -> "ProcessManager":
    """Get or create the global process manager instance."""
```

## Configuration Integration

### Environment Variables

Hooks automatically read configuration from environment variables:

- `PROMETHEUS_MULTIPROC_DIR` - Multiprocess directory
- `PROMETHEUS_METRICS_PORT` - Metrics server port
- `PROMETHEUS_BIND_ADDRESS` - Metrics server bind address
- `REDIS_ENABLED` - Enable Redis storage
- `REDIS_HOST` - Redis server host
- `REDIS_PORT` - Redis server port

### CLI Integration

Hooks automatically detect and apply CLI options:

```bash
# Override workers from CLI
gunicorn -c gunicorn.conf.py app:app --workers 8

# Override bind address from CLI
gunicorn -c gunicorn.conf.py app:app --bind 0.0.0.0:9000
```

## Error Handling

### Safe Execution

All managers include comprehensive error handling:

```python
# Safe execution with error handling
manager = HookManager()
success = manager.safe_execute(risky_function)

# Graceful degradation
if not success:
    logger.warning("Function failed, continuing with fallback")
```

### Retry Logic

Metrics server startup includes retry logic:

```python
# Retry with exponential backoff
for attempt in range(max_retries):
    if start_server():
        return True
    wait_time = retry_delay * (attempt + 1)
    time.sleep(wait_time)
```

## Best Practices

### Hook Implementation

1. **Use HookContext** - Always use structured context for hook execution
2. **Safe Execution** - Wrap risky operations in try-catch blocks
3. **Logging** - Provide detailed logging for debugging
4. **Graceful Degradation** - Continue operation even if some features fail

### Configuration Management

1. **Environment Variables** - Use environment variables for configuration
2. **CLI Integration** - Support CLI option overrides
3. **Validation** - Validate configuration before use
4. **Defaults** - Provide sensible defaults for all options

## Related Documentation

- [Hooks Overview](index.md) - Hooks component overview
- [Configuration Guide](../config/configuration.md) - Configuration options
- [Plugin Component](../plugin/) - Worker classes and metrics collection

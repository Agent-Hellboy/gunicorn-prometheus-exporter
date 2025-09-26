# Hooks Component

The hooks component provides pre-built Gunicorn hooks for automatic setup and lifecycle management of the Prometheus metrics system.

## Overview

The hooks component manages:

- Gunicorn lifecycle events
- Metrics server startup and shutdown
- Worker initialization and cleanup
- Environment variable management
- Redis storage integration

## Available Hooks

### Default Hooks

- `default_on_starting` - Initialize master metrics and multiprocess directory
- `default_when_ready` - Start Prometheus metrics server
- `default_worker_int` - Handle worker interrupts and cleanup
- `default_on_exit` - Cleanup on server exit
- `default_post_fork` - Configure CLI options after worker fork

### Redis Hooks

- `redis_when_ready` - Start metrics server with Redis storage support

## Architecture

The hooks system uses a modular, class-based architecture with the **Manager pattern**:

### Core Classes

- **`HookManager`** - Centralized logging and execution management
- **`EnvironmentManager`** - CLI-to-environment variable mapping
- **`MetricsServerManager`** - Prometheus metrics server lifecycle
- **`ProcessManager`** - Process cleanup and termination

## Design Pattern Choice: Manager

### Why Manager Pattern for Hooks?

We chose the **Manager pattern** for the hooks component because:

1. **Centralized Control**: Managers coordinate complex operations across multiple systems
2. **Lifecycle Management**: Handle startup, shutdown, and cleanup operations
3. **Error Handling**: Provide consistent error handling and retry logic
4. **Resource Management**: Manage connections, processes, and other resources
5. **Separation of Concerns**: Each manager handles a specific domain (hooks, environment, metrics, processes)

### Alternative Patterns Considered

- **Factory Pattern**: Not suitable since we're not creating objects, but managing operations
- **Observer Pattern**: Overkill for simple hook execution
- **Command Pattern**: Unnecessary complexity for straightforward hook functions

### Implementation Benefits

```python
# Global manager instances
_hook_manager = None
_metrics_manager = None
_process_manager = None

def _get_hook_manager() -> HookManager:
    """Get or create the global hook manager instance."""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
    return _hook_manager

# Centralized execution with error handling
manager = _get_hook_manager()
success = manager.safe_execute(hook_function)
```

### HookContext

Provides structured context for hook execution:

```python
@dataclass
class HookContext:
    server: Any
    worker: Optional[Any] = None
    logger: Optional[logging.Logger] = None
```

## Usage

### Basic Configuration

```python
# gunicorn.conf.py
from gunicorn_prometheus_exporter.hooks import (
    default_on_starting,
    default_when_ready,
    default_worker_int,
    default_on_exit,
    default_post_fork,
)

# Use pre-built hooks
on_starting = default_on_starting
when_ready = default_when_ready
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork
```

### Redis Configuration

```python
# gunicorn.conf.py
from gunicorn_prometheus_exporter.hooks import (
    default_on_starting,
    redis_when_ready,
    default_worker_int,
    default_on_exit,
    default_post_fork,
)

# Use Redis-enabled hooks
on_starting = default_on_starting
when_ready = redis_when_ready
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork
```

## Documentation

- [API Reference](api-reference.md) - Complete hooks API documentation

## Configuration

Hooks automatically read configuration from environment variables and Gunicorn settings. No additional configuration is required for basic usage.

For advanced configuration, see the [Configuration Guide](../config/configuration.md).

## Examples

See the [Examples](../examples/) for configuration examples and usage patterns.

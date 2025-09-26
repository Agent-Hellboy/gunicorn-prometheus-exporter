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

The hooks system uses a modular, class-based architecture:

### Core Classes

- **`HookManager`** - Centralized logging and execution management
- **`EnvironmentManager`** - CLI-to-environment variable mapping
- **`MetricsServerManager`** - Prometheus metrics server lifecycle
- **`ProcessManager`** - Process cleanup and termination

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

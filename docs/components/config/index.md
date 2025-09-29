# Configuration Component

The configuration component manages all settings and options for the Gunicorn Prometheus Exporter using a **ConfigManager pattern** with lifecycle management that follows software engineering best practices.

## Overview

The configuration component handles:

- **ConfigManager Pattern**: Centralized configuration lifecycle management
- **State Management**: Proper initialization, validation, and cleanup states
- **Lazy Loading**: Environment variables are read only when needed
- **Type Safety**: Automatic type conversion with validation
- **CLI Integration**: Gunicorn CLI options update environment variables
- **Comprehensive Validation**: Clear error messages for missing or invalid configuration
- **Thread Safety**: Safe concurrent access with proper locking

## Design Pattern Choice: ConfigManager

### Why ConfigManager for Configuration?

We chose the **ConfigManager pattern** for the configuration component because:

1. **Lifecycle Management**: Proper initialization, validation, and cleanup states
2. **State Tracking**: Clear state transitions and error handling
3. **Thread Safety**: Safe concurrent access with proper locking mechanisms
4. **Validation Control**: Centralized validation with detailed error reporting
5. **Resource Management**: Proper cleanup and resource management
6. **Global Access**: All components can access the same configuration instance

### Alternative Patterns Considered

- **Singleton Pattern**: Lacks lifecycle management and state tracking
- **Factory Pattern**: Overkill since we only need one configuration type
- **Builder Pattern**: Unnecessary complexity for simple configuration loading
- **Strategy Pattern**: Not needed since configuration behavior is consistent

### Implementation Benefits

```python
# ConfigManager with lifecycle management

from gunicorn_prometheus_exporter.config import get_config, initialize_config

# Initialize configuration with validation

initialize_config(
    PROMETHEUS_METRICS_PORT="9091",
    PROMETHEUS_BIND_ADDRESS="0.0.0.0",
    GUNICORN_WORKERS="2"
)

# All components access the same instance
config = get_config()
port = config.prometheus_metrics_port  # Consistent across all modules
```

## Configuration Sources

### Environment Variables

Primary configuration method:

```bash
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
export PROMETHEUS_METRICS_PORT="9091"
export PROMETHEUS_BIND_ADDRESS="0.0.0.0"
export GUNICORN_WORKERS="2"
```

### Gunicorn Configuration Files

Configuration can also be set in Gunicorn config files:

```python
# gunicorn.conf.py
import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

## Configuration Categories

### Core Configuration

| Variable                   | Default                     | Description                               |
| -------------------------- | --------------------------- | ----------------------------------------- |
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus_multiproc` | Directory for multiprocess metrics        |
| `PROMETHEUS_METRICS_PORT`  | `9091`                      | Port for metrics endpoint                 |
| `PROMETHEUS_BIND_ADDRESS`  | `0.0.0.0`                   | Bind address for metrics server           |
| `GUNICORN_WORKERS`         | `1`                         | Number of workers for metrics calculation |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_ENABLED` | `false` | Enable Redis storage backend |
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis database number |
| `REDIS_KEY_PREFIX` | `gunicorn` | Prefix for Redis keys |
| `REDIS_TTL_SECONDS` | `300` | Key expiration time in seconds |

### Debug Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_DEBUG` | `false` | Enable debug logging |
| `REDIS_DEBUG` | `false` | Enable Redis debug logging |

## Documentation

- [Configuration Guide](configuration.md) - Complete configuration guide with all options and scenarios
- [Configuration Flow](configuration-flow.md) - Visual representation of the configuration loading process
- [API Reference](api-reference.md) - Detailed API documentation for configuration classes and methods

## Configuration Access Patterns

### ConfigManager Access
```python
# Import the config manager functions
from gunicorn_prometheus_exporter.config import get_config, initialize_config

# Initialize configuration (typically done once at startup)
initialize_config(
    PROMETHEUS_METRICS_PORT="9091",
    PROMETHEUS_BIND_ADDRESS="0.0.0.0",
    GUNICORN_WORKERS="2"
)

# Get the configuration instance
config = get_config()
port = config.prometheus_metrics_port
redis_enabled = config.redis_enabled
```

### Direct ConfigManager Access
```python
# Import the ConfigManager class
from gunicorn_prometheus_exporter.config import ConfigManager

# Create and manage configuration
manager = ConfigManager()
manager.initialize(
    PROMETHEUS_METRICS_PORT="9091",
    PROMETHEUS_BIND_ADDRESS="0.0.0.0",
    GUNICORN_WORKERS="2"
)

# Get configuration
config = manager.get_config()
port = config.prometheus_metrics_port
```

### Module-Level Access
```python
# Import config from the main module
from gunicorn_prometheus_exporter import get_config

# Access configuration values
config = get_config()
port = config.prometheus_metrics_port
```

## Validation

The configuration component validates all settings and provides helpful error messages for invalid configurations.

## Examples

See the [Examples](../examples/) for configuration examples and best practices.

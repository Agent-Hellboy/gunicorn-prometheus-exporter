# Configuration Component

The configuration component manages all settings and options for the Gunicorn Prometheus Exporter using a **singleton pattern** that follows software engineering best practices.

## Overview

The configuration component handles:

- **Singleton Pattern**: Single configuration instance for the entire application
- **Lazy Loading**: Environment variables are read only when needed
- **Type Safety**: Automatic type conversion with validation
- **CLI Integration**: Gunicorn CLI options update environment variables
- **Comprehensive Validation**: Clear error messages for missing or invalid configuration

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

### Global Singleton Access
```python
# Import the global config instance
from gunicorn_prometheus_exporter.config import config

# Access configuration values
port = config.prometheus_metrics_port
redis_enabled = config.redis_enabled
```

### Function-Based Access
```python
# Import the get_config function
from gunicorn_prometheus_exporter.config import get_config

# Get the singleton instance
config = get_config()
port = config.prometheus_metrics_port
```

### Module-Level Access
```python
# Import config from the main module
from gunicorn_prometheus_exporter import config

# Access configuration values
port = config.prometheus_metrics_port
```

## Validation

The configuration component validates all settings and provides helpful error messages for invalid configurations.

## Examples

See the [Examples](../examples/) for configuration examples and best practices.

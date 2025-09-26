# Configuration Component

The configuration component manages all settings and options for the Gunicorn Prometheus Exporter.

## Overview

The configuration component handles:

- Environment variable management
- Configuration validation
- Default value assignment
- Runtime configuration updates

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

- [Configuration Guide](configuration.md) - Complete configuration documentation
- [API Reference](api-reference.md) - Configuration API documentation

## Validation

The configuration component validates all settings and provides helpful error messages for invalid configurations.

## Examples

See the [Examples](../examples/) for configuration examples and best practices.

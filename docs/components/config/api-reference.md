# Configuration API Reference

This document provides detailed API reference for the configuration component using the **singleton pattern**.

## Core Classes

### ExporterConfig

Main configuration management class using singleton pattern.

```python
class ExporterConfig:
    """Configuration class for Gunicorn Prometheus Exporter."""

    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        self._setup_multiproc_dir()

    def _setup_multiproc_dir(self):
        """Set up the Prometheus multiprocess directory."""
        if not os.environ.get(self.ENV_PROMETHEUS_MULTIPROC_DIR):
            os.environ[self.ENV_PROMETHEUS_MULTIPROC_DIR] = self.PROMETHEUS_MULTIPROC_DIR

    @property
    def prometheus_metrics_port(self) -> int:
        """Get the Prometheus metrics server port."""
        value = os.environ.get(self.ENV_PROMETHEUS_METRICS_PORT, self.PROMETHEUS_METRICS_PORT)
        if value is None:
            raise ValueError(f"Environment variable {self.ENV_PROMETHEUS_METRICS_PORT} must be set in production.")
        return int(value)

    @property
    def redis_enabled(self) -> bool:
        """Check if Redis storage is enabled."""
        return os.environ.get(self.ENV_REDIS_ENABLED, "").lower() in ("true", "1", "yes", "on")
```

**Properties:**

- `prometheus_multiproc_dir` - Prometheus multiprocess directory
- `prometheus_metrics_port` - Metrics server port (required in production)
- `prometheus_bind_address` - Metrics server bind address (required in production)
- `gunicorn_workers` - Number of Gunicorn workers (required in production)
- `gunicorn_timeout` - Gunicorn worker timeout
- `gunicorn_keepalive` - Gunicorn keepalive setting
- `redis_enabled` - Whether Redis storage is enabled
- `redis_host` - Redis server host
- `redis_port` - Redis server port
- `redis_db` - Redis database number
- `redis_password` - Redis password
- `redis_key_prefix` - Redis key prefix
- `redis_ttl_seconds` - Redis TTL in seconds
- `redis_ttl_disabled` - Whether Redis TTL is disabled

**Methods:**

- `validate()` - Validate configuration
- `get_gunicorn_config()` - Get Gunicorn-specific configuration
- `get_prometheus_config()` - Get Prometheus-specific configuration
- `print_config()` - Print current configuration

### Global Configuration Instance

The configuration system uses a global singleton instance:

```python
# Global configuration instance
config = ExporterConfig()

def get_config() -> ExporterConfig:
    """Get the global configuration instance."""
    return config
```

**Usage:**

```python
# Import the global config instance
from gunicorn_prometheus_exporter.config import config

# Access configuration values
port = config.prometheus_metrics_port
redis_enabled = config.redis_enabled

# Or use the get_config function
from gunicorn_prometheus_exporter.config import get_config
config = get_config()
port = config.prometheus_metrics_port
```

## Configuration Loading

### Lazy Loading Pattern

The configuration system uses lazy loading - environment variables are read only when properties are accessed:

```python
@property
def prometheus_metrics_port(self) -> int:
    """Get the Prometheus metrics server port."""
    value = os.environ.get(self.ENV_PROMETHEUS_METRICS_PORT, self.PROMETHEUS_METRICS_PORT)
    if value is None:
        raise ValueError(
            f"Environment variable {self.ENV_PROMETHEUS_METRICS_PORT} "
            f"must be set in production. "
            f"Example: export {self.ENV_PROMETHEUS_METRICS_PORT}=9091"
        )
    return int(value)

@property
def redis_enabled(self) -> bool:
    """Check if Redis storage is enabled."""
    return os.environ.get(self.ENV_REDIS_ENABLED, "").lower() in (
        "true", "1", "yes", "on"
    )
```

### Environment Variable Processing

Environment variables are processed in multiple phases:

1. **Module-level defaults** - Some variables read at import time
2. **Singleton initialization** - Multiprocess directory setup
3. **Property access** - Lazy loading with validation
4. **CLI integration** - Gunicorn CLI options update environment variables

### Configuration Validation

The configuration system includes comprehensive validation with clear error messages:

```python
@property
def prometheus_metrics_port(self) -> int:
    """Get the Prometheus metrics server port."""
    value = os.environ.get(self.ENV_PROMETHEUS_METRICS_PORT, self.PROMETHEUS_METRICS_PORT)
    if value is None:
        raise ValueError(
            f"Environment variable {self.ENV_PROMETHEUS_METRICS_PORT} "
            f"must be set in production. "
            f"Example: export {self.ENV_PROMETHEUS_METRICS_PORT}=9091"
        )
    return int(value)

@property
def gunicorn_timeout(self) -> int:
    """Get the Gunicorn worker timeout."""
    return int(
        os.environ.get(self.ENV_GUNICORN_TIMEOUT, str(self.GUNICORN_TIMEOUT))
    )

def validate(self) -> bool:
    """Validate configuration."""
    try:
        # Test required properties
        _ = self.prometheus_metrics_port
        _ = self.prometheus_bind_address
        _ = self.gunicorn_workers
        return True
    except ValueError:
        return False
```

## Configuration Sources

### Environment Variables

Primary configuration source - environment variables are read lazily through properties:

```python
# Environment variable names (constants)
ENV_PROMETHEUS_MULTIPROC_DIR = "PROMETHEUS_MULTIPROC_DIR"
ENV_PROMETHEUS_METRICS_PORT = "PROMETHEUS_METRICS_PORT"
ENV_PROMETHEUS_BIND_ADDRESS = "PROMETHEUS_BIND_ADDRESS"
ENV_GUNICORN_WORKERS = "GUNICORN_WORKERS"
ENV_REDIS_ENABLED = "REDIS_ENABLED"
ENV_REDIS_HOST = "REDIS_HOST"
ENV_REDIS_PORT = "REDIS_PORT"
ENV_REDIS_DB = "REDIS_DB"
ENV_REDIS_KEY_PREFIX = "REDIS_KEY_PREFIX"
ENV_REDIS_TTL_SECONDS = "REDIS_TTL_SECONDS"
ENV_REDIS_PASSWORD = "REDIS_PASSWORD"
```

### CLI Integration

Gunicorn CLI options are integrated through the `post_fork` hook:

```python
def default_post_fork(server, worker):
    """Default post_fork hook to configure CLI options after worker fork."""
    env_manager = EnvironmentManager(logger)
    env_manager.update_from_cli(server.cfg)

def _update_workers_env(self, cfg):
    """Update GUNICORN_WORKERS environment variable from CLI."""
    if hasattr(cfg, "workers") and cfg.workers:
        os.environ["GUNICORN_WORKERS"] = str(cfg.workers)
```

## Configuration Categories

### Required (Production)

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `PROMETHEUS_METRICS_PORT` | int | Metrics server port | `9091` |
| `PROMETHEUS_BIND_ADDRESS` | str | Metrics server bind address | `0.0.0.0` |
| `GUNICORN_WORKERS` | int | Number of workers | `4` |

### Optional (Defaults)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PROMETHEUS_MULTIPROC_DIR` | str | `~/.gunicorn_prometheus` | Multiprocess directory |
| `GUNICORN_TIMEOUT` | int | `30` | Worker timeout |
| `GUNICORN_KEEPALIVE` | int | `2` | Keepalive setting |

### Redis Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_ENABLED` | bool | `false` | Enable Redis storage |
| `REDIS_HOST` | str | `127.0.0.1` | Redis host |
| `REDIS_PORT` | int | `6379` | Redis port |
| `REDIS_DB` | int | `0` | Redis database |
| `REDIS_PASSWORD` | str | `None` | Redis password |
| `REDIS_KEY_PREFIX` | str | `gunicorn` | Key prefix |
| `REDIS_TTL_SECONDS` | int | `300` | TTL for keys |
| `REDIS_TTL_DISABLED` | bool | `false` | Disable TTL |

### SSL/TLS Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PROMETHEUS_SSL_CERTFILE` | str | `None` | SSL certificate file |
| `PROMETHEUS_SSL_KEYFILE` | str | `None` | SSL key file |
| `PROMETHEUS_SSL_CLIENT_CAFILE` | str | `None` | Client CA file |
| `PROMETHEUS_SSL_CLIENT_CAPATH` | str | `None` | Client CA path |
| `PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED` | bool | `false` | Require client auth |

## Error Handling

### Configuration Validation Errors

The configuration system provides clear error messages for missing or invalid configuration:

```python
@property
def prometheus_metrics_port(self) -> int:
    """Get the Prometheus metrics server port."""
    value = os.environ.get(self.ENV_PROMETHEUS_METRICS_PORT, self.PROMETHEUS_METRICS_PORT)
    if value is None:
        raise ValueError(
            f"Environment variable {self.ENV_PROMETHEUS_METRICS_PORT} "
            f"must be set in production. "
            f"Example: export {self.ENV_PROMETHEUS_METRICS_PORT}=9091"
        )
    return int(value)

@property
def gunicorn_workers(self) -> int:
    """Get the number of Gunicorn workers."""
    value = os.environ.get(self.ENV_GUNICORN_WORKERS, self.GUNICORN_WORKERS)
    if value is None:
        raise ValueError(
            f"Environment variable {self.ENV_GUNICORN_WORKERS} "
            f"must be set in production. "
            f"Example: export {self.ENV_GUNICORN_WORKERS}=4"
        )
    return int(value)
```

### Type Conversion Errors

Automatic type conversion with error handling:

```python
@property
def gunicorn_timeout(self) -> int:
    """Get the Gunicorn worker timeout."""
    return int(
        os.environ.get(self.ENV_GUNICORN_TIMEOUT, str(self.GUNICORN_TIMEOUT))
    )

@property
def redis_port(self) -> int:
    """Get Redis port."""
    return int(os.environ.get(self.ENV_REDIS_PORT, "6379"))
```

## Configuration Access Patterns

### Global Singleton Access

```python
# Import the global config instance
from gunicorn_prometheus_exporter.config import config

# Access configuration values
port = config.prometheus_metrics_port
redis_enabled = config.redis_enabled
timeout = config.gunicorn_timeout
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

### Testing Configuration

```python
# For testing purposes, you can modify the singleton
config.redis_enabled = True
config.redis_host = "test-host"

# Or delete properties to test defaults
del config.redis_enabled
```

## Best Practices

### Singleton Pattern Benefits

1. **Single Source of Truth**: One configuration instance for the entire application
2. **Consistent State**: All modules access the same configuration values
3. **Lazy Loading**: Environment variables are read only when needed
4. **Thread Safety**: Safe for multi-threaded and multi-process environments
5. **Memory Efficiency**: Only one configuration object exists in memory

### Configuration Management

1. **Use Environment Variables**: Primary configuration method
2. **Lazy Loading**: Properties read environment variables on access
3. **Validation**: Clear error messages for missing or invalid configuration
4. **Type Safety**: Automatic type conversion with validation
5. **CLI Integration**: Gunicorn CLI options update environment variables

### Security Considerations

1. **Sensitive Data**: Use environment variables for secrets
2. **Validation**: Validate all input parameters
3. **Error Messages**: Provide helpful error messages without exposing sensitive data
4. **Default Values**: Use secure defaults for development

## Related Documentation

- [Configuration Guide](configuration.md) - Complete configuration guide with all options and scenarios
- [Configuration Flow](configuration-flow.md) - Visual representation of the configuration loading process
- [Examples Component](../examples/) - Configuration examples
- [Metrics Component](../metrics/) - Metrics configuration
- [Backend Component](../backend/) - Backend configuration

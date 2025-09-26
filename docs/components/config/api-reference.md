# Configuration API Reference

This document provides detailed API reference for the configuration component.

## Core Classes

### Config

Main configuration management class.

```python
class Config:
    """Configuration management for Gunicorn Prometheus Exporter."""

    def __init__(self):
        self.prometheus_multiproc_dir = os.getenv('PROMETHEUS_MULTIPROC_DIR', '/tmp/prometheus_multiproc')
        self.prometheus_metrics_port = int(os.getenv('PROMETHEUS_METRICS_PORT', '9091'))
        self.prometheus_bind_address = os.getenv('PROMETHEUS_BIND_ADDRESS', '0.0.0.0')
        self.gunicorn_workers = int(os.getenv('GUNICORN_WORKERS', '1'))
        self.redis_enabled = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_db = int(os.getenv('REDIS_DB', '0'))
        self.redis_key_prefix = os.getenv('REDIS_KEY_PREFIX', 'gunicorn')
        self.redis_ttl_seconds = int(os.getenv('REDIS_TTL_SECONDS', '300'))
        self.redis_password = os.getenv('REDIS_PASSWORD')
        self.redis_ssl = os.getenv('REDIS_SSL', 'false').lower() == 'true'
        self.debug = os.getenv('PROMETHEUS_DEBUG', 'false').lower() == 'true'
```

**Methods:**

- `validate()` - Validate configuration
- `get_prometheus_config()` - Get Prometheus-specific configuration
- `get_redis_config()` - Get Redis-specific configuration
- `is_redis_enabled()` - Check if Redis is enabled
- `is_debug_enabled()` - Check if debug mode is enabled

### PrometheusConfig

Prometheus-specific configuration.

```python
class PrometheusConfig:
    """Prometheus-specific configuration."""

    def __init__(self, multiproc_dir, metrics_port, bind_address, workers):
        self.multiproc_dir = multiproc_dir
        self.metrics_port = metrics_port
        self.bind_address = bind_address
        self.workers = workers
```

**Methods:**

- `validate()` - Validate Prometheus configuration
- `get_multiproc_dir()` - Get multiprocess directory
- `get_metrics_port()` - Get metrics port
- `get_bind_address()` - Get bind address
- `get_workers()` - Get number of workers

### RedisConfig

Redis-specific configuration.

```python
class RedisConfig:
    """Redis-specific configuration."""

    def __init__(self, enabled, host, port, db, key_prefix, ttl_seconds, password=None, ssl=False):
        self.enabled = enabled
        self.host = host
        self.port = port
        self.db = db
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_seconds
        self.password = password
        self.ssl = ssl
```

**Methods:**

- `validate()` - Validate Redis configuration
- `is_enabled()` - Check if Redis is enabled
- `get_connection_params()` - Get Redis connection parameters
- `get_key_prefix()` - Get Redis key prefix
- `get_ttl()` - Get TTL in seconds

## Configuration Loading

### Environment Variable Loading

```python
def load_from_env():
    """Load configuration from environment variables."""
    config = {}

    # Prometheus configuration
    config['prometheus'] = {
        'multiproc_dir': os.getenv('PROMETHEUS_MULTIPROC_DIR', '/tmp/prometheus_multiproc'),
        'metrics_port': int(os.getenv('PROMETHEUS_METRICS_PORT', '9091')),
        'bind_address': os.getenv('PROMETHEUS_BIND_ADDRESS', '0.0.0.0'),
        'workers': int(os.getenv('GUNICORN_WORKERS', '1'))
    }

    # Redis configuration
    config['redis'] = {
        'enabled': os.getenv('REDIS_ENABLED', 'false').lower() == 'true',
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', '6379')),
        'db': int(os.getenv('REDIS_DB', '0')),
        'key_prefix': os.getenv('REDIS_KEY_PREFIX', 'gunicorn'),
        'ttl_seconds': int(os.getenv('REDIS_TTL_SECONDS', '300')),
        'password': os.getenv('REDIS_PASSWORD'),
        'ssl': os.getenv('REDIS_SSL', 'false').lower() == 'true'
    }

    # Debug configuration
    config['debug'] = {
        'prometheus': os.getenv('PROMETHEUS_DEBUG', 'false').lower() == 'true',
        'redis': os.getenv('REDIS_DEBUG', 'false').lower() == 'true'
    }

    return config
```

### Configuration Validation

```python
def validate_config(config):
    """Validate configuration parameters."""
    errors = []

    # Validate Prometheus configuration
    prometheus = config.get('prometheus', {})
    if not prometheus.get('multiproc_dir'):
        errors.append("PROMETHEUS_MULTIPROC_DIR is required")

    if not (1 <= prometheus.get('metrics_port', 0) <= 65535):
        errors.append("PROMETHEUS_METRICS_PORT must be between 1 and 65535")

    if not (1 <= prometheus.get('workers', 0) <= 100):
        errors.append("GUNICORN_WORKERS must be between 1 and 100")

    # Validate Redis configuration
    redis = config.get('redis', {})
    if redis.get('enabled'):
        if not redis.get('host'):
            errors.append("REDIS_HOST is required when Redis is enabled")

        if not (1 <= redis.get('port', 0) <= 65535):
            errors.append("REDIS_PORT must be between 1 and 65535")

        if not (0 <= redis.get('db', -1) <= 15):
            errors.append("REDIS_DB must be between 0 and 15")

    if errors:
        raise ConfigurationError(f"Configuration validation failed: {', '.join(errors)}")

    return True
```

## Configuration Sources

### Environment Variables

Primary configuration source:

```python
def get_env_config():
    """Get configuration from environment variables."""
    return {
        'PROMETHEUS_MULTIPROC_DIR': os.getenv('PROMETHEUS_MULTIPROC_DIR'),
        'PROMETHEUS_METRICS_PORT': os.getenv('PROMETHEUS_METRICS_PORT'),
        'PROMETHEUS_BIND_ADDRESS': os.getenv('PROMETHEUS_BIND_ADDRESS'),
        'GUNICORN_WORKERS': os.getenv('GUNICORN_WORKERS'),
        'REDIS_ENABLED': os.getenv('REDIS_ENABLED'),
        'REDIS_HOST': os.getenv('REDIS_HOST'),
        'REDIS_PORT': os.getenv('REDIS_PORT'),
        'REDIS_DB': os.getenv('REDIS_DB'),
        'REDIS_KEY_PREFIX': os.getenv('REDIS_KEY_PREFIX'),
        'REDIS_TTL_SECONDS': os.getenv('REDIS_TTL_SECONDS'),
        'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD'),
        'REDIS_SSL': os.getenv('REDIS_SSL'),
        'PROMETHEUS_DEBUG': os.getenv('PROMETHEUS_DEBUG'),
        'REDIS_DEBUG': os.getenv('REDIS_DEBUG')
    }
```

### Configuration Files

Support for configuration files:

```python
def load_config_file(filepath):
    """Load configuration from file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Configuration file not found: {filepath}")

    with open(filepath, 'r') as f:
        if filepath.endswith('.json'):
            return json.load(f)
        elif filepath.endswith('.yaml') or filepath.endswith('.yml'):
            return yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {filepath}")
```

## Configuration Categories

### Core Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PROMETHEUS_MULTIPROC_DIR` | str | `/tmp/prometheus_multiproc` | Directory for multiprocess metrics |
| `PROMETHEUS_METRICS_PORT` | int | `9091` | Port for metrics endpoint |
| `PROMETHEUS_BIND_ADDRESS` | str | `0.0.0.0` | Bind address for metrics server |
| `GUNICORN_WORKERS` | int | `1` | Number of workers for metrics calculation |

### Redis Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_ENABLED` | bool | `false` | Enable Redis storage backend |
| `REDIS_HOST` | str | `localhost` | Redis server hostname |
| `REDIS_PORT` | int | `6379` | Redis server port |
| `REDIS_DB` | int | `0` | Redis database number |
| `REDIS_KEY_PREFIX` | str | `gunicorn` | Prefix for Redis keys |
| `REDIS_TTL_SECONDS` | int | `300` | Key expiration time in seconds |
| `REDIS_PASSWORD` | str | - | Redis password (if required) |
| `REDIS_SSL` | bool | `false` | Enable SSL connection to Redis |

### Debug Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PROMETHEUS_DEBUG` | bool | `false` | Enable debug logging |
| `REDIS_DEBUG` | bool | `false` | Enable Redis debug logging |

## Error Handling

### Configuration Errors

```python
class ConfigurationError(Exception):
    """Configuration-related error."""
    pass

class ValidationError(ConfigurationError):
    """Configuration validation error."""
    pass

class MissingConfigError(ConfigurationError):
    """Missing configuration error."""
    pass
```

### Error Handling

```python
def safe_get_config(key, default=None, required=False):
    """Safely get configuration value."""
    try:
        value = os.getenv(key, default)
        if required and value is None:
            raise MissingConfigError(f"Required configuration {key} is missing")
        return value
    except Exception as e:
        raise ConfigurationError(f"Failed to get configuration {key}: {e}")
```

## Configuration Updates

### Runtime Updates

```python
def update_config(new_config):
    """Update configuration at runtime."""
    global current_config
    old_config = current_config.copy()

    try:
        # Validate new configuration
        validate_config(new_config)

        # Update configuration
        current_config.update(new_config)

        # Apply changes
        apply_config_changes(old_config, new_config)

    except Exception as e:
        # Rollback on error
        current_config = old_config
        raise ConfigurationError(f"Failed to update configuration: {e}")
```

### Configuration Reload

```python
def reload_config():
    """Reload configuration from sources."""
    try:
        # Load from environment
        env_config = load_from_env()

        # Load from files if specified
        file_config = {}
        config_file = os.getenv('CONFIG_FILE')
        if config_file:
            file_config = load_config_file(config_file)

        # Merge configurations
        merged_config = {**env_config, **file_config}

        # Validate and apply
        validate_config(merged_config)
        update_config(merged_config)

    except Exception as e:
        raise ConfigurationError(f"Failed to reload configuration: {e}")
```

## Best Practices

### Configuration Management

1. **Use Environment Variables**: Primary configuration method
2. **Validate Early**: Validate configuration at startup
3. **Provide Defaults**: Always provide sensible defaults
4. **Document Options**: Document all configuration options
5. **Handle Errors**: Provide clear error messages

### Security Considerations

1. **Sensitive Data**: Use environment variables for secrets
2. **Validation**: Validate all input parameters
3. **Access Control**: Restrict configuration file access
4. **Audit Logging**: Log configuration changes

## Related Documentation

- [Configuration Guide](../configuration.md) - Complete configuration documentation
- [Examples Component](../examples/) - Configuration examples
- [Metrics Component](../metrics/) - Metrics configuration
- [Backend Component](../backend/) - Backend configuration

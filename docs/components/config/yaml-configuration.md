# YAML Configuration Guide

Complete guide for using YAML configuration files with the Gunicorn Prometheus Exporter.

## Overview

The YAML configuration system provides a structured, readable way to configure the Gunicorn Prometheus Exporter. It offers several advantages over environment variables:

- **Structured Configuration**: Clean, hierarchical configuration structure
- **Readability**: Easy to read and understand configuration options
- **Validation**: Comprehensive validation with clear error messages
- **Environment Override**: YAML settings can be overridden by environment variables
- **Backward Compatibility**: Full compatibility with existing environment variable configuration

## YAML Configuration Structure

### Basic Structure

```yaml
exporter:
  prometheus:
    # Prometheus metrics server configuration
  gunicorn:
    # Gunicorn worker configuration
  redis:
    # Redis storage configuration
  ssl:
    # SSL/TLS configuration
  cleanup:
    # Cleanup configuration
```

### Complete Configuration Example

```yaml
# gunicorn-prometheus-exporter.yml
exporter:
  prometheus:
    metrics_port: 9091
    bind_address: "0.0.0.0"
    multiproc_dir: "/tmp/prometheus_multiproc"
  gunicorn:
    workers: 2
    timeout: 30
    keepalive: 2
  redis:
    enabled: false
    host: "localhost"
    port: 6379
    db: 0
    password: ""
    key_prefix: "gunicorn"
    ttl_seconds: 300
    ttl_disabled: false
  ssl:
    enabled: false
    certfile: ""
    keyfile: ""
    client_cafile: ""
    client_capath: ""
    client_auth_required: false
  cleanup:
    db_files: true
```

## Configuration Sections

### Prometheus Configuration

Controls the Prometheus metrics server settings:

```yaml
exporter:
  prometheus:
    metrics_port: 9091          # Port for metrics endpoint
    bind_address: "0.0.0.0"     # Bind address for metrics server
    multiproc_dir: "/tmp/prometheus_multiproc"  # Directory for multiprocess metrics
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `metrics_port` | int | `9091` | Port for the Prometheus metrics endpoint |
| `bind_address` | str | `"0.0.0.0"` | Bind address for the metrics server |
| `multiproc_dir` | str | `"/tmp/prometheus_multiproc"` | Directory for multiprocess metrics storage |

### Gunicorn Configuration

Controls Gunicorn worker settings:

```yaml
exporter:
  gunicorn:
    workers: 2        # Number of workers
    timeout: 30       # Worker timeout in seconds
    keepalive: 2      # Keepalive timeout in seconds
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `workers` | int | `1` | Number of Gunicorn workers |
| `timeout` | int | `30` | Worker timeout in seconds |
| `keepalive` | int | `2` | Keepalive timeout in seconds |

### Redis Configuration

Controls Redis storage backend settings:

```yaml
exporter:
  redis:
    enabled: false           # Enable Redis storage
    host: "localhost"        # Redis server host
    port: 6379              # Redis server port
    db: 0                   # Redis database number
    password: ""            # Redis password
    key_prefix: "gunicorn"  # Prefix for Redis keys
    ttl_seconds: 300        # TTL for keys in seconds
    ttl_disabled: false     # Disable TTL
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `false` | Enable Redis storage backend |
| `host` | str | `"localhost"` | Redis server hostname |
| `port` | int | `6379` | Redis server port |
| `db` | int | `0` | Redis database number |
| `password` | str | `""` | Redis password (empty for no auth) |
| `key_prefix` | str | `"gunicorn"` | Prefix for Redis keys |
| `ttl_seconds` | int | `300` | TTL for keys in seconds |
| `ttl_disabled` | bool | `false` | Disable TTL for keys |

### SSL Configuration

Controls SSL/TLS settings for the metrics server:

```yaml
exporter:
  ssl:
    enabled: false                    # Enable SSL/TLS
    certfile: ""                      # SSL certificate file
    keyfile: ""                       # SSL key file
    client_cafile: ""                 # Client CA file
    client_capath: ""                 # Client CA path
    client_auth_required: false       # Require client authentication
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `false` | Enable SSL/TLS for metrics server |
| `certfile` | str | `""` | Path to SSL certificate file |
| `keyfile` | str | `""` | Path to SSL key file |
| `client_cafile` | str | `""` | Path to client CA file |
| `client_capath` | str | `""` | Path to client CA directory |
| `client_auth_required` | bool | `false` | Require client certificate authentication |

### Cleanup Configuration

Controls cleanup behavior:

```yaml
exporter:
  cleanup:
    db_files: true    # Clean up old metric files
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `db_files` | bool | `true` | Clean up old metric database files |

## Configuration Examples

### Basic Configuration

Simple setup for development or testing:

```yaml
# gunicorn-prometheus-exporter-basic.yml
exporter:
  prometheus:
    metrics_port: 9091
    bind_address: "0.0.0.0"
    multiproc_dir: "/tmp/prometheus_multiproc"
  gunicorn:
    workers: 2
    timeout: 30
    keepalive: 2
  redis:
    enabled: false
  ssl:
    enabled: false
  cleanup:
    db_files: true
```

### Redis Configuration

Production setup with Redis storage:

```yaml
# gunicorn-prometheus-exporter-redis.yml
exporter:
  prometheus:
    metrics_port: 9091
    bind_address: "0.0.0.0"
    multiproc_dir: "/tmp/prometheus_multiproc"
  gunicorn:
    workers: 4
    timeout: 60
    keepalive: 5
  redis:
    enabled: true
    host: "redis.example.com"
    port: 6379
    db: 0
    password: "secret"
    key_prefix: "gunicorn_prod"
    ttl_seconds: 600
    ttl_disabled: false
  ssl:
    enabled: false
  cleanup:
    db_files: false
```

### SSL Configuration

Secure setup with SSL/TLS:

```yaml
# gunicorn-prometheus-exporter-ssl.yml
exporter:
  prometheus:
    metrics_port: 9091
    bind_address: "0.0.0.0"
    multiproc_dir: "/tmp/prometheus_multiproc"
  gunicorn:
    workers: 2
    timeout: 30
    keepalive: 2
  redis:
    enabled: false
  ssl:
    enabled: true
    certfile: "/etc/ssl/certs/prometheus.crt"
    keyfile: "/etc/ssl/private/prometheus.key"
    client_cafile: "/etc/ssl/certs/ca.crt"
    client_capath: "/etc/ssl/certs"
    client_auth_required: true
  cleanup:
    db_files: true
```

### Production Configuration

Comprehensive production setup:

```yaml
# gunicorn-prometheus-exporter-production.yml
exporter:
  prometheus:
    metrics_port: 9091
    bind_address: "127.0.0.1"  # Bind to localhost only
    multiproc_dir: "/var/tmp/prometheus_multiproc"
  gunicorn:
    workers: 8
    timeout: 60
    keepalive: 5
  redis:
    enabled: true
    host: "redis.example.com"
    port: 6379
    db: 0
    password: "secret"
    key_prefix: "gunicorn_prod"
    ttl_seconds: 600
    ttl_disabled: false
  ssl:
    enabled: true
    certfile: "/etc/ssl/certs/prometheus.crt"
    keyfile: "/etc/ssl/private/prometheus.key"
    client_cafile: "/etc/ssl/certs/ca.crt"
    client_capath: "/etc/ssl/certs"
    client_auth_required: true
  cleanup:
    db_files: true
```

## Loading YAML Configuration

### In Gunicorn Configuration File

```python
# gunicorn_yaml.conf.py
from gunicorn_prometheus_exporter import load_yaml_config

# Load YAML configuration
load_yaml_config("gunicorn-prometheus-exporter.yml")

# Import hooks after loading YAML config
from gunicorn_prometheus_exporter.hooks import (
    default_when_ready,
    default_on_starting,
    default_worker_int,
    default_on_exit,
    default_post_fork,
)

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Use pre-built hooks
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork
```

### In Application Code

```python
# app.py
from gunicorn_prometheus_exporter import load_yaml_config

# Load YAML configuration
load_yaml_config("gunicorn-prometheus-exporter.yml")

# Your application code here
def app(environ, start_response):
    # Application logic
    pass
```

## Environment Variable Override

YAML configuration values can be overridden by environment variables. This allows you to:

- Use YAML for default configuration
- Override specific values for different environments
- Maintain security by keeping secrets in environment variables

### Override Examples

```bash
# Override metrics port
export PROMETHEUS_METRICS_PORT="9092"

# Override Redis settings
export REDIS_ENABLED="true"
export REDIS_HOST="redis.production.com"
export REDIS_PASSWORD="production_secret"

# Override SSL settings
export PROMETHEUS_SSL_ENABLED="true"
export PROMETHEUS_SSL_CERTFILE="/etc/ssl/certs/prod.crt"
export PROMETHEUS_SSL_KEYFILE="/etc/ssl/private/prod.key"
```

### Environment Variable Mapping

| YAML Path | Environment Variable |
|-----------|---------------------|
| `exporter.prometheus.metrics_port` | `PROMETHEUS_METRICS_PORT` |
| `exporter.prometheus.bind_address` | `PROMETHEUS_BIND_ADDRESS` |
| `exporter.prometheus.multiproc_dir` | `PROMETHEUS_MULTIPROC_DIR` |
| `exporter.gunicorn.workers` | `GUNICORN_WORKERS` |
| `exporter.gunicorn.timeout` | `GUNICORN_TIMEOUT` |
| `exporter.gunicorn.keepalive` | `GUNICORN_KEEPALIVE` |
| `exporter.redis.enabled` | `REDIS_ENABLED` |
| `exporter.redis.host` | `REDIS_HOST` |
| `exporter.redis.port` | `REDIS_PORT` |
| `exporter.redis.db` | `REDIS_DB` |
| `exporter.redis.password` | `REDIS_PASSWORD` |
| `exporter.redis.key_prefix` | `REDIS_KEY_PREFIX` |
| `exporter.redis.ttl_seconds` | `REDIS_TTL_SECONDS` |
| `exporter.redis.ttl_disabled` | `REDIS_TTL_DISABLED` |
| `exporter.ssl.enabled` | `PROMETHEUS_SSL_ENABLED` |
| `exporter.ssl.certfile` | `PROMETHEUS_SSL_CERTFILE` |
| `exporter.ssl.keyfile` | `PROMETHEUS_SSL_KEYFILE` |
| `exporter.ssl.client_cafile` | `PROMETHEUS_SSL_CLIENT_CAFILE` |
| `exporter.ssl.client_capath` | `PROMETHEUS_SSL_CLIENT_CAPATH` |
| `exporter.ssl.client_auth_required` | `PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED` |
| `exporter.cleanup.db_files` | `CLEANUP_DB_FILES` |

## Validation and Error Handling

### Configuration Validation

The YAML configuration system includes comprehensive validation:

```python
from gunicorn_prometheus_exporter import load_yaml_config

try:
    load_yaml_config("gunicorn-prometheus-exporter.yml")
    print("Configuration loaded successfully")
except FileNotFoundError:
    print("Configuration file not found")
except yaml.YAMLError as e:
    print(f"Invalid YAML: {e}")
except ValueError as e:
    print(f"Configuration validation failed: {e}")
```

### Common Validation Errors

1. **Missing Required Fields**: Required configuration sections are missing
2. **Invalid Values**: Values that don't match expected types or ranges
3. **File Not Found**: The YAML configuration file doesn't exist
4. **Invalid YAML**: The YAML file has syntax errors
5. **SSL Configuration**: SSL is enabled but certificate files are missing

### Error Messages

The system provides clear, actionable error messages:

```
ValueError: Configuration validation failed: SSL certificate file not found: /path/to/cert.pem
ValueError: Configuration validation failed: Invalid metrics port: 99999 (must be between 1 and 65535)
ValueError: Configuration validation failed: Redis host cannot be empty when Redis is enabled
```

## Best Practices

### Configuration Organization

1. **Use Descriptive Names**: Choose clear, descriptive names for configuration files
2. **Environment-Specific Files**: Create separate files for different environments
3. **Version Control**: Keep configuration files in version control
4. **Documentation**: Document any custom configuration options

### Security Considerations

1. **Sensitive Data**: Use environment variables for passwords and secrets
2. **File Permissions**: Ensure configuration files have appropriate permissions
3. **SSL Certificates**: Store SSL certificates in secure locations
4. **Network Security**: Bind to appropriate addresses (localhost for internal use)

### Performance Considerations

1. **Redis Configuration**: Use Redis for high-traffic applications
2. **Worker Count**: Set appropriate worker counts based on your application
3. **Timeout Settings**: Configure timeouts based on your application's needs
4. **Cleanup Settings**: Enable cleanup for development, disable for production

### Deployment Strategies

1. **Configuration Management**: Use configuration management tools (Ansible, Chef, etc.)
2. **Environment Variables**: Override configuration for different environments
3. **Docker**: Use Docker secrets for sensitive configuration
4. **Kubernetes**: Use ConfigMaps and Secrets for configuration

## Migration from Environment Variables

### Step 1: Create YAML Configuration

Create a YAML file with your current environment variable settings:

```yaml
# gunicorn-prometheus-exporter.yml
exporter:
  prometheus:
    metrics_port: 9091  # From PROMETHEUS_METRICS_PORT
    bind_address: "0.0.0.0"  # From PROMETHEUS_BIND_ADDRESS
    multiproc_dir: "/tmp/prometheus_multiproc"  # From PROMETHEUS_MULTIPROC_DIR
  gunicorn:
    workers: 2  # From GUNICORN_WORKERS
    timeout: 30  # From GUNICORN_TIMEOUT
    keepalive: 2  # From GUNICORN_KEEPALIVE
  redis:
    enabled: false  # From REDIS_ENABLED
    host: "localhost"  # From REDIS_HOST
    port: 6379  # From REDIS_PORT
    db: 0  # From REDIS_DB
  ssl:
    enabled: false  # From PROMETHEUS_SSL_ENABLED
  cleanup:
    db_files: true  # From CLEANUP_DB_FILES
```

### Step 2: Update Gunicorn Configuration

Update your Gunicorn configuration file to load YAML:

```python
# gunicorn.conf.py
from gunicorn_prometheus_exporter import load_yaml_config

# Load YAML configuration
load_yaml_config("gunicorn-prometheus-exporter.yml")

# Import hooks after loading YAML config
from gunicorn_prometheus_exporter.hooks import (
    default_when_ready,
    default_on_starting,
    default_worker_int,
    default_on_exit,
    default_post_fork,
)

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Use pre-built hooks
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork
```

### Step 3: Test Configuration

Test the new configuration:

```bash
# Test YAML configuration
gunicorn -c gunicorn.conf.py your_app:app

# Verify metrics endpoint
curl http://localhost:9091/metrics
```

### Step 4: Gradual Migration

You can gradually migrate by:

1. **Keep Environment Variables**: Environment variables will override YAML settings
2. **Test in Development**: Use YAML in development first
3. **Deploy to Staging**: Test in staging environment
4. **Production Deployment**: Deploy to production with monitoring

## Troubleshooting

### Common Issues

1. **Configuration Not Loading**: Check file path and permissions
2. **Validation Errors**: Verify YAML syntax and required fields
3. **Environment Override Not Working**: Check environment variable names
4. **SSL Issues**: Verify certificate file paths and permissions
5. **Redis Connection Issues**: Check Redis server availability and credentials

### Debugging

Enable debug logging to troubleshoot configuration issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from gunicorn_prometheus_exporter import load_yaml_config
load_yaml_config("gunicorn-prometheus-exporter.yml")
```

### Getting Help

If you encounter issues:

1. **Check Logs**: Review application logs for error messages
2. **Validate YAML**: Use a YAML validator to check syntax
3. **Test Configuration**: Use the configuration validation features
4. **Documentation**: Refer to the API reference for detailed information
5. **Community**: Check the project's issue tracker and discussions

## Related Documentation

- [Configuration Guide](configuration.md) - Complete configuration guide with all options
- [Configuration API Reference](api-reference.md) - Detailed API documentation
- [Hooks API Reference](../hooks/api-reference.md) - Hooks and configuration loading
- [Examples](../examples/) - Configuration examples and best practices

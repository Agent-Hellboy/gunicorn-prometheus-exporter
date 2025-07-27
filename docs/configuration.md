# Configuration Reference

Complete reference for all configuration options available in the Gunicorn Prometheus Exporter.

## Environment Variables

### Required Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_METRICS_PORT` | - | Port for the Prometheus metrics server |
| `PROMETHEUS_MULTIPROC_DIR` | - | Directory for multiprocess metrics storage |
| `GUNICORN_WORKERS` | - | Number of Gunicorn workers |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_BIND_ADDRESS` | `0.0.0.0` | Bind address for metrics server |
| `GUNICORN_TIMEOUT` | `30` | Worker timeout in seconds |
| `GUNICORN_KEEPALIVE` | `2` | Keep-alive connection timeout |
| `CLEANUP_DB_FILES` | `true` | Clean up old multiprocess files |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_ENABLED` | `false` | Enable Redis metrics forwarding |
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis database number |
| `REDIS_PASSWORD` | - | Redis authentication password |
| `REDIS_KEY_PREFIX` | `gunicorn_metrics:` | Prefix for Redis keys |
| `REDIS_FORWARD_INTERVAL` | `30` | Metrics forwarding interval in seconds |

## 📝 Gunicorn Configuration

### Basic Configuration

```python
# gunicorn.conf.py

# Server settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
master_class = "gunicorn_prometheus_exporter.PrometheusMaster"

# Environment variables
raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc",
    "GUNICORN_WORKERS=4"
]

# Prometheus hooks
when_ready = "gunicorn_prometheus_exporter.default_when_ready"
on_starting = "gunicorn_prometheus_exporter.default_on_starting"
worker_int = "gunicorn_prometheus_exporter.default_worker_int"
on_exit = "gunicorn_prometheus_exporter.default_on_exit"
```

### Advanced Configuration

```python
# gunicorn.conf.py

# Server settings
bind = "0.0.0.0:8000"
workers = 8
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
master_class = "gunicorn_prometheus_exporter.PrometheusMaster"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Environment variables
raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc",
    "PROMETHEUS_BIND_ADDRESS=0.0.0.0",
    "GUNICORN_WORKERS=8",
    "GUNICORN_TIMEOUT=30",
    "GUNICORN_KEEPALIVE=2",
    "CLEANUP_DB_FILES=true"
]

# Prometheus hooks
when_ready = "gunicorn_prometheus_exporter.default_when_ready"
on_starting = "gunicorn_prometheus_exporter.default_on_starting"
worker_int = "gunicorn_prometheus_exporter.default_worker_int"
on_exit = "gunicorn_prometheus_exporter.default_on_exit"

# Worker settings
preload_app = True
worker_tmp_dir = "/dev/shm"
```

### Redis Configuration

```python
# gunicorn.conf.py

# Environment variables with Redis
raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc",
    "GUNICORN_WORKERS=4",
    "REDIS_ENABLED=true",
    "REDIS_HOST=redis.example.com",
    "REDIS_PORT=6379",
    "REDIS_DB=0",
    "REDIS_PASSWORD=your_password",
    "REDIS_KEY_PREFIX=gunicorn_metrics:",
    "REDIS_FORWARD_INTERVAL=30"
]

# Use Redis-enabled hook
when_ready = "gunicorn_prometheus_exporter.redis_when_ready"
```

## Programmatic Configuration

### Using the Config Class

```python
from gunicorn_prometheus_exporter.config import ExporterConfig

# Create configuration
config = ExporterConfig()

# Access configuration values
port = config.prometheus_metrics_port
mp_dir = config.prometheus_multiproc_dir
workers = config.gunicorn_workers

# Validate configuration
if config.validate():
    print("Configuration is valid")
else:
    print("Configuration has errors")
```

### Custom Configuration

```python
import os
from gunicorn_prometheus_exporter.config import ExporterConfig

# Set custom environment variables
os.environ["PROMETHEUS_METRICS_PORT"] = "9092"
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/custom/path"
os.environ["GUNICORN_WORKERS"] = "6"

# Create configuration
config = ExporterConfig()

# Use in your application
print(f"Metrics will be available on port {config.prometheus_metrics_port}")
```

## 🐳 Docker Configuration

### Environment Variables in Docker

```dockerfile
# Dockerfile
ENV PROMETHEUS_METRICS_PORT=9091
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
ENV GUNICORN_WORKERS=4
ENV REDIS_ENABLED=false
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    environment:
      - PROMETHEUS_METRICS_PORT=9091
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
      - GUNICORN_WORKERS=4
      - REDIS_ENABLED=true
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    ports:
      - "8000:8000"
      - "9091:9091"
    volumes:
      - prometheus_data:/tmp/prometheus_multiproc

volumes:
  prometheus_data:
```

## Configuration Validation

### Validation Rules

The configuration system validates:

1. **Required Variables**: All required environment variables must be set
2. **Port Range**: Metrics port must be between 1 and 65535
3. **Worker Count**: Must be a positive integer
4. **Directory Permissions**: Multiprocess directory must be writable
5. **Redis Connection**: If Redis is enabled, connection must be testable

### Validation Example

```python
from gunicorn_prometheus_exporter.config import ExporterConfig

config = ExporterConfig()

try:
    if config.validate():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors")
        config.print_config()  # Show current configuration
except Exception as e:
    print(f"❌ Configuration error: {e}")
```

## Configuration Examples by Use Case

### Development Setup

```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc",
    "GUNICORN_WORKERS=2"
]

when_ready = "gunicorn_prometheus_exporter.default_when_ready"
loglevel = "debug"
```

### Production Setup

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 8
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
master_class = "gunicorn_prometheus_exporter.PrometheusMaster"

raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/var/lib/prometheus/multiproc",
    "GUNICORN_WORKERS=8",
    "GUNICORN_TIMEOUT=30",
    "CLEANUP_DB_FILES=true"
]

when_ready = "gunicorn_prometheus_exporter.default_when_ready"
on_starting = "gunicorn_prometheus_exporter.default_on_starting"
worker_int = "gunicorn_prometheus_exporter.default_worker_int"
on_exit = "gunicorn_prometheus_exporter.default_on_exit"

preload_app = True
max_requests = 1000
max_requests_jitter = 50
```

### High-Availability Setup

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 16
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
master_class = "gunicorn_prometheus_exporter.PrometheusMaster"

raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/var/lib/prometheus/multiproc",
    "GUNICORN_WORKERS=16",
    "REDIS_ENABLED=true",
    "REDIS_HOST=redis-cluster.example.com",
    "REDIS_PORT=6379",
    "REDIS_FORWARD_INTERVAL=15"
]

when_ready = "gunicorn_prometheus_exporter.redis_when_ready"
on_starting = "gunicorn_prometheus_exporter.default_on_starting"
worker_int = "gunicorn_prometheus_exporter.default_worker_int"
on_exit = "gunicorn_prometheus_exporter.default_on_exit"

preload_app = True
max_requests = 2000
max_requests_jitter = 100
worker_connections = 2000
```

## Related Documentation

- [Installation Guide](installation.md) - Setup instructions
- [Metrics Documentation](metrics.md) - Available metrics
- [API Reference](api-reference.md) - Programmatic usage
- [Troubleshooting](troubleshooting.md) - Common issues

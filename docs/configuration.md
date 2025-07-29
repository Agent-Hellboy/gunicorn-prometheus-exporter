# Configuration Guide

Complete configuration guide for the Gunicorn Prometheus Exporter with all options and scenarios.

## 🔧 Environment Variables Reference

### Required Variables

| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `PROMETHEUS_MULTIPROC_DIR` | String | `/tmp/prometheus_multiproc` | Directory for multiprocess metrics | `/var/tmp/prometheus_multiproc` |
| `PROMETHEUS_METRICS_PORT` | Integer | `9090` | Port for metrics endpoint | `9091` |
| `PROMETHEUS_BIND_ADDRESS` | String | `0.0.0.0` | Bind address for metrics server | `127.0.0.1` |
| `GUNICORN_WORKERS` | Integer | `1` | Number of workers for metrics | `4` |

### Optional Variables

| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `GUNICORN_KEEPALIVE` | Integer | `2` | Keep-alive timeout | `5` |
| `CLEANUP_DB_FILES` | Boolean | `false` | Clean up old metric files | `true` |

### Redis Variables

| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `REDIS_ENABLED` | Boolean | `false` | Enable Redis forwarding | `true` |
| `REDIS_HOST` | String | `localhost` | Redis server host | `redis.example.com` |
| `REDIS_PORT` | Integer | `6379` | Redis server port | `6380` |
| `REDIS_DB` | Integer | `0` | Redis database number | `1` |
| `REDIS_PASSWORD` | String | `None` | Redis password | `secret123` |
| `REDIS_KEY_PREFIX` | String | `gunicorn_metrics` | Redis key prefix | `myapp_metrics` |
| `REDIS_FORWARD_INTERVAL` | Integer | `30` | Forwarding interval | `60` |

## 🚀 Configuration Scenarios

### Basic Setup

**Use Case:** Simple monitoring for a single Gunicorn instance.

```python
# gunicorn_basic.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
```

**Environment Variables:**
```bash
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
export PROMETHEUS_METRICS_PORT="9090"
export PROMETHEUS_BIND_ADDRESS="0.0.0.0"
export GUNICORN_WORKERS="2"
```

### High-Performance Setup

**Use Case:** High-traffic application with optimized settings.

```python
# gunicorn_high_performance.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "8")
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")
os.environ.setdefault("CLEANUP_DB_FILES", "true")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 8
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
worker_connections = 2000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5
preload_app = True
```

### Async Application Setup

**Use Case:** Async application using eventlet workers.

```python
# gunicorn_async.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
```

### Production Setup

**Use Case:** Production environment with security and reliability.

```python
# gunicorn_production.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/var/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # Bind to localhost only
os.environ.setdefault("GUNICORN_WORKERS", "4")
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")
os.environ.setdefault("CLEANUP_DB_FILES", "true")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5
preload_app = True
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
```

### Redis Integration Setup

**Use Case:** Distributed setup with Redis metrics forwarding.

```python
# gunicorn_redis.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Redis configuration
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("REDIS_PASSWORD", "")
os.environ.setdefault("REDIS_KEY_PREFIX", "gunicorn_metrics")
os.environ.setdefault("REDIS_FORWARD_INTERVAL", "30")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5
```

### Development Setup

**Use Case:** Development environment with debugging enabled.

```python
# gunicorn_development.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
reload = True
reload_extra_files = ["app.py", "config.py"]
accesslog = "-"
errorlog = "-"
loglevel = "debug"
```

## 🔧 Worker Type Configurations

### Sync Worker

```python
# gunicorn_sync.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
```

**Best for:** CPU-bound applications, simple setups.

### Thread Worker

```python
# gunicorn_thread.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
threads = 4
```

**Best for:** I/O-bound applications, better concurrency.

### Eventlet Worker

```python
# gunicorn_eventlet.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
worker_connections = 1000
```

**Best for:** Async applications, high concurrency.

### Gevent Worker

```python
# gunicorn_gevent.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"
worker_connections = 1000
```

**Best for:** Async applications, high concurrency.

### Tornado Worker (⚠️ Not Recommended)

```python
# gunicorn_tornado.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusTornadoWorker"
```

**⚠️ Warning:** TornadoWorker has known compatibility issues with metrics collection. The Prometheus metrics endpoint may hang or become unresponsive. Use `PrometheusEventletWorker` or `PrometheusGeventWorker` instead for async applications.

**Best for:** Tornado-based applications (⚠️ Not recommended for production).

## 🔧 Advanced Configuration

### Custom Hooks

```python
# gunicorn_custom_hooks.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Custom hooks
def on_starting(server):
    """Custom startup hook."""
    print("Starting Gunicorn with Prometheus exporter...")

def when_ready(server):
    """Custom ready hook."""
    from gunicorn_prometheus_exporter.hooks import default_when_ready
    default_when_ready(server)
    print("Gunicorn is ready to accept connections")

def worker_int(worker):
    """Custom worker initialization hook."""
    from gunicorn_prometheus_exporter.hooks import default_worker_int
    default_worker_int(worker)
    print(f"Worker {worker.pid} initialized")

def on_exit(server):
    """Custom exit hook."""
    from gunicorn_prometheus_exporter.hooks import default_on_exit
    default_on_exit(server)
    print("Gunicorn shutting down...")
```

### CLI Options and Post-Fork Hook

Some Gunicorn CLI options like `--timeout`, `--workers`, `--bind`, and `--worker-class` do not automatically populate environment variables. To ensure these CLI options are properly configured and consistent with environment-based settings, use the `post_fork` hook.

**Why use post_fork hook for CLI options:**
- CLI options like `--timeout` don't automatically set environment variables
- The post_fork hook runs after each worker is forked and can access Gunicorn's configuration
- It ensures consistency between CLI and environment-based configuration
- It logs worker-specific configuration for debugging

**Example with post_fork hook:**

```python
# gunicorn_with_cli.conf.py
from gunicorn_prometheus_exporter.hooks import (
    default_on_starting,
    default_when_ready,
    default_worker_int,
    default_on_exit,
    default_post_fork,
)

bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
timeout = 300

# Use pre-built hooks including post_fork
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork  # Configure CLI options after worker fork

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
```

**CLI usage with post_fork hook:**

```bash
# Override timeout from CLI
gunicorn -c gunicorn_with_cli.conf.py app:app --timeout 600

# Override workers from CLI
gunicorn -c gunicorn_with_cli.conf.py app:app --workers 8

# Override bind address from CLI
gunicorn -c gunicorn_with_cli.conf.py app:app --bind 0.0.0.0:9000

# Override worker class from CLI
gunicorn -c gunicorn_with_cli.conf.py app:app --worker-class gunicorn_prometheus_exporter.PrometheusWorker
```

The post_fork hook will automatically detect these CLI options and update the corresponding environment variables, ensuring consistency between CLI and environment-based configuration.

**Supported CLI options in post_fork hook:**
- `--timeout`: Worker timeout in seconds
- `--workers`: Number of worker processes
- `--bind`: Bind address and port
- `--worker-class`: Worker class to use

### SSL/TLS Configuration

```
```

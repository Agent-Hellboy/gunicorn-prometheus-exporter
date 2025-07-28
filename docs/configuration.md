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
| `GUNICORN_TIMEOUT` | Integer | `30` | Worker timeout in seconds | `60` |
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
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
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
bind = "0.0.0.0:8000"
workers = 8
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
worker_connections = 2000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5
preload_app = True

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "8")
os.environ.setdefault("GUNICORN_TIMEOUT", "60")
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")
os.environ.setdefault("CLEANUP_DB_FILES", "true")
```

### Async Application Setup

**Use Case:** Async application using eventlet workers.

```python
# gunicorn_async.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
os.environ.setdefault("GUNICORN_TIMEOUT", "60")
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")
```

### Production Setup

**Use Case:** Production environment with security and reliability.

```python
# gunicorn_production.conf.py
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

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/var/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # Bind to localhost only
os.environ.setdefault("GUNICORN_WORKERS", "4")
os.environ.setdefault("GUNICORN_TIMEOUT", "60")
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")
os.environ.setdefault("CLEANUP_DB_FILES", "true")
```

### Redis Integration Setup

**Use Case:** Distributed setup with Redis metrics forwarding.

```python
# gunicorn_redis.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5

import os
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
```

### Development Setup

**Use Case:** Development environment with debugging enabled.

```python
# gunicorn_development.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
reload = True
reload_extra_files = ["app.py", "config.py"]
accesslog = "-"
errorlog = "-"
loglevel = "debug"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

## 🔧 Worker Type Configurations

### Sync Worker

```python
# gunicorn_sync.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
```

**Best for:** CPU-bound applications, simple setups.

### Thread Worker

```python
# gunicorn_thread.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
threads = 4

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

**Best for:** I/O-bound applications, better concurrency.

### Eventlet Worker

```python
# gunicorn_eventlet.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
worker_connections = 1000

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
```

**Best for:** Async applications, high concurrency.

### Gevent Worker

```python
# gunicorn_gevent.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"
worker_connections = 1000

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
```

**Best for:** Async applications, high concurrency.

### Tornado Worker (⚠️ Not Recommended)

```python
# gunicorn_tornado.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusTornadoWorker"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
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

### SSL/TLS Configuration

```python
# gunicorn_ssl.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
keyfile = "/path/to/key.pem"
certfile = "/path/to/cert.pem"
ca_certs = "/path/to/ca.pem"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
```

### Load Balancer Configuration

```python
# gunicorn_load_balancer.conf.py
bind = "0.0.0.0:8000"
workers = 8
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 2000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5
preload_app = True
forwarded_allow_ips = "*"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "8")
```

## 🔧 Environment-Specific Configurations

### Docker Configuration

```python
# gunicorn_docker.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
```

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install gunicorn-prometheus-exporter[async]

# Copy application
COPY . .

# Create multiprocess directory
RUN mkdir -p /tmp/prometheus_multiproc

# Expose ports
EXPOSE 8000 9090

# Set environment variables
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
ENV PROMETHEUS_METRICS_PORT=9090
ENV PROMETHEUS_BIND_ADDRESS=0.0.0.0
ENV GUNICORN_WORKERS=4

# Start with gunicorn
CMD ["gunicorn", "-c", "gunicorn_docker.conf.py", "app:app"]
```

### Kubernetes Configuration

```python
# gunicorn_kubernetes.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
```

**Kubernetes Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gunicorn-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gunicorn-app
  template:
    metadata:
      labels:
        app: gunicorn-app
    spec:
      containers:
      - name: gunicorn-app
        image: your-app:latest
        ports:
        - containerPort: 8000
        - containerPort: 9090
        env:
        - name: PROMETHEUS_MULTIPROC_DIR
          value: "/tmp/prometheus_multiproc"
        - name: PROMETHEUS_METRICS_PORT
          value: "9090"
        - name: PROMETHEUS_BIND_ADDRESS
          value: "0.0.0.0"
        - name: GUNICORN_WORKERS
          value: "4"
```

### AWS Configuration

```python
# gunicorn_aws.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5
preload_app = True

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# AWS-specific settings
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
```

## 🔧 Validation and Testing

### Configuration Validation

```python
# validate_config.py
import os
from gunicorn_prometheus_exporter.config import ExporterConfig

def validate_configuration():
    """Validate the current configuration."""
    config = ExporterConfig()

    print("Configuration Validation:")
    print("=" * 50)

    # Check required variables
    required_vars = [
        "PROMETHEUS_MULTIPROC_DIR",
        "PROMETHEUS_METRICS_PORT",
        "PROMETHEUS_BIND_ADDRESS",
        "GUNICORN_WORKERS"
    ]

    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")

    # Validate configuration
    if config.validate():
        print("\n✅ Configuration is valid")
        return True
    else:
        print("\n❌ Configuration has errors")
        return False

if __name__ == "__main__":
    validate_configuration()
```

### Configuration Testing

```bash
# Test configuration without starting server
python -c "
from gunicorn_prometheus_exporter.config import ExporterConfig
config = ExporterConfig()
print('Configuration:')
config.print_config()
print(f'Valid: {config.validate()}')
"
```

## 🔧 Best Practices

### Security Best Practices

1. **Bind to localhost in production:**
```python
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")
```

2. **Use secure directories:**
```python
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/var/tmp/prometheus_multiproc")
```

3. **Set appropriate permissions:**
```bash
chmod 755 /var/tmp/prometheus_multiproc
chown gunicorn:gunicorn /var/tmp/prometheus_multiproc
```

### Performance Best Practices

1. **Match worker count to CPU cores:**
```python
workers = 4  # For 4 CPU cores
```

2. **Use appropriate worker type:**
```python
# For I/O-bound apps
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"

# For async apps
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
```

3. **Enable cleanup for long-running processes:**
```python
os.environ.setdefault("CLEANUP_DB_FILES", "true")
```

### Monitoring Best Practices

1. **Set up health checks:**
```bash
curl http://localhost:9090/metrics
```

2. **Monitor key metrics:**
```bash
# Check worker requests
curl http://localhost:9090/metrics | grep gunicorn_worker_requests_total

# Check memory usage
curl http://localhost:9090/metrics | grep gunicorn_worker_memory_bytes

# Check error rates
curl http://localhost:9090/metrics | grep gunicorn_worker_failed_requests_total
```

3. **Set up alerts for critical metrics:**

- High error rates
- Memory usage spikes
- Worker restarts

## 📚 Next Steps

After configuration:

1. **Test your configuration** with the validation script
2. **Start Gunicorn** with your configuration file
3. **Verify metrics** are being collected
4. **Set up Prometheus** to scrape your metrics
5. **Configure Grafana** for visualization

For troubleshooting, see the [Troubleshooting Guide](troubleshooting.md).

For API reference, see the [API Reference](api-reference.md).

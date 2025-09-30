# Configuration Examples

This page provides advanced configuration examples for different scenarios and use cases.

> **Note**: For basic setup, see the [Setup Guide](../setup.md).

## Advanced Configuration

### Production Configuration

```python
# gunicorn_production.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
```

## Async Worker Configurations

### Eventlet Worker

```python
# gunicorn_eventlet.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
worker_connections = 1000

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

### Gevent Worker

```python
# gunicorn_gevent.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"
worker_connections = 1000

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

### Thread Worker

```python
# gunicorn_thread.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
threads = 4

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

## Redis Storage Configuration

### Basic Redis Setup

```python
# gunicorn_redis_basic.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

import os
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9092")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Redis storage configuration
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
```

### Production Redis Configuration

```python
# gunicorn_redis_production.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000

import os
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9092")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Redis storage configuration
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "redis-cluster.example.com")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("REDIS_KEY_PREFIX", "prod-gunicorn")
os.environ.setdefault("REDIS_TTL_SECONDS", "600")
os.environ.setdefault("REDIS_PASSWORD", "your-redis-password")
os.environ.setdefault("REDIS_SSL", "true")
```

## High-Performance Configurations

### High Concurrency Setup

```python
# gunicorn_high_concurrency.conf.py
bind = "0.0.0.0:8000"
workers = 1
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"
worker_connections = 2000
max_requests = 0
max_requests_jitter = 0

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "1")
```

### CPU-Intensive Application

```python
# gunicorn_cpu_intensive.conf.py
bind = "0.0.0.0:8000"
workers = 8
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
max_requests = 1000
max_requests_jitter = 100
timeout = 60

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "8")
```

## Docker Configurations

### Basic Docker Setup

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 9091

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
```

```python
# gunicorn_docker.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

### Docker Compose with Redis

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
      - "9091:9091"
    environment:
      - REDIS_ENABLED=true
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Kubernetes Configurations

### Basic Kubernetes Deployment

```yaml
# k8s-deployment.yaml
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
      - name: app
        image: your-app:latest
        ports:
        - containerPort: 8000
        - containerPort: 9091
        env:
        - name: PROMETHEUS_MULTIPROC_DIR
          value: "/tmp/prometheus_multiproc"
        - name: PROMETHEUS_METRICS_PORT
          value: "9091"
        - name: PROMETHEUS_BIND_ADDRESS
          value: "0.0.0.0"
        - name: GUNICORN_WORKERS
          value: "2"
---
apiVersion: v1
kind: Service
metadata:
  name: gunicorn-app-service
spec:
  selector:
    app: gunicorn-app
  ports:
  - name: http
    port: 8000
    targetPort: 8000
  - name: metrics
    port: 9091
    targetPort: 9091
```

## Environment-Specific Configurations

### Development Environment

```python
# gunicorn_dev.conf.py
bind = "127.0.0.1:8000"
workers = 1
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
reload = True
debug = True

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")
os.environ.setdefault("GUNICORN_WORKERS", "1")
```

### Staging Environment

```python
# gunicorn_staging.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
max_requests = 1000
timeout = 30

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

## Custom Metrics Configuration

### Adding Custom Metrics

```python
# custom_metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Custom metrics
custom_requests_total = Counter('custom_requests_total', 'Total custom requests', ['method', 'endpoint'])
custom_request_duration = Histogram('custom_request_duration_seconds', 'Custom request duration')
custom_active_connections = Gauge('custom_active_connections', 'Active connections')

def track_custom_metric(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            custom_requests_total.labels(method='GET', endpoint='/custom').inc()
            return result
        finally:
            custom_request_duration.observe(time.time() - start_time)
    return wrapper
```

## Monitoring and Alerting

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'gunicorn-app'
    static_configs:
      - targets: ['localhost:9091']
    scrape_interval: 5s
    metrics_path: /metrics
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Gunicorn Prometheus Exporter",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(gunicorn_worker_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(gunicorn_worker_request_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

## Troubleshooting Examples

### Debug Configuration

```python
# gunicorn_debug.conf.py
bind = "0.0.0.0:8000"
workers = 1
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
loglevel = "debug"
accesslog = "-"
errorlog = "-"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "1")
os.environ.setdefault("PROMETHEUS_DEBUG", "true")
```

## Related Documentation

- [Setup Guide](../setup.md) - Basic setup and configuration
- [Configuration Guide](../components/config/configuration.md) - Complete configuration options
- [Worker Types](../components/metrics/worker-types.md) - Supported worker types
- [Redis Backend](../components/backend/redis-backend.md) - Redis storage configuration
- [Troubleshooting Guide](../troubleshooting.md) - Common issues and solutions

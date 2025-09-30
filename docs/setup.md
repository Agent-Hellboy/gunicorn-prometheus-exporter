# Setup Guide

This guide will help you get the Gunicorn Prometheus Exporter up and running quickly.

## Prerequisites

- Python 3.8+
- Gunicorn
- Your WSGI application

## Quick Setup

### 1. Install the Package

```bash
pip install gunicorn-prometheus-exporter
```

### 2. Create Configuration

#### Option A: YAML Configuration (Recommended)

Create `gunicorn-prometheus-exporter.yml`:

```yaml
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

Create `gunicorn.conf.py`:

```python
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

#### Option B: Environment Variables

Create `gunicorn.conf.py`:

```python
import os

# Set environment variables
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
```

### 3. Start Your Application

```bash
gunicorn -c gunicorn.conf.py your_app:app
```

### 4. Access Metrics

Your metrics will be available at:
- **Application**: http://localhost:8000
- **Metrics**: http://localhost:9091/metrics

## Setup with Redis (Recommended for Production)

### 1. Install with Redis Support

```bash
pip install gunicorn-prometheus-exporter[redis]
```

### 2. Configure Redis

Update your `gunicorn.conf.py`:

```python
import os

# Redis configuration
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")

# Metrics configuration
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
```

### 3. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally
# Ubuntu/Debian: sudo apt install redis-server
# macOS: brew install redis
```

## Setup with Prometheus

### 1. Install Prometheus

```bash
# Download from https://prometheus.io/download/
# Or use Docker
docker run -d -p 9090:9090 prom/prometheus:latest
```

### 2. Configure Prometheus

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'gunicorn-app'
    static_configs:
      - targets: ['localhost:9091']
    metrics_path: /metrics
    scrape_interval: 5s
```

### 3. Start Prometheus

```bash
prometheus --config.file=prometheus.yml --storage.tsdb.path=./prometheus-data
```

### 4. Access Prometheus UI

Open http://localhost:9090 in your browser.

## Common Setup Scenarios

### Development Setup

```python
# gunicorn_dev.conf.py
import os

os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")
os.environ.setdefault("GUNICORN_WORKERS", "1")

bind = "127.0.0.1:8000"
workers = 1
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
reload = True
```

### Production Setup

```python
# gunicorn_prod.conf.py
import os

os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "redis.production.com")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_PASSWORD", "your-password")

os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
max_requests = 1000
timeout = 30
```

## Verification

### Check Metrics Endpoint

```bash
curl http://localhost:9091/metrics
```

You should see Prometheus metrics output.

### Test Prometheus Queries

In Prometheus UI (http://localhost:9090), try these queries:

```promql
# Request rate
rate(gunicorn_worker_requests_total[5m])

# Memory usage
gunicorn_worker_memory_bytes

# CPU usage
gunicorn_worker_cpu_percent
```

## Next Steps

- [Configuration Guide](components/config/configuration.md) - Advanced configuration options
- [Examples](examples/) - Framework-specific examples
- [Deployment Guide](examples/deployment-guide.md) - Production deployment
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## Need Help?

- Check the [Troubleshooting Guide](troubleshooting.md) for common issues
- Review [Configuration Examples](examples/examples.md) for advanced setups
- See [Framework Integration](examples/) for specific framework examples

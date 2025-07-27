# Installation Guide

This guide covers installing and setting up the Gunicorn Prometheus Exporter for any WSGI framework.

## 📋 Prerequisites

- Python 3.9 or higher
- Gunicorn 21.2.0 or higher
- A WSGI application (Django, FastAPI, Flask, etc.)

## Installation Methods

### Method 1: pip (Recommended)

```bash
pip install gunicorn-prometheus-exporter
```

### Method 2: From Source

```bash
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter.git
cd gunicorn-prometheus-exporter
pip install -e .
```

### Method 3: With Development Dependencies

```bash
pip install gunicorn-prometheus-exporter[dev]
```

## Basic Setup

### 1. Environment Variables

Set these environment variables for the exporter to work:

```bash
export PROMETHEUS_METRICS_PORT=9091
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
export GUNICORN_WORKERS=4
```

### 2. Gunicorn Configuration

Create a `gunicorn.conf.py` file:

```python
# Basic server configuration
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

### 3. Start Your Application

```bash
gunicorn -c gunicorn.conf.py your_app:app
```

## Verification

### Check Metrics Endpoint

Visit `http://localhost:9091/metrics` to see your Prometheus metrics:

```bash
curl http://localhost:9091/metrics
```

You should see output like:

```
# HELP gunicorn_worker_requests_total Total number of requests processed by worker
# TYPE gunicorn_worker_requests_total counter
gunicorn_worker_requests_total{worker_id="worker_1_1234567890"} 42.0

# HELP gunicorn_worker_request_duration_seconds Request duration in seconds
# TYPE gunicorn_worker_request_duration_seconds histogram
gunicorn_worker_request_duration_seconds_bucket{worker_id="worker_1_1234567890",le="0.1"} 35.0
```

### Check Application Health

Your main application should still be accessible at `http://localhost:8000`.

## 🐳 Docker Setup

### Dockerfile Example

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install gunicorn-prometheus-exporter

# Copy application
COPY . .

# Create multiprocess directory
RUN mkdir -p /tmp/prometheus_multiproc

# Expose ports
EXPOSE 8000 9091

# Set environment variables
ENV PROMETHEUS_METRICS_PORT=9091
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
ENV GUNICORN_WORKERS=4

# Start with gunicorn
CMD ["gunicorn", "-c", "gunicorn.conf.py", "your_app:app"]
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
      - "9091:9091"
    environment:
      - PROMETHEUS_METRICS_PORT=9091
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
      - GUNICORN_WORKERS=4
    volumes:
      - /tmp/prometheus_multiproc:/tmp/prometheus_multiproc

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## Advanced Configuration

### Redis Forwarding Setup

For distributed setups, enable Redis forwarding:

```python
# gunicorn.conf.py
raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc",
    "GUNICORN_WORKERS=4",
    "REDIS_ENABLED=true",
    "REDIS_HOST=localhost",
    "REDIS_PORT=6379"
]

# Use Redis-enabled hook
when_ready = "gunicorn_prometheus_exporter.redis_when_ready"
```

### Custom Metrics Port

```bash
export PROMETHEUS_METRICS_PORT=9092
```

### Custom Multiprocess Directory

```bash
export PROMETHEUS_MULTIPROC_DIR=/var/lib/prometheus/multiproc
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :9091

   # Use a different port
   export PROMETHEUS_METRICS_PORT=9092
   ```

2. **Permission Denied for Multiprocess Directory**
   ```bash
   # Create directory with proper permissions
   sudo mkdir -p /tmp/prometheus_multiproc
   sudo chown $USER:$USER /tmp/prometheus_multiproc
   ```

3. **Metrics Not Appearing**
   - Ensure environment variables are set
   - Check Gunicorn logs for errors
   - Verify the multiprocess directory exists and is writable

### Debug Mode

Enable debug logging:

```python
# gunicorn.conf.py
loglevel = "debug"
```

## 📚 Next Steps

- [Configuration Reference](configuration.md) - All available options
- [Framework Examples](examples/) - Setup guides for specific frameworks
- [Metrics Documentation](metrics.md) - Understanding the metrics
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

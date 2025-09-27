# Deployment Guide

This guide covers deploying Gunicorn Prometheus Exporter in various environments.

## Understanding the Three URLs

When deploying with Gunicorn Prometheus Exporter, you'll work with three distinct URLs:

| Service              | URL                             | Purpose                                                       |
| -------------------- | ------------------------------- | ------------------------------------------------------------- |
| **Prometheus UI**    | `http://localhost:9090`         | Prometheus web interface for querying and visualizing metrics |
| **Your Application** | `http://localhost:8200`         | Your actual web application (Gunicorn server)                 |
| **Metrics Endpoint** | `http://127.0.0.1:9091/metrics` | Raw metrics data for Prometheus to scrape                     |

### Basic Configuration

```bash
# Basic metrics server configuration
export PROMETHEUS_METRICS_PORT="9091"        # Port for metrics endpoint
export PROMETHEUS_BIND_ADDRESS="127.0.0.1"   # Bind address for metrics server
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"  # Metrics storage directory
export GUNICORN_WORKERS="2"                  # Number of workers
```

## Quick Start

### 1. Create Gunicorn Configuration

Create `gunicorn.conf.py`:

```python
import os

# Environment variables (must be set before imports)
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")
os.environ.setdefault("GUNICORN_WORKERS", "2")

from gunicorn_prometheus_exporter.hooks import (
    default_on_exit,
    default_on_starting,
    default_post_fork,
    default_when_ready,
    default_worker_int,
)

# Gunicorn settings
bind = "0.0.0.0:8200"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
timeout = 300

# Use pre-built hooks
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork
```

### 2. Start Services

```bash
# Start Prometheus
prometheus --config.file=prometheus.yml --storage.tsdb.path=./prometheus-data

# Start your application
gunicorn --config gunicorn.conf.py app:app
```

### 3. Access Services

- **Application**: http://localhost:8200
- **Metrics Endpoint**: http://127.0.0.1:9091/metrics
- **Prometheus UI**: http://localhost:9090

### 4. Prometheus Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "gunicorn-app"
    static_configs:
      - targets: ["127.0.0.1:9091"]
    metrics_path: /metrics
    scrape_interval: 5s
```

## Docker Deployment

### Basic Docker Setup

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install gunicorn gunicorn-prometheus-exporter

# Copy application
COPY . .

# Create metrics directory
RUN mkdir -p /tmp/prometheus_multiproc

# Expose ports
EXPOSE 8200 9091

# Set environment variables
ENV PROMETHEUS_METRICS_PORT=9091
ENV PROMETHEUS_BIND_ADDRESS=0.0.0.0
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
ENV GUNICORN_WORKERS=4

# Start with gunicorn
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
```

**docker-compose.yml:**

```yaml
version: "3.8"

services:
  app:
    build: .
    ports:
      - "8200:8200" # Application port
      - "9091:9091" # Metrics port
    environment:
      - PROMETHEUS_METRICS_PORT=9091
      - PROMETHEUS_BIND_ADDRESS=0.0.0.0
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
      - GUNICORN_WORKERS=4
    volumes:
      - prometheus_data:/tmp/prometheus_multiproc

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090" # Prometheus UI
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_storage:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"

volumes:
  prometheus_data:
  prometheus_storage:
```

**prometheus.yml:**

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "gunicorn-app"
    static_configs:
      - targets: ["app:9091"] # Docker service name
    metrics_path: /metrics
    scrape_interval: 5s
```

## Kubernetes Deployment

### Basic Kubernetes Setup

**deployment.yaml:**

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
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9091"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: app
          image: your-registry/gunicorn-app:latest
          ports:
            - containerPort: 8200
              name: http
            - containerPort: 9091
              name: metrics
          env:
            - name: PROMETHEUS_METRICS_PORT
              value: "9091"
            - name: PROMETHEUS_BIND_ADDRESS
              value: "0.0.0.0"
            - name: PROMETHEUS_MULTIPROC_DIR
              value: "/tmp/prometheus_multiproc"
            - name: GUNICORN_WORKERS
              value: "4"
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```

**service.yaml:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gunicorn-app-service
spec:
  selector:
    app: gunicorn-app
  ports:
    - name: http
      port: 8200
      targetPort: 8200
    - name: metrics
      port: 9091
      targetPort: 9091
  type: ClusterIP
```

## Sidecar Deployment

Deploy the exporter as a sidecar container within the same Kubernetes pod for isolated monitoring:

**deployment-with-sidecar.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gunicorn-app-with-sidecar
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gunicorn-app
  template:
    metadata:
      labels:
        app: gunicorn-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9091"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        # Main application container
        - name: app
          image: your-registry/gunicorn-app:latest
          ports:
            - containerPort: 8200
              name: http
          env:
            - name: PROMETHEUS_MULTIPROC_DIR
              value: "/tmp/prometheus_multiproc"
            - name: GUNICORN_WORKERS
              value: "4"
          volumeMounts:
            - name: prometheus-data
              mountPath: /tmp/prometheus_multiproc
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"

        # Prometheus exporter sidecar
        - name: prometheus-exporter
          image: your-registry/gunicorn-prometheus-exporter:latest
          ports:
            - containerPort: 9091
              name: metrics
          env:
            - name: PROMETHEUS_METRICS_PORT
              value: "9091"
            - name: PROMETHEUS_BIND_ADDRESS
              value: "0.0.0.0"
            - name: PROMETHEUS_MULTIPROC_DIR
              value: "/tmp/prometheus_multiproc"
          volumeMounts:
            - name: prometheus-data
              mountPath: /tmp/prometheus_multiproc
          resources:
            requests:
              memory: "64Mi"
              cpu: "50m"
            limits:
              memory: "128Mi"
              cpu: "100m"
      volumes:
        - name: prometheus-data
          emptyDir: {}
```

**Benefits of Sidecar Deployment:**

- **Isolation**: Metrics collection is separate from application logic
- **Resource Management**: Independent resource limits for monitoring
- **Scaling**: Can scale monitoring independently
- **Security**: Reduced attack surface for main application
- **Maintenance**: Update monitoring without touching application

## Production Considerations

### Security

```bash
# Enable SSL/TLS for metrics endpoint
export PROMETHEUS_SSL_CERTFILE="/etc/ssl/certs/metrics.crt"
export PROMETHEUS_SSL_KEYFILE="/etc/ssl/private/metrics.key"
export PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED="true"
```

### Performance

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Monitoring Queries

### Key Prometheus Queries

```promql
# Request rate
rate(gunicorn_worker_requests_total[5m])

# Memory usage
gunicorn_worker_memory_bytes

# CPU usage
gunicorn_worker_cpu_percent

# Error rate
rate(gunicorn_worker_failed_requests_total[5m])

# Worker uptime
gunicorn_worker_uptime_seconds
```

## Troubleshooting

### Common Issues

1. **Connection Refused on Metrics Port:**
   - Check if metrics server is running: `curl http://localhost:9091/metrics`
   - Verify bind address configuration (`PROMETHEUS_BIND_ADDRESS`)

2. **Prometheus Not Scraping:**
   - Check Prometheus targets: `curl http://localhost:9090/api/v1/targets`
   - Verify network connectivity

3. **Port Conflicts:**
   - Default metrics port is 9091 (not 9090)
   - Change `PROMETHEUS_METRICS_PORT` if needed

## Future Deployment Options

I'm actively testing and will add support for:

- **Helm Charts** - Kubernetes package management
- **Terraform** - Infrastructure as Code
- **Ansible** - Configuration management
- **AWS ECS/Fargate** - Container orchestration
- **Google Cloud Run** - Serverless containers
- **Azure Container Instances** - Managed containers

Stay tuned for updates in the [Deployment Guide](deployment-guide.md)!

## Related Documentation

- [Django Integration](django-integration.md)
- [Configuration Reference](../config/configuration.md)
- [Troubleshooting Guide](../troubleshooting.md)

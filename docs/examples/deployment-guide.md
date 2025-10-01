# Deployment Guide

This guide covers deploying Gunicorn Prometheus Exporter in production environments.

> **Note**: For basic setup, see the [Setup Guide](../setup.md).

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
EXPOSE 8000 9091

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
      - "8000:8000" # Application port
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
          image: princekrroshan01/gunicorn-app:0.1.8
          ports:
            - containerPort: 8000
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
      port: 8000
      targetPort: 8000
    - name: metrics
      port: 9091
      targetPort: 9091
  type: ClusterIP
```

## Sidecar Deployment

Deploy the exporter as a sidecar container within the same Kubernetes pod for isolated monitoring.

### Docker Hub Images

Pre-built Docker images are available on Docker Hub:

```bash
# Sidecar exporter image
docker pull princekrroshan01/gunicorn-prometheus-exporter:0.1.8

# Sample Flask application (for testing)
docker pull princekrroshan01/gunicorn-app:latest
```

Images are automatically built and published for:
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64)

### Quick Start with Docker Compose

> *Production recommendation*: Keep Redis storage enabled (`REDIS_ENABLED=true`) so that metrics aggregate across all workers/pods. Only disable Redis for single-worker demos.

```bash
# Clone the repository
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter.git
cd gunicorn-prometheus-exporter

# Start all services (app, sidecar, Redis, Prometheus, Grafana)
docker-compose up --build

# Access services:
# - Application: http://localhost:8000
# - Metrics: http://localhost:9091/metrics
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
#   Username: admin
#   Password: from grafana-secret (kubectl get secret grafana-secret -o jsonpath='{.data.admin-password}' | base64 -d)
```

See [docker/README.md](../../docker/README.md) for detailed Docker Compose documentation.

### Kubernetes Sidecar Deployment

For a complete Kubernetes deployment with Redis, Prometheus, and Grafana:

**Quick Deploy:**

```bash
# Create required secrets
kubectl create secret generic grafana-secret \
  --from-literal=admin-password="$(openssl rand -base64 32)"

# Deploy everything
kubectl apply -f k8s/

# Access services via port-forwarding
kubectl port-forward service/gunicorn-app-service 8000:8000
kubectl port-forward service/gunicorn-metrics-service 9091:9091
kubectl port-forward service/prometheus-service 9090:9090
kubectl port-forward service/grafana-service 3000:3000
```

**Minimal Sidecar Example:**

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
          image: princekrroshan01/gunicorn-app:0.1.8
          securityContext:
            allowPrivilegeEscalation: false
            runAsNonRoot: true
            runAsUser: 1000
            capabilities:
              drop:
                - ALL
          ports:
            - containerPort: 8000
              name: http
          env:
            - name: PROMETHEUS_MULTIPROC_DIR
              value: "/tmp/prometheus_multiproc"
            - name: GUNICORN_WORKERS
              value: "2"
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
          image: princekrroshan01/gunicorn-prometheus-exporter:0.1.8
          securityContext:
            allowPrivilegeEscalation: false
            runAsNonRoot: true
            runAsUser: 1000
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
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
            - name: REDIS_ENABLED
              value: "false"
          volumeMounts:
            - name: prometheus-data
              mountPath: /tmp/prometheus_multiproc
              readOnly: true
          resources:
            requests:
              memory: "64Mi"
              cpu: "50m"
            limits:
              memory: "128Mi"
              cpu: "100m"
      volumes:
        - name: prometheus-data
          emptyDir:
            medium: Memory
            sizeLimit: 1Gi
```

For production-ready Kubernetes deployments with Redis, security contexts, secrets management, and monitoring stack, see the [Kubernetes Deployment Guide](../../k8s/README.md).

**Benefits of Sidecar Deployment:**

- *Isolation*: Metrics collection is separate from application logic
- *Pre-built Images*: Ready-to-use Docker images on Docker Hub
- *Multi-arch Support*: Works on AMD64 and ARM64 architectures
- *Production-Ready*: Includes security contexts and resource limits
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

```promql
# Request rate
rate(gunicorn_worker_requests_total[5m])

# Memory usage
gunicorn_worker_memory_bytes

# CPU usage
gunicorn_worker_cpu_percent

# Error rate
rate(gunicorn_worker_failed_requests_total[5m])
```

## Related Documentation

- [Setup Guide](../setup.md) - Basic setup and configuration
- [Configuration Examples](examples.md) - Advanced configuration examples
- [Troubleshooting Guide](../troubleshooting.md) - Common issues and solutions

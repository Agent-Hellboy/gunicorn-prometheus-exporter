# Deployment Guide

This guide covers deploying Gunicorn Prometheus Exporter in production environments.

> **Note**: For basic setup, see the [Setup Guide](../setup.md).

## Docker Deployment

### Redis-Only Mode (Recommended for Containers)

For containerized deployments (Docker Compose and Kubernetes), Redis-only mode is **required**:

```yaml
# docker-compose.yml - Redis-only mode
version: "3.8"

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_ENABLED=true
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_DB=0
      - REDIS_KEY_PREFIX=gunicorn
      # Disable multiprocess files for Redis-only mode
      - PROMETHEUS_MULTIPROC_DIR=
    depends_on:
      redis:
        condition: service_healthy

  sidecar:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "9091:9091"
    environment:
      - REDIS_ENABLED=true
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_DB=0
      - REDIS_KEY_PREFIX=gunicorn
      # Disable multiprocess files for Redis-only mode
      - PROMETHEUS_MULTIPROC_DIR=
    depends_on:
      app:
        condition: service_healthy

volumes:
  redis_data:
```

**Benefits of Redis-only mode:**
- No shared filesystem required
- Works with read-only containers
- Scales across multiple pods/nodes
- Production-ready for Kubernetes

### Basic Docker Setup (Local Development)

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
ENV REDIS_ENABLED=false

# Start with gunicorn
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
```

**docker-compose.yml:**

```yaml
version: "3.8"

services:
  # Redis for shared metrics storage (required for containerized deployments)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

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
      - REDIS_ENABLED=false
    depends_on:
      redis:
        condition: service_healthy
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
  redis_data:
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

The Gunicorn Prometheus Exporter supports two main Kubernetes deployment patterns:

### Deployment Patterns

| Pattern | Use Case | Scaling | Network | Best For |
|---------|----------|---------|---------|----------|
| **Deployment** | Application-specific monitoring | Manual replica scaling | ClusterIP services | Production applications |
| **DaemonSet** | Cluster-wide infrastructure monitoring | Automatic (one per node) | Host network access | Infrastructure monitoring, development environments |

### Basic Kubernetes Setup (Deployment)

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
          image: princekrroshan01/gunicorn-app:0.2.2
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
docker pull princekrroshan01/gunicorn-prometheus-exporter:0.2.2

# Sample Flask application (for testing)
docker pull princekrroshan01/gunicorn-app:0.2.2

# Or build locally if the release is not yet available:
# docker build -t princekrroshan01/gunicorn-prometheus-exporter:0.2.2 .
# docker build -f docker/Dockerfile.app -t princekrroshan01/gunicorn-app:0.2.2 .
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
#   Password: admin (set GF_SECURITY_ADMIN_PASSWORD to override in production)
```

See [docker/README.md](../../docker/README.md) for detailed Docker Compose documentation.

#### DaemonSet Deployment

For cluster-wide infrastructure monitoring across all nodes:

**Quick Deploy:**

```bash
# Deploy DaemonSet for cluster-wide monitoring
kubectl apply -f k8s/sidecar-daemonset.yaml
kubectl apply -f k8s/daemonset-service.yaml
kubectl apply -f k8s/daemonset-metrics-service.yaml
kubectl apply -f k8s/daemonset-netpol.yaml

# Check DaemonSet status
kubectl get daemonset gunicorn-prometheus-exporter-daemonset
kubectl get pods -l app=gunicorn-prometheus-exporter,component=daemonset -o wide
```

**DaemonSet Example:**

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: gunicorn-prometheus-exporter-daemonset
spec:
  selector:
    matchLabels:
      app: gunicorn-prometheus-exporter
      component: daemonset
  template:
    metadata:
      labels:
        app: gunicorn-prometheus-exporter
        component: daemonset
    spec:
      hostNetwork: true
      containers:
        - name: prometheus-exporter
          image: princekrroshan01/gunicorn-prometheus-exporter:0.2.2
          ports:
            - containerPort: 9091
              name: metrics
          env:
            - name: PROMETHEUS_METRICS_PORT
              value: "9091"
            - name: REDIS_ENABLED
              value: "true"
            - name: REDIS_HOST
              value: "redis-service"
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
```

**DaemonSet Benefits:**

- **Cluster Coverage**: One pod per node for complete cluster monitoring
- **Infrastructure Monitoring**: Node-level application insights
- **Automatic Scaling**: Scales automatically with cluster size
- **Host Network Access**: Direct access to node-level services
- **Multi-Application Support**: Monitor multiple applications per node

**Use Cases:**

- Development environments with multiple applications
- Infrastructure monitoring across all nodes
- Cluster-wide observability
- Multi-tenant application monitoring

### Complete Kubernetes Examples

Find complete Kubernetes manifests in the [`k8s/`](../../k8s/) directory:

- **Standard Deployment**: `k8s/sidecar-deployment.yaml`
- **DaemonSet Deployment**: `k8s/sidecar-daemonset.yaml`
- **Services**: `k8s/daemonset-service.yaml`, `k8s/daemonset-metrics-service.yaml`
- **Network Policies**: `k8s/daemonset-netpol.yaml`
- **Complete Setup**: See [`k8s/README.md`](../../k8s/README.md) for full deployment guide

**Quick Deploy (Standard Deployment):**

```bash
# Create required secrets
kubectl create secret generic grafana-secret \
  --from-literal=admin-password="$(openssl rand -base64 32)"

# Deploy standard sidecar deployment
kubectl apply -f k8s/sidecar-deployment.yaml
kubectl apply -f k8s/gunicorn-app-service.yaml
kubectl apply -f k8s/gunicorn-metrics-service.yaml

# Access services via port-forwarding
kubectl port-forward service/gunicorn-app-service 8000:8000
kubectl port-forward service/gunicorn-metrics-service 9091:9091
```

**Quick Deploy (DaemonSet):**

```bash
# Deploy DaemonSet for cluster-wide monitoring
kubectl apply -f k8s/sidecar-daemonset.yaml
kubectl apply -f k8s/daemonset-service.yaml
kubectl apply -f k8s/daemonset-metrics-service.yaml
kubectl apply -f k8s/daemonset-netpol.yaml

# Check DaemonSet status
kubectl get daemonset gunicorn-prometheus-exporter-daemonset
kubectl get pods -l app=gunicorn-prometheus-exporter,component=daemonset -o wide
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
          image: princekrroshan01/gunicorn-app:0.2.2
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
          image: princekrroshan01/gunicorn-prometheus-exporter:0.2.2
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

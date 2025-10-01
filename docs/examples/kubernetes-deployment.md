# Kubernetes Deployment Guide

Complete guide for deploying Gunicorn Prometheus Exporter in Kubernetes with production-ready configurations.

## Overview

This guide covers deploying the exporter as a sidecar container in Kubernetes, including:

- Pre-built Docker images from Docker Hub
- Production-ready security contexts
- Redis integration for distributed metrics
- Complete monitoring stack (Prometheus + Grafana)
- Secret management best practices
- Multi-architecture support (AMD64, ARM64)

## Quick Start

### Prerequisites

- Kubernetes cluster (1.23+) - Required for `autoscaling/v2` HPA
- kubectl configured
- Docker (for local testing)

### 1. Pull Pre-built Images

```bash
# Sidecar exporter image (use specific version for production)
docker pull princekrroshan01/gunicorn-prometheus-exporter:0.1.8

# Sample Flask application (for testing)
docker pull princekrroshan01/gunicorn-app:0.1.8
```

**Production Note**: Always use specific version tags (e.g., `0.1.8`) instead of `:latest` for reproducibility and stability.

> *Redis recommendation*: Redis storage is required for multi-worker deployments. The manifests enable it by default (`REDIS_ENABLED=true`). Only disable Redis when running a single worker for local demos.

Images are automatically built and published for:
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64)

### 2. Deploy to Kubernetes

```bash
# Clone the repository
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter.git
cd gunicorn-prometheus-exporter

# Create required secrets
kubectl create secret generic grafana-secret \
  --from-literal=admin-password="$(openssl rand -base64 32)"

# Deploy everything
kubectl apply -f k8s/

# Verify deployment
kubectl get pods
kubectl get services
```

### 3. Access Services

```bash
# Port forward to access services
kubectl port-forward service/gunicorn-app-service 8000:8000
kubectl port-forward service/gunicorn-metrics-service 9091:9091
kubectl port-forward service/prometheus-service 9090:9090
kubectl port-forward service/grafana-service 3000:3000
```

Access URLs:
- **Application**: http://localhost:8000
- **Metrics**: http://localhost:9091/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## Architecture

### Sidecar Pattern

The exporter runs as a sidecar container alongside your application:

```
┌─────────────────────────────────────┐
│           Pod                       │
│  ┌──────────────┐  ┌─────────────┐ │
│  │     App      │  │   Sidecar   │ │
│  │  Container   │  │  Exporter   │ │
│  │              │  │             │ │
│  │ Writes       │  │ Reads       │ │
│  │ metrics to   │──│ metrics     │ │
│  │ shared vol   │  │ from vol    │ │
│  └──────────────┘  └─────────────┘ │
│         │                  │        │
│         │                  │        │
│     Port 8000         Port 9091     │
└─────────────────────────────────────┘
              │
              │
              ▼
        ┌──────────┐
        │Prometheus│
        │  Scrape  │
        └──────────┘
```

**Benefits:**
- Isolation: Metrics collection separate from application
- Independent scaling and resource management
- Read-only filesystem for sidecar (security)
- Shared memory volume for high performance

## Deployment Options

### Option 1: Minimal Sidecar (File-based)

Basic deployment with file-based metrics storage:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gunicorn-app-minimal
spec:
  replicas: 2
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
    spec:
      containers:
        - name: app
          image: princekrroshan01/gunicorn-app:0.1.8
          securityContext:
            allowPrivilegeEscalation: false
            runAsNonRoot: true
            runAsUser: 1000
            capabilities:
              drop: [ALL]
          ports:
            - containerPort: 8000
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

        - name: prometheus-exporter
          image: princekrroshan01/gunicorn-prometheus-exporter:0.1.8
          securityContext:
            allowPrivilegeEscalation: false
            runAsNonRoot: true
            runAsUser: 1000
            readOnlyRootFilesystem: true
            capabilities:
              drop: [ALL]
          ports:
            - containerPort: 9091
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
            medium: Memory  # Use tmpfs for better performance
            sizeLimit: 1Gi
```

### Option 2: Production with Redis

Full production deployment with Redis for distributed metrics:

For a complete production setup, use the manifests in the `k8s/` directory:

```bash
# Deploy Redis
kubectl apply -f k8s/redis-pvc.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# Deploy application with sidecar
kubectl apply -f k8s/sidecar-deployment.yaml
kubectl apply -f k8s/gunicorn-app-service.yaml
kubectl apply -f k8s/gunicorn-metrics-service.yaml

# Deploy monitoring stack
kubectl apply -f k8s/prometheus-config.yaml
kubectl apply -f k8s/prometheus-pvc.yaml
kubectl apply -f k8s/prometheus-deployment.yaml
kubectl apply -f k8s/prometheus-service.yaml

kubectl apply -f k8s/grafana-datasources.yaml
kubectl apply -f k8s/grafana-dashboards.yaml
kubectl apply -f k8s/grafana-pvc.yaml
kubectl apply -f k8s/grafana-deployment.yaml
kubectl apply -f k8s/grafana-service.yaml
```

**Features:**
- Redis for distributed metrics storage
- Persistent volumes for data retention
- Pre-configured Prometheus scraping
- Pre-built Grafana dashboards
- Security contexts for all containers
- Resource limits and requests

## Security

### Secret Management

**Important**: Never commit secrets to version control!

The repository provides templates for secrets:

```bash
# Create Grafana admin password (required)
kubectl create secret generic grafana-secret \
  --from-literal=admin-password="$(openssl rand -base64 32)"

# Optional: Redis password (for production)
kubectl create secret generic redis-secret \
  --from-literal=password="$(openssl rand -base64 32)"
```

Templates available:
- `k8s/grafana-secret.yaml.template`
- `k8s/redis-secret.yaml.template`

All `*-secret.yaml` files are blocked by `.gitignore`.

### Security Contexts

All containers run with hardened security contexts:

**Application Container:**
```yaml
securityContext:
  allowPrivilegeEscalation: false
  runAsNonRoot: true
  runAsUser: 1000
  capabilities:
    drop: [ALL]
```

**Sidecar Container:**
```yaml
securityContext:
  allowPrivilegeEscalation: false
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  capabilities:
    drop: [ALL]
```

**Redis Container:**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 999  # redis user
  allowPrivilegeEscalation: false
  capabilities:
    drop: [ALL]
```

### Image Versions

All images use pinned versions for reproducible deployments:
- `redis:7-alpine`
- `prom/prometheus:v2.54.1`
- `grafana/grafana:11.2.0`
- `princekrroshan01/gunicorn-prometheus-exporter:latest` (or use version tags)

## Configuration

### Environment Variables

**Application Container:**

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus_multiproc` | Metrics directory |
| `GUNICORN_WORKERS` | `2` | Number of workers |
| `REDIS_ENABLED` | `false` | Enable Redis storage |
| `REDIS_HOST` | `redis-service` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database |
| `REDIS_PASSWORD` | *(none)* | Redis password |
| `REDIS_KEY_PREFIX` | `gunicorn` | Redis key prefix |

**Sidecar Container:**

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_METRICS_PORT` | `9091` | Metrics port |
| `PROMETHEUS_BIND_ADDRESS` | `0.0.0.0` | Bind address |
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus_multiproc` | Metrics directory |
| `SIDECAR_UPDATE_INTERVAL` | `30` | Update interval (seconds) |
| `REDIS_ENABLED` | `false` | Enable Redis |

### Resource Limits

Recommended resource limits for production:

**Application:**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**Sidecar:**
```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
  limits:
    memory: "128Mi"
    cpu: "100m"
```

**Redis:**
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## Monitoring

### Prometheus Queries

Common queries for monitoring:

```promql
# Request rate per worker
rate(gunicorn_worker_requests_total[5m])

# Request duration 95th percentile
histogram_quantile(0.95, rate(gunicorn_worker_request_duration_seconds_bucket[5m]))

# Memory usage per worker
gunicorn_worker_memory_bytes

# CPU usage per worker
gunicorn_worker_cpu_percent

# Worker state (1=running, 0=stopped)
gunicorn_worker_state
```

### Grafana Dashboards

Pre-built dashboards are included in `k8s/grafana-dashboards.yaml`:

- Request rate over time
- Request duration percentiles
- Memory usage per worker
- CPU usage per worker
- Worker state monitoring

Access Grafana:
```bash
kubectl port-forward service/grafana-service 3000:3000
# Open http://localhost:3000
# Username: admin
# Password: from grafana-secret
```

## Scaling

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gunicorn-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gunicorn-app-minimal
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Adjusting Workers

Update the `GUNICORN_WORKERS` environment variable:

```bash
kubectl set env deployment/gunicorn-app-with-sidecar GUNICORN_WORKERS=4
```

Or edit the deployment:

```bash
kubectl edit deployment gunicorn-app-with-sidecar
```

## Troubleshooting

### Check Pod Status

```bash
# List all pods
kubectl get pods

# Describe pod
kubectl describe pod <pod-name>

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp
```

### View Logs

```bash
# Application logs
kubectl logs -f deployment/gunicorn-app-with-sidecar -c app

# Sidecar logs
kubectl logs -f deployment/gunicorn-app-with-sidecar -c prometheus-exporter

# Redis logs
kubectl logs -f deployment/redis

# Prometheus logs
kubectl logs -f deployment/prometheus
```

### Common Issues

**1. Pods not starting:**
```bash
kubectl describe pod <pod-name>
# Check resource limits and node capacity
```

**2. Metrics not appearing:**
```bash
# Check sidecar logs
kubectl logs <pod-name> -c prometheus-exporter

# Verify volume mount
kubectl exec <pod-name> -c prometheus-exporter -- ls -la /tmp/prometheus_multiproc
```

**3. Prometheus not scraping:**
```bash
# Check Prometheus targets
kubectl port-forward service/prometheus-service 9090:9090
# Open http://localhost:9090/targets
```

**4. Redis connection issues:**
```bash
# Test Redis connectivity
kubectl exec <pod-name> -c app -- nc -zv redis-service 6379

# Check Redis logs
kubectl logs deployment/redis
```

### Debug Mode

Enable debug logging:

```bash
kubectl set env deployment/gunicorn-app-with-sidecar LOG_LEVEL=debug
```

## Production Checklist

Before deploying to production:

- [ ] Create strong secrets (not default passwords)
- [ ] Configure resource limits for all containers
- [ ] Enable Redis for distributed metrics
- [ ] Set up persistent volumes with appropriate storage class
- [ ] Configure horizontal pod autoscaling
- [ ] Set up monitoring alerts in Prometheus
- [ ] Enable TLS/SSL for external endpoints
- [ ] Configure network policies
- [ ] Set up backup strategy for persistent volumes
- [ ] Document scaling procedures
- [ ] Test failover scenarios
- [ ] Configure logging aggregation
- [ ] Set up health checks and liveness probes
- [ ] Review security contexts
- [ ] Pin specific image versions (not `:latest`)

## Complete Reference

For complete Kubernetes manifests and detailed configuration:

**📁 [k8s/ Directory](../../k8s/README.md)** - Complete K8s deployment guide with:
- All manifest files (deployment, service, configmap, etc.)
- Detailed secret management instructions
- Production configuration examples
- Networking and security setup
- Monitoring stack configuration
- Troubleshooting guide

**🐳 [Docker Setup](../docker/README.md)** - Local testing with Docker Compose

**🚀 [Deployment Guide](deployment-guide.md)** - General deployment strategies

## Next Steps

1. **Test Locally**: Start with Docker Compose to understand the setup
2. **Deploy to Dev**: Use minimal sidecar deployment for testing
3. **Add Redis**: Enable Redis for production workloads
4. **Add Monitoring**: Deploy Prometheus and Grafana
5. **Configure Alerts**: Set up alerting rules
6. **Scale Up**: Configure HPA and resource limits
7. **Production Deploy**: Follow the production checklist

## Support

- **Issues**: [GitHub Issues](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/discussions)
- **Documentation**: [Full Docs](../../README.md)

---

*For the complete set of production-ready Kubernetes manifests, see the [k8s/ directory](../../k8s/)*

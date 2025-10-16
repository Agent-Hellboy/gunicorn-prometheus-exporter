# Gunicorn Prometheus Exporter

[![Docker Pulls](https://badgen.net/docker/pulls/princekrroshan01/gunicorn-prometheus-exporter)](https://hub.docker.com/r/princekrroshan01/gunicorn-prometheus-exporter)
[![Docker Image Size](https://badgen.net/docker/size/princekrroshan01/gunicorn-prometheus-exporter/0.2.2/amd64)](https://hub.docker.com/r/princekrroshan01/gunicorn-prometheus-exporter)
[![Docker Stars](https://badgen.net/docker/stars/princekrroshan01/gunicorn-prometheus-exporter)](https://hub.docker.com/r/princekrroshan01/gunicorn-prometheus-exporter)

Production-ready Prometheus metrics exporter for Gunicorn applications, designed to run as a sidecar container with Redis-backed distributed metrics storage.

## Quick Start

### Pull the Image

```bash
# Sidecar exporter (latest)
docker pull princekrroshan01/gunicorn-prometheus-exporter:0.2.2

# Sample Flask application (for testing)
docker pull princekrroshan01/gunicorn-app:latest
```

### Docker Compose (with Redis)

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  app:
    image: princekrroshan01/gunicorn-app:latest
    ports:
      - "8000:8000"
    environment:
      - REDIS_ENABLED=true
      - REDIS_HOST=redis
      - REDIS_PORT=6379

  sidecar:
    image: princekrroshan01/gunicorn-prometheus-exporter:0.2.2
    ports:
      - "9091:9091"
    environment:
      - REDIS_ENABLED=true
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - PROMETHEUS_METRICS_PORT=9091
```

### Kubernetes Deployment (with Redis)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gunicorn-app-with-sidecar
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
        prometheus.io/path: "/metrics"
    spec:
      containers:
        # Container 1: Your Gunicorn Application
        - name: app
          image: your-app:latest
          ports:
            - containerPort: 8000
              name: http
          env:
            - name: REDIS_ENABLED
              value: "true"
            - name: REDIS_HOST
              value: "redis-service"
            - name: REDIS_PORT
              value: "6379"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 30

        # Container 2: Sidecar Exporter
        - name: prometheus-exporter
          image: princekrroshan01/gunicorn-prometheus-exporter:0.2.2
          ports:
            - containerPort: 9091
              name: metrics
          env:
            - name: REDIS_ENABLED
              value: "true"
            - name: REDIS_HOST
              value: "redis-service"
            - name: REDIS_PORT
              value: "6379"
          livenessProbe:
            httpGet:
              path: /metrics
              port: 9091
            initialDelaySeconds: 5
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /metrics
              port: 9091
            initialDelaySeconds: 3
            periodSeconds: 10
          securityContext:
            readOnlyRootFilesystem: true
            runAsNonRoot: true
            runAsUser: 1000

---
apiVersion: v1
kind: Service
metadata:
  name: gunicorn-app-service
spec:
  selector:
    app: gunicorn-app
  ports:
    - port: 8000
      name: http
    - port: 9091
      name: metrics
  type: ClusterIP

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
      name: redis
  type: ClusterIP
```

## Architecture

The sidecar pattern with Redis backend provides a scalable, secure metrics collection system:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        KUBERNETES POD (Multi-Pod)                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  POD REPLICA 1                           POD REPLICA 2                    │
│  ┌─────────────────────────┐            ┌─────────────────────────┐    │
│  │ Container: Gunicorn App │            │ Container: Gunicorn App │    │
│  │                         │            │                         │    │
│  │ ✓ Runs at :8000        │            │ ✓ Runs at :8000        │    │
│  │ ✓ REDIS_ENABLED=true   │            │ ✓ REDIS_ENABLED=true   │    │
│  │ ✓ readOnlyRootFS=false │            │ ✓ readOnlyRootFS=false │    │
│  │                         │            │                         │    │
│  │ Metrics Flow:           │            │ Metrics Flow:           │    │
│  │ counter.inc() ──┐       │            │ counter.inc() ──┐       │    │
│  │ gauge.set()    │       │            │ gauge.set()    │       │    │
│  │ histogram.obs()│       │            │ histogram.obs()│       │    │
│  └────────────────┼───────┘            └────────────────┼───────┘    │
│                   │                                      │              │
│        ┌──────────┴──────────────────────────────────────┘              │
│        │                                                                 │
│        ▼                                                                 │
│   REDIS STORAGE (Shared Backend)                                        │
│   ┌──────────────────────────────────────┐                             │
│   │ Key: gunicorn:counter:*:data         │                             │
│   │ Key: gunicorn:gauge:*:data           │                             │
│   │ Key: gunicorn:histogram:*:data       │                             │
│   │ TTL: Auto-cleanup enabled            │                             │
│   └──────────────────────────────────────┘                             │
│        ▲                                                                 │
│        │                                                                 │
│   ┌────┴─────────────────────────────────────────────────┐             │
│   │                                                      │              │
│  ┌───────────────────────┐        ┌───────────────────────┐           │
│  │ Container: Sidecar    │        │ Container: Sidecar    │           │
│  │ Exporter              │        │ Exporter              │           │
│  │                       │        │                       │           │
│  │ ✓ Reads from Redis   │        │ ✓ Reads from Redis   │           │
│  │ ✓ Port 9091 metrics  │        │ ✓ Port 9091 metrics  │           │
│  │ ✓ readOnlyRootFS=true│        │ ✓ readOnlyRootFS=true│           │
│  │                       │        │                       │           │
│  │ /metrics endpoint:    │        │ /metrics endpoint:    │           │
│  │ gunicorn_worker_*     │        │ gunicorn_worker_*     │           │
│  │ gunicorn_master_*     │        │ gunicorn_master_*     │           │
│  │ gunicorn_sidecar_*    │        │ gunicorn_sidecar_*    │           │
│  └─────────┬─────────────┘        └─────────┬─────────────┘           │
│            │                               │                           │
└────────────┼───────────────────────────────┼──────────────────────────┘
             │                               │
             └───────────────┬───────────────┘
                             │
                    ┌────────▼─────────┐
                    │   PROMETHEUS     │
                    │  Scraper Agent   │
                    │                  │
                    │ GET :9091/metrics│
                    │ (from sidecar)   │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   PROMETHEUS    │
                    │   Time-Series   │
                    │   Database      │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   GRAFANA       │
                    │   Dashboards    │
                    └─────────────────┘
```

## Complete Data Flow

```
1. APP CONTAINER (Gunicorn Process)
   counter.inc() / gauge.set() / histogram.observe()
   ↓
2. REDIS STORAGE (Distributed Backend)
   Metrics stored as Redis hashes with TTL
   - gunicorn:counter:*:data
   - gunicorn:gauge:*:data
   - gunicorn:histogram:*:data
   ↓
3. SIDECAR CONTAINER (Metrics Exporter)
   Reads all metrics from Redis
   Aggregates from all workers/pods
   ↓
4. PROMETHEUS SCRAPER
   Pulls from :9091/metrics endpoint
   Stores time-series data
   ↓
5. GRAFANA VISUALIZATION
   Queries Prometheus
   Displays dashboards
```

## Features

- *Multi-Architecture*: AMD64 and ARM64 support
- *Redis Backend*: Distributed metrics storage for multi-instance deployments (RECOMMENDED)
- *File-Based Storage*: Traditional multiprocess file storage (local development)
- *Production Ready*: Security contexts, non-root user, read-only filesystem
- *Complete Stack*: Includes Prometheus and Grafana configurations
- *Zero Configuration*: Works out of the box with sensible defaults
- *Kubernetes Ready*: DaemonSet and Deployment patterns supported
- *Multi-Pod Scaling*: Metrics aggregated from all replicas

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_METRICS_PORT` | `9091` | Port for metrics endpoint |
| `PROMETHEUS_BIND_ADDRESS` | `0.0.0.0` | Bind address for metrics server |
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus_multiproc` | Directory for multiprocess metrics (file storage) |
| `REDIS_ENABLED` | `true` | Enable Redis storage backend (RECOMMENDED) |
| `REDIS_HOST` | `redis-service` | Redis host (use `localhost` for local dev) |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database number |
| `REDIS_PASSWORD` | *(none)* | Redis password (optional) |
| `REDIS_KEY_PREFIX` | `gunicorn` | Redis key prefix |
| `SIDECAR_UPDATE_INTERVAL` | `30` | Metrics update interval (seconds) |
| `SIDECAR_MODE` | `true` | Run in sidecar mode (skip metrics server in app) |

## Use Cases

### Recommended: Redis-Backed Sidecar (Kubernetes/Multi-Pod)

The exporter runs alongside your application in the same pod/container group with Redis as shared backend:

- Application writes metrics to Redis (no shared filesystem needed)
- Sidecar reads from Redis and exposes metrics via HTTP
- Prometheus scrapes the sidecar endpoint (:9091/metrics)
- Works across multiple pods/replicas
- Supports read-only filesystem for sidecar container
- Scalable to multi-node deployments

### Classic: File-Based Sidecar (Docker/Local Development)

Run with shared volume for metrics:

- Application writes metrics to shared volume
- Sidecar reads from shared volume and exposes metrics
- Prometheus scrapes the sidecar endpoint

### Standalone Mode

Run metrics server directly within your application container (less recommended).

## Metrics Exposed

Core metrics include:

- `gunicorn_worker_requests_total` - Total requests per worker
- `gunicorn_worker_request_duration_seconds` - Request duration histogram
- `gunicorn_worker_memory_bytes` - Memory usage per worker
- `gunicorn_worker_cpu_percent` - CPU usage per worker
- `gunicorn_worker_state` - Worker state (running/stopped)
- `gunicorn_worker_uptime_seconds` - Worker uptime
- `gunicorn_master_worker_restart_total` - Master worker restart count
- `gunicorn_sidecar_uptime_seconds` - Sidecar uptime
- `gunicorn_sidecar_redis_connected` - Redis connection status

### Access Metrics

```bash
curl http://localhost:9091/metrics
```

## Security

The container runs with:

- Non-root user (UID 1000)
- Read-only root filesystem (for sidecar in Kubernetes)
- No privilege escalation
- All capabilities dropped
- Security contexts for Kubernetes
- No shared filesystem required (with Redis backend)

## Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'gunicorn-app'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        target_label: __meta_kubernetes_pod_container_port_number
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
```

Or with pod annotations:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9091"
  prometheus.io/path: "/metrics"
```

## Documentation

- [GitHub Repository](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter)
- [Complete Documentation](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/tree/main/docs)
- [User Setup Guide](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/blob/main/docker/README.md#user-setup-guide-using-the-sidecar-container)
- [Kubernetes Deployment Guide](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/tree/main/k8s)
- [Docker Compose Examples](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/tree/main/docker)
- [Deployment Examples](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/tree/main/docs/examples)

## Related Images

- `princekrroshan01/gunicorn-prometheus-exporter:0.2.2` - Sidecar exporter
- `princekrroshan01/gunicorn-app:latest` - Sample Flask application

## Troubleshooting

### Metrics not appearing?

1. Verify Redis is running: `redis-cli ping`
2. Check `REDIS_ENABLED=true` in both app and sidecar
3. Verify `REDIS_HOST` and `REDIS_PORT` are correct
4. Ensure application is generating requests
5. Check sidecar logs: `docker logs <container-id>`

### Redis connection issues?

- Verify Redis is accessible: `nc -zv redis 6379`
- Check Redis password if configured
- Verify network connectivity between containers
- Check Redis logs for errors

### Sidecar not exposing metrics?

- Verify sidecar health check: `curl http://localhost:9091/metrics`
- Check port 9091 is exposed correctly
- Verify PROMETHEUS_METRICS_PORT is set to 9091
- Check sidecar container logs for startup errors

### Permission issues?

- Ensure containers run as same user (1000)
- Verify security contexts are applied correctly
- Check container logs for permission denied errors

## License

MIT License - See [LICENSE](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/blob/main/LICENSE)

## Contributing

Contributions welcome! Please see our [Contributing Guide](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/blob/main/docs/contributing.md)

## Support

If you find this project useful, please consider giving it a star on [GitHub](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter)!

---

*Built with for the Python community*

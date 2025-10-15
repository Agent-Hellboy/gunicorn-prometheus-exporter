# Gunicorn Prometheus Exporter

[![Docker Pulls](https://badgen.net/docker/pulls/princekrroshan01/gunicorn-prometheus-exporter)](https://hub.docker.com/r/princekrroshan01/gunicorn-prometheus-exporter)
[![Docker Image Size](https://badgen.net/docker/size/princekrroshan01/gunicorn-prometheus-exporter/0.2.2/amd64)](https://hub.docker.com/r/princekrroshan01/gunicorn-prometheus-exporter)
[![Docker Stars](https://badgen.net/docker/stars/princekrroshan01/gunicorn-prometheus-exporter)](https://hub.docker.com/r/princekrroshan01/gunicorn-prometheus-exporter)

Production-ready Prometheus metrics exporter for Gunicorn applications, designed to run as a sidecar container.

## Quick Start

### Pull the Image

```bash
# Sidecar exporter
docker pull princekrroshan01/gunicorn-prometheus-exporter:0.2.2

# Sample Flask application (for testing)
docker pull princekrroshan01/gunicorn-app:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    image: princekrroshan01/gunicorn-app:latest
    ports:
      - "8000:8000"
    environment:
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
      - GUNICORN_WORKERS=2
    volumes:
      - prometheus_data:/tmp/prometheus_multiproc

  sidecar:
    image: princekrroshan01/gunicorn-prometheus-exporter:0.2.2
    ports:
      - "9091:9091"
    environment:
      - PROMETHEUS_METRICS_PORT=9091
      - PROMETHEUS_BIND_ADDRESS=0.0.0.0
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
    volumes:
      - prometheus_data:/tmp/prometheus_multiproc

volumes:
  prometheus_data:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gunicorn-app-with-sidecar
spec:
  template:
    spec:
      containers:
        - name: app
          image: your-app:latest
          volumeMounts:
            - name: prometheus-data
              mountPath: /tmp/prometheus_multiproc

        - name: prometheus-exporter
          image: princekrroshan01/gunicorn-prometheus-exporter:0.2.2
          ports:
            - containerPort: 9091
          volumeMounts:
            - name: prometheus-data
              mountPath: /tmp/prometheus_multiproc
              readOnly: true

      volumes:
        - name: prometheus-data
          emptyDir: {}
```

## Architecture

The sidecar pattern separates metrics collection from your application:

```
┌─────────────────────────────────────────┐
│              Kubernetes Pod              │
│                                          │
│  ┌──────────────┐    ┌──────────────┐  │
│  │ Your App     │    │  Sidecar     │  │
│  │ (Gunicorn)   │    │  Exporter    │  │
│  │              │    │              │  │
│  │ Writes ─────▶│    │◀──── Reads   │  │
│  │ metrics      │    │  metrics     │  │
│  │              │    │              │  │
│  └──────────────┘    └──────────────┘  │
│         │                    │          │
│    Port 8000            Port 9091       │
│    (Your API)         (Metrics HTTP)    │
└─────────────────────────────────────────┘
                  │
                  ▼
          ┌──────────────┐
          │  Prometheus  │
          │   Scrapes    │
          └──────────────┘
```

## Features

- *Multi-Architecture*: AMD64 and ARM64 support
- *Redis Backend*: Distributed metrics storage for multi-instance deployments
- *File-Based Storage*: Traditional multiprocess file storage
- *Production Ready*: Security contexts, non-root user, read-only filesystem
- *Complete Stack*: Includes Prometheus and Grafana configurations
- *Zero Configuration*: Works out of the box with sensible defaults

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_METRICS_PORT` | `9091` | Port for metrics endpoint |
| `PROMETHEUS_BIND_ADDRESS` | `0.0.0.0` | Bind address for metrics server |
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus_multiproc` | Directory for multiprocess metrics |
| `REDIS_ENABLED` | `false` | Enable Redis storage backend |
| `REDIS_HOST` | `redis-service` | Redis host (use `localhost` for local dev) |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database number |
| `REDIS_PASSWORD` | *(none)* | Redis password |
| `REDIS_KEY_PREFIX` | `gunicorn` | Redis key prefix |
| `SIDECAR_UPDATE_INTERVAL` | `30` | Metrics update interval (seconds) |

### With Redis Backend

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  sidecar:
    image: princekrroshan01/gunicorn-prometheus-exporter:0.2.2
    environment:
      - REDIS_ENABLED=true
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
```

## Security

The container runs with:
- Non-root user (UID 1000)
- Read-only root filesystem
- No privilege escalation
- All capabilities dropped
- Security contexts for Kubernetes

## Metrics

Exposed metrics include:

- `gunicorn_worker_requests_total` - Total requests per worker
- `gunicorn_worker_request_duration_seconds` - Request duration histogram
- `gunicorn_worker_memory_bytes` - Memory usage per worker
- `gunicorn_worker_cpu_percent` - CPU usage per worker
- `gunicorn_worker_state` - Worker state (running/stopped)
- `gunicorn_worker_uptime_seconds` - Worker uptime

### Access Metrics

```bash
curl http://localhost:9091/metrics
```

## Use Cases

### Sidecar Pattern (Recommended)

The exporter runs alongside your application in the same pod/container group:

- Application writes metrics to shared volume
- Sidecar reads and exposes metrics via HTTP
- Prometheus scrapes the sidecar endpoint

### Standalone Mode

Run metrics server directly within your application container.

### With Prometheus

```yaml
scrape_configs:
  - job_name: 'gunicorn-app'
    static_configs:
      - targets: ['sidecar:9091']
    scrape_interval: 15s
```

## Documentation

- [GitHub Repository](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter)
- [Complete Documentation](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/tree/main/docs)
- [Kubernetes Deployment Guide](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/tree/main/k8s)
- [Docker Compose Examples](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/tree/main/docker)
- [Integration Examples](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/tree/main/docs/examples)

## Related Images

- `princekrroshan01/gunicorn-prometheus-exporter:0.2.2` - Sidecar exporter
- `princekrroshan01/gunicorn-app:latest` - Sample Flask application

## Troubleshooting

### Metrics not appearing?

1. Verify shared volume is mounted correctly
2. Check `PROMETHEUS_MULTIPROC_DIR` matches in both containers
3. Ensure application is generating requests
4. Check sidecar logs: `docker logs <container-id>`

### Permission issues?

- Ensure shared volume has correct permissions
- Both containers should run as same user/group
- Check volume ownership with `ls -la /tmp/prometheus_multiproc`

### Redis connection issues?

- Verify Redis is accessible: `nc -zv redis 6379`
- Check `REDIS_HOST` and `REDIS_PORT` settings
- Verify Redis is running: `docker ps | grep redis`

## License

MIT License - See [LICENSE](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/blob/main/LICENSE)

## Contributing

Contributions welcome! Please see our [Contributing Guide](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/blob/main/docs/contributing.md)

## Support

If you find this project useful, please consider giving it a star on [GitHub](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter)!

---

*Built with ❤️ for the Python community*

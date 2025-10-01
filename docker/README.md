# Gunicorn Prometheus Exporter - Docker Sidecar

This directory contains Docker configurations for running the Gunicorn Prometheus Exporter as a sidecar container.

## Quick Start

### 1. Build and Run with Docker Compose

```bash
# Clone the repository
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter.git
cd gunicorn-prometheus-exporter

# (Optional) Set Grafana admin password for production
export GRAFANA_ADMIN_PASSWORD=your-secure-password

# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

**Security Note**: For production deployments, always set `GRAFANA_ADMIN_PASSWORD` environment variable. The default `admin` password is only for local development.

### 2. Access the Services

- **Application**: http://localhost:8000
- **Metrics (Sidecar)**: http://localhost:9091/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `${GRAFANA_ADMIN_PASSWORD}` (default: `admin`)

### 3. Test the Setup

```bash
# Test the application
curl http://localhost:8000/health

# Test metrics endpoint
curl http://localhost:9091/metrics

# Generate some load
for i in {1..10}; do
  curl http://localhost:8000/slow &
  curl http://localhost:8000/heavy &
done
```

## Docker Images

### Sidecar Image

The main sidecar image is built from the `Dockerfile` in the root directory:

```bash
# Build the sidecar image
docker build -t gunicorn-prometheus-exporter:latest .

# Run the sidecar
docker run -d \
  --name gunicorn-sidecar \
  -p 9091:9091 \
  -v /tmp/prometheus_multiproc:/tmp/prometheus_multiproc \
  gunicorn-prometheus-exporter:0.1.8
```

### Application Image

The sample application image is built from `docker/Dockerfile.app`:

```bash
# Build the application image
docker build -f docker/Dockerfile.app -t gunicorn-app:0.1.8 .

# Run with increased shared memory (required for Gunicorn workers using /dev/shm)
docker run -d \
  --name gunicorn-app \
  --shm-size=1g \
  -p 8000:8000 \
  -e PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc \
  -v /tmp/prometheus_multiproc:/tmp/prometheus_multiproc \
  gunicorn-app:0.1.8
```

**Important**: Gunicorn uses `/dev/shm` for worker temporary files. The default Docker shared memory is only 64MB, which may be insufficient for production workloads. Always set `--shm-size` (Docker) or `shm_size` (Docker Compose) to at least 1GB.

## Configuration

> *Production recommendation*: Enable Redis (`REDIS_ENABLED=true`) for any deployment running more than one Gunicorn worker or multiple containers. The sample Compose and Kubernetes manifests already wire Redis by default.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_METRICS_PORT` | `9091` | Port for metrics endpoint |
| `PROMETHEUS_BIND_ADDRESS` | `0.0.0.0` | Bind address for metrics |
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus_multiproc` | Multiprocess directory |
| `REDIS_ENABLED` | `false` | Enable Redis storage |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database |
| `REDIS_PASSWORD` | *(none)* | Redis password |
| `REDIS_KEY_PREFIX` | `gunicorn` | Redis key prefix |
| `SIDECAR_UPDATE_INTERVAL` | `30` | Update interval in seconds |

### Redis Configuration

To enable Redis storage, set the following environment variables:

```bash
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_KEY_PREFIX=gunicorn
```

## Deployment Modes

### 1. Sidecar Mode (Default)

Run as a sidecar container alongside your application:

```bash
docker run -d \
  --name gunicorn-sidecar \
  -p 9091:9091 \
  -v /tmp/prometheus_multiproc:/tmp/prometheus_multiproc \
  gunicorn-prometheus-exporter:0.1.8 sidecar
```

### 2. Standalone Mode

Run as a standalone metrics server:

```bash
docker run -d \
  --name gunicorn-standalone \
  -p 9091:9091 \
  -v /tmp/prometheus_multiproc:/tmp/prometheus_multiproc \
  gunicorn-prometheus-exporter:0.1.8 standalone
```

### 3. Health Check Mode

Run health check:

```bash
docker run --rm \
  gunicorn-prometheus-exporter:0.1.8 health
```

## Kubernetes Deployment

### Sidecar Deployment

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
          ports:
            - containerPort: 8000
              name: http
          env:
            - name: PROMETHEUS_MULTIPROC_DIR
              value: "/tmp/prometheus_multiproc"
            - name: GUNICORN_WORKERS
              value: "4"
          volumeMounts:
            - name: prometheus-data
              mountPath: /tmp/prometheus_multiproc

        # Prometheus exporter sidecar
        - name: prometheus-exporter
          image: princekrroshan01/gunicorn-prometheus-exporter:0.1.8
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
      volumes:
        - name: prometheus-data
          emptyDir: {}
```

### Redis Integration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gunicorn-app-with-redis
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
        # Main application container
        - name: app
          image: princekrroshan01/gunicorn-app:0.1.8
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

        # Prometheus exporter sidecar
        - name: prometheus-exporter
          image: princekrroshan01/gunicorn-prometheus-exporter:0.1.8
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
```

## Docker Hub Publishing

### 1. Build and Tag

```bash
# Build the image
docker build -t gunicorn-prometheus-exporter:latest .

# Tag for Docker Hub
docker tag gunicorn-prometheus-exporter:latest princekrroshan01/gunicorn-prometheus-exporter:latest
docker tag gunicorn-prometheus-exporter:latest princekrroshan01/gunicorn-prometheus-exporter:0.1.8
```

### 2. Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Push the images
docker push princekrroshan01/gunicorn-prometheus-exporter:latest
docker push princekrroshan01/gunicorn-prometheus-exporter:0.1.8
```

### 3. Automated Builds

Set up automated builds on Docker Hub:

1. Connect your GitHub repository to Docker Hub
2. Create a new automated build
3. Configure build rules for different branches/tags
4. Enable build triggers

## Monitoring and Alerting

### Prometheus Queries

```promql
# Request rate
rate(gunicorn_worker_requests_total[5m])

# Error rate
rate(gunicorn_worker_failed_requests[5m])

# Memory usage
gunicorn_worker_memory_bytes

# CPU usage
gunicorn_worker_cpu_percent

# Request duration
histogram_quantile(0.95, rate(gunicorn_worker_request_duration_seconds_bucket[5m]))
```

### Grafana Dashboard

Import the provided Grafana dashboard to visualize metrics:

1. Open Grafana at http://localhost:3000
2. Go to Dashboards > Import
3. Upload the dashboard JSON file
4. Configure the Prometheus data source

## Troubleshooting

### Common Issues

1. **Metrics not appearing**: Check if the multiprocess directory is shared between containers
2. **Redis connection failed**: Verify Redis is running and accessible
3. **Port conflicts**: Ensure ports 9091, 8000, 9090, 3000 are available
4. **Permission issues**: Check file permissions on the multiprocess directory

### Debug Mode

Run the sidecar in debug mode:

```bash
docker run -it --rm \
  -v /tmp/prometheus_multiproc:/tmp/prometheus_multiproc \
  gunicorn-prometheus-exporter:0.1.8 \
  python3 /app/sidecar.py --port 9091 --bind 0.0.0.0
```

### Logs

Check container logs:

```bash
# Sidecar logs
docker logs gunicorn-sidecar

# Application logs
docker logs gunicorn-app

# All services
docker-compose logs -f
```

## Security Considerations

1. **Network Security**: Use internal networks for container communication
2. **Authentication**: Implement authentication for metrics endpoints in production
3. **TLS**: Enable TLS for secure communication
4. **Resource Limits**: Set appropriate CPU and memory limits
5. **Non-root User**: The container runs as a non-root user for security

## Performance Tuning

1. **Worker Count**: Adjust based on CPU cores and workload
2. **Memory Limits**: Set appropriate memory limits for containers
3. **Update Intervals**: Tune metrics update intervals based on requirements
4. **Redis Configuration**: Optimize Redis settings for your use case

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker Compose
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

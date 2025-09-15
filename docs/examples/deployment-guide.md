# Deployment Guide

This comprehensive guide covers deploying Gunicorn Prometheus Exporter in various environments, from local development to production Kubernetes clusters.

## 🌐 Understanding the Three URLs

When deploying with Gunicorn Prometheus Exporter, you'll work with three distinct URLs:

| Service | URL | Purpose |
|---------|-----|---------|
| **Prometheus UI** | `http://localhost:9090` | Prometheus web interface for querying and visualizing metrics |
| **Your Application** | `http://localhost:8200` | Your actual web application (Gunicorn server) |
| **Metrics Endpoint** | `http://127.0.0.1:9091/metrics` | Raw metrics data for Prometheus to scrape |

### URL Configuration

The metrics endpoint URL is configurable through environment variables:

```bash
# Basic metrics server configuration
export PROMETHEUS_METRICS_PORT="9091"        # Port for metrics endpoint
export PROMETHEUS_BIND_ADDRESS="127.0.0.1"   # Bind address for metrics server
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"  # Metrics storage directory

# SSL/TLS configuration (optional, for production)
export PROMETHEUS_SSL_CERTFILE="/path/to/cert.pem"           # SSL certificate file
export PROMETHEUS_SSL_KEYFILE="/path/to/key.pem"             # SSL private key file
export PROMETHEUS_SSL_CLIENT_CAFILE="/path/to/ca.pem"       # Client CA file (optional)
export PROMETHEUS_SSL_CLIENT_CAPATH="/path/to/ca/dir"        # Client CA directory (optional)
export PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED="false"           # Require client cert auth
```

> **Security Note**: For production deployments, consider enabling SSL/TLS to secure the metrics endpoint, especially if it's accessible over the network.

## 🚀 Integration Guide

This section walks you through integrating Gunicorn Prometheus Exporter with Prometheus monitoring.

### Step-by-Step Integration

1. **Start your Gunicorn application with the Prometheus exporter on port 9091**
   ```bash
   # Set up environment variables
   export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
   export PROMETHEUS_METRICS_PORT="9091"
   export PROMETHEUS_BIND_ADDRESS="127.0.0.1"
   export GUNICORN_WORKERS="2"
   
   # Start your application
   gunicorn --config gunicorn.conf.py app:app
   ```
   
   You should see logs like:
   ```
   INFO:gunicorn_prometheus_exporter.hooks:Starting Prometheus multiprocess metrics server on 127.0.0.1:9091
   INFO:gunicorn_prometheus_exporter.hooks:HTTP metrics server started successfully on 127.0.0.1:9091
   ```

2. **Open Prometheus UI in your browser at: http://localhost:9090**
   - This is the Prometheus web interface for querying and visualizing metrics
   - You should see the Prometheus dashboard with various menu options

3. **View targets at: http://localhost:9090/targets to see if your Gunicorn exporter is being scraped successfully**
   - Navigate to the "Targets" page in Prometheus UI
   - Look for your Gunicorn application target
   - Status should show "UP" if everything is working correctly
   - If status is "DOWN", check your Prometheus configuration and network connectivity

4. **Query metrics at: http://localhost:9090/graph to explore the Gunicorn metrics**
   - Go to the "Graph" page in Prometheus UI
   - Try these sample queries:
     - `gunicorn_worker_requests_total` - Total requests per worker
     - `gunicorn_worker_memory_bytes` - Memory usage per worker
     - `gunicorn_worker_cpu_percent` - CPU usage per worker
     - `rate(gunicorn_worker_requests_total[5m])` - Request rate

### Basic Configuration

Create `gunicorn.conf.py`:

```python
# gunicorn.conf.py
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
bind = "0.0.0.0:8200"  # Your application port
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

### Start Services

1. **Start Prometheus:**
```bash
prometheus --config.file=prometheus.yml --storage.tsdb.path=./prometheus-data
```

2. **Start Your Application:**
```bash
gunicorn --config gunicorn.conf.py app:app
```

3. **Access Services:**
- **Application**: http://localhost:8200
- **Metrics Endpoint**: http://127.0.0.1:9091/metrics
- **Prometheus UI**: http://localhost:9090

### Prometheus Configuration

Create `prometheus.yml` to scrape your Gunicorn metrics:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'gunicorn-app'
    static_configs:
      - targets: ['127.0.0.1:9091']  # Your metrics endpoint
    metrics_path: /metrics
    scrape_interval: 5s
```

### Integration Troubleshooting

**If your target shows as "DOWN" in Prometheus:**

1. **Check if metrics endpoint is accessible:**
   ```bash
   curl http://127.0.0.1:9091/metrics
   ```

2. **Verify Prometheus configuration:**
   - Ensure `prometheus.yml` has the correct target address
   - Check if the scrape interval is reasonable (5-15 seconds)

3. **Check network connectivity:**
   - Ensure Prometheus can reach your application
   - Verify firewall settings if applicable

4. **Check application logs:**
   - Look for "Metrics server started successfully" message
   - Check for any SSL or binding errors

**If metrics are not appearing:**

1. **Generate some traffic:**
   ```bash
   # Make requests to your application to generate metrics
   curl http://localhost:8200/
   ```

2. **Check worker metrics:**
   - Look for `gunicorn_worker_requests_total` in Prometheus
   - Verify worker IDs are being generated correctly

## 🐳 Docker Deployment

### Single Container Setup

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install gunicorn gunicorn-prometheus-exporter

# Copy application
COPY . .

# Create necessary directories
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
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8200:8200"  # Application port
      - "9091:9091"  # Metrics port
    environment:
      - PROMETHEUS_METRICS_PORT=9091
      - PROMETHEUS_BIND_ADDRESS=0.0.0.0
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
      - GUNICORN_WORKERS=4
      # SSL/TLS configuration (optional)
      - PROMETHEUS_SSL_CERTFILE=/etc/ssl/certs/metrics.crt
      - PROMETHEUS_SSL_KEYFILE=/etc/ssl/private/metrics.key
      - PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED=false
    volumes:
      - prometheus_data:/tmp/prometheus_multiproc
      # Mount SSL certificates (if using SSL)
      - ./ssl:/etc/ssl/certs:ro
      - ./ssl:/etc/ssl/private:ro

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"  # Prometheus UI
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_storage:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus' #local testing
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'

volumes:
  prometheus_data:
  prometheus_storage:
```

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'gunicorn-app'
    static_configs:
      - targets: ['app:9091']  # Docker service name
    metrics_path: /metrics
    scrape_interval: 5s
```

### Multi-Container Setup

**docker-compose.yml (Multi-Service):**
```yaml
version: '3.8'

services:
  app1:
    build: .
    ports:
      - "8201:8200"
      - "9091:9091"
    environment:
      - PROMETHEUS_METRICS_PORT=9091
      - PROMETHEUS_BIND_ADDRESS=0.0.0.0
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
      - GUNICORN_WORKERS=2
    volumes:
      - prometheus_data_1:/tmp/prometheus_multiproc

  app2:
    build: .
    ports:
      - "8202:8200"
      - "9092:9091"
    environment:
      - PROMETHEUS_METRICS_PORT=9091
      - PROMETHEUS_BIND_ADDRESS=0.0.0.0
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
      - GUNICORN_WORKERS=2
    volumes:
      - prometheus_data_2:/tmp/prometheus_multiproc

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_storage:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

volumes:
  prometheus_data_1:
  prometheus_data_2:
  prometheus_storage:
```

## ☸️ Kubernetes Deployment

### Namespace and ConfigMap

**namespace.yaml:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: gunicorn-prometheus
```

**configmap.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gunicorn-config
  namespace: gunicorn-prometheus
data:
  gunicorn.conf.py: |
    import os
    
    os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
    os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
    os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
    os.environ.setdefault("GUNICORN_WORKERS", "4")
    
    from gunicorn_prometheus_exporter.hooks import (
        default_on_exit,
        default_on_starting,
        default_post_fork,
        default_when_ready,
        default_worker_int,
    )
    
    bind = "0.0.0.0:8200"
    workers = 4
    worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
    timeout = 300
    
    when_ready = default_when_ready
    on_starting = default_on_starting
    worker_int = default_worker_int
    on_exit = default_on_exit
    post_fork = default_post_fork
```

### Application Deployment

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gunicorn-app
  namespace: gunicorn-prometheus
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
        volumeMounts:
        - name: config
          mountPath: /app/gunicorn.conf.py
          subPath: gunicorn.conf.py
        - name: prometheus-data
          mountPath: /tmp/prometheus_multiproc
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: gunicorn-config
      - name: prometheus-data
        emptyDir: {}
```

### Service and Ingress

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: gunicorn-app-service
  namespace: gunicorn-prometheus
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

**ingress.yaml:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gunicorn-app-ingress
  namespace: gunicorn-prometheus
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: your-app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: gunicorn-app-service
            port:
              number: 8200
```

### Prometheus Operator Setup

**prometheus.yaml:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: prometheus
  namespace: gunicorn-prometheus
spec:
  serviceAccountName: prometheus
  serviceMonitorSelector:
    matchLabels:
      app: gunicorn-app
  resources:
    requests:
      memory: 400Mi
  enableAdminAPI: false
```

**servicemonitor.yaml:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: gunicorn-app-monitor
  namespace: gunicorn-prometheus
  labels:
    app: gunicorn-app
spec:
  selector:
    matchLabels:
      app: gunicorn-app
  endpoints:
  - port: metrics
    path: /metrics
    interval: 15s
```

## 🌐 Network Configuration

### Docker Networks

**Custom Network:**
```yaml
version: '3.8'

networks:
  gunicorn-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  app:
    build: .
    networks:
      gunicorn-network:
        ipv4_address: 172.20.0.10
    ports:
      - "8200:8200"
      - "9091:9091"

  prometheus:
    image: prom/prometheus:latest
    networks:
      gunicorn-network:
        ipv4_address: 172.20.0.20
    ports:
      - "9090:9090"
```

### Kubernetes Network Policies

**network-policy.yaml:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gunicorn-app-netpol
  namespace: gunicorn-prometheus
spec:
  podSelector:
    matchLabels:
      app: gunicorn-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8200
    - protocol: TCP
      port: 9091
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090
```

## 🔧 Production Considerations

### Security

1. **SSL/TLS Configuration:**
```bash
# Enable SSL/TLS for metrics endpoint
export PROMETHEUS_SSL_CERTFILE="/etc/ssl/certs/metrics.crt"
export PROMETHEUS_SSL_KEYFILE="/etc/ssl/private/metrics.key"
export PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED="true"
export PROMETHEUS_SSL_CLIENT_CAFILE="/etc/ssl/certs/ca.crt"
```

2. **Network Segmentation:**
```yaml
# Only expose metrics port internally
ports:
- containerPort: 8200
  name: http
- containerPort: 9091
  name: metrics
  # Don't expose metrics port externally
```

3. **Authentication:**
```python
# Add basic auth to metrics endpoint
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from django.http import HttpResponse
from django.contrib.auth import authenticate

def metrics_view(request):
    if not authenticate(request):
        return HttpResponse('Unauthorized', status=401)
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
```

### Performance

1. **Resource Limits:**
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

2. **Scaling:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gunicorn-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gunicorn-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 📊 Monitoring Queries

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

### Grafana Dashboard

Create a Grafana dashboard with panels for:
- Request rate and duration
- Memory and CPU usage
- Error rates
- Worker health status

## 🚨 Troubleshooting

### Common Issues

1. **Connection Refused on Metrics Port:**
   - **Root Cause**: The metrics server was not binding to the configured address
   - **Solution**: Ensure you're using the latest version with the bind address fix
   - **Check**: Verify logs show "Metrics server started successfully on [address]:[port]"
   - **Test**: `curl http://your-bind-address:9091/metrics`

2. **Metrics Not Accessible:**
   - Check firewall rules
   - Verify bind address configuration (`PROMETHEUS_BIND_ADDRESS`)
   - Ensure ports are properly exposed
   - Check if metrics server is binding to `0.0.0.0` vs `127.0.0.1`

3. **Prometheus Not Scraping:**
   - Verify service discovery
   - Check network connectivity
   - Validate scrape configuration
   - Ensure metrics endpoint is accessible from Prometheus server

4. **Port Conflicts:**
   - Default metrics port is 9091 (not 9090) to avoid conflicts with Prometheus UI
   - Change `PROMETHEUS_METRICS_PORT` if needed
   - Check for other services using the same port

5. **High Memory Usage:**
   - Adjust worker count
   - Monitor multiprocess directory size
   - Implement metrics cleanup

6. **SSL/TLS Issues:**
   - Verify certificate files exist and are readable
   - Check certificate validity and expiration
   - Ensure private key permissions are correct (600)
   - Test SSL connection: `curl -k https://localhost:9091/metrics`
   - Check for SSL handshake errors in logs

7. **Client Certificate Authentication:**
   - Verify client CA file/directory configuration
   - Test with valid client certificate
   - Check `PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED` setting

### Debug Commands

```bash
# Check metrics endpoint
curl http://localhost:9091/metrics

# Check HTTPS metrics endpoint (if SSL enabled)
curl -k https://localhost:9091/metrics

# Test SSL certificate
openssl s_client -connect localhost:9091 -servername localhost

# Check certificate details
openssl x509 -in /path/to/cert.pem -text -noout

# Check private key
openssl rsa -in /path/to/key.pem -check

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Kubernetes service
kubectl get svc -n gunicorn-prometheus

# Check pod logs
kubectl logs -f deployment/gunicorn-app -n gunicorn-prometheus
```

## 🔗 Related Documentation

- [Django Integration](django-integration.md)
- [FastAPI Integration](fastapi-integration.md)
- [Flask Integration](flask-integration.md)
- [Configuration Reference](../configuration.md)
- [Troubleshooting Guide](../troubleshooting.md)

# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Gunicorn Prometheus Exporter as a sidecar container.

## Quick Start

### 1. Deploy Redis (Required for shared metrics)

```bash
kubectl apply -f redis-deployment.yaml
```

### 2. Deploy the Application with Sidecar

```bash
kubectl apply -f sidecar-deployment.yaml
```

### 3. Deploy Prometheus (Optional)

```bash
kubectl apply -f prometheus-deployment.yaml
```

### 4. Deploy Grafana (Optional)

```bash
kubectl apply -f grafana-deployment.yaml
```

## Complete Deployment

Deploy everything at once:

```bash
kubectl apply -f .
```

## Accessing the Services

### Port Forwarding

```bash
# Application
kubectl port-forward service/gunicorn-app-service 8000:8000

# Metrics (Sidecar)
kubectl port-forward service/gunicorn-metrics-service 9091:9091

# Prometheus
kubectl port-forward service/prometheus-service 9090:9090

# Grafana
kubectl port-forward service/grafana-service 3000:3000
```

### Access URLs

- **Application**: http://localhost:8000
- **Metrics**: http://localhost:9091/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## Configuration

### Environment Variables

The sidecar container supports the following environment variables:

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

### Customizing the Deployment

#### 1. Update Image References

Replace `your-registry/gunicorn-app:latest` and `your-registry/gunicorn-prometheus-exporter:latest` with your actual image references.

#### 2. Adjust Resource Limits

Modify the `resources` section in the deployment manifests:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

#### 3. Configure Redis Password

Update the Redis secret:

```bash
echo -n "your-password" | base64
```

Then update the `redis-secret` in `redis-deployment.yaml`.

#### 4. Modify Prometheus Configuration

Edit the `prometheus-config` ConfigMap in `prometheus-deployment.yaml` to customize scraping rules.

## Monitoring

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

# Request duration percentiles
histogram_quantile(0.95, rate(gunicorn_worker_request_duration_seconds_bucket[5m]))
histogram_quantile(0.50, rate(gunicorn_worker_request_duration_seconds_bucket[5m]))
```

### Grafana Dashboard

The included Grafana dashboard provides:

- Request rate over time
- Memory usage per worker
- CPU usage per worker
- Request duration percentiles

## Scaling

### Horizontal Pod Autoscaling

Create an HPA for the application:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gunicorn-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gunicorn-app-with-sidecar
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

### Vertical Pod Autoscaling

Create a VPA for the application:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: gunicorn-app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gunicorn-app-with-sidecar
  updatePolicy:
    updateMode: "Auto"
```

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check resource limits and node capacity
2. **Metrics not appearing**: Verify Redis connectivity and multiprocess directory sharing
3. **Prometheus not scraping**: Check service discovery and network policies
4. **Grafana not loading**: Verify persistent volume claims and storage class

### Debug Commands

```bash
# Check pod status
kubectl get pods -l app=gunicorn-app

# Check pod logs
kubectl logs -l app=gunicorn-app -c app
kubectl logs -l app=gunicorn-app -c prometheus-exporter

# Check services
kubectl get services

# Check persistent volumes
kubectl get pv,pvc

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp
```

### Logs

```bash
# Application logs
kubectl logs -f deployment/gunicorn-app-with-sidecar -c app

# Sidecar logs
kubectl logs -f deployment/gunicorn-app-with-sidecar -c prometheus-exporter

# Redis logs
kubectl logs -f deployment/redis

# Prometheus logs
kubectl logs -f deployment/prometheus

# Grafana logs
kubectl logs -f deployment/grafana
```

## Security

### Network Policies

Create network policies to restrict traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gunicorn-app-netpol
spec:
  podSelector:
    matchLabels:
      app: gunicorn-app
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: prometheus
      ports:
        - protocol: TCP
          port: 9091
    - from:
        - podSelector:
            matchLabels:
              app: grafana
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
```

### Pod Security Standards

Apply pod security standards:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: gunicorn-monitoring
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## Production Considerations

### 1. Resource Management

- Set appropriate CPU and memory limits
- Use resource quotas and limits
- Monitor resource usage with Prometheus

### 2. High Availability

- Deploy multiple replicas
- Use anti-affinity rules
- Configure proper health checks

### 3. Backup and Recovery

- Backup persistent volumes
- Export Grafana dashboards
- Document configuration changes

### 4. Monitoring and Alerting

- Set up Prometheus alerts
- Configure Grafana notifications
- Monitor cluster health

## Cleanup

Remove all resources:

```bash
kubectl delete -f .
```

Or remove specific components:

```bash
kubectl delete -f grafana-deployment.yaml
kubectl delete -f prometheus-deployment.yaml
kubectl delete -f sidecar-deployment.yaml
kubectl delete -f redis-deployment.yaml
```

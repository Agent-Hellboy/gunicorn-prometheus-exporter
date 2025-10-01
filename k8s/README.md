# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Gunicorn Prometheus Exporter as a sidecar container.

## Quick Start

### 1. Create Secrets (Required)

**Important**: Never commit secrets to version control. Create them from templates:

```bash
# Create Grafana admin password
kubectl create secret generic grafana-secret \
  --from-literal=admin-password="$(openssl rand -base64 32)"

# Optional: Create Redis password (if using Redis with authentication)
# kubectl create secret generic redis-secret \
#   --from-literal=password="$(openssl rand -base64 32)"
```

### 2. Deploy Redis (Required for shared metrics)

```bash
kubectl apply -f redis-pvc.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f redis-service.yaml
```

### 3. Deploy the Application with Sidecar

```bash
kubectl apply -f sidecar-deployment.yaml
kubectl apply -f gunicorn-app-service.yaml
kubectl apply -f gunicorn-metrics-service.yaml
```

### 4. Deploy Prometheus (Optional)

```bash
kubectl apply -f prometheus-config.yaml
kubectl apply -f prometheus-pvc.yaml
kubectl apply -f prometheus-deployment.yaml
kubectl apply -f prometheus-service.yaml
```

### 5. Deploy Grafana (Optional)

```bash
kubectl apply -f grafana-datasources.yaml
kubectl apply -f grafana-dashboards.yaml
kubectl apply -f grafana-pvc.yaml
kubectl apply -f grafana-deployment.yaml
kubectl apply -f grafana-service.yaml
```

## Complete Deployment

Deploy everything at once:

```bash
kubectl apply -f '*.yaml'
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
- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: Use the password from the `grafana-secret` you created

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

Replace the default registry `docker.io/princekrroshan01/...` only if you are publishing to a different registry.

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

#### 3. Modify Prometheus Configuration

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

### Secret Management

*Important*: All secrets are managed via templates and should be created at deployment time, never committed to version control.

**Available Secret Templates:**
- `grafana-secret.yaml.template` - Grafana admin password
- `redis-secret.yaml.template` - Redis authentication password (optional)

**Creating Secrets:**

```bash
# Required: Grafana admin password
kubectl create secret generic grafana-secret \
  --from-literal=admin-password="$(openssl rand -base64 32)"

# Optional: Redis password (for production with authentication enabled)
kubectl create secret generic redis-secret \
  --from-literal=password="$(openssl rand -base64 32)"
```

*Note*: Redis runs without password authentication by default for development/testing. For production, enable authentication by:
1. Creating the `redis-secret` as shown above
2. Uncommenting the password-related configuration in `redis-deployment.yaml`

**Protected Files:**
All `*-secret.yaml` files are blocked by `.gitignore` to prevent accidental commits.

### Security Contexts

All containers run with hardened security contexts following the principle of least privilege:

**Application Container:**
- Non-root user (UID 1000)
- No privilege escalation
- All capabilities dropped
- Writable `/tmp` for Prometheus multiprocess files

**Sidecar Container:**
- Non-root user (UID 1000)
- Read-only root filesystem
- No privilege escalation
- All capabilities dropped

**Redis Container:**
- Non-root user (UID 999, redis user)
- No privilege escalation
- All capabilities dropped

**Prometheus Container:**
- Non-root user (UID 65534, nobody)
- No privilege escalation
- All capabilities dropped

**Grafana Container:**
- Non-root user (UID 472, grafana user)
- No privilege escalation
- All capabilities dropped

### Image Versions

All container images use pinned versions for reproducible deployments:
- `redis:7-alpine`
- `prom/prometheus:v2.54.1`
- `grafana/grafana:11.2.0`

### Network Policies

Create network policies to restrict traffic between services:

**Application Network Policy:**

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

**Prometheus Network Policy:**

*Important*: Prometheus has `--web.enable-admin-api` enabled for operations like deleting time series. This should be restricted to authorized services only.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: prometheus-netpol
spec:
  podSelector:
    matchLabels:
      app: prometheus
  policyTypes:
    - Ingress
  ingress:
    # Allow Grafana to query metrics
    - from:
        - podSelector:
            matchLabels:
              app: grafana
      ports:
        - protocol: TCP
          port: 9090
    # Allow Prometheus to scrape gunicorn metrics
    - from:
        - podSelector:
            matchLabels:
              app: gunicorn-app
      ports:
        - protocol: TCP
          port: 9090
```

**Deploy Network Policies:**

```bash
# Save the policies to files
kubectl apply -f gunicorn-app-netpol.yaml
kubectl apply -f prometheus-netpol.yaml
```

*Note*: Network policies require a CNI plugin that supports them (Calico, Cilium, Weave Net, etc.). If using a managed Kubernetes service:
- GKE: Network policies are supported by default
- EKS: Requires Calico or AWS VPC CNI plugin
- AKS: Requires Azure Network Policy or Calico

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

### Additional Security Recommendations

1. *Secrets Management*:
   - Use external secrets operators (AWS Secrets Manager, HashiCorp Vault, etc.) for production
   - Rotate secrets regularly
   - Use RBAC to restrict secret access

2. *Network Security*:
   - Enable TLS/SSL for all external-facing services
   - Use service mesh for mTLS between services
   - Implement proper network policies

3. *Monitoring*:
   - Enable audit logging
   - Monitor for security events
   - Set up alerts for suspicious activities

4. *Access Control*:
   - Use RBAC for fine-grained permissions
   - Enable authentication for Prometheus and Grafana
   - Secure Redis with password authentication in production
   - Consider disabling `--web.enable-admin-api` in Prometheus if not needed
   - If admin API is required, use network policies to restrict access

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

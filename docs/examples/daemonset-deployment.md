# DaemonSet Deployment Guide

This guide covers deploying the Gunicorn Prometheus Exporter as a DaemonSet for cluster-wide infrastructure monitoring.

## Overview

DaemonSet deployment provides cluster-wide monitoring capabilities by ensuring one exporter pod runs on every node in the cluster. This pattern is ideal for infrastructure monitoring, development environments, and multi-application scenarios.

## When to Use DaemonSet

### Use DaemonSet When:
- **Infrastructure Monitoring**: Monitor all nodes in the cluster
- **Development Environments**: Multiple applications per node
- **Multi-Tenant Applications**: Monitor multiple applications across nodes
- **Cluster-Wide Observability**: Complete cluster coverage
- **Node-Level Insights**: Correlate application metrics with node performance

### Use Standard Deployment When:
- **Application-Specific Monitoring**: Focus on specific applications
- **Production Applications**: Dedicated application monitoring
- **Resource Optimization**: Shared resources across pods
- **Internal Networking**: ClusterIP services

## Deployment Comparison

| Feature | Standard Deployment | DaemonSet Deployment |
|---------|-------------------|---------------------|
| **Use Case** | Application-specific monitoring | Cluster-wide infrastructure monitoring |
| **Scaling** | Manual replica scaling | Automatic (one per node) |
| **Network** | ClusterIP services | Host network access |
| **Coverage** | Specific applications | All applications on all nodes |
| **Resource** | Shared across pods | Dedicated per node |
| **Best For** | Production applications | Infrastructure monitoring, development environments |
| **Manifest Location** | `k8s/sidecar-deployment.yaml` | `k8s/sidecar-daemonset.yaml` |

## Quick Start

### 1. Deploy Redis (Required)

```bash
kubectl apply -f k8s/redis-pvc.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml
```

### 2. Deploy DaemonSet

```bash
kubectl apply -f k8s/sidecar-daemonset.yaml
kubectl apply -f k8s/daemonset-service.yaml
kubectl apply -f k8s/daemonset-metrics-service.yaml
kubectl apply -f k8s/daemonset-netpol.yaml
```

### 3. Verify Deployment

```bash
# Check DaemonSet status
kubectl get daemonset gunicorn-prometheus-exporter-daemonset

# Check pods on all nodes
kubectl get pods -l app=gunicorn-prometheus-exporter,component=daemonset -o wide

# Check services
kubectl get services -l app=gunicorn-prometheus-exporter,component=daemonset
```

## Configuration

### Environment Variables

The DaemonSet supports the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_METRICS_PORT` | `9091` | Port for metrics endpoint |
| `PROMETHEUS_BIND_ADDRESS` | `0.0.0.0` | Bind address for metrics |
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus_multiproc` | Multiprocess directory |
| `REDIS_ENABLED` | `true` | Enable Redis storage |
| `REDIS_HOST` | `redis-service` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database |
| `REDIS_KEY_PREFIX` | `gunicorn-daemonset` | Redis key prefix |
| `SIDECAR_UPDATE_INTERVAL` | `30` | Update interval in seconds |
| `NODE_NAME` | *(auto)* | Node name from fieldRef |
| `POD_NAME` | *(auto)* | Pod name from fieldRef |
| `POD_NAMESPACE` | *(auto)* | Pod namespace from fieldRef |

### Redis Key Prefix

The DaemonSet uses `gunicorn-daemonset` as the Redis key prefix to isolate metrics from other deployments:

```yaml
env:
  - name: REDIS_KEY_PREFIX
    value: "gunicorn-daemonset"
```

This ensures DaemonSet metrics don't conflict with standard deployment metrics.

## Network Configuration

### Host Network

The DaemonSet uses host networking for node-level access:

```yaml
spec:
  hostNetwork: true
  dnsPolicy: ClusterFirstWithHostNet
```

**Benefits:**
- Direct access to node network interfaces
- Monitor node-level network traffic
- Access node-specific services and ports

### Network Policies

The included network policy (`daemonset-netpol.yaml`) provides:

- **Ingress**: Allow Prometheus and Grafana access
- **Egress**: Allow Redis and DNS access
- **Security**: Restrict unnecessary network access

## Resource Management

### Resource Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Volume Mounts

```yaml
volumeMounts:
  - name: prometheus-multiproc
    mountPath: /tmp/prometheus_multiproc
  - name: tmp
    mountPath: /tmp
```

## Monitoring

### Prometheus Configuration

Add the DaemonSet to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: "gunicorn-daemonset"
    kubernetes_sd_configs:
      - role: endpoints
    relabel_configs:
      - source_labels: [__meta_kubernetes_service_label_component]
        action: keep
        regex: daemonset
      - source_labels: [__meta_kubernetes_endpoint_port_name]
        action: keep
        regex: metrics
```

### Grafana Dashboard

The DaemonSet metrics can be visualized in Grafana using the same dashboard as the standard deployment, with additional node-level context.

## Troubleshooting

### Common Issues

1. **Pods not starting on all nodes**: Check node selectors and tolerations
2. **Metrics not appearing**: Verify Redis connectivity and network policies
3. **Host network issues**: Check for port conflicts on nodes

### Debug Commands

```bash
# Check DaemonSet status
kubectl get daemonset gunicorn-prometheus-exporter-daemonset

# Check pods on all nodes
kubectl get pods -l app=gunicorn-prometheus-exporter,component=daemonset -o wide

# Check pod logs
kubectl logs -l app=gunicorn-prometheus-exporter,component=daemonset -c app
kubectl logs -l app=gunicorn-prometheus-exporter,component=daemonset -c prometheus-exporter

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp

# Check node information
kubectl describe nodes
```

### Logs

```bash
# Application logs
kubectl logs -f daemonset/gunicorn-prometheus-exporter-daemonset -c app

# Sidecar logs
kubectl logs -f daemonset/gunicorn-prometheus-exporter-daemonset -c prometheus-exporter
```

## Security

### Security Contexts

All containers run with hardened security contexts:

```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 1000
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```

### Network Policies

The included network policy restricts traffic to necessary services only.

## Scaling

### Automatic Scaling

DaemonSet automatically scales with cluster size:
- New nodes automatically get a pod
- Removed nodes automatically clean up pods
- No manual scaling required

### Node Selection

Control which nodes run the DaemonSet:

```yaml
# Node selector (optional)
nodeSelector:
  kubernetes.io/os: linux

# Tolerations for master nodes (optional)
tolerations:
- key: node-role.kubernetes.io/master
  operator: Exists
  effect: NoSchedule
- key: node-role.kubernetes.io/control-plane
  operator: Exists
  effect: NoSchedule
```

## Use Cases

### 1. Development Environments

Monitor multiple development applications across all nodes:

```bash
# Deploy to development cluster
kubectl apply -f k8s/sidecar-daemonset.yaml
```

### 2. Infrastructure Monitoring

Monitor cluster-wide infrastructure health:

```bash
# Check cluster-wide metrics
kubectl port-forward service/gunicorn-daemonset-metrics-service 9091:9091
curl http://localhost:9091/metrics
```

### 3. Multi-Tenant Applications

Monitor multiple applications per node with isolated metrics:

```yaml
env:
  - name: REDIS_KEY_PREFIX
    value: "gunicorn-daemonset-tenant-1"
```

## Best Practices

1. **Resource Limits**: Set appropriate resource limits for node capacity
2. **Network Policies**: Use network policies for security
3. **Monitoring**: Monitor DaemonSet health and metrics
4. **Logging**: Centralize logs for troubleshooting
5. **Security**: Use security contexts and network policies

## Migration from Standard Deployment

To migrate from standard deployment to DaemonSet:

1. **Backup Metrics**: Export existing metrics from Redis
2. **Deploy DaemonSet**: Apply DaemonSet manifests
3. **Verify Coverage**: Check all nodes have pods
4. **Update Prometheus**: Update scrape configuration
5. **Cleanup**: Remove standard deployment after verification

## Support

For issues and questions:
- Check the [troubleshooting section](#troubleshooting)
- Review [Kubernetes documentation](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
- See [main project README](../../README.md) for general support

# Metrics Documentation

Complete reference for all metrics exposed by the Gunicorn Prometheus Exporter.

## Available Metrics

The exporter provides comprehensive metrics for monitoring Gunicorn workers, requests, and application performance.

### Worker Metrics

#### `gunicorn_worker_requests_total`
**Type**: Counter
**Description**: Total number of requests processed by each worker
**Labels**: `worker_id`

```
# HELP gunicorn_worker_requests_total Total number of requests processed by worker
# TYPE gunicorn_worker_requests_total counter
gunicorn_worker_requests_total{worker_id="worker_1_1234567890"} 42.0
```

#### `gunicorn_worker_request_duration_seconds`
**Type**: Histogram
**Description**: Request duration in seconds
**Labels**: `worker_id`
**Buckets**: `[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]`

```
# HELP gunicorn_worker_request_duration_seconds Request duration in seconds
# TYPE gunicorn_worker_request_duration_seconds histogram
gunicorn_worker_request_duration_seconds_bucket{worker_id="worker_1_1234567890",le="0.1"} 35.0
gunicorn_worker_request_duration_seconds_bucket{worker_id="worker_1_1234567890",le="0.5"} 40.0
gunicorn_worker_request_duration_seconds_bucket{worker_id="worker_1_1234567890",le="1.0"} 42.0
gunicorn_worker_request_duration_seconds_bucket{worker_id="worker_1_1234567890",le="+Inf"} 42.0
gunicorn_worker_request_duration_seconds_sum{worker_id="worker_1_1234567890"} 15.234
gunicorn_worker_request_duration_seconds_count{worker_id="worker_1_1234567890"} 42.0
```

#### `gunicorn_worker_memory_bytes`
**Type**: Gauge
**Description**: Memory usage of each worker in bytes
**Labels**: `worker_id`

```
# HELP gunicorn_worker_memory_bytes Memory usage of worker in bytes
# TYPE gunicorn_worker_memory_bytes gauge
gunicorn_worker_memory_bytes{worker_id="worker_1_1234567890"} 52428800.0
```

#### `gunicorn_worker_cpu_percent`
**Type**: Gauge
**Description**: CPU usage percentage of each worker
**Labels**: `worker_id`

```
# HELP gunicorn_worker_cpu_percent CPU usage percentage of worker
# TYPE gunicorn_worker_cpu_percent gauge
gunicorn_worker_cpu_percent{worker_id="worker_1_1234567890"} 2.5
```

#### `gunicorn_worker_uptime_seconds`
**Type**: Gauge
**Description**: Uptime of each worker in seconds
**Labels**: `worker_id`

```
# HELP gunicorn_worker_uptime_seconds Worker uptime in seconds
# TYPE gunicorn_worker_uptime_seconds gauge
gunicorn_worker_uptime_seconds{worker_id="worker_1_1234567890"} 3600.0
```

### Error Metrics

#### `gunicorn_worker_failed_requests_total`
**Type**: Counter
**Description**: Total number of failed requests (4xx, 5xx status codes)
**Labels**: `worker_id`, `method`, `endpoint`, `status_code`

```
# HELP gunicorn_worker_failed_requests_total Total number of failed requests
# TYPE gunicorn_worker_failed_requests_total counter
gunicorn_worker_failed_requests_total{worker_id="worker_1_1234567890",method="GET",endpoint="/api/users",status_code="404"} 5.0
```

#### `gunicorn_worker_error_handling_total`
**Type**: Counter
**Description**: Total number of errors handled by workers
**Labels**: `worker_id`, `method`, `endpoint`, `error_type`

```
# HELP gunicorn_worker_error_handling_total Total number of errors handled
# TYPE gunicorn_worker_error_handling_total counter
gunicorn_worker_error_handling_total{worker_id="worker_1_1234567890",method="POST",endpoint="/api/data",error_type="ValueError"} 2.0
```

### Worker State Metrics

#### `gunicorn_worker_state`
**Type**: Gauge
**Description**: Current state of each worker
**Labels**: `worker_id`, `state`, `timestamp`

```
# HELP gunicorn_worker_state Current state of worker
# TYPE gunicorn_worker_state gauge
gunicorn_worker_state{worker_id="worker_1_1234567890",state="running",timestamp="1640995200.123"} 1.0
```

### Master Metrics

#### `gunicorn_master_worker_restarts_total`
**Type**: Counter
**Description**: Total number of worker restarts initiated by the master
**Labels**: None

```
# HELP gunicorn_master_worker_restarts_total Total number of worker restarts
# TYPE gunicorn_master_worker_restarts_total counter
gunicorn_master_worker_restarts_total 3.0
```

## Metric Labels

### Worker ID Format
Worker IDs follow the pattern: `worker_{age}_{start_time}`

- `age`: Worker age (incremental number)
- `start_time`: Unix timestamp when worker started

Example: `worker_1_1234567890`

### State Values
- `running`: Worker is actively processing requests
- `quit`: Worker is shutting down gracefully
- `abort`: Worker is shutting down forcefully

### Error Types
Common error types include:

- `ValueError`: Invalid request data
- `TypeError`: Type mismatch errors
- `AttributeError`: Missing attribute errors
- `KeyError`: Missing key errors
- `ConnectionError`: Network connection issues
- `TimeoutError`: Request timeout errors

## Querying Metrics

### Prometheus Queries

#### Request Rate
```promql
# Requests per second per worker
rate(gunicorn_worker_requests_total[5m])

# Total requests across all workers
sum(rate(gunicorn_worker_requests_total[5m]))
```

#### Response Time
```promql
# 95th percentile response time
histogram_quantile(0.95, rate(gunicorn_worker_request_duration_seconds_bucket[5m]))

# Average response time
rate(gunicorn_worker_request_duration_seconds_sum[5m]) / rate(gunicorn_worker_request_duration_seconds_count[5m])
```

#### Error Rate
```promql
# Error rate per worker
rate(gunicorn_worker_failed_requests_total[5m])

# Overall error rate
sum(rate(gunicorn_worker_failed_requests_total[5m])) / sum(rate(gunicorn_worker_requests_total[5m]))
```

#### Memory Usage
```promql
# Memory usage per worker
gunicorn_worker_memory_bytes

# Average memory usage across workers
avg(gunicorn_worker_memory_bytes)
```

#### CPU Usage
```promql
# CPU usage per worker
gunicorn_worker_cpu_percent

# Average CPU usage across workers
avg(gunicorn_worker_cpu_percent)
```

#### Worker Health
```promql
# Number of running workers
sum(gunicorn_worker_state{state="running"})

# Worker uptime
gunicorn_worker_uptime_seconds
```

### Grafana Dashboards

#### Key Panels to Include

1. **Request Rate Panel**
   ```promql
   sum(rate(gunicorn_worker_requests_total[5m]))
   ```

2. **Response Time Panel**
   ```promql
   histogram_quantile(0.95, rate(gunicorn_worker_request_duration_seconds_bucket[5m]))
   ```

3. **Error Rate Panel**
   ```promql
   sum(rate(gunicorn_worker_failed_requests_total[5m])) / sum(rate(gunicorn_worker_requests_total[5m])) * 100
   ```

4. **Memory Usage Panel**
   ```promql
   avg(gunicorn_worker_memory_bytes) / 1024 / 1024
   ```

5. **CPU Usage Panel**
   ```promql
   avg(gunicorn_worker_cpu_percent)
   ```

6. **Active Workers Panel**
   ```promql
   sum(gunicorn_worker_state{state="running"})
   ```

## Alerting Rules

### High Error Rate
```yaml
groups:
  - name: gunicorn_alerts
    rules:
      - alert: HighErrorRate
        expr: sum(rate(gunicorn_worker_failed_requests_total[5m])) / sum(rate(gunicorn_worker_requests_total[5m])) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"
```

### High Response Time
```yaml
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(gunicorn_worker_request_duration_seconds_bucket[5m])) > 1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"
```

### Worker Restarts
```yaml
      - alert: WorkerRestarts
        expr: increase(gunicorn_master_worker_restarts_total[5m]) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Worker restarts detected"
          description: "{{ $value }} worker restarts in the last 5 minutes"
```

### High Memory Usage
```yaml
      - alert: HighMemoryUsage
        expr: avg(gunicorn_worker_memory_bytes) / 1024 / 1024 > 512
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Average memory usage is {{ $value }}MB"
```

## Custom Metrics

### Adding Custom Metrics

You can extend the monitoring with custom application metrics:

```python
# custom_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Custom business metrics
orders_total = Counter(
    'app_orders_total',
    'Total number of orders',
    ['status', 'payment_method']
)

order_value = Histogram(
    'app_order_value_dollars',
    'Order value in dollars',
    ['status']
)

active_users = Gauge(
    'app_active_users',
    'Number of active users'
)

# Update metrics in your application
def process_order(order):
    orders_total.labels(
        status=order.status,
        payment_method=order.payment_method
    ).inc()

    order_value.labels(status=order.status).observe(order.value)
```

### Integration with Gunicorn

The custom metrics will automatically be available at the `/metrics` endpoint alongside the built-in Gunicorn metrics.

## Metric Cardinality

### Label Cardinality Considerations

- **Worker IDs**: Limited by number of workers (typically 1-32)
- **Endpoints**: Limited by your application's routes
- **Error Types**: Limited by exception types in your application
- **Status Codes**: Limited to HTTP status codes (100-599)

### Best Practices

1. **Limit Label Values**: Avoid high-cardinality labels like user IDs or session IDs
2. **Use Aggregation**: Prefer aggregated metrics over per-request metrics
3. **Monitor Cardinality**: Watch for metrics with too many unique label combinations
4. **Clean Up Old Metrics**: Use the cleanup functionality to remove old worker metrics

## Related Documentation

- [Installation Guide](installation.md)
- [Configuration Reference](configuration.md)
- [API Reference](api-reference.md)
- [Troubleshooting](troubleshooting.md)

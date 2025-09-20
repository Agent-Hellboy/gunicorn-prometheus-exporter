# Metrics Documentation

Complete reference for all metrics exposed by the Gunicorn Prometheus Exporter.

## Compatibility Issues

### TornadoWorker Compatibility Issues

**Important**: The `PrometheusTornadoWorker` has known compatibility issues and is **not recommended for production use**.

#### Known Issues

1. **Metrics Endpoint Hanging**: The Prometheus metrics endpoint (`/metrics`) may hang or become unresponsive when using TornadoWorker
2. **IOLoop Conflicts**: Tornado's event loop architecture conflicts with the metrics collection mechanism
3. **Thread Safety Problems**: Metrics collection from TornadoWorker processes can cause deadlocks
4. **Request Object Access**: TornadoWorker doesn't expose request objects in the same way as other workers, limiting method and endpoint tracking

#### Recommended Alternatives

- Use `PrometheusWorker` (sync worker) for most applications
- Use `PrometheusEventletWorker` for async applications requiring eventlet
- Use `PrometheusGeventWorker` for async applications requiring gevent
- Use `PrometheusThreadWorker` for threaded applications

#### Technical Details

The TornadoWorker uses Tornado's single-threaded IOLoop which can block the main thread when the metrics endpoint is accessed. This creates a fundamental incompatibility with the current metrics collection approach.

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
**Multiprocess Mode**: `all` (preserves individual worker instances)

```
# HELP gunicorn_worker_memory_bytes Memory usage of worker in bytes
# TYPE gunicorn_worker_memory_bytes gauge
gunicorn_worker_memory_bytes{worker_id="worker_1_1234567890"} 52428800.0
gunicorn_worker_memory_bytes{worker_id="worker_2_1234567891"} 61234560.0
```

#### `gunicorn_worker_cpu_percent`

**Type**: Gauge
**Description**: CPU usage percentage of each worker
**Labels**: `worker_id`
**Multiprocess Mode**: `all` (preserves individual worker instances)

```
# HELP gunicorn_worker_cpu_percent CPU usage percentage of worker
# TYPE gunicorn_worker_cpu_percent gauge
gunicorn_worker_cpu_percent{worker_id="worker_1_1234567890"} 2.5
gunicorn_worker_cpu_percent{worker_id="worker_2_1234567891"} 3.2
```

#### `gunicorn_worker_uptime_seconds`

**Type**: Gauge
**Description**: Uptime of each worker in seconds
**Labels**: `worker_id`
**Multiprocess Mode**: `all` (preserves individual worker instances)

```
# HELP gunicorn_worker_uptime_seconds Worker uptime in seconds
# TYPE gunicorn_worker_uptime_seconds gauge
gunicorn_worker_uptime_seconds{worker_id="worker_1_1234567890"} 3600.0
gunicorn_worker_uptime_seconds{worker_id="worker_2_1234567891"} 3580.5
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
**Multiprocess Mode**: `all` (preserves individual worker instances)

```
# HELP gunicorn_worker_state Current state of worker
# TYPE gunicorn_worker_state gauge
gunicorn_worker_state{worker_id="worker_1_1234567890",state="running",timestamp="1640995200.123"} 1.0
gunicorn_worker_state{worker_id="worker_2_1234567891",state="running",timestamp="1640995200.124"} 1.0
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

## Multiprocess Mode Behavior

### Gauge Metrics Multiprocess Modes

All gauge metrics in this exporter use `multiprocess_mode="all"` to preserve individual worker instances with their `worker_id` labels. This ensures you can monitor each worker separately rather than getting aggregated values.

#### Available Multiprocess Modes

The Prometheus Python client supports several multiprocess modes for gauge metrics:

- **`all`**: Sum all values across processes (used by this exporter)
- **`liveall`**: Sum values from live processes only
- **`max`**: Use maximum value across processes
- **`min`**: Use minimum value across processes
- **`sum`**: Sum all values (same as `all`)
- **`mostrecent`**: Use most recent value

#### Why `all` Mode for Worker Metrics

Worker metrics use `multiprocess_mode="all"` because:

1. **Per-Worker Visibility**: You want to see individual worker performance, not aggregated values
2. **Worker ID Labels**: Each metric has a `worker_id` label to distinguish between workers
3. **Monitoring Individual Workers**: Allows you to identify problematic workers or performance patterns
4. **Debugging**: Easier to debug issues when you can see per-worker metrics

#### Example Output

With `multiprocess_mode="all"`, you get separate metrics for each worker:

```
gunicorn_worker_memory_bytes{worker_id="worker_1_1234567890"} 52428800.0
gunicorn_worker_memory_bytes{worker_id="worker_2_1234567891"} 61234560.0
gunicorn_worker_memory_bytes{worker_id="worker_3_1234567892"} 48912345.0
```

Instead of a single aggregated value:

```
gunicorn_worker_memory_bytes 162575705.0  # This would be the sum
```

#### Redis Storage Integration

When using Redis storage, the multiprocess mode is stored in Redis metadata and correctly applied during metric collection, ensuring consistent behavior across different storage backends.

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

# Maximum memory usage across workers
max(gunicorn_worker_memory_bytes)

# Memory usage for a specific worker
gunicorn_worker_memory_bytes{worker_id="worker_1_1234567890"}
```

#### CPU Usage

```promql
# CPU usage per worker
gunicorn_worker_cpu_percent

# Average CPU usage across workers
avg(gunicorn_worker_cpu_percent)

# Maximum CPU usage across workers
max(gunicorn_worker_cpu_percent)

# CPU usage for a specific worker
gunicorn_worker_cpu_percent{worker_id="worker_1_1234567890"}
```

#### Worker Health

```promql
# Number of running workers
sum(gunicorn_worker_state{state="running"})

# Worker uptime per worker
gunicorn_worker_uptime_seconds

# Average uptime across workers
avg(gunicorn_worker_uptime_seconds)

# Uptime for a specific worker
gunicorn_worker_uptime_seconds{worker_id="worker_1_1234567890"}

# Workers that have been running for more than 1 hour
gunicorn_worker_uptime_seconds > 3600
```

### Gauge Aggregation Queries

Since gauge metrics use `multiprocess_mode="all"`, you can apply various aggregation functions to get different views of your worker metrics:

#### Memory Usage Aggregations

```promql
# Individual worker memory usage
gunicorn_worker_memory_bytes

# Maximum memory usage across all workers
max(gunicorn_worker_memory_bytes)

# Minimum memory usage across all workers
min(gunicorn_worker_memory_bytes)

# Average memory usage across all workers
avg(gunicorn_worker_memory_bytes)

# Sum of memory usage across all workers
sum(gunicorn_worker_memory_bytes)

# Standard deviation of memory usage
stddev(gunicorn_worker_memory_bytes)

# Memory usage in MB
gunicorn_worker_memory_bytes / 1024 / 1024

# Maximum memory usage in MB
max(gunicorn_worker_memory_bytes) / 1024 / 1024

# Average memory usage in MB
avg(gunicorn_worker_memory_bytes) / 1024 / 1024
```

#### CPU Usage Aggregations

```promql
# Individual worker CPU usage
gunicorn_worker_cpu_percent

# Maximum CPU usage across all workers
max(gunicorn_worker_cpu_percent)

# Minimum CPU usage across all workers
min(gunicorn_worker_cpu_percent)

# Average CPU usage across all workers
avg(gunicorn_worker_cpu_percent)

# Sum of CPU usage across all workers
sum(gunicorn_worker_cpu_percent)

# Standard deviation of CPU usage
stddev(gunicorn_worker_cpu_percent)

# Workers with CPU usage above 50%
gunicorn_worker_cpu_percent > 50

# Workers with CPU usage below 10%
gunicorn_worker_cpu_percent < 10
```

#### Uptime Aggregations

```promql
# Individual worker uptime
gunicorn_worker_uptime_seconds

# Maximum uptime across all workers
max(gunicorn_worker_uptime_seconds)

# Minimum uptime across all workers
min(gunicorn_worker_uptime_seconds)

# Average uptime across all workers
avg(gunicorn_worker_uptime_seconds)

# Sum of uptime across all workers
sum(gunicorn_worker_uptime_seconds)

# Uptime in hours
gunicorn_worker_uptime_seconds / 3600

# Maximum uptime in hours
max(gunicorn_worker_uptime_seconds) / 3600

# Workers running for more than 1 hour
gunicorn_worker_uptime_seconds > 3600

# Workers running for less than 30 minutes
gunicorn_worker_uptime_seconds < 1800
```

#### Worker State Aggregations

```promql
# Individual worker states
gunicorn_worker_state

# Number of running workers
sum(gunicorn_worker_state{state="running"})

# Number of workers in any state
sum(gunicorn_worker_state)

# Workers by state
sum by (state) (gunicorn_worker_state)

# Percentage of workers running
sum(gunicorn_worker_state{state="running"}) / sum(gunicorn_worker_state) * 100
```

#### Advanced Gauge Queries

```promql
# Top 3 workers by memory usage
topk(3, gunicorn_worker_memory_bytes)

# Bottom 3 workers by memory usage
bottomk(3, gunicorn_worker_memory_bytes)

# Top 3 workers by CPU usage
topk(3, gunicorn_worker_cpu_percent)

# Workers with highest uptime
topk(5, gunicorn_worker_uptime_seconds)

# Memory usage percentiles
quantile(0.5, gunicorn_worker_memory_bytes)  # 50th percentile (median)
quantile(0.95, gunicorn_worker_memory_bytes) # 95th percentile
quantile(0.99, gunicorn_worker_memory_bytes) # 99th percentile

# CPU usage percentiles
quantile(0.5, gunicorn_worker_cpu_percent)  # 50th percentile (median)
quantile(0.95, gunicorn_worker_cpu_percent) # 95th percentile
quantile(0.99, gunicorn_worker_cpu_percent) # 99th percentile

# Count of workers above certain thresholds
count(gunicorn_worker_memory_bytes > 100*1024*1024)  # Workers using >100MB
count(gunicorn_worker_cpu_percent > 50)             # Workers using >50% CPU
count(gunicorn_worker_uptime_seconds > 3600)       # Workers running >1 hour
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
   # Average memory usage
   avg(gunicorn_worker_memory_bytes) / 1024 / 1024

   # Per-worker memory usage
   gunicorn_worker_memory_bytes / 1024 / 1024
   ```

5. **CPU Usage Panel**

   ```promql
   # Average CPU usage
   avg(gunicorn_worker_cpu_percent)

   # Per-worker CPU usage
   gunicorn_worker_cpu_percent
   ```

6. **Active Workers Panel**
   ```promql
   sum(gunicorn_worker_state{state="running"})
   ```

7. **Per-Worker Monitoring Panel**
   ```promql
   # Memory usage by worker
   gunicorn_worker_memory_bytes / 1024 / 1024

   # CPU usage by worker
   gunicorn_worker_cpu_percent

   # Uptime by worker
   gunicorn_worker_uptime_seconds
   ```

8. **Gauge Aggregation Panel**
   ```promql
   # Memory aggregations
   max(gunicorn_worker_memory_bytes) / 1024 / 1024
   avg(gunicorn_worker_memory_bytes) / 1024 / 1024
   min(gunicorn_worker_memory_bytes) / 1024 / 1024

   # CPU aggregations
   max(gunicorn_worker_cpu_percent)
   avg(gunicorn_worker_cpu_percent)
   min(gunicorn_worker_cpu_percent)

   # Top workers by memory
   topk(3, gunicorn_worker_memory_bytes) / 1024 / 1024
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

- alert: HighMemoryUsagePerWorker
  expr: gunicorn_worker_memory_bytes / 1024 / 1024 > 1024
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High memory usage detected on worker {{ $labels.worker_id }}"
    description: "Worker {{ $labels.worker_id }} memory usage is {{ $value }}MB"
```

### High CPU Usage

```yaml
- alert: HighCPUUsagePerWorker
  expr: gunicorn_worker_cpu_percent > 80
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High CPU usage detected on worker {{ $labels.worker_id }}"
    description: "Worker {{ $labels.worker_id }} CPU usage is {{ $value }}%"

- alert: HighAverageCPUUsage
  expr: avg(gunicorn_worker_cpu_percent) > 70
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High average CPU usage across all workers"
    description: "Average CPU usage is {{ $value }}%"

- alert: HighMaxCPUUsage
  expr: max(gunicorn_worker_cpu_percent) > 90
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Critical CPU usage detected"
    description: "Maximum CPU usage is {{ $value }}%"
```

### Memory Usage Alerts

```yaml
- alert: HighMemoryUsagePerWorker
  expr: gunicorn_worker_memory_bytes / 1024 / 1024 > 1024
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High memory usage detected on worker {{ $labels.worker_id }}"
    description: "Worker {{ $labels.worker_id }} memory usage is {{ $value }}MB"

- alert: HighAverageMemoryUsage
  expr: avg(gunicorn_worker_memory_bytes) / 1024 / 1024 > 512
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High average memory usage across all workers"
    description: "Average memory usage is {{ $value }}MB"

- alert: HighMaxMemoryUsage
  expr: max(gunicorn_worker_memory_bytes) / 1024 / 1024 > 2048
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Critical memory usage detected"
    description: "Maximum memory usage is {{ $value }}MB"
```

### Worker Distribution Alerts

```yaml
- alert: UnevenWorkerLoad
  expr: (max(gunicorn_worker_cpu_percent) - min(gunicorn_worker_cpu_percent)) > 50
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Uneven CPU load distribution across workers"
    description: "CPU usage difference between max and min workers is {{ $value }}%"

- alert: TooManyHighMemoryWorkers
  expr: count(gunicorn_worker_memory_bytes / 1024 / 1024 > 1024) > 2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Multiple workers using high memory"
    description: "{{ $value }} workers are using more than 1GB of memory"
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

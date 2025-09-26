# Metrics API Reference

This document provides detailed API reference for the metrics component.

## Core Classes

### PrometheusWorker

Base worker class that provides metrics collection for sync workers.

```python
class PrometheusWorker(gunicorn.workers.sync.SyncWorker):
    """Prometheus-enabled sync worker."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = Metrics()
```

**Methods:**

- `__init__(*args, **kwargs)` - Initialize worker with metrics collection
- `run()` - Run the worker with metrics tracking
- `handle_request(*args, **kwargs)` - Handle individual requests with metrics

### PrometheusThreadWorker

Thread-based worker with metrics collection.

```python
class PrometheusThreadWorker(gunicorn.workers.gthread.ThreadWorker):
    """Prometheus-enabled thread worker."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = Metrics()
```

### PrometheusEventletWorker

Eventlet-based async worker with metrics collection.

```python
class PrometheusEventletWorker(gunicorn.workers.geventlet.EventletWorker):
    """Prometheus-enabled eventlet worker."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = Metrics()
```

### PrometheusGeventWorker

Gevent-based async worker with metrics collection.

```python
class PrometheusGeventWorker(gunicorn.workers.ggevent.GeventWorker):
    """Prometheus-enabled gevent worker."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = Metrics()
```

## Metrics Collection

### Metrics Class

Main metrics collection class.

```python
class Metrics:
    """Metrics collection and management."""

    def __init__(self):
        self.requests_total = Counter(
            'gunicorn_worker_requests_total',
            'Total requests handled by worker',
            ['worker_id', 'method', 'endpoint']
        )
        self.request_duration = Histogram(
            'gunicorn_worker_request_duration_seconds',
            'Request duration in seconds',
            ['worker_id', 'method', 'endpoint']
        )
        self.memory_usage = Gauge(
            'gunicorn_worker_memory_bytes',
            'Memory usage in bytes',
            ['worker_id']
        )
        self.cpu_usage = Gauge(
            'gunicorn_worker_cpu_percent',
            'CPU usage percentage',
            ['worker_id']
        )
        self.uptime = Gauge(
            'gunicorn_worker_uptime_seconds',
            'Worker uptime in seconds',
            ['worker_id']
        )
        self.worker_state = Gauge(
            'gunicorn_worker_state',
            'Worker state with timestamp',
            ['worker_id', 'state']
        )
        self.failed_requests = Counter(
            'gunicorn_worker_failed_requests_total',
            'Failed requests with method/endpoint labels',
            ['worker_id', 'method', 'endpoint', 'error_type']
        )
        self.error_handling = Counter(
            'gunicorn_worker_error_handling_total',
            'Error tracking with method and endpoint labels',
            ['worker_id', 'method', 'endpoint', 'error_type']
        )
```

**Methods:**

- `record_request(method, endpoint, duration, success=True)` - Record request metrics
- `record_error(method, endpoint, error_type)` - Record error metrics
- `update_resource_usage()` - Update memory and CPU usage metrics
- `update_uptime()` - Update worker uptime metric
- `update_worker_state(state)` - Update worker state metric

## Master Process Metrics

### MasterMetrics Class

Metrics collection for the master process.

```python
class MasterMetrics:
    """Master process metrics collection."""

    def __init__(self):
        self.worker_restarts = Counter(
            'gunicorn_master_worker_restarts_total',
            'Total worker restarts',
            ['worker_id', 'reason']
        )
        self.signals = Counter(
            'gunicorn_master_signals_total',
            'Signal handling metrics',
            ['signal', 'action']
        )
```

**Methods:**

- `record_worker_restart(worker_id, reason)` - Record worker restart
- `record_signal(signal, action)` - Record signal handling

## Hooks

### on_starting

Called when the master process starts.

```python
def on_starting(server):
    """Initialize metrics collection on master start."""
    server.master_metrics = MasterMetrics()
```

### on_reload

Called when the master process reloads.

```python
def on_reload(server):
    """Handle metrics collection on reload."""
    # Cleanup old metrics
    # Initialize new metrics
```

### worker_int

Called when a worker is initialized.

```python
def worker_int(worker):
    """Initialize worker metrics."""
    worker.metrics = Metrics()
    worker.start_time = time.time()
```

### pre_request

Called before processing a request.

```python
def pre_request(worker, req):
    """Record request start time."""
    req.start_time = time.time()
```

### post_request

Called after processing a request.

```python
def post_request(worker, req, environ, resp):
    """Record request metrics."""
    duration = time.time() - req.start_time
    method = environ.get('REQUEST_METHOD', 'UNKNOWN')
    endpoint = environ.get('PATH_INFO', '/')

    worker.metrics.record_request(method, endpoint, duration)
```

## Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PROMETHEUS_MULTIPROC_DIR` | str | `/tmp/prometheus_multiproc` | Directory for multiprocess metrics |
| `PROMETHEUS_METRICS_PORT` | int | `9091` | Port for metrics endpoint |
| `PROMETHEUS_BIND_ADDRESS` | str | `0.0.0.0` | Bind address for metrics server |
| `GUNICORN_WORKERS` | int | `1` | Number of workers for metrics calculation |

## Error Handling

### Error Types

- `RequestError` - General request processing errors
- `TimeoutError` - Request timeout errors
- `MemoryError` - Memory-related errors
- `CPUError` - CPU-related errors

### Error Recording

```python
def record_error(worker, method, endpoint, error_type, error_message):
    """Record error metrics."""
    worker.metrics.error_handling.labels(
        worker_id=worker.pid,
        method=method,
        endpoint=endpoint,
        error_type=error_type
    ).inc()
```

## Performance Considerations

### Metrics Collection Overhead

- Request timing adds minimal overhead (~0.1ms per request)
- Memory usage tracking runs every 30 seconds
- CPU usage tracking runs every 10 seconds

### Optimization Tips

- Use appropriate worker types for your workload
- Monitor metrics endpoint performance
- Consider Redis backend for high-traffic applications
- Implement proper error handling to avoid metric bloat

## Related Documentation

- [Metrics Guide](../metrics.md) - Detailed metrics documentation
- [Worker Types](worker-types.md) - Supported worker types
- [Configuration Guide](../configuration.md) - Configuration options

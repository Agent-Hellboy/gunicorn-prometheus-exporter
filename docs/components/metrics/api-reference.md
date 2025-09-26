# Metrics API Reference

This document provides detailed API reference for the metrics component.

## Core Classes

### BaseMetric

Base class for all metrics using metaclass for automatic registry registration.

```python
class BaseMetric(metaclass=MetricMeta):
    """Base class for all metrics."""

    name: str
    documentation: str
    labelnames: List[str]

    @classmethod
    def labels(cls, **kwargs):
        """Get a labeled instance of the metric."""
        return cls._metric.labels(**kwargs)

    @classmethod
    def inc(cls, **labels):
        return cls._metric.labels(**labels).inc()

    @classmethod
    def set(cls, value, **labels):
        return cls._metric.labels(**labels).set(value)

    @classmethod
    def observe(cls, value, **labels):
        return cls._metric.labels(**labels).observe(value)
```

**Methods:**

- `labels(**kwargs)` - Get a labeled instance of the metric
- `inc(**labels)` - Increment the metric
- `set(value, **labels)` - Set the metric value
- `observe(value, **labels)` - Observe a value (for histograms)

### WorkerRequests

Counter metric for total requests handled by workers.

```python
class WorkerRequests(BaseMetric, metric_type=Counter):
    """Total number of requests handled by this worker."""

    name = "gunicorn_worker_requests_total"
    documentation = "Total number of requests handled by this worker"
    labelnames = ["worker_id"]
```

### WorkerRequestDuration

Histogram metric for request duration.

```python
class WorkerRequestDuration(BaseMetric, metric_type=Histogram):
    """Request duration in seconds."""

    name = "gunicorn_worker_request_duration_seconds"
    documentation = "Request duration in seconds"
    labelnames = ["worker_id"]
    buckets = (0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf"))
```

### WorkerMemory

Gauge metric for worker memory usage.

```python
class WorkerMemory(BaseMetric, metric_type=Gauge):
    """Memory usage of the worker process."""

    name = "gunicorn_worker_memory_bytes"
    documentation = "Memory usage of the worker process"
    labelnames = ["worker_id"]
    multiprocess_mode = "all"  # Keep all worker instances with worker_id labels
```

## Available Metrics

### Worker Metrics

All worker metrics are available as class constants:

```python
from gunicorn_prometheus_exporter.metrics import (
    WORKER_REQUESTS,
    WORKER_REQUEST_DURATION,
    WORKER_MEMORY,
    WORKER_CPU,
    WORKER_UPTIME,
    WORKER_FAILED_REQUESTS,
    WORKER_ERROR_HANDLING,
    WORKER_STATE,
    WORKER_REQUEST_SIZE,
    WORKER_RESPONSE_SIZE,
    WORKER_RESTART_REASON,
    WORKER_RESTART_COUNT,
)
```

### Master Metrics

Master process metrics:

```python
from gunicorn_prometheus_exporter.metrics import (
    MASTER_WORKER_RESTARTS,
    MASTER_WORKER_RESTART_COUNT,
)
```

### Registry Access

```python
from gunicorn_prometheus_exporter.metrics import get_shared_registry

# Get the shared Prometheus registry
registry = get_shared_registry()
```

## Metric Usage Examples

### Using Worker Metrics

```python
from gunicorn_prometheus_exporter.metrics import WORKER_REQUESTS, WORKER_MEMORY

# Increment request counter
WORKER_REQUESTS.labels(worker_id="worker_1_1234567890").inc()

# Set memory usage
WORKER_MEMORY.labels(worker_id="worker_1_1234567890").set(1024 * 1024 * 100)  # 100MB
```

### Using Master Metrics

```python
from gunicorn_prometheus_exporter.metrics import MASTER_WORKER_RESTARTS

# Record worker restart
MASTER_WORKER_RESTARTS.labels(reason="timeout").inc()
```

## Configuration

### Environment Variables

The metrics component uses the following environment variables:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PROMETHEUS_MULTIPROC_DIR` | str | `~/.gunicorn_prometheus` | Directory for multiprocess metrics |
| `PROMETHEUS_METRICS_PORT` | int | `None` | Port for metrics endpoint (required in production) |
| `PROMETHEUS_BIND_ADDRESS` | str | `None` | Bind address for metrics server (required in production) |

### Multiprocess Mode

The metrics component automatically sets up multiprocess mode:

```python
def _ensure_multiproc_dir():
    """Ensure the multiprocess directory exists.

    This function is called lazily when the registry is actually used,
    avoiding import-time side effects.
    """
    try:
        os.makedirs(config.prometheus_multiproc_dir, exist_ok=True)
    except Exception as e:
        logger.warning("Failed to prepare PROMETHEUS_MULTIPROC_DIR: %s", e)
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
    WorkerErrorHandling.inc(
        worker_id=worker.pid,
        method=method,
        endpoint=endpoint,
        error_type=error_type
    )
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

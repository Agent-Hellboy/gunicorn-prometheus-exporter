# Metrics Component

The metrics component provides comprehensive monitoring capabilities for Gunicorn applications.

## Overview

The metrics component collects and exposes various metrics about your Gunicorn application, including:

- Worker performance metrics
- Request handling statistics
- Resource usage monitoring
- Error tracking
- Master process monitoring

## Design Pattern Choice: Metaclass + Base Class

### Why Metaclass + Base Class for Metrics?

We chose the **Metaclass + Base Class pattern** for the metrics component because:

1. **Automatic Registration**: Metaclass automatically registers metrics with the Prometheus registry
2. **Consistent Interface**: Base class provides uniform interface for all metric types
3. **Type Safety**: Metaclass ensures proper metric type (Counter, Gauge, Histogram)
4. **Reduced Boilerplate**: No need to manually create and register each metric
5. **Prometheus Integration**: Seamless integration with Prometheus client library

### Alternative Patterns Considered

- **Factory Pattern**: Would require manual registration and more boilerplate
- **Builder Pattern**: Overkill for simple metric creation
- **Singleton Pattern**: Not suitable since we need multiple metric instances

### Implementation Benefits

```python
class MetricMeta(ABCMeta):
    """Metaclass for automatically registering metrics with the registry."""

    def __new__(mcs, name: str, bases: tuple, namespace: Dict, metric_type: Optional[Type[Union[Counter, Gauge, Histogram]]] = None, **kwargs) -> Type:
        cls = super().__new__(mcs, name, bases, namespace)

        if metric_type is not None:
            metric = metric_type(
                name=namespace.get("name", name.lower()),
                documentation=namespace.get("documentation", ""),
                labelnames=namespace.get("labelnames", []),
                registry=registry,
            )
            cls._metric = metric
        return cls

class BaseMetric(metaclass=MetricMeta):
    """Base class for all metrics."""

    @classmethod
    def inc(cls, **labels):
        return cls._metric.labels(**labels).inc()

    @classmethod
    def set(cls, value, **labels):
        return cls._metric.labels(**labels).set(value)

# Usage - automatic registration
class WorkerRequests(BaseMetric, metric_type=Counter):
    name = "gunicorn_worker_requests_total"
    documentation = "Total number of requests handled by this worker"
    labelnames = ["worker_id"]
```

## Available Metrics

### Worker Metrics

- `gunicorn_worker_requests_total` - Total requests handled by each worker
- `gunicorn_worker_request_duration_seconds` - Request duration histogram
- `gunicorn_worker_memory_bytes` - Memory usage per worker
- `gunicorn_worker_cpu_percent` - CPU usage per worker
- `gunicorn_worker_uptime_seconds` - Worker uptime
- `gunicorn_worker_state` - Worker state with timestamp
- `gunicorn_worker_failed_requests_total` - Failed requests with method/endpoint labels

### Master Metrics

- `gunicorn_master_worker_restarts_total` - Total worker restarts
- `gunicorn_master_signals_total` - Signal handling metrics

### Error Metrics

- `gunicorn_worker_error_handling_total` - Error tracking with method and endpoint labels

## Documentation

- [Worker Types](worker-types.md) - Supported worker types and their metrics
- [API Reference](api-reference.md) - Metrics API documentation

## Configuration

Metrics collection is automatically enabled when using the Prometheus worker classes. No additional configuration is required for basic metrics.

For advanced configuration, see the [Configuration Guide](../config/configuration.md).

## Examples

See the [Examples](../examples/) for configuration examples and usage patterns.

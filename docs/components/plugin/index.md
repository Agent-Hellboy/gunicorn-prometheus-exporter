# Plugin Component

The plugin component provides Prometheus-enabled worker classes that extend Gunicorn's built-in workers with comprehensive metrics collection.

## Overview

The plugin component provides:

- Prometheus-enabled worker classes
- Metrics collection for all worker types
- Request tracking and error handling
- Worker state management
- Resource usage monitoring

## Available Worker Classes

### Sync Workers

- **`PrometheusWorker`** - Sync worker with Prometheus metrics
- **`PrometheusThreadWorker`** - Thread worker with Prometheus metrics

### Async Workers

- **`PrometheusEventletWorker`** - Eventlet worker with Prometheus metrics
- **`PrometheusGeventWorker`** - Gevent worker with Prometheus metrics

## Core Architecture

### PrometheusMixin

The core mixin class that provides Prometheus functionality to all worker types:

```python
class PrometheusMixin:
    """Mixin class that adds Prometheus metrics functionality to any worker type."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.worker_id = f"worker_{self.age}_{int(self.start_time)}"
        self.start_time = time.time()
```

### Key Methods

- `update_worker_metrics()` - Update worker-specific metrics
- `_handle_request_metrics()` - Track request metrics
- `_handle_request_error_metrics()` - Track error metrics
- `_generic_handle_request()` - Generic request handler wrapper
- `_generic_handle_error()` - Generic error handler wrapper

## Metrics Collection

### Worker Metrics

- Memory usage tracking
- CPU usage monitoring
- Uptime measurement
- Worker state management
- Request counting and timing
- Error tracking with labels

### Request Metrics

- Request duration histograms
- Request count per worker
- Failed request tracking
- Error type classification

## Usage

### Basic Configuration

```python
# gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
```

### Thread Worker

```python
# gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
threads = 4
```

### Eventlet Worker

```python
# gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
worker_connections = 1000
```

### Gevent Worker

```python
# gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"
worker_connections = 1000
```

## Installation Requirements

### Sync and Thread Workers

```bash
pip install gunicorn-prometheus-exporter
```

### Eventlet Worker

```bash
pip install gunicorn-prometheus-exporter[eventlet]
```

### Gevent Worker

```bash
pip install gunicorn-prometheus-exporter[gevent]
```

## Documentation

- [API Reference](api-reference.md) - Complete plugin API documentation

## Configuration

Worker classes automatically collect metrics when used. No additional configuration is required for basic metrics collection.

For advanced configuration, see the [Configuration Guide](../config/configuration.md).

## Examples

See the [Examples](../examples/) for configuration examples and usage patterns.

# API Reference

Complete reference for the Gunicorn Prometheus Exporter API, including worker classes, hooks, and configuration options.

## 🔧 Worker Classes

### PrometheusWorker

The base sync worker class that provides Prometheus metrics integration.

```python
from gunicorn_prometheus_exporter import PrometheusWorker

# Usage in gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
```

**Features:**
- Request counting and timing
- Memory and CPU usage tracking
- Error handling with method/endpoint labels
- Worker state management with timestamps

### PrometheusThreadWorker

Thread-based worker for I/O-bound applications.

```python
from gunicorn_prometheus_exporter import PrometheusThreadWorker

# Usage in gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
```

**Features:**
- All features of PrometheusWorker
- Thread-based concurrency
- Better performance for I/O-bound applications

### PrometheusEventletWorker

Eventlet-based worker for async applications.

```python
from gunicorn_prometheus_exporter import PrometheusEventletWorker

# Usage in gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
```

**Requirements:**
```bash
pip install gunicorn-prometheus-exporter[eventlet]
```

**Features:**
- All features of PrometheusWorker
- Eventlet-based async I/O
- High concurrency for async applications

### PrometheusGeventWorker

Gevent-based worker for async applications.

```python
from gunicorn_prometheus_exporter import PrometheusGeventWorker

# Usage in gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"
```

**Requirements:**
```bash
pip install gunicorn-prometheus-exporter[gevent]
```

**Features:**
- All features of PrometheusWorker
- Gevent-based async I/O
- High concurrency for async applications

### PrometheusTornadoWorker (⚠️ Not Recommended)

Tornado-based worker for async applications.

```python
from gunicorn_prometheus_exporter import PrometheusTornadoWorker

# Usage in gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusTornadoWorker"
```

**Requirements:**
```bash
pip install gunicorn-prometheus-exporter[tornado]
```

**⚠️ Warning:** TornadoWorker has known compatibility issues with metrics collection. The Prometheus metrics endpoint may hang or become unresponsive. Use `PrometheusEventletWorker` or `PrometheusGeventWorker` instead for async applications.

**Features:**
- All features of PrometheusWorker
- Tornado-based async IOLoop
- High concurrency for async applications
- ⚠️ **Known issues with metrics collection**

## 🔌 Plugin Architecture

### PrometheusMixin

The core mixin class that provides Prometheus functionality to all worker types.

```python
from gunicorn_prometheus_exporter.plugin import PrometheusMixin
```

**Core Methods:**

#### `update_worker_metrics()`

Updates worker-specific metrics including memory, CPU, and uptime.

```python
def update_worker_metrics(self):
    """Update worker metrics including memory, CPU, and uptime."""
    # Updates gunicorn_worker_memory_bytes
    # Updates gunicorn_worker_cpu_percent
    # Updates gunicorn_worker_uptime_seconds
    # Updates gunicorn_worker_state
```

#### `_handle_request_metrics()`

Handles request-level metrics tracking.

```python
def _handle_request_metrics(self):
    """Track request metrics including count and duration."""
    # Updates gunicorn_worker_requests_total
    # Updates gunicorn_worker_request_duration_seconds
```

#### `_handle_request_error_metrics(req, e)`

Handles error metrics with method and endpoint labels.

```python
def _handle_request_error_metrics(self, req, e):
    """Track error metrics with method and endpoint labels."""
    # Updates gunicorn_worker_failed_requests_total
    # Updates gunicorn_worker_error_handling_total
```

#### `_generic_handle_request(parent_method, *args, **kwargs)`

Generic request handler that wraps parent worker methods.

```python
def _generic_handle_request(self, parent_method, *args, **kwargs):
    """Generic request handler with metrics tracking."""
    # Calls parent method
    # Updates request metrics
    # Handles exceptions
```

#### `_generic_handle_error(parent_method, *args, **kwargs)`

Generic error handler that wraps parent worker methods.

```python
def _generic_handle_error(self, parent_method, *args, **kwargs):
    """Generic error handler with metrics tracking."""
    # Calls parent method
    # Updates error metrics
    # Handles exceptions
```

## 🎣 Gunicorn Hooks

### Default Hooks

The exporter provides several Gunicorn hooks for automatic setup:

#### `default_on_starting(server)`

Called when the server is starting up.

```python
from gunicorn_prometheus_exporter.hooks import default_on_starting

def on_starting(server):
    default_on_starting(server)
```

#### `default_when_ready(server)`

Called when the server is ready to accept connections.

```python
from gunicorn_prometheus_exporter.hooks import default_when_ready

def when_ready(server):
    default_when_ready(server)
```

#### `default_worker_int(worker)`

Called when a worker is initialized.

```python
from gunicorn_prometheus_exporter.hooks import default_worker_int

def worker_int(worker):
    default_worker_int(worker)
```

#### `default_on_exit(server)`

Called when the server is shutting down.

```python
from gunicorn_prometheus_exporter.hooks import default_on_exit

def on_exit(server):
    default_on_exit(server)
```

### Redis Hooks

For Redis integration, use the Redis-specific hooks:

#### `redis_when_ready(server)`

Sets up Redis forwarding when the server is ready.

```python
from gunicorn_prometheus_exporter.hooks import redis_when_ready

def when_ready(server):
    redis_when_ready(server)
```

## 📊 Metrics Reference

### Worker Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `gunicorn_worker_requests_total` | Counter | `worker_id` | Total requests handled by each worker |
| `gunicorn_worker_request_duration_seconds` | Histogram | `worker_id` | Request duration distribution |
| `gunicorn_worker_memory_bytes` | Gauge | `worker_id` | Memory usage per worker |
| `gunicorn_worker_cpu_percent` | Gauge | `worker_id` | CPU usage per worker |
| `gunicorn_worker_uptime_seconds` | Gauge | `worker_id` | Worker uptime |
| `gunicorn_worker_state` | Gauge | `worker_id`, `state`, `timestamp` | Worker state with timestamp |
| `gunicorn_worker_failed_requests_total` | Counter | `worker_id`, `method`, `endpoint` | Failed requests with labels |

### Master Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `gunicorn_master_worker_restarts_total` | Counter | None | Total worker restarts |
| `gunicorn_master_signals_total` | Counter | `signal` | Signal handling metrics |

### Error Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `gunicorn_worker_error_handling_total` | Counter | `worker_id`, `method`, `endpoint`, `error_type` | Error tracking with labels |

## ⚙️ Configuration Options

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PROMETHEUS_MULTIPROC_DIR` | String | `/tmp/prometheus_multiproc` | Directory for multiprocess metrics |
| `PROMETHEUS_METRICS_PORT` | Integer | `9090` | Port for metrics endpoint |
| `PROMETHEUS_BIND_ADDRESS` | String | `0.0.0.0` | Bind address for metrics server |
| `GUNICORN_WORKERS` | Integer | `1` | Number of workers for metrics calculation |

### Redis Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_ENABLED` | Boolean | `false` | Enable Redis forwarding |
| `REDIS_HOST` | String | `localhost` | Redis server host |
| `REDIS_PORT` | Integer | `6379` | Redis server port |
| `REDIS_DB` | Integer | `0` | Redis database number |
| `REDIS_FORWARD_INTERVAL` | Integer | `30` | Forwarding interval in seconds |

## 🔧 Advanced Usage

### Custom Metrics

You can extend the exporter with custom metrics:

```python
from prometheus_client import Counter, Gauge

# Custom metrics
CUSTOM_REQUESTS = Counter('custom_requests_total', 'Custom request counter')
CUSTOM_MEMORY = Gauge('custom_memory_bytes', 'Custom memory usage')

# Use in your application
CUSTOM_REQUESTS.inc()
CUSTOM_MEMORY.set(1024)
```

### Custom Hooks

Create custom hooks for specific requirements:

```python
def custom_when_ready(server):
    """Custom hook for additional setup."""
    # Your custom logic here
    pass

def custom_worker_int(worker):
    """Custom worker initialization."""
    # Your custom logic here
    pass
```

### Error Handling

The exporter includes robust error handling:

```python
# All metrics operations are wrapped in try-catch blocks
try:
    # Metric operation
    metric.labels(**labels).inc()
except Exception as e:
    logger.error("Failed to update metric: %s", e)
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_plugin.py

# Run with coverage
pytest --cov=src/gunicorn_prometheus_exporter --cov-report=html
```

### Integration Tests

```bash
# Test with actual Gunicorn
cd example
gunicorn --config gunicorn_simple.conf.py app:app

# Test metrics endpoint
curl http://0.0.0.0:9090/metrics
```

## 🔍 Troubleshooting

### Common Issues

1. **Port already in use**: Change `PROMETHEUS_METRICS_PORT`
2. **Permission denied**: Check multiprocess directory permissions
3. **Import errors**: Install required dependencies for async workers
4. **Metrics not updating**: Verify environment variables are set

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('gunicorn_prometheus_exporter').setLevel(logging.DEBUG)
```

### Health Checks

Check exporter health:

```bash
# Check if metrics endpoint is responding
curl http://0.0.0.0:9090/metrics

# Check for specific metrics
curl http://0.0.0.0:9090/metrics | grep gunicorn_worker
```

---

**For more detailed information, see the [Installation Guide](installation.md) and [Configuration Reference](configuration.md).**

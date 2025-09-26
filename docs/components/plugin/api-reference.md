# Plugin API Reference

This document provides detailed API reference for the plugin component.

## Core Classes

### PrometheusMixin

The core mixin class that provides Prometheus functionality to all worker types.

```python
class PrometheusMixin:
    """Mixin class that adds Prometheus metrics functionality to any worker type."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.worker_id = f"worker_{self.age}_{int(self.start_time)}"
        self.start_time = time.time()
        self.process = psutil.Process()
        self._request_count = 0
```

**Properties:**

- `worker_id` - Unique worker identifier
- `start_time` - Worker start timestamp
- `process` - psutil Process instance
- `_request_count` - Internal request counter

**Methods:**

- `update_worker_metrics()` - Update worker-specific metrics
- `_handle_request_metrics(start_time=None)` - Handle request metrics tracking
- `_handle_request_error_metrics(req, e, start_time=None)` - Handle request error metrics
- `_extract_request_from_args(args)` - Extract request object from method arguments
- `_extract_request_info(req)` - Extract method and endpoint information
- `_generic_handle_request(parent_method, *args, **kwargs)` - Generic request handler wrapper
- `_generic_handle_error(req, client, addr, e)` - Generic error handler wrapper
- `_generic_handle_quit(sig, frame)` - Generic quit handler wrapper
- `_generic_handle_abort(sig, frame)` - Generic abort handler wrapper
- `_clear_old_metrics()` - Clear old PID-based worker samples

## Worker Classes

### PrometheusWorker

Sync worker with Prometheus metrics.

```python
class PrometheusWorker(PrometheusMixin, SyncWorker):
    """Sync worker with Prometheus metrics."""

    def handle_request(self, listener, req, client, addr):
        """Handle a request and update metrics."""
        return self._generic_handle_request(
            super().handle_request, listener, req, client, addr
        )

    def handle_error(self, req, client, addr, e):
        """Handle request errors and update error metrics."""
        return self._generic_handle_error(req, client, addr, e)

    def handle_quit(self, sig, frame):
        """Handle quit signal and update worker state."""
        self._generic_handle_quit(sig, frame)

    def handle_abort(self, sig, frame):
        """Handle abort signal and update worker state."""
        self._generic_handle_abort(sig, frame)
```

### PrometheusThreadWorker

Thread worker with Prometheus metrics.

```python
class PrometheusThreadWorker(PrometheusMixin, ThreadWorker):
    """Thread worker with Prometheus metrics."""

    def handle_request(self, req, conn):
        """Handle a request and update metrics."""
        return self._generic_handle_request(super().handle_request, req, conn)

    def handle_error(self, req, client, addr, e):
        """Handle request errors and update error metrics."""
        return self._generic_handle_error(req, client, addr, e)

    def handle_quit(self, sig, frame):
        """Handle quit signal and update worker state."""
        self._generic_handle_quit(sig, frame)

    def handle_abort(self, sig, frame):
        """Handle abort signal and update worker state."""
        self._generic_handle_abort(sig, frame)
```

### PrometheusEventletWorker

Eventlet worker with Prometheus metrics.

```python
class PrometheusEventletWorker(PrometheusMixin, EventletWorker):
    """Eventlet worker with Prometheus metrics."""

    def handle_request(self, listener_name, req, sock, addr):
        """Handle a request and update metrics."""
        return self._generic_handle_request(
            super().handle_request, listener_name, req, sock, addr
        )

    def handle_error(self, req, client, addr, e):
        """Handle request errors and update error metrics."""
        return self._generic_handle_error(req, client, addr, e)

    def handle_quit(self, sig, frame):
        """Handle quit signal and update worker state."""
        self._generic_handle_quit(sig, frame)

    def handle_abort(self, sig, frame):
        """Handle abort signal and update worker state."""
        self._generic_handle_abort(sig, frame)
```

### PrometheusGeventWorker

Gevent worker with Prometheus metrics.

```python
class PrometheusGeventWorker(PrometheusMixin, GeventWorker):
    """Gevent worker with Prometheus metrics."""

    def handle_request(self, listener_name, req, sock, addr):
        """Handle a request and update metrics."""
        return self._generic_handle_request(
            super().handle_request, listener_name, req, sock, addr
        )

    def handle_error(self, req, client, addr, e):
        """Handle request errors and update error metrics."""
        return self._generic_handle_error(req, client, addr, e)

    def handle_quit(self, sig, frame):
        """Handle quit signal and update worker state."""
        self._generic_handle_quit(sig, frame)

    def handle_abort(self, sig, frame):
        """Handle abort signal and update worker state."""
        self._generic_handle_abort(sig, frame)
```

## Metrics Collection

### Worker Metrics

The plugin collects comprehensive worker metrics:

#### Memory Usage

```python
def update_worker_metrics(self):
    """Update worker metrics."""
    memory_info = self.process.memory_info()
    WORKER_MEMORY.labels(worker_id=self.worker_id).set(memory_info.rss)
```

#### CPU Usage

```python
def update_worker_metrics(self):
    """Update worker metrics."""
    cpu_percent = self.process.cpu_percent()
    WORKER_CPU.labels(worker_id=self.worker_id).set(cpu_percent)
```

#### Uptime

```python
def update_worker_metrics(self):
    """Update worker metrics."""
    uptime = time.time() - self.start_time
    WORKER_UPTIME.labels(worker_id=self.worker_id).set(uptime)
```

#### Worker State

```python
def update_worker_metrics(self):
    """Update worker metrics."""
    timestamp = int(time.time())
    WORKER_STATE.labels(
        worker_id=self.worker_id, state="running", timestamp=timestamp
    ).set(1)
```

### Request Metrics

#### Request Counting

```python
def _handle_request_metrics(self, start_time=None):
    """Handle request metrics tracking."""
    self._request_count += 1
    WORKER_REQUESTS.labels(worker_id=self.worker_id).inc()
```

#### Request Duration

```python
def _handle_request_metrics(self, start_time=None):
    """Handle request metrics tracking."""
    duration = time.time() - start_time
    WORKER_REQUEST_DURATION.labels(worker_id=self.worker_id).observe(duration)
```

### Error Metrics

#### Failed Requests

```python
def _handle_request_error_metrics(self, req, e, start_time=None):
    """Handle request error metrics tracking."""
    method, endpoint = self._extract_request_info(req)
    error_type = type(e).__name__

    WORKER_FAILED_REQUESTS.labels(
        worker_id=self.worker_id,
        method=method,
        endpoint=endpoint,
        error_type=error_type,
    ).inc()
```

#### Error Handling

```python
def _generic_handle_error(self, req, client, addr, e):
    """Generic error handler wrapper."""
    method, endpoint = self._extract_request_info(req)
    error_type = type(e).__name__

    WORKER_ERROR_HANDLING.labels(
        worker_id=self.worker_id,
        method=method,
        endpoint=endpoint,
        error_type=error_type,
    ).inc()
```

## Worker State Management

### Quit Signal Handling

```python
def _generic_handle_quit(self, sig, frame):
    """Generic quit handler wrapper."""
    timestamp = int(time.time())
    WORKER_STATE.labels(
        worker_id=self.worker_id, state="quitting", timestamp=timestamp
    ).set(1)

    WORKER_RESTART_REASON.labels(worker_id=self.worker_id, reason="quit").inc()
    WORKER_RESTART_COUNT.labels(
        worker_id=self.worker_id, restart_type="graceful", reason="quit"
    ).inc()
```

### Abort Signal Handling

```python
def _generic_handle_abort(self, sig, frame):
    """Generic abort handler wrapper."""
    timestamp = int(time.time())
    WORKER_STATE.labels(
        worker_id=self.worker_id, state="aborting", timestamp=timestamp
    ).set(1)

    WORKER_RESTART_REASON.labels(worker_id=self.worker_id, reason="abort").inc()
    WORKER_RESTART_COUNT.labels(
        worker_id=self.worker_id, restart_type="forced", reason="abort"
    ).inc()
```

## Request Processing

### Generic Request Handler

```python
def _generic_handle_request(self, parent_method, *args, **kwargs):
    """Generic request handler wrapper."""
    start_time = time.time()

    try:
        # Update worker metrics on each request
        self.update_worker_metrics()

        # Call parent handle_request
        result = parent_method(*args, **kwargs)

        # Update request metrics after successful request
        self._handle_request_metrics(start_time)

        return result
    except Exception as e:
        # Handle request error metrics
        req = self._extract_request_from_args(args)
        self._handle_request_error_metrics(req, e, start_time)
        raise
```

### Request Information Extraction

```python
def _extract_request_from_args(self, args):
    """Extract request object from method arguments."""
    for arg in args:
        # Check if this looks like a request object
        if hasattr(arg, "method") and hasattr(arg, "path"):
            return arg
    return None

def _extract_request_info(self, req):
    """Extract method and endpoint information from request object."""
    method = req.method if req and hasattr(req, "method") else "UNKNOWN"
    endpoint = req.path if req and hasattr(req, "path") else "UNKNOWN"
    return method, endpoint
```

## Metrics Cleanup

### Old Metrics Cleanup

```python
def _clear_old_metrics(self):
    """Clear only the old PID-based worker samples."""
    for MetricClass in [
        WORKER_REQUESTS,
        WORKER_REQUEST_DURATION,
        WORKER_MEMORY,
        WORKER_CPU,
        WORKER_UPTIME,
        WORKER_FAILED_REQUESTS,
        WORKER_ERROR_HANDLING,
        WORKER_STATE,
        WORKER_RESTART_REASON,
        WORKER_RESTART_COUNT,
    ]:
        metric = MetricClass._metric
        labelnames = list(metric._labelnames)

        # Collect the old label-tuples to delete
        to_delete = []
        for label_values in list(metric._metrics.keys()):
            try:
                wid = label_values[labelnames.index("worker_id")]
            except ValueError:
                continue

            # Check if this is an old worker ID (different from current)
            if wid != self.worker_id:
                to_delete.append(label_values)

        # Delete the old samples
        for label_values in to_delete:
            metric.remove(*label_values)
```

## Async Worker Support

### Eventlet Worker Creation

```python
def _create_eventlet_worker():
    """Create PrometheusEventletWorker class if available."""
    global PrometheusEventletWorker
    if EVENTLET_AVAILABLE:
        try:
            from gunicorn.workers.geventlet import EventletWorker

            class PrometheusEventletWorker(PrometheusMixin, EventletWorker):
                # ... implementation
        except (ImportError, RuntimeError):
            PrometheusEventletWorker = None
```

### Gevent Worker Creation

```python
def _create_gevent_worker():
    """Create PrometheusGeventWorker class if available."""
    global PrometheusGeventWorker
    if GEVENT_AVAILABLE:
        try:
            from gunicorn.workers.ggevent import GeventWorker

            class PrometheusGeventWorker(PrometheusMixin, GeventWorker):
                # ... implementation
        except (ImportError, RuntimeError):
            PrometheusGeventWorker = None
```

## Utility Functions

### Worker Class Getters

```python
def get_prometheus_eventlet_worker():
    """Get PrometheusEventletWorker class if available."""
    return PrometheusEventletWorker

def get_prometheus_gevent_worker():
    """Get PrometheusGeventWorker class if available."""
    return PrometheusGeventWorker
```

## Configuration

### Logging Setup

```python
def _setup_logging():
    """Setup logging with configuration."""
    try:
        log_level = config.get_gunicorn_config().get("loglevel", "INFO").upper()
        logging.basicConfig(level=getattr(logging, log_level))
    except Exception as e:
        # Fallback to INFO level if config is not available
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).warning(
            "Could not setup logging from config: %s", e
        )
```

## Error Handling

### Exception Handling

All metrics operations are wrapped in try-catch blocks to ensure worker stability:

```python
try:
    # Metric operation
    WORKER_REQUESTS.labels(worker_id=self.worker_id).inc()
except Exception as e:
    logger.error("Failed to update metric: %s", e)
```

### Graceful Degradation

If metrics collection fails, the worker continues to function normally:

```python
def update_worker_metrics(self):
    """Update worker metrics."""
    try:
        # Update metrics
        memory_info = self.process.memory_info()
        WORKER_MEMORY.labels(worker_id=self.worker_id).set(memory_info.rss)
    except Exception as e:
        logger.error("Failed to update worker metrics: %s", e)
```

## Related Documentation

- [Plugin Overview](index.md) - Plugin component overview
- [Metrics Component](../metrics/) - Metrics collection and monitoring
- [Configuration Guide](../config/configuration.md) - Configuration options

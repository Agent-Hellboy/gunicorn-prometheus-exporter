# Supported Worker Types

Gunicorn Prometheus Exporter supports all major Gunicorn worker types with comprehensive metrics collection and monitoring capabilities.

## Worker Types Overview

| Worker Type         | Installation                                                          | Usage                                                                                     |
| ------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **Sync Worker**     | `pip install gunicorn-prometheus-exporter`                            | `worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"`                          |
| **Thread Worker**   | `pip install gunicorn-prometheus-exporter`                            | `worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"`                    |
| **Eventlet Worker** | `pip install gunicorn-prometheus-exporter[eventlet]`                  | `worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"`                  |
| **Gevent Worker**   | `pip install gunicorn-prometheus-exporter[gevent]`                    | `worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"`                    |

## Testing Status

All worker types have been thoroughly tested and validated:

| Worker Type         | Status          | Metrics                 | Master Signals  | Load Distribution |
| ------------------- | --------------- | ----------------------- | --------------- | ----------------- |
| **Sync Worker**     | Working         | All metrics             | HUP, USR1, CHLD | Balanced          |
| **Thread Worker**   | Working         | All metrics             | HUP, USR1, CHLD | Balanced          |
| **Eventlet Worker** | Working         | All metrics             | HUP, USR1, CHLD | Balanced          |
| **Gevent Worker**   | Working         | All metrics             | HUP, USR1, CHLD | Balanced          |

### Validation Includes:

- Request counting and distribution across workers
- Memory and CPU usage tracking
- Error handling with method/endpoint labels
- Master process signal tracking (HUP, USR1, CHLD)
- Worker state management with timestamps
- Multiprocess metrics collection
- Load balancing verification

## Sync Worker

The default synchronous worker type, suitable for CPU-bound applications.

### Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
```

### Use Cases

- CPU-intensive applications
- Applications with blocking I/O operations
- Traditional web applications

## Thread Worker

Uses threads to handle multiple requests concurrently within a single process.

### Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
threads = 4
```

### Use Cases

- I/O-bound applications
- Applications that can benefit from threading
- When you need more concurrency than sync workers

## Eventlet Worker

Asynchronous worker using the eventlet library for high concurrency.

### Installation

```bash
pip install gunicorn-prometheus-exporter[eventlet]
```

### Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
worker_connections = 1000
```

### Use Cases

- High-concurrency applications
- WebSocket applications
- Real-time applications

## Gevent Worker

Asynchronous worker using the gevent library for high concurrency.

### Installation

```bash
pip install gunicorn-prometheus-exporter[gevent]
```

### Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"
worker_connections = 1000
```

### Use Cases

- High-concurrency applications
- Applications with many concurrent connections
- Real-time applications

## Choosing the Right Worker Type

### Sync Worker
- **Best for**: CPU-bound applications, traditional web apps
- **Pros**: Simple, reliable, good for CPU-intensive tasks
- **Cons**: Limited concurrency, blocking I/O

### Thread Worker
- **Best for**: I/O-bound applications, database-heavy apps
- **Pros**: Better concurrency than sync, shared memory
- **Cons**: GIL limitations in Python, memory overhead

### Eventlet Worker
- **Best for**: High-concurrency, WebSocket applications
- **Pros**: High concurrency, good for I/O-bound tasks
- **Cons**: Requires eventlet-compatible libraries

### Gevent Worker
- **Best for**: High-concurrency, real-time applications
- **Pros**: High concurrency, mature library
- **Cons**: Requires gevent-compatible libraries

## Performance Considerations

### Memory Usage
- **Sync/Thread**: Lower memory per worker
- **Eventlet/Gevent**: Higher memory per worker but fewer workers needed

### CPU Usage
- **Sync**: Best for CPU-bound tasks
- **Thread**: Good balance for mixed workloads
- **Eventlet/Gevent**: Best for I/O-bound tasks

### Concurrency
- **Sync**: 1 request per worker
- **Thread**: Multiple requests per worker (limited by GIL)
- **Eventlet/Gevent**: Thousands of concurrent requests per worker

## Monitoring and Metrics

All worker types provide the same comprehensive metrics:

- Request counting and timing
- Memory and CPU usage
- Error tracking
- Worker state management
- Master process monitoring

For detailed metrics information, see the [Metrics Guide](index.md).

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you have the correct dependencies installed
2. **Performance Issues**: Choose the right worker type for your workload
3. **Memory Issues**: Monitor memory usage and adjust worker count

For more troubleshooting information, see the [Troubleshooting Guide](../../troubleshooting.md).

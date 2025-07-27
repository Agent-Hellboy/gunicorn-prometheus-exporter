# Gunicorn Prometheus Exporter

[![CI](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter/graph/badge.svg?token=NE7JS4FZHC)](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter)
[![PyPI - Version](https://img.shields.io/pypi/v/gunicorn-prometheus-exporter.svg)](https://pypi.org/project/gunicorn-prometheus-exporter/)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://agent-hellboy.github.io/gunicorn-prometheus-exporter)

A Gunicorn worker plugin that exports Prometheus metrics to monitor worker
performance, including memory usage, CPU usage, request durations, and error
tracking (trying to replace
<https://docs.gunicorn.org/en/stable/instrumentation.html> with extra info).
It also aims to replace request-level tracking, such as the number of requests
made to a particular endpoint, for any framework (e.g., Flask, Django, and
others) that conforms to the WSGI specification.

## Features

- **Worker Metrics**: Memory, CPU, request durations, error tracking
- **Master Process Intelligence**: Signal tracking, restart analytics
- **Multiprocess Support**: Full Prometheus multiprocess compatibility
- **Redis Integration**: Forward metrics to Redis for external storage
- **Zero Configuration**: Works out-of-the-box with minimal setup
- **Production Ready**: Retry logic, error handling, health monitoring

## Quick Start

### Installation

```bash
pip install gunicorn-prometheus-exporter
```

### Basic Usage

Create a Gunicorn config file (`gunicorn.conf.py`):

```python
# Basic configuration
bind = "0.0.0.0:8000"
workers = 2

# Prometheus exporter
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Optional: Custom hooks for advanced setup
def when_ready(server):
    from gunicorn_prometheus_exporter.hooks import default_when_ready
    default_when_ready(server)
```

### Start Gunicorn

```bash
gunicorn -c gunicorn.conf.py app:app
```

### Access Metrics

Metrics are automatically exposed on the configured bind address and port (default: `0.0.0.0:9091`):

```bash
# Using default configuration
curl http://0.0.0.0:9091/metrics

# Or use your configured bind address
curl http://YOUR_BIND_ADDRESS:9091/metrics
```

## Documentation

📖 **Complete documentation is available at: [https://agent-hellboy.github.io/gunicorn-prometheus-exporter](https://agent-hellboy.github.io/gunicorn-prometheus-exporter)**

The documentation includes:
- Installation and configuration guides
- Complete metrics reference
- Framework-specific examples (Django, FastAPI, Flask, Pyramid)
- API reference and troubleshooting
- Contributing guidelines

## Available Metrics

### Worker Metrics
- `gunicorn_worker_requests_total`: Total requests processed
- `gunicorn_worker_request_duration_seconds`: Request duration histogram
- `gunicorn_worker_memory_usage_bytes`: Memory usage per worker
- `gunicorn_worker_cpu_usage_percent`: CPU usage per worker
- `gunicorn_worker_uptime_seconds`: Worker uptime

### Master Metrics
- `gunicorn_master_signals_total`: Signal counts by type
- `gunicorn_master_worker_restarts_total`: Worker restart counts
- `gunicorn_master_workers_current`: Current worker count

### Redis Metrics (if enabled)
- `gunicorn_redis_forwarder_status`: Forwarder health status
- `gunicorn_redis_forwarder_errors_total`: Forwarder error counts

## Examples

See the `example/` directory for complete working examples:
- `gunicorn_simple.conf.py`: Basic setup
- `gunicorn_redis_based.conf.py`: Redis forwarding setup
- `gunicorn_basic.conf.py`: Standard configuration

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_METRICS_PORT` | `9091` | Port for metrics endpoint |
| `PROMETHEUS_BIND_ADDRESS` | `0.0.0.0` | Bind address for metrics |
| `GUNICORN_WORKERS` | `1` | Number of workers |
| `PROMETHEUS_MULTIPROC_DIR` | Auto-generated | Multiprocess directory |
| `REDIS_ENABLED` | `false` | Enable Redis forwarding |
| `REDIS_URL` | `redis://127.0.0.1:6379` | Redis connection URL (configure for your environment) |

### Gunicorn Hooks

```python
# Basic setup
from gunicorn_prometheus_exporter.hooks import default_when_ready

def when_ready(server):
    default_when_ready(server)

# With Redis forwarding
from gunicorn_prometheus_exporter.hooks import redis_when_ready

def when_ready(server):
    redis_when_ready(server)
```

## Contributing

Contributions are welcome! Please see our [contributing guide](https://agent-hellboy.github.io/gunicorn-prometheus-exporter/contributing/) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

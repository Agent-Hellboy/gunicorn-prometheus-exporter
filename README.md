# Gunicorn Prometheus Exporter

[![CI](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml)

[![codecov](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter/graph/badge.svg?token=NE7JS4FZHC)](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter)

[![PyPI - Version](https://img.shields.io/pypi/v/gunicorn-prometheus-exporter.svg)](https://pypi.org/project/gunicorn-prometheus-exporter/)

A Gunicorn worker plugin that exports Prometheus metrics to monitor worker
performance, including memory usage, CPU usage, request durations, and error
tracking (trying to replace
<https://docs.gunicorn.org/en/stable/instrumentation.html> with extra info).
It also aims to replace request-level tracking, such as the number of requests
made to a particular endpoint, for any framework (e.g., Flask, Django, and
others) that conforms to the WSGI specification.

## Features

- **Worker Metrics**: Exports comprehensive Prometheus metrics for Gunicorn workers
  - Memory usage, CPU usage, and uptime tracking
  - Request durations and counts with histogram buckets
  - Failed requests and error handling with detailed labels
  - Worker state monitoring (running, quit, abort)
- **Master Metrics**: Master process metrics for worker management and signal handling
  - Worker restart tracking with signal-specific reasons
  - Automatic capture of SIGHUP, SIGCHLD, SIGTTIN, SIGTTOU, SIGUSR1, SIGUSR2 signals
  - Multiprocess metrics support for both worker and master processes
- **Easy Integration**: Simple configuration with existing Prometheus setups
  - Automatic metrics exposure through configuration
  - No manual endpoint creation required
  - Compatible with Prometheus multiprocess collectors

## Quick Start

### 1. Installation

```bash
pip install gunicorn-prometheus-exporter
```

### 2. Basic Usage

Create a Gunicorn config file (`gunicorn.conf.py`):
See `./example/gunicorn.conf.py` for a complete working example.

### 3. Start Gunicorn

```bash
gunicorn -c gunicorn.conf.py app:app
```

### 4. Access Metrics

Metrics are automatically exposed on `http://localhost:9091/metrics`:

```bash
curl http://localhost:9091/metrics
```

## Available Metrics

### Worker Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|---------|
| `gunicorn_worker_requests_total` | Counter | Total requests handled | `worker_id` |
| `gunicorn_worker_request_duration_seconds` | Histogram | Request duration | `worker_id` |
| `gunicorn_worker_memory_bytes` | Gauge | Memory usage | `worker_id` |
| `gunicorn_worker_cpu_percent` | Gauge | CPU usage | `worker_id` |
| `gunicorn_worker_uptime_seconds` | Gauge | Worker uptime | `worker_id` |
| `gunicorn_worker_failed_requests_total` | Counter | Failed requests | `worker_id`, `method`, `endpoint`, `error_type` |
| `gunicorn_worker_error_handling_total` | Counter | Error handling | `worker_id`, `method`, `endpoint`, `error_type` |
| `gunicorn_worker_state` | Gauge | Worker state | `worker_id`, `state`, `timestamp` |

### Master Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|---------|
| `gunicorn_master_worker_restart_total` | Counter | Worker restarts by reason | `reason` |

**Signal Reasons:**

- `usr1`: USR1 signal received
- `usr2`: USR2 signal received
- `hup`: HUP signal received
- `chld`: CHLD signal (worker exit/restart)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus` | Metrics storage directory |
| `PROMETHEUS_METRICS_PORT` | `9091` | Metrics server port |

### Advanced Configuration

```python
# gunicorn.conf.py
import os
import gunicorn_prometheus_exporter

# Set custom metrics directory
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/var/lib/gunicorn/metrics"
os.environ["PROMETHEUS_METRICS_PORT"] = "9092"

# Gunicorn settings
bind = "0.0.0.0:8080"
workers = 4
worker_class = "gunicorn_prometheus_exporter.plugin.PrometheusWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

## Gunicorn Hooks Integration

This exporter provides a set of hooks that can be used directly in your Gunicorn config files for advanced metrics and Redis forwarding support. Example usage:

```python
from gunicorn_prometheus_exporter.hooks import (
    default_on_exit,
    default_on_starting,
    default_worker_int,
    redis_when_ready,  # or default_when_ready for non-Redis
)

when_ready = redis_when_ready  # Enables Redis metrics forwarding
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
```

See the `example/` directory for ready-to-use config files:
- `gunicorn_simple.conf.py` (basic metrics)
- `gunicorn_basic.conf.py` (custom hooks)
- `gunicorn_redis.conf.py` (Redis forwarding)
- `gunicorn_redis_based.conf.py` (Redis multiprocess)

## Redis Metrics Forwarding & Custom Collector

**Current status:**
- The exporter can forward metrics to Redis for multi-process setups using the provided hooks.
- **A custom Prometheus collector that reads metrics from Redis and exposes them at the `/metrics` endpoint will be implemented.**
- This will include a custom server/collector that reads from Redis and merges with in-process metrics for complete Redis-based metrics functionality.

**Important:**
- When using Redis-based metrics forwarding, you **must** set:
  ```
  export CLEANUP_DB_FILES=false
  ```
  or in your config:
  ```python
  os.environ.setdefault("CLEANUP_DB_FILES", "false")
  ```
  This prevents the exporter from deleting the multiprocess DB files, which is necessary for correct operation in a multi-worker or Redis-forwarded setup.

The custom collector implementation is planned and will provide seamless Redis-based metrics exposure.

---

## Signal Handling

The exporter automatically tracks Gunicorn master process signals:

```bash
# Send signals to test
kill -USR1 <master_pid>  # Graceful reload
kill -USR2 <master_pid>  # Reload configuration
kill -HUP <master_pid>   # Reload workers
kill -TERM <worker_pid>  # Kill worker (triggers CHLD)
```

## Example Output

```prometheus
# Worker metrics
gunicorn_worker_requests_total{worker_id="worker_1_1234567890"} 42.0
gunicorn_worker_memory_bytes{worker_id="worker_1_1234567890"} 52428800.0
gunicorn_worker_cpu_percent{worker_id="worker_1_1234567890"} 2.5
gunicorn_worker_uptime_seconds{worker_id="worker_1_1234567890"} 3600.0

# Master metrics
gunicorn_master_worker_restart_total{reason="usr1"} 5.0
gunicorn_master_worker_restart_total{reason="usr2"} 2.0
gunicorn_master_worker_restart_total{reason="hup"} 3.0
gunicorn_master_worker_restart_total{reason="chld"} 12.0
```

## Architecture

### How It Works

1. **Import Patching**: When imported, the module patches Gunicorn's `Arbiter` class with `PrometheusMaster`
2. **Worker Plugin**: Uses custom `PrometheusWorker` class to collect worker metrics
3. **Signal Handling**: `PrometheusMaster` overrides signal handlers to track master signals
4. **Multiprocess**: Uses Prometheus multiprocess mode for shared metrics collection
5. **HTTP Server**: Starts metrics server in `when_ready` hook

### Key Components

- **`PrometheusMaster`**: Extends Gunicorn's Arbiter for signal tracking
- **`PrometheusWorker`**: Custom worker class for request/resource metrics
- **`metrics.py`**: Defines all Prometheus metrics with proper naming
- **`gunicorn.conf.py`**: Configuration with hooks for metrics server

## Development

### Setup

```bash
git clone <repository>
cd gunicorn-prometheus-exporter
pip install -e .
```

### Testing

```bash
# Run tests
tox

# Manual testing
cd example
gunicorn -c gunicorn.conf.py app:app
curl http://localhost:9091/metrics
```

### Project Structure

```text
gunicorn-prometheus-exporter/
├── src/gunicorn_prometheus_exporter/
│   ├── __init__.py          # Patching logic
│   ├── master.py            # PrometheusMaster class
│   ├── metrics.py           # Metric definitions
│   ├── plugin.py            # PrometheusWorker class
│   └── utils.py             # Utility functions
├── example/
│   ├── app.py               # Sample Flask app
│   └── gunicorn.conf.py     # Gunicorn config
└── tests/                   # Test suite
```

## Troubleshooting

### Common Issues

**Metrics server not starting:**

- Check if port 9091 is available
- Verify `PROMETHEUS_MULTIPROC_DIR` is set and writable
- Check Gunicorn logs for errors

**No metrics appearing:**

- Ensure `worker_class` is set to `PrometheusWorker`
- Check that the exporter module is imported early
- Verify multiprocess directory exists

**Signal metrics not incrementing:**

- Confirm `PrometheusMaster` is being used (check logs)
- Verify signal handlers are properly overridden
- Check that signals are being sent to master process

### Configuration Management

The exporter provides a centralized configuration system through `config.py`:

```python
from gunicorn_prometheus_exporter import config, get_config

# Get configuration instance
cfg = get_config()

# Access configuration values
print(f"Metrics port: {cfg.prometheus_metrics_port}")
print(f"Workers: {cfg.gunicorn_workers}")
print(f"Multiproc dir: {cfg.prometheus_multiproc_dir}")

# Access configuration values directly
print(f"Metrics port: {cfg.prometheus_metrics_port}")
print(f"Workers: {cfg.gunicorn_workers}")
print(f"Multiproc dir: {cfg.prometheus_multiproc_dir}")
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### **Required (Production):**

- `PROMETHEUS_BIND_ADDRESS`: Bind address for metrics server (e.g., `0.0.0.0`)
- `PROMETHEUS_METRICS_PORT`: Port for metrics endpoint (e.g., `9091`)
- `GUNICORN_WORKERS`: Number of Gunicorn workers (e.g., `4`)

#### **Optional (with defaults):**

- `PROMETHEUS_MULTIPROC_DIR`: Directory for multiprocess metrics (default: `/tmp/prometheus`)
- `GUNICORN_TIMEOUT`: Worker timeout in seconds (default: 30)
- `GUNICORN_KEEPALIVE`: Keepalive setting (default: 2)

#### **Production Setup Example:**

```bash
# Required variables
export PROMETHEUS_BIND_ADDRESS=0.0.0.0
export PROMETHEUS_METRICS_PORT=9091
export GUNICORN_WORKERS=4

# Optional variables
export PROMETHEUS_MULTIPROC_DIR=/var/tmp/prometheus
export GUNICORN_TIMEOUT=60
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:

- Check the troubleshooting section
- Review the example configuration
- Open an issue on GitHub

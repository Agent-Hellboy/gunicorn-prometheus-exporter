# Gunicorn Prometheus Exporter

[![CI](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml)

[![codecov](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter/graph/badge.svg?token=NE7JS4FZHC)](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter)

A Gunicorn worker plugin that exports Prometheus metrics for monitoring worker performance, including memory usage, CPU usage, request durations, and error tracking.

## Features

- Exports Prometheus metrics for Gunicorn workers
- Tracks worker memory usage, CPU usage, and uptime
- Monitors request durations and counts
- Tracks failed requests and error handling
- Supports worker state monitoring (running, quit, abort)
- Master process metrics for worker management
- Easy integration with existing Prometheus setups

## Installation

```bash
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter
cd gunicorn-prometheus-exporter
pip install .
```

## Usage

1. Install the package
2. Configure Gunicorn to use the plugin:

```bash
gunicorn --worker-class gunicorn_prometheus_exporter.PrometheusWorker your_app:app
```

## Available Metrics

### Worker Metrics

- `gunicorn_worker_requests`: Total number of requests handled by each worker
- `gunicorn_worker_request_duration_seconds`: Request duration in seconds
- `gunicorn_worker_memory_bytes`: Memory usage of each worker process
- `gunicorn_worker_cpu_percent`: CPU usage of each worker process
- `gunicorn_worker_uptime_seconds`: Uptime of each worker process
- `gunicorn_worker_failed_requests`: Total number of failed requests with method, endpoint, and error type
- `gunicorn_worker_error_handling`: Total number of errors handled with method, endpoint, and error type
- `gunicorn_worker_state`: Current state of the worker (running, quit, abort)

### Master Process Metrics

- `gunicorn_master_worker_restart_total`: Total number of worker restarts with reason

To enable master process metrics, use the PrometheusMaster class:

```python
# In your Gunicorn configuration
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
from gunicorn_prometheus_exporter.master import PrometheusMaster

# You have to patch master , gunicron doesn't allow master worker plugin
# This can change , it's an internal implemenation
from gunicorn_prometheus_exporter.plugin import PrometheusMaster

gunicorn.arbiter.Arbiter = PrometheusMaster
```


## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Configuration

### Gunicorn Configuration

Create a `gunicorn.conf.py` file with the following configuration:

```python
from prometheus_client import start_http_server
import os
import logging

def when_ready(server):
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.info("Starting Prometheus metrics server on port 9090")
        start_http_server(9090)
```

### Environment Variables

The exporter supports the following configuration options:

- `PROMETHEUS_MULTIPROC_DIR`: Directory for multiprocess metrics (default: `/tmp/prometheus`)
- `PROMETHEUS_METRICS_PORT`: Port for metrics endpoint (default: 8000)



## License

MIT License - Prince Roshan


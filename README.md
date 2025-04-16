# Gunicorn Prometheus Exporter

[![CI](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml)

[![codecov](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter/graph/badge.svg?token=NE7JS4FZHC)](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter)

A Gunicorn plugin that exports Prometheus metrics for monitoring worker performance.

## Features

- Worker metrics:
  - Request counts and durations
  - Memory and CPU usage
  - Uptime tracking
  - Error tracking (failed requests and error handling)
  - Worker state tracking (running/stopped)

## Installation

```bash
pip install gunicorn-prometheus-exporter
```

## Usage

Add to your Gunicorn config:

```python
# gunicorn.conf.py
from gunicorn_prometheus_exporter import PrometheusWorker

worker_class = PrometheusWorker
```

Or use command line:

```bash
gunicorn --worker-class gunicorn_prometheus_exporter.PrometheusWorker app:app
```

## Metrics

- `gunicorn_worker_requests_total`: Total requests handled
- `gunicorn_worker_request_duration_seconds`: Request duration
- `gunicorn_worker_memory_bytes`: Memory usage
- `gunicorn_worker_cpu_percent`: CPU usage
- `gunicorn_worker_uptime_seconds`: Worker uptime
- `gunicorn_worker_failed_requests_total`: Failed requests
- `gunicorn_worker_error_handling_total`: Error handling counts
- `gunicorn_worker_state`: Worker state (1=running, 0=stopped)

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

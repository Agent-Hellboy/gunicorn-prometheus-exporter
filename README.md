# Gunicorn Prometheus Exporter

[![CI](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml)

[![codecov](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter/graph/badge.svg?token=NE7JS4FZHC)](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter)

A Gunicorn worker plugin that exports Prometheus metrics for monitoring worker performance.

## Architecture

### Gunicorn Worker Architecture with Metrics Collection

```
                          ┌────────────────────────────┐
                          │        HTTP Client         │
                          └────────────┬───────────────┘
                                       │
                                       ▼
                          ┌────────────────────────────┐
                          │     Gunicorn Master        │
                          │ - Initializes config       │
                          │ - Binds socket (listener)  │
                          │ - Forks worker processes   │
                          └────────────┬───────────────┘
                                       │
             ┌─────────────────────────┴─────────────────────────┐
             ▼                         ▼                         ▼
      ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
      │  Worker 1    │         │  Worker 2    │   ...   │  Worker N    │
      │ (Sync/Gevent │         │ (Sync/Gevent │         │ (Sync/Gevent │
      │  Worker)     │         │  Worker)     │         │  Worker)     │
      └──────┬───────┘         └──────┬───────┘         └──────┬───────┘
             │                        │                        │
             ▼                        ▼                        ▼
      ┌────────────────────────────────────────────────────────────────────┐
      │                      Prometheus Metrics Layer                      │
      │ ┌────────────────┐ ┌────────────────┐ ┌──────────────────────────┐ │
      │ │ Worker Metrics │ │ Request Timing │ │ Error/Exception Counters │ │
      │ └────────────────┘ └────────────────┘ └──────────────────────────┘ │
      └────────────────────────────────────────────────────────────────────┘
             │                         │                         │
             ▼                         ▼                         ▼
      ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
      │ Parse HTTP Request │   │ Parse HTTP Request │   │ Parse HTTP Request │
      └──────────┬─────────┘   └──────────┬─────────┘   └──────────┬─────────┘
                 ▼                        ▼                        ▼
      ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
      │  WSGI App Adapter  │   │  WSGI App Adapter  │   │  WSGI App Adapter  │
      └──────────┬─────────┘   └──────────┬─────────┘   └──────────┬─────────┘
                 ▼                        ▼                        ▼
      ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
      │ Flask/Django App   │   │ Flask/Django App   │   │ Flask/Django App   │
      │   Business Logic   │   │   Business Logic   │   │   Business Logic   │
      └──────────┬─────────┘   └──────────┬─────────┘   └──────────┬─────────┘
                 ▼                        ▼                        ▼
      ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
      │   Build Response   │   │   Build Response   │   │   Build Response   │
      └──────────┬─────────┘   └──────────┬─────────┘   └──────────┬─────────┘
                 ▼                        ▼                        ▼
      ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
      │  Return to Worker  │   │  Return to Worker  │   │  Return to Worker  │
      └──────────┬─────────┘   └──────────┬─────────┘   └──────────┬─────────┘
                 ▼                        ▼                        ▼
             ┌────────────────────────────────────────────────────────┐
             │           Gunicorn Worker sends HTTP Response          │
             └──────────────────────────┬─────────────────────────────┘
                                        ▼
                          ┌────────────────────────────┐
                          │   Client receives Response │
                          └────────────────────────────┘

```

### What Our Plugin Does

1. **Worker Resource Monitoring**:
   - Tracks memory usage of each worker
   - Monitors CPU utilization
   - Records worker uptime
   - All metrics are labeled with worker ID

2. **Request Processing Metrics**:
   - Counts total requests handled by each worker
   - Measures request duration
   - Tracks failed requests
   - Provides per-worker request statistics

3. **Integration Points**:
   - Extends Gunicorn's `SyncWorker` class
   - Hooks into request handling pipeline
   - Collects metrics before and after request processing
   - Maintains worker-specific metrics

4. **Metrics Exposed**:
   - `gunicorn_worker_memory_bytes`: Worker memory usage
   - `gunicorn_worker_cpu_percent`: Worker CPU usage
   - `gunicorn_worker_uptime_seconds`: Worker uptime
   - `gunicorn_worker_requests_total`: Total requests handled
   - `gunicorn_worker_request_duration_seconds`: Request duration
   - `gunicorn_worker_failed_requests_total`: Failed requests

## Features

- Request metrics (count, latency)
- Worker metrics (memory, CPU, uptime)
- Error tracking
- Multiprocess support
- Easy integration

## Installation

```bash
pip install gunicorn-prometheus-exporter
```

## Usage

1. Install the package:
```bash
pip install gunicorn-prometheus-exporter
```

2. Run Gunicorn with the Prometheus worker:
```bash
gunicorn --worker-class gunicorn_prometheus_exporter.PrometheusWorker your_app:app
```

3. Access metrics at `/metrics` endpoint.

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


## Development

1. Clone the repository:
```bash
git clone https://github.com/agent-hellboy/gunicorn-prometheus-exporter.git
cd gunicorn-prometheus-exporter
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. Run tests:
```bash
pytest
```

## License

MIT License - Prince Roshan

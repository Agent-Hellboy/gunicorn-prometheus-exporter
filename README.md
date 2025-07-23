# Gunicorn Prometheus Exporter

[![CI](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml)

[![codecov](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter/graph/badge.svg?token=NE7JS4FZHC)](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter)

[![PyPI - Version](https://img.shields.io/pypi/v/gunicorn-prometheus-exporter.svg)](https://pypi.org/project/gunicorn-prometheus-exporter/)

A Gunicorn worker plugin that exports Prometheus metrics to monitor worker performance, including memory usage, CPU usage, request durations, and error tracking (trying to replace https://docs.gunicorn.org/en/stable/instrumentation.html with extra info). It also aims to replace request-level tracking, such as the number of requests made to a particular endpoint, for any framework (e.g., Flask, Django, and others) that conforms to the WSGI specification.
## Features

- Exports Prometheus metrics for Gunicorn workers
- Tracks worker memory usage, CPU usage, and uptime
- Monitors request durations and counts
- Tracks failed requests and error handling
- Supports worker state monitoring (running, quit, abort)
- Master process metrics for worker management
- Easy integration with existing Prometheus setups

## Installation

### Stable
```bash 
pip install gunicorn-prometheus-exporter==0.1.0
```

### Development
```bash
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter
cd gunicorn-prometheus-exporter
pip install .
```

## Usage

1. Install the package
2. Configure Gunicorn to use the plugin:

```bash
gunicorn --config gunicorn.conf.py your_app:app
```

## Available Metrics

### Worker Metrics

Each worker is identified by a unique worker ID in the format `worker_<age>_<timestamp>`. This ensures:
- Unique identification across worker restarts
- Easy tracking of worker lifecycle
- Consistent metrics across worker replacements

Available worker metrics:

- `gunicorn_worker_requests`: Total number of requests handled by each worker
  - Labels: `worker_id` (format: `worker_<age>_<timestamp>`)
- `gunicorn_worker_request_duration_seconds`: Request duration in seconds
  - Labels: `worker_id`
  - Buckets: 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, +Inf
- `gunicorn_worker_memory_bytes`: Memory usage of each worker process
  - Labels: `worker_id`
- `gunicorn_worker_cpu_percent`: CPU usage of each worker process
  - Labels: `worker_id`
- `gunicorn_worker_uptime_seconds`: Uptime of each worker process
  - Labels: `worker_id`
- `gunicorn_worker_failed_requests`: Total number of failed requests
  - Labels: `worker_id`, `method`, `endpoint`, `error_type`
- `gunicorn_worker_error_handling`: Total number of errors handled
  - Labels: `worker_id`, `method`, `endpoint`, `error_type`
- `gunicorn_worker_state`: Current state of the worker
  - Labels: `worker_id`, `state`, `timestamp`
  - Values: 1 (running), 0 (stopped)

### Example PromQL Queries

Here are some useful PromQL queries for monitoring your Gunicorn workers:

```promql
# Current active workers and their uptime
gunicorn_worker_uptime_seconds{worker_id=~"worker_.*"}

# Worker memory usage (in MB)
gunicorn_worker_memory_bytes{worker_id=~"worker_.*"} / 1024 / 1024

# Request rate per worker (requests per second)
rate(gunicorn_worker_requests{worker_id=~"worker_.*"}[5m])

# Average request duration per worker
rate(gunicorn_worker_request_duration_seconds_sum{worker_id=~"worker_.*"}[5m]) 
/ 
rate(gunicorn_worker_request_duration_seconds_count{worker_id=~"worker_.*"}[5m])

# Error rate per worker
rate(gunicorn_worker_failed_requests{worker_id=~"worker_.*"}[5m])

# CPU usage per worker
gunicorn_worker_cpu_percent{worker_id=~"worker_.*"}

# Worker state changes
changes(gunicorn_worker_state{worker_id=~"worker_.*"}[5m])
```

### Master Process Metrics

- `gunicorn_master_worker_restart_total`: Total number of worker restarts
  - Labels: `reason` (e.g., "restart", "timeout", "error")

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

## Configuration

### Prometheus UI Setup

To visualize the metrics using Prometheus UI:

1. Create a `prometheus.yml` configuration file:
```yaml
global:
  scrape_interval: 15s

# Scrape our example exporter
scrape_configs:
  - job_name: 'gunicorn-prometheus-exporter'         
    metrics_path: '/metrics'       
    static_configs:
      - targets: ['127.0.0.1:9090'] # our example exporter
```

2. Run Prometheus using Docker:
```bash
docker run -d \
  --name prometheus \
  --network host \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
  prom/prometheus
```

3. Access Prometheus UI at `http://localhost:9090` to:
   - View metrics in the Graph interface
   - Use PromQL queries to analyze worker performance
   - Create graphs and dashboards
   - Set up alerts based on metric thresholds

### Gunicorn Configuration

Create a `gunicorn.conf.py` file with the following configuration:

```python
from prometheus_client import start_http_server, multiprocess
from gunicorn_prometheus_exporter.metrics import create_master_registry

# ———————————————————————————————————————————————————————————————————————————————————
# Hook to start a multiprocess‐aware Prometheus metrics server when Gunicorn is ready
# ———————————————————————————————————————————————————————————————————————————————————
def when_ready(server):
    mp_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if not mp_dir:
        logging.warning("PROMETHEUS_MULTIPROC_DIR not set; skipping metrics server")
        return

    # Use the master registry factory for reading and serving metrics
    registry = create_master_registry()

    # Serve that registry on HTTP
    start_http_server(port, registry=registry)
```


# —————————————————————————————————————————————————————————————————————————————
# Hook to mark dead workers so their metric files get merged & cleaned up
# —————————————————————————————————————————————————————————————————————————————
def child_exit(server, worker):
    try:
        multiprocess.mark_process_dead(worker.pid)
    except Exception:
        logging.exception(f"Failed to mark process {worker.pid} dead in multiprocess collector")

```

### Environment Variables

The exporter supports the following configuration options:

- `PROMETHEUS_MULTIPROC_DIR`: Directory for multiprocess metrics (default: `/tmp/prometheus`)
- `PROMETHEUS_METRICS_PORT`: Port for metrics endpoint (default: 8000)

## License

MIT License - Prince Roshan


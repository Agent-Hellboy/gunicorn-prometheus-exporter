# Gunicorn Prometheus Exporter

[![CI](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml)

[![codecov](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter/graph/badge.svg?token=NE7JS4FZHC)](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter)

[![PyPI - Version](https://img.shields.io/pypi/v/gunicorn-prometheus-exporter.svg)](https://pypi.org/project/gunicorn-prometheus-exporter/)

A Gunicorn worker plugin that exports Prometheus metrics to monitor worker performance, including memory usage, CPU usage, request durations, and error tracking (trying to replace https://docs.gunicorn.org/en/stable/instrumentation.html with extra info). It also aims to replace request-level tracking, such as the number of requests made to a particular endpoint, for any framework (e.g., Flask, Django, and others) that conforms to the WSGI specification.
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

The exporter provides master-level metrics for monitoring Gunicorn's master process behavior and worker management:

- `gunicorn_master_worker_restart_total`: Total number of worker restarts triggered by various signals
  - Labels: `reason` - The signal or reason that triggered the restart:
    - `"hup"` - SIGHUP signal (configuration reload)
    - `"chld"` - SIGCHLD signal (worker process died)
    - `"ttin"` - SIGTTIN signal (increase number of workers)
    - `"ttou"` - SIGTTOU signal (decrease number of workers)
    - `"usr1"` - SIGUSR1 signal (reopen log files)
    - `"usr2"` - SIGUSR2 signal (graceful restart)

To enable master process metrics, use the PrometheusMaster class in your Gunicorn configuration:

```python
# In your gunicorn.conf.py
import gunicorn.arbiter
from gunicorn_prometheus_exporter.master import PrometheusMaster

# Replace the default Gunicorn Arbiter with our PrometheusMaster
# This allows us to capture master-level metrics like signal handling
gunicorn.arbiter.Arbiter = PrometheusMaster

# Use our custom worker class for worker metrics
worker_class = "gunicorn_prometheus_exporter.plugin.PrometheusWorker"
```

#### Example Master Metrics Usage

```bash
# Check master metrics
curl http://localhost:9090/metrics | grep gunicorn_master_worker_restart

# Trigger signals to test master metrics
kill -HUP <master_pid>    # Should increment hup metric
kill -TTIN <master_pid>   # Should increment ttin metric  
kill -TTOU <master_pid>   # Should increment ttou metric
```

#### Master Metrics PromQL Queries

```promql
# Total worker restarts by reason
gunicorn_master_worker_restart_total

# Worker restart rate by reason (restarts per minute)
rate(gunicorn_master_worker_restart_total[5m]) * 60

# Most common restart reasons
topk(3, sum by (reason) (gunicorn_master_worker_restart_total))

# Alert on high restart rate
rate(gunicorn_master_worker_restart_total{reason="chld"}[5m]) > 0.1
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
import logging
import os

import gunicorn.arbiter
from prometheus_client import start_http_server

# Import our custom master to replace the default Gunicorn Arbiter
from gunicorn_prometheus_exporter.master import PrometheusMaster

# —————————————————————————————————————————————————————————————————————————————
# Hook to start a multiprocess‐aware Prometheus metrics server when Gunicorn is ready
# —————————————————————————————————————————————————————————————————————————————
def when_ready(server):
    mp_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if not mp_dir:
        logging.warning("PROMETHEUS_MULTIPROC_DIR not set; skipping metrics server")
        return

    port = int(os.environ.get("PROMETHEUS_METRICS_PORT", 9090))
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Prometheus multiprocess metrics server on :{port}")

    # Use the existing registry from our metrics module
    from gunicorn_prometheus_exporter.metrics import registry
    
    # Serve that registry on HTTP
    start_http_server(port, registry=registry)
    
    logger.info("Metrics server started successfully - includes both worker and master metrics")

# —————————————————————————————————————————————————————————————————————————————
# Hook to mark dead workers so their metric files get merged & cleaned up
# —————————————————————————————————————————————————————————————————————————————
def child_exit(server, worker):
    try:
        from prometheus_client import multiprocess
        multiprocess.mark_process_dead(worker.pid)
    except Exception:
        logging.exception(f"Failed to mark process {worker.pid} dead in multiprocess collector")

# —————————————————————————————————————————————————————————————————————————————
# Gunicorn configuration
# —————————————————————————————————————————————————————————————————————————————
bind = "127.0.0.1:8080"
workers = 2
worker_class = "gunicorn_prometheus_exporter.plugin.PrometheusWorker"

# Replace the default Gunicorn Arbiter with our PrometheusMaster
gunicorn.arbiter.Arbiter = PrometheusMaster
```

### Environment Variables

The exporter supports the following configuration options:

- `PROMETHEUS_MULTIPROC_DIR`: Directory for multiprocess metrics (default: `/tmp/prometheus`)
- `PROMETHEUS_METRICS_PORT`: Port for metrics endpoint (default: 9090)

### Testing Master Metrics

To verify that master metrics are working correctly:

1. Start Gunicorn with the configuration:
```bash
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
gunicorn --config gunicorn.conf.py your_app:app
```

2. Check that master metrics are exposed:
```bash
curl http://localhost:9090/metrics | grep gunicorn_master
```

3. Test signal handling by sending signals to the master process:
```bash
# Find the master process ID
ps aux | grep gunicorn | grep -v grep

# Send SIGHUP to test configuration reload
kill -HUP <master_pid>

# Check that the metric was incremented
curl http://localhost:9090/metrics | grep gunicorn_master_worker_restart
```

You should see the `gunicorn_master_worker_restart_total{reason="hup"}` metric increment after sending the signal.

## License

MIT License - Prince Roshan


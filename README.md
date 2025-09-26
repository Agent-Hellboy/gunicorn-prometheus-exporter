# Gunicorn Prometheus Exporter

[![CI](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-hellboy/gunicorn-prometheus-exporter/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter/graph/badge.svg?token=NE7JS4FZHC)](https://codecov.io/gh/Agent-Hellboy/gunicorn-prometheus-exporter)
[![PyPI - Version](https://img.shields.io/pypi/v/gunicorn-prometheus-exporter.svg)](https://pypi.org/project/gunicorn-prometheus-exporter/)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://agent-hellboy.github.io/gunicorn-prometheus-exporter)
[![PyPI Downloads](https://static.pepy.tech/badge/gunicorn-prometheus-exporter)](https://pepy.tech/projects/gunicorn-prometheus-exporter)

A comprehensive Prometheus metrics exporter for Gunicorn WSGI servers with support for multiple worker types and advanced monitoring capabilities, featuring innovative Redis-based storage and advanced signal handling. This Gunicorn worker plugin exports Prometheus metrics to monitor worker performance, including memory usage, CPU usage, request durations, and error tracking (trying to replace <https://docs.gunicorn.org/en/stable/instrumentation.html> with extra info). It also aims to replace request-level tracking, such as the number of requests made to a particular endpoint, for any framework (e.g., Flask, Django, and others) that conforms to the WSGI specification.

## Redis Storage Architecture

### Separating Storage from Compute

I've extended the Prometheus Python client to support **Redis-based storage** as an alternative to traditional multiprocess files. This architectural innovation provides several key benefits:

#### **Traditional Approach (File-Based)**

- Metrics stored in local files (`/tmp/prometheus_multiproc/`)
- Storage and compute are coupled on the same server
- Limited scalability across multiple instances
- File I/O overhead for metrics collection

#### **New Redis Storage Approach**

- Metrics stored directly in Redis (`gunicorn:*:metric:*` keys)
- **Storage and compute are completely separated**
- Shared metrics across multiple Gunicorn instances
- No local files created - pure Redis storage
- Better performance and scalability
- **Direct Redis integration** - no forwarding layer needed

### **Key Benefits:**

| Feature                | File-Based    | Redis Storage    |
| ---------------------- | ------------- | ---------------- |
| **Storage Location**   | Local files   | Redis server     |
| **Scalability**        | Single server | Multiple servers |
| **File I/O**           | High overhead | No file I/O      |
| **Shared Metrics**     | No            | Yes              |
| **Storage Separation** | Coupled       | Separated        |

### **Use Cases:**

- **Microservices Architecture**: Multiple services sharing metrics
- **Container Orchestration**: Kubernetes pods with shared Redis
- **High Availability**: Metrics survive server restarts
- **Cost Optimization**: Separate storage and compute resources

## Features

- **Worker Metrics**: Memory, CPU, request durations, error tracking
- **Master Process Intelligence**: Signal tracking, restart analytics
- **Multiprocess Support**: Full Prometheus multiprocess compatibility
- **Redis Storage**: Store metrics directly in Redis (no files created)
- **Zero Configuration**: Works out-of-the-box with minimal setup
- **Production Ready**: Retry logic, error handling, health monitoring

## Quick Start

### Installation

**Basic installation (sync and thread workers only):**

```bash
pip install gunicorn-prometheus-exporter
```

**With async worker support:**

```bash
# Install with all async worker types
pip install gunicorn-prometheus-exporter[async]

# Or install specific worker types
pip install gunicorn-prometheus-exporter[eventlet]  # For eventlet workers
pip install gunicorn-prometheus-exporter[gevent]    # For gevent workers
```

**With Redis storage:**

```bash
pip install gunicorn-prometheus-exporter[redis]
```

**Complete installation (all features):**

```bash
pip install gunicorn-prometheus-exporter[all]
```

### Basic Usage

Create a Gunicorn config file (`gunicorn.conf.py`):

```python
# Basic configuration
bind = "0.0.0.0:8000"
workers = 2

# Prometheus exporter (sync worker)
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Optional: Custom hooks for advanced setup
def when_ready(server):
    from gunicorn_prometheus_exporter.hooks import default_when_ready
    default_when_ready(server)
```

### Supported Worker Types

The exporter supports all major Gunicorn worker types:

| Worker Class               | Concurrency Model | Use Case                               | Installation                                         |
| -------------------------- | ----------------- | -------------------------------------- | ---------------------------------------------------- |
| `PrometheusWorker`         | Pre-fork (sync)   | Simple, reliable, 1 request per worker | `pip install gunicorn-prometheus-exporter`           |
| `PrometheusThreadWorker`   | Threads           | I/O-bound apps, better concurrency     | `pip install gunicorn-prometheus-exporter`           |
| `PrometheusEventletWorker` | Greenlets         | Async I/O with eventlet                | `pip install gunicorn-prometheus-exporter[eventlet]` |
| `PrometheusGeventWorker`   | Greenlets         | Async I/O with gevent                  | `pip install gunicorn-prometheus-exporter[gevent]`   |

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

The Gunicorn Prometheus Exporter provides comprehensive metrics for monitoring both worker processes and the master process. All metrics include appropriate labels for detailed analysis.

### Worker Metrics

#### Request Metrics
- **`gunicorn_worker_requests_total`** - Total number of requests handled by each worker
  - Labels: `worker_id`
  - Type: Counter

- **`gunicorn_worker_request_duration_seconds`** - Request duration histogram
  - Labels: `worker_id`
  - Type: Histogram
  - Buckets: 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, +Inf

- **`gunicorn_worker_request_size_bytes`** - Request size histogram
  - Labels: `worker_id`
  - Type: Histogram
  - Buckets: 1KB, 4KB, 16KB, 64KB, 256KB, 1MB, 4MB, +Inf

- **`gunicorn_worker_response_size_bytes`** - Response size histogram
  - Labels: `worker_id`
  - Type: Histogram
  - Buckets: 1KB, 4KB, 16KB, 64KB, 256KB, 1MB, 4MB, +Inf

#### Error Metrics
- **`gunicorn_worker_failed_requests`** - Total number of failed requests
  - Labels: `worker_id`, `method`, `endpoint`, `error_type`
  - Type: Counter

- **`gunicorn_worker_error_handling`** - Total number of errors handled
  - Labels: `worker_id`, `method`, `endpoint`, `error_type`
  - Type: Counter

#### System Metrics
- **`gunicorn_worker_memory_bytes`** - Memory usage per worker
  - Labels: `worker_id`
  - Type: Gauge

- **`gunicorn_worker_cpu_percent`** - CPU usage per worker
  - Labels: `worker_id`
  - Type: Gauge

- **`gunicorn_worker_uptime_seconds`** - Worker uptime
  - Labels: `worker_id`
  - Type: Gauge

#### State Metrics
- **`gunicorn_worker_state`** - Current state of the worker
  - Labels: `worker_id`, `state`, `timestamp`
  - Type: Gauge
  - Values: 1=running, 0=stopped

#### Restart Metrics
- **`gunicorn_worker_restart_total`** - Total worker restarts by reason
  - Labels: `worker_id`, `reason`
  - Type: Counter

- **`gunicorn_worker_restart_count_total`** - Worker restarts by type and reason
  - Labels: `worker_id`, `restart_type`, `reason`
  - Type: Counter

### Master Metrics

#### Restart Metrics
- **`gunicorn_master_worker_restart_total`** - Total worker restarts by reason
  - Labels: `reason`
  - Type: Counter
  - Common reasons: `hup`, `usr1`, `usr2`, `ttin`, `ttou`, `chld`, `int`

- **`gunicorn_master_worker_restart_count_total`** - Worker restarts by worker and reason
  - Labels: `worker_id`, `reason`, `restart_type`
  - Type: Counter

### Metric Labels Explained

#### Worker Labels
- **`worker_id`**: Unique identifier for each worker process
- **`method`**: HTTP method (GET, POST, PUT, DELETE, etc.)
- **`endpoint`**: Request endpoint/path
- **`error_type`**: Type of error (exception class name)
- **`state`**: Worker state (running, stopped, etc.)
- **`timestamp`**: Unix timestamp of state change
- **`reason`**: Reason for restart (signal name or error type)
- **`restart_type`**: Type of restart (signal, error, manual, etc.)

#### Master Labels
- **`reason`**: Signal or reason that triggered the restart
  - `hup`: HUP signal (reload configuration)
  - `usr1`: USR1 signal (reopen log files)
  - `usr2`: USR2 signal (upgrade on the fly)
  - `ttin`: TTIN signal (increase worker count)
  - `ttou`: TTOU signal (decrease worker count)
  - `chld`: CHLD signal (child process status change)
  - `int`: INT signal (interrupt/Ctrl+C)

### Example Queries

#### Basic Monitoring
```promql
# Total requests across all workers
sum(gunicorn_worker_requests_total)

# Average request duration
rate(gunicorn_worker_request_duration_seconds_sum[5m]) / rate(gunicorn_worker_request_duration_seconds_count[5m])

# Memory usage per worker
gunicorn_worker_memory_bytes

# CPU usage per worker
gunicorn_worker_cpu_percent
```

#### Error Analysis
```promql
# Failed requests by endpoint
sum by (endpoint) (rate(gunicorn_worker_failed_requests[5m]))

# Error rate by worker
sum by (worker_id) (rate(gunicorn_worker_error_handling[5m]))
```

#### Restart Monitoring
```promql
# Worker restarts by reason
sum by (reason) (rate(gunicorn_master_worker_restart_total[5m]))

# Restart frequency per worker
sum by (worker_id) (rate(gunicorn_worker_restart_total[5m]))
```

#### Performance Analysis
```promql
# Request size distribution
histogram_quantile(0.95, rate(gunicorn_worker_request_size_bytes_bucket[5m]))

# Response time percentiles
histogram_quantile(0.99, rate(gunicorn_worker_request_duration_seconds_bucket[5m]))
```


## Examples

See the `example/` directory for complete working examples with all worker types:

### Basic Examples

- `gunicorn_simple.conf.py`: Basic sync worker setup
- `gunicorn_thread_worker.conf.py`: Threaded workers for I/O-bound apps
- `gunicorn_redis_integration.conf.py`: Redis storage setup (no files)

### Async Worker Examples

- `gunicorn_eventlet_async.conf.py`: Eventlet workers with async app
- `gunicorn_gevent_async.conf.py`: Gevent workers with async app

### Test Applications

- `app.py`: Simple Flask app for sync/thread workers
- `async_app.py`: Async-compatible Flask app for async workers

Run any example with:

```bash
cd example
gunicorn --config gunicorn_simple.conf.py app:app
```

## Testing Status

All worker types have been thoroughly tested and are production-ready:

| Worker Type         | Status  | Metrics     | Master Signals  | Load Distribution |
| ------------------- | ------- | ----------- | --------------- | ----------------- |
| **Sync Worker**     | Working | All metrics | HUP, USR1, CHLD | Balanced          |
| **Thread Worker**   | Working | All metrics | HUP, USR1, CHLD | Balanced          |
| **Eventlet Worker** | Working | All metrics | HUP, USR1, CHLD | Balanced          |
| **Gevent Worker**   | Working | All metrics | HUP, USR1, CHLD | Balanced          |

All async workers require their respective dependencies:

- Eventlet: `pip install eventlet`
- Gevent: `pip install gevent`

## Configuration

### Environment Variables

| Variable                   | Default                  | Description                                               |
| -------------------------- | ------------------------ | --------------------------------------------------------- |
| `PROMETHEUS_METRICS_PORT`  | `9091`                   | Port for metrics endpoint                                 |
| `PROMETHEUS_BIND_ADDRESS`  | `0.0.0.0`                | Bind address for metrics                                  |
| `GUNICORN_WORKERS`         | `1`                      | Number of workers                                         |
| `PROMETHEUS_MULTIPROC_DIR` | Auto-generated           | Multiprocess directory                                    |
| `REDIS_ENABLED`            | `false`                  | Enable Redis storage (no files created)                   |
| `REDIS_HOST`               | `127.0.0.1`              | Redis server hostname                                     |
| `REDIS_PORT`               | `6379`                   | Redis server port                                         |
| `REDIS_DB`                 | `0`                      | Redis database number                                     |
| `REDIS_PASSWORD`           | *(none)*                 | Redis password (optional)                                 |
| `REDIS_KEY_PREFIX`         | `gunicorn`               | Prefix for Redis keys                                     |

### Gunicorn Hooks

```python
# Basic setup
from gunicorn_prometheus_exporter.hooks import default_when_ready

def when_ready(server):
    default_when_ready(server)

# With Redis storage (no files created)
from gunicorn_prometheus_exporter.hooks import redis_when_ready

def when_ready(server):
    redis_when_ready(server)
```

## System Testing

I provide comprehensive system tests to validate the complete functionality of the Gunicorn Prometheus Exporter with Redis integration.

### Quick Test (Local Development)

```bash
# Make sure Redis is running
brew services start redis  # macOS
sudo systemctl start redis  # Linux

# Run quick test
cd system-test
make quick-test
```

### Full System Test (CI/CD)

```bash
# Complete automated test (installs everything)
cd system-test
make system-test
```

### Using Make Commands

```bash
cd system-test
make quick-test    # Fast local testing
make system-test   # Full automated testing
make install       # Install dependencies
make clean         # Clean up
```

**Test Coverage**:

- ✅ Redis integration and storage
- ✅ Multi-worker Gunicorn setup
- ✅ All metric types (counters, gauges, histograms)
- ✅ Request processing and metrics capture
- ✅ Signal handling and graceful shutdown
- ✅ CI/CD automation

See [`system-test/README.md`](system-test/README.md) for detailed documentation.

## Contributing

Contributions are welcome! Please see our [contributing guide](https://agent-hellboy.github.io/gunicorn-prometheus-exporter/contributing/) for details.

### Development Setup

```bash
# Install dependencies
cd system-test
make install

# Run tests
make quick-test
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

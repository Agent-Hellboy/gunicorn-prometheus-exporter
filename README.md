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

### **Core Functionality**
- **Comprehensive Worker Metrics**: Real-time monitoring of Gunicorn worker performance
  - **Resource Monitoring**: Memory usage, CPU usage, and uptime tracking
  - **Request Analytics**: Request durations with histogram buckets and total counts
  - **Error Tracking**: Failed requests and error handling with detailed labels (Note: Currently not implemented - framework-level error tracking may be better handled by application-specific exporters)
  - **State Management**: Worker state monitoring (running, quit, abort, error)
  - **Performance Insights**: Request throughput and latency analysis

- **Master Process Intelligence**: Advanced master process metrics for worker lifecycle management
  - **Signal Tracking**: Automatic capture of all Gunicorn signals (SIGHUP, SIGCHLD, SIGTTIN, SIGTTOU, SIGUSR1, SIGUSR2)
  - **Restart Analytics**: Worker restart tracking with signal-specific reasons and patterns
  - **Process Management**: Real-time monitoring of worker creation, termination, and health

### **Developer Experience**
- **Zero-Configuration Setup**: Works out-of-the-box with minimal configuration
  - **Automatic Integration**: No manual endpoint creation or complex setup required
  - **Pre-built Hooks**: Ready-to-use Gunicorn hook functions for easy integration
  - **Flexible Configuration**: Environment variables and Python configuration support
  - **Example Configurations**: Multiple working examples for different use cases

- **Production-Ready Features**
  - **Multiprocess Support**: Full compatibility with Prometheus multiprocess collectors
  - **Retry Logic**: Built-in retry mechanisms for port conflicts during USR2 upgrades
  - **Error Handling**: Comprehensive error handling and graceful degradation
  - **Logging Integration**: Structured logging with configurable levels
  - **Health Monitoring**: Built-in health checks and status reporting

### **Advanced Capabilities**
- **Redis Integration**: Forward metrics to Redis for external storage and aggregation
  - **Dual-Interval Architecture**: Efficient collection (1s) and forwarding (10s) intervals
  - **Status Tracking**: Comprehensive monitoring of forwarder health and performance
  - **Error Recovery**: Automatic retry mechanisms and connection management
  - **Data Persistence**: Historical metrics storage with configurable retention

- **Extensibility & Customization**
  - **Hook System**: Extensible hook architecture for custom integrations
  - **Custom Metrics**: Framework for adding application-specific metrics
  - **Configuration Management**: Centralized configuration with validation
  - **Plugin Architecture**: Modular design for easy extension and customization

### **Monitoring & Observability**
- **Prometheus Native**: Full compatibility with Prometheus ecosystem
  - **Standard Metrics**: Follows Prometheus naming conventions and best practices
  - **Rich Labels**: Detailed labeling for precise filtering and aggregation
  - **Histogram Buckets**: Configurable histogram buckets for latency analysis
  - **Counter Precision**: Accurate request and error counting with proper increments

- **Operational Excellence**
  - **Signal Handling**: Robust signal processing for graceful restarts and reloads
  - **Resource Efficiency**: Minimal overhead with optimized metric collection
  - **Scalability**: Designed for high-traffic applications with multiple workers
  - **Reliability**: Production-tested with comprehensive error handling

## Quick Start

### 1. Installation

```bash
pip install gunicorn-prometheus-exporter
```

### 2. Basic Usage

Create a Gunicorn config file (`gunicorn.conf.py`):
See `./example/gunicorn_simple.conf.py` for a complete working example.

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

## How It Works

1. **Import Patching**: When imported, the module patches Gunicorn's `Arbiter` class with `PrometheusMaster`
2. **Worker Plugin**: Uses custom `PrometheusWorker` class to collect worker metrics
3. **Signal Handling**: `PrometheusMaster` overrides signal handlers to track master signals
4. **Multiprocess**: Uses Prometheus multiprocess mode for shared metrics collection
5. **HTTP Server**: Starts metrics server in `when_ready` hook

## Key Components

- **`PrometheusMaster`**: Extends Gunicorn's Arbiter for signal tracking
- **`PrometheusWorker`**: Custom worker class for request/resource metrics
- **`metrics.py`**: Defines all Prometheus metrics with proper naming
- **`hooks.py`**: Pre-built Gunicorn hook functions for easy integration
- **`forwarder/`**: Redis-based metrics forwarding system
- **`gunicorn.conf.py`**: Configuration with hooks for metrics server

## Gunicorn Hooks Integration

The exporter provides pre-built Gunicorn hook functions that can be easily imported and used in your configuration files. This eliminates the need to write custom hook logic and ensures consistent behavior across different setups.

### Available Hooks

#### **`default_on_starting`**
Initializes master metrics and ensures the multiprocess directory exists.

#### **`default_when_ready`**
Sets up Prometheus multiprocess metrics collection and starts the HTTP server with retry logic for port conflicts.

#### **`default_worker_int`**
Handles worker interrupt signals.

#### **`default_on_exit`**
Performs cleanup when the server shuts down.

#### **`redis_when_ready`**
Combines Prometheus setup with Redis forwarding functionality. Includes the same retry logic as `default_when_ready`.

### Usage Examples

#### **Basic Setup (Prometheus Only)**
```python
# gunicorn.conf.py
from gunicorn_prometheus_exporter.hooks import (
    default_on_starting,
    default_when_ready,
    default_worker_int,
    default_on_exit,
)

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Use pre-built hooks
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
```

#### **Redis Forwarding Setup**
```python
# gunicorn.conf.py
from gunicorn_prometheus_exporter.hooks import (
    default_on_starting,
    redis_when_ready,
    default_worker_int,
    default_on_exit,
)

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Environment variables
import os
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("CLEANUP_DB_FILES", "false")

# Use Redis-enabled hook
when_ready = redis_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
```

#### **Custom Hook Extension**
```python
# gunicorn.conf.py
from gunicorn_prometheus_exporter.hooks import default_when_ready

def custom_when_ready(server):
    # Call the default implementation
    default_when_ready(server)

    # Add custom logic
    print("Custom initialization complete!")

# Use custom hook
when_ready = custom_when_ready
```

### Hook Features

- **Retry Logic**: Both `default_when_ready` and `redis_when_ready` include retry logic for port conflicts during USR2 upgrades
- **Consistent Logging**: All hooks use proper logging with configurable levels
- **Error Handling**: Comprehensive error handling and graceful degradation
- **Shared Setup**: Common Prometheus setup logic is shared between hooks to eliminate duplication

## Redis Metrics Forwarding

**⚠️ Important Note**: The Redis forwarding functionality is currently of limited use without a custom collector implementation. While metrics are successfully pushed to Redis, there is no built-in way to expose them via a `/metrics` endpoint. This feature will be fully functional once a custom Prometheus collector and WSGI server are implemented to read from Redis and serve metrics.

The exporter includes a Redis-based forwarding system that can push collected Prometheus metrics to a Redis instance for external storage and aggregation.

### Forwarder Architecture

#### **`BaseForwarder`**
Abstract base class that provides the core forwarding loop and metric generation logic.

#### **`RedisForwarder`**
Implements Redis-specific forwarding functionality:
- Connects to Redis using configurable host, port, and authentication
- Pushes metrics with configurable key prefixes
- Supports dual-interval approach (collect every 1s, forward every 10s)
- Includes comprehensive status tracking and error handling

#### **`ForwarderManager`**
Manages multiple forwarder instances and provides centralized control.

### Configuration

#### **Environment Variables**
```bash
# Enable Redis forwarding
export REDIS_ENABLED=true

# Redis connection settings
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=your_password  # Optional

# Forwarding settings
export REDIS_KEY_PREFIX=gunicorn:metrics
export REDIS_FORWARD_INTERVAL=10
export REDIS_COLLECT_INTERVAL=1

# Important: Prevent DB file cleanup when using Redis
export CLEANUP_DB_FILES=false
```

#### **Python Configuration**
```python
import os

# Redis settings
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "127.0.0.1")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_KEY_PREFIX", "gunicorn:metrics")
os.environ.setdefault("CLEANUP_DB_FILES", "false")
```

### Usage

**⚠️ Current Limitation**: The Redis forwarder pushes metrics to Redis but there's no built-in collector to serve them. You can view the metrics in Redis directly, but they cannot be scraped by Prometheus until a custom collector is implemented.

#### **Automatic Startup**
When using the `redis_when_ready` hook, the Redis forwarder starts automatically if Redis is enabled:

```python
from gunicorn_prometheus_exporter.hooks import redis_when_ready

# The forwarder starts automatically when this hook runs
when_ready = redis_when_ready
```

#### **Manual Control**
```python
from gunicorn_prometheus_exporter import start_redis_forwarder

# Start the forwarder manually
start_redis_forwarder()
```

### Redis Data Structure

Metrics are stored in Redis with the following structure:

```
gunicorn:metrics:latest          # Latest metrics snapshot
gunicorn:metrics:metadata        # Forwarder metadata
gunicorn:metrics:{timestamp}     # Historical snapshots
```

#### **Example Redis Commands**
```bash
# View latest metrics
redis-cli get "gunicorn:metrics:latest"

# View forwarder status
redis-cli get "gunicorn:metrics:metadata"

# List all metric keys
redis-cli keys "gunicorn:metrics:*"
```

### Forwarder Status

The forwarder provides comprehensive status information:

```python
from gunicorn_prometheus_exporter.forwarder.manager import get_forwarder_manager

manager = get_forwarder_manager()
status = manager.get_status()

print(f"Running forwarders: {status['running_count']}")
print(f"Total forwards: {status['total_forwards']}")
print(f"Last forward: {status['last_forward_time']}")
```

### Dual-Interval Approach

The forwarder uses a dual-interval approach for optimal performance:

- **Collection Interval** (1 second): Collects metrics from the multiprocess directory
- **Forwarding Interval** (10 seconds): Pushes aggregated metrics to Redis

This approach ensures:
- Frequent metric collection for accuracy
- Efficient Redis usage with batched updates
- Reduced network overhead
- Better performance during high-traffic periods

### Error Handling

The forwarder includes robust error handling:

- **Connection Failures**: Automatic retry with exponential backoff
- **Redis Errors**: Graceful degradation with detailed logging
- **Metric Generation Errors**: Fallback mechanisms and error reporting
- **Status Tracking**: Comprehensive monitoring of forwarder health

### Monitoring

Monitor the forwarder through:

1. **Logs**: Detailed logging of all operations
2. **Status API**: Programmatic access to forwarder status
3. **Redis Keys**: Direct inspection of forwarded data
4. **Metrics**: Forwarder performance metrics in Prometheus format

**⚠️ Note**: While you can monitor the forwarder's operation and view metrics in Redis, there is currently no way to expose these Redis-stored metrics to Prometheus for scraping. The metrics are stored but not accessible via HTTP endpoint until a custom collector is implemented.


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

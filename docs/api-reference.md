# API Reference

Complete reference for the Gunicorn Prometheus Exporter API, including worker classes, hooks, and configuration options.

## 🏗️ Redis Backend Architecture

### Overview

The Redis backend provides a complete storage implementation that extends the Prometheus Python client to support distributed metrics storage. This implementation follows Prometheus multiprocess specifications while providing enhanced scalability and separation of concerns.

### Core Components

#### RedisStorageManager

The main service layer for Redis storage management.

```python
from gunicorn_prometheus_exporter.backend.service import RedisStorageManager

# Create Redis storage manager
manager = RedisStorageManager(
    redis_host="localhost",
    redis_port=6379,
    redis_db=0,
    key_prefix="gunicorn",
    ttl_seconds=300
)

# Setup Redis storage
manager.setup()

# Get Redis-based collector
collector = manager.get_collector()

# Teardown when done
manager.teardown()
```

**Methods:**

- `setup()` - Initialize Redis storage backend
- `get_collector()` - Returns RedisMultiProcessCollector instance
- `get_client()` - Returns RedisStorageClient instance
- `teardown()` - Clean up Redis resources

#### RedisStorageClient

Main client for Redis operations.

```python
from gunicorn_prometheus_exporter.backend.core.client import RedisStorageClient

# Create Redis storage client
client = RedisStorageClient(redis_client, key_prefix="gunicorn")

# Get value class for metrics
value_class = client.get_value_class()
```

**Key Features:**

- Connection management with pooling
- Structured key generation with process information
- Value operations for metric data
- Metadata management
- TTL support for automatic cleanup

#### RedisStorageDict

Storage abstraction implementing Prometheus multiprocess protocols.

```python
from gunicorn_prometheus_exporter.backend.core.client import RedisStorageDict

# Create storage dict
storage = RedisStorageDict(redis_client, key_prefix="gunicorn")

# Read metric value
value, timestamp = storage.read_value("metric_key", "gauge", "all")

# Write metric value
storage.write_value("metric_key", 42.5, 1640995200.123, "gauge", "all")
```

**Methods:**

- `read_value(key, metric_type, multiprocess_mode)` - Read metric value and timestamp
- `write_value(key, value, timestamp, metric_type, multiprocess_mode)` - Write metric value
- `read_all_values()` - Read all metrics from Redis
- `cleanup_process_keys()` - Clean up keys for specific process

#### RedisMultiProcessCollector

Collector that aggregates metrics from Redis across multiple processes.

```python
from gunicorn_prometheus_exporter.backend.core.collector import RedisMultiProcessCollector

# Create collector
collector = RedisMultiProcessCollector(registry, redis_client, key_prefix="gunicorn")

# Collect metrics
for metric in collector.collect():
    print(f"Metric: {metric.name}")
```

**Key Features:**

- Metric aggregation across processes
- Process discovery via Redis key scanning
- Multiprocess mode handling
- Label preservation
- Streaming collection for memory efficiency

#### RedisValue

Redis-backed value implementation for individual metrics.

```python
from gunicorn_prometheus_exporter.backend.core.values import RedisValue

# Create Redis value
value = RedisValue("counter", "metric_name", {}, {}, "help_text",
                  redis_client=redis_client, redis_key_prefix="gunicorn")

# Increment counter
value.inc(1.0)

# Set gauge value
value.set(42.5)

# Get current value
current_value = value.get()
```

**Methods:**

- `inc(amount)` - Increment counter value
- `set(value)` - Set gauge value
- `get()` - Get current value
- `get_timestamp()` - Get last update timestamp
- `set_exemplar(exemplar)` - Set exemplar data

### Redis Key Architecture

#### Key Structure

```
gunicorn:{metric_type}_{mode}:{pid}:{data_type}:{hash}
```

**Components:**

- `gunicorn` - Fixed prefix for all keys
- `{metric_type}_{mode}` - Metric type and multiprocess mode
- `{pid}` - Process ID for process isolation
- `{data_type}` - Either `metric` or `meta`
- `{hash}` - MD5 hash of original metric key

#### Examples

```
gunicorn:gauge_all:12345:metric:abc123def456
gunicorn:counter:12345:meta:def456ghi789
gunicorn:histogram:12345:metric:ghi789jkl012
```

### Multiprocess Mode Support

All Prometheus multiprocess modes are supported:

| Mode | Description | Implementation |
|------|-------------|----------------|
| `all` | All processes (including dead ones) | Stores all metric instances with PID labels |
| `liveall` | All live processes | Filters out dead processes during collection |
| `live` | Only live processes (default) | Same as liveall for our use case |
| `max` | Maximum value across processes | Aggregates using Redis MAX operations |
| `min` | Minimum value across processes | Aggregates using Redis MIN operations |
| `sum` | Sum of values across processes | Aggregates using Redis SUM operations |
| `mostrecent` | Most recent value | Uses timestamp-based selection |

### Configuration

#### Environment Variables

```bash
# Enable Redis storage
export REDIS_ENABLED="true"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"
export REDIS_KEY_PREFIX="gunicorn"
export REDIS_TTL_SECONDS="300"
```

#### Programmatic Configuration

```python
from gunicorn_prometheus_exporter.backend.service import get_redis_storage_manager

# Get configured manager
manager = get_redis_storage_manager()

# Or create custom manager
from gunicorn_prometheus_exporter.backend.service import RedisStorageManager

manager = RedisStorageManager(
    redis_host="redis-cluster.example.com",
    redis_port=6379,
    redis_db=0,
    key_prefix="myapp",
    ttl_seconds=600
)
```

### Integration Examples

#### Basic Integration

```python
from gunicorn_prometheus_exporter.backend.service import setup_redis_metrics

# Setup Redis storage
setup_redis_metrics()

# Metrics will now be stored in Redis instead of files
```

#### Custom Integration

```python
from gunicorn_prometheus_exporter.backend.service import RedisStorageManager
from prometheus_client import CollectorRegistry

# Create custom registry
registry = CollectorRegistry()

# Setup Redis storage
manager = RedisStorageManager()
manager.setup()

# Register Redis collector
collector = manager.get_collector()
registry.register(collector)
```

#### Gunicorn Hook Integration

```python
# In gunicorn.conf.py
def when_ready(server):
    from gunicorn_prometheus_exporter.hooks import redis_when_ready
    redis_when_ready(server)
```

## 🔧 Worker Classes

### PrometheusWorker

The base sync worker class that provides Prometheus metrics integration.

```python
from gunicorn_prometheus_exporter import PrometheusWorker

# Usage in gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
```

**Features:**

- Request counting and timing
- Memory and CPU usage tracking
- Error handling with method/endpoint labels
- Worker state management with timestamps

### PrometheusThreadWorker

Thread-based worker for I/O-bound applications.

```python
from gunicorn_prometheus_exporter import PrometheusThreadWorker

# Usage in gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
```

**Features:**

- All features of PrometheusWorker
- Thread-based concurrency
- Better performance for I/O-bound applications

### PrometheusEventletWorker

Eventlet-based worker for async applications.

```python
from gunicorn_prometheus_exporter import PrometheusEventletWorker

# Usage in gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
```

**Requirements:**

```bash
pip install gunicorn-prometheus-exporter[eventlet]
```

**Features:**

- All features of PrometheusWorker
- Eventlet-based async I/O
- High concurrency for async applications

### PrometheusGeventWorker

Gevent-based worker for async applications.

```python
from gunicorn_prometheus_exporter import PrometheusGeventWorker

# Usage in gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"
```

**Requirements:**

```bash
pip install gunicorn-prometheus-exporter[gevent]
```

**Features:**

- All features of PrometheusWorker
- Gevent-based async I/O
- High concurrency for async applications


## 🔌 Plugin Architecture

### PrometheusMixin

The core mixin class that provides Prometheus functionality to all worker types.

```python
from gunicorn_prometheus_exporter.plugin import PrometheusMixin
```

**Core Methods:**

#### `update_worker_metrics()`

Updates worker-specific metrics including memory, CPU, and uptime.

```python
def update_worker_metrics(self):
    """Update worker metrics including memory, CPU, and uptime."""
    # Updates gunicorn_worker_memory_bytes
    # Updates gunicorn_worker_cpu_percent
    # Updates gunicorn_worker_uptime_seconds
    # Updates gunicorn_worker_state
```

#### `_handle_request_metrics()`

Handles request-level metrics tracking.

```python
def _handle_request_metrics(self):
    """Track request metrics including count and duration."""
    # Updates gunicorn_worker_requests_total
    # Updates gunicorn_worker_request_duration_seconds
```

#### `_handle_request_error_metrics(req, e)`

Handles error metrics with method and endpoint labels.

```python
def _handle_request_error_metrics(self, req, e):
    """Track error metrics with method and endpoint labels."""
    # Updates gunicorn_worker_failed_requests_total
    # Updates gunicorn_worker_error_handling_total
```

#### `_generic_handle_request(parent_method, *args, **kwargs)`

Generic request handler that wraps parent worker methods.

```python
def _generic_handle_request(self, parent_method, *args, **kwargs):
    """Generic request handler with metrics tracking."""
    # Calls parent method
    # Updates request metrics
    # Handles exceptions
```

#### `_generic_handle_error(parent_method, *args, **kwargs)`

Generic error handler that wraps parent worker methods.

```python
def _generic_handle_error(self, parent_method, *args, **kwargs):
    """Generic error handler with metrics tracking."""
    # Calls parent method
    # Updates error metrics
    # Handles exceptions
```

## 🎣 Gunicorn Hooks

The exporter provides a comprehensive hooks system with a modular, class-based architecture for managing Gunicorn lifecycle events.

### Hooks Architecture

The hooks system is built around several specialized manager classes:

#### **HookManager**

Centralized logging and execution management for all hooks.

#### **EnvironmentManager**

Handles CLI-to-environment variable mapping and configuration updates.

#### **MetricsServerManager**

Manages Prometheus metrics server lifecycle with retry logic and error handling.

#### **WorkerManager**

Handles worker metrics updates and graceful shutdown procedures.

#### **ProcessManager**

Manages process cleanup and termination with timeout handling.

### 📋 Default Hooks

The exporter provides several pre-built Gunicorn hooks for automatic setup:

#### `default_on_starting(server)`

Called when the server is starting up. Initializes master metrics and multiprocess directory.

```python
from gunicorn_prometheus_exporter.hooks import default_on_starting

def on_starting(server):
    default_on_starting(server)
```

**What it does:**

- Sets up logging with proper configuration
- Initializes PrometheusMaster metrics
- Ensures multiprocess directory exists
- Handles missing configuration gracefully

#### `default_when_ready(server)`

Called when the server is ready to accept connections. Sets up the Prometheus metrics server.

```python
from gunicorn_prometheus_exporter.hooks import default_when_ready

def when_ready(server):
    default_when_ready(server)
```

**What it does:**

- Initializes MultiProcessCollector
- Starts HTTP server for metrics endpoint
- Implements retry logic for port conflicts
- Handles server startup failures gracefully

#### `default_worker_int(worker)`

Called when a worker receives an interrupt signal (e.g., SIGINT from Ctrl+C).

```python
from gunicorn_prometheus_exporter.hooks import default_worker_int

def worker_int(worker):
    default_worker_int(worker)
```

**What it does:**

- Updates worker metrics before shutdown
- Calls `worker.handle_quit()` for graceful shutdown
- Falls back to `worker.alive = False` if needed
- Handles exceptions during shutdown process

#### `default_on_exit(server)`

Called when the server is shutting down. Performs cleanup operations.

```python
from gunicorn_prometheus_exporter.hooks import default_on_exit

def on_exit(server):
    default_on_exit(server)
```

**What it does:**

- Cleans up Prometheus metrics server
- Terminates any remaining child processes
- Uses psutil for comprehensive process cleanup
- Handles cleanup failures gracefully

#### `default_post_fork(server, worker)`

Called after each worker process is forked. Configures CLI options and environment variables.

```python
from gunicorn_prometheus_exporter.hooks import default_post_fork

def post_fork(server, worker):
    default_post_fork(server, worker)
```

**What it does:**

- Accesses Gunicorn configuration (`server.cfg`)
- Logs detailed worker-specific configuration
- Updates environment variables with CLI values
- Ensures consistency between CLI and environment-based configuration

**Supported CLI options:**

- `--workers`: Number of worker processes
- `--bind`: Bind address and port
- `--worker-class`: Worker class to use

**Example usage:**

```bash
# Override workers from CLI
gunicorn -c gunicorn.conf.py app:app --workers 8

# Override bind address from CLI
gunicorn -c gunicorn.conf.py app:app --bind 0.0.0.0:9000
```

The post_fork hook will automatically detect these CLI options and update the corresponding environment variables.

### Redis Hooks

For Redis integration, use the Redis-specific hooks:

#### `redis_when_ready(server)`

Sets up Redis storage when the server is ready.

```python
from gunicorn_prometheus_exporter.hooks import redis_when_ready

def when_ready(server):
    redis_when_ready(server)
```

**What it does:**

- Sets up Prometheus metrics server (same as `default_when_ready`)
- Initializes Redis storage if enabled
- Handles Redis connection failures gracefully
- Provides detailed logging for debugging

### Advanced Usage

#### **Custom Hook Context**

Create custom hooks with structured context:

```python
from gunicorn_prometheus_exporter.hooks import HookContext, HookManager

def custom_hook(server, worker=None):
    context = HookContext(server=server, worker=worker)
    manager = HookManager()

    # Use manager for safe execution
    success = manager.safe_execute(your_custom_function, context)
    if not success:
        context.logger.error("Custom hook failed")
```

#### **Direct Manager Usage**

Use managers directly for specific functionality:

```python
from gunicorn_prometheus_exporter.hooks import (
    EnvironmentManager,
    MetricsServerManager,
    WorkerManager,
    ProcessManager
)

# Update environment from CLI
env_manager = EnvironmentManager(logger)
env_manager.update_from_cli(server.cfg)

# Setup metrics server
metrics_manager = MetricsServerManager(logger)
result = metrics_manager.setup_server()
if result:
    port, registry = result
    metrics_manager.start_server(port, registry)

# Handle worker shutdown
worker_manager = WorkerManager(logger)
worker_manager.update_metrics(worker)
worker_manager.shutdown_worker(worker)

# Cleanup processes
process_manager = ProcessManager(logger)
process_manager.cleanup_processes()
```

#### **Error Handling**

All managers include comprehensive error handling:

```python
# Safe execution with error handling
manager = HookManager()
success = manager.safe_execute(risky_function)

# Graceful degradation
if not success:
    logger.warning("Function failed, continuing with fallback")
```

### 🔧 Configuration Examples

#### **Basic Configuration**

```python
# gunicorn_basic.conf.py
import os

# Environment variables (set before imports)
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")

from gunicorn_prometheus_exporter.hooks import (
    default_on_starting,
    default_when_ready,
    default_worker_int,
    default_on_exit,
    default_post_fork,
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
post_fork = default_post_fork
```

#### **Redis Configuration**

```python
# gunicorn_redis.conf.py
import os

# Environment variables
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")

from gunicorn_prometheus_exporter.hooks import (
    default_on_starting,
    redis_when_ready,
    default_worker_int,
    default_on_exit,
    default_post_fork,
)

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Use Redis-enabled hooks
when_ready = redis_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork
```

### 🎯 Benefits of the New Architecture

1. **Modular Design**: Each responsibility is isolated in its own manager class
2. **Lazy Initialization**: Managers are created on-demand to avoid import-time issues
3. **Enhanced Error Handling**: Comprehensive exception handling with graceful fallbacks
4. **Better Testability**: Each manager can be tested independently
5. **Extensible**: Easy to add new functionality by creating new managers
6. **Backward Compatible**: All existing hook functions continue to work
7. **Structured Logging**: Consistent logging patterns across all managers
8. **Resource Management**: Proper cleanup and timeout handling

### 🔍 Debugging

The hooks system provides detailed logging for debugging:

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Hooks will log detailed information about:
# - Configuration updates
# - Server startup/shutdown
# - Worker lifecycle events
# - Error conditions and recovery
```

## Metrics Reference

### Worker Metrics

| Metric                                     | Type      | Labels                            | Description                           |
| ------------------------------------------ | --------- | --------------------------------- | ------------------------------------- |
| `gunicorn_worker_requests_total`           | Counter   | `worker_id`                       | Total requests handled by each worker |
| `gunicorn_worker_request_duration_seconds` | Histogram | `worker_id`                       | Request duration distribution         |
| `gunicorn_worker_memory_bytes`             | Gauge     | `worker_id`                       | Memory usage per worker               |
| `gunicorn_worker_cpu_percent`              | Gauge     | `worker_id`                       | CPU usage per worker                  |
| `gunicorn_worker_uptime_seconds`           | Gauge     | `worker_id`                       | Worker uptime                         |
| `gunicorn_worker_state`                    | Gauge     | `worker_id`, `state`, `timestamp` | Worker state with timestamp           |
| `gunicorn_worker_failed_requests_total`    | Counter   | `worker_id`, `method`, `endpoint` | Failed requests with labels           |

### Master Metrics

| Metric                                  | Type    | Labels   | Description             |
| --------------------------------------- | ------- | -------- | ----------------------- |
| `gunicorn_master_worker_restarts_total` | Counter | None     | Total worker restarts   |
| `gunicorn_master_signals_total`         | Counter | `signal` | Signal handling metrics |

### Error Metrics

| Metric                                 | Type    | Labels                                          | Description                |
| -------------------------------------- | ------- | ----------------------------------------------- | -------------------------- |
| `gunicorn_worker_error_handling_total` | Counter | `worker_id`, `method`, `endpoint`, `error_type` | Error tracking with labels |

## Configuration Options

### Environment Variables

| Variable                   | Type    | Default                     | Description                               |
| -------------------------- | ------- | --------------------------- | ----------------------------------------- |
| `PROMETHEUS_MULTIPROC_DIR` | String  | `/tmp/prometheus_multiproc` | Directory for multiprocess metrics        |
| `PROMETHEUS_METRICS_PORT`  | Integer | `9090`                      | Port for metrics endpoint                 |
| `PROMETHEUS_BIND_ADDRESS`  | String  | `0.0.0.0`                   | Bind address for metrics server           |
| `GUNICORN_WORKERS`         | Integer | `1`                         | Number of workers for metrics calculation |

### Redis Configuration

#### Redis Storage (No Files Created)

| Variable        | Type    | Default     | Description                                  |
| --------------- | ------- | ----------- | -------------------------------------------- |
| `REDIS_ENABLED` | Boolean | `false`     | Enable Redis storage (replaces file storage) |
| `REDIS_HOST`    | String  | `localhost` | Redis server host                            |
| `REDIS_PORT`    | Integer | `6379`      | Redis server port                            |
| `REDIS_DB`      | Integer | `0`         | Redis database number                        |

## 🏗️ Redis Backend Architecture

The Gunicorn Prometheus Exporter includes a sophisticated Redis backend system that replaces traditional file-based multiprocess storage with Redis for better scalability and storage-compute separation.

### Architecture Overview

The Redis backend is organized into two main packages:

#### `backend.service` - High-Level Management

- **`RedisStorageManager`**: Centralized management of Redis storage lifecycle
- **`setup_redis_metrics()`**: Initialize Redis-based metrics storage
- **`teardown_redis_metrics()`**: Clean shutdown and resource cleanup
- **`get_redis_storage_manager()`**: Access the global storage manager instance

#### `backend.core` - Low-Level Operations

- **`RedisStorageClient`**: Main client for Redis operations
- **`RedisStorageDict`**: Dictionary-like interface for Redis storage
- **`RedisValue`**: Redis-backed metric value implementation
- **`RedisMultiProcessCollector`**: Collects metrics from Redis storage
- **`RedisDict`**: Low-level Redis dictionary operations

### Key Components

#### RedisStorageManager

The central component that manages the entire Redis storage lifecycle:

```python
from gunicorn_prometheus_exporter.backend import RedisStorageManager

# Initialize manager
manager = RedisStorageManager()

# Setup Redis storage (replaces file-based storage)
success = manager.setup()

# Check if Redis is enabled and working
if manager.is_enabled():
    print("Redis storage is active")

# Get Redis client for custom operations
redis_client = manager.get_client()

# Cleanup on shutdown
manager.teardown()
```

#### RedisStorageClient

Provides a clean interface for Redis operations:

```python
from gunicorn_prometheus_exporter.backend import RedisStorageClient
import redis

# Create Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Create storage client
storage_client = RedisStorageClient(redis_client, key_prefix="gunicorn")

# Get value class for Prometheus metrics
value_class = storage_client.get_value_class()

# Cleanup process-specific keys
storage_client.cleanup_process_keys(pid=12345)
```

#### RedisValue

Redis-backed implementation of Prometheus metric values:

```python
from gunicorn_prometheus_exporter.backend import RedisValue, RedisStorageDict

# Create Redis-backed value
redis_dict = RedisStorageDict(redis_client, "gunicorn")
value = RedisValue(redis_dict, metric_name="requests_total")

# Standard Prometheus operations
value.inc(1)           # Increment by 1
value.set(100)         # Set to 100
current_value = value.get()  # Get current value
```

### Configuration Integration

The Redis backend integrates seamlessly with Gunicorn configuration:

```python
# gunicorn_redis_backend.conf.py
import os

# Enable Redis backend
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("REDIS_KEY_PREFIX", "gunicorn")

# Import Redis hooks
from gunicorn_prometheus_exporter.hooks import (
    redis_when_ready,
    default_on_starting,
    default_worker_int,
    default_on_exit,
)

# Gunicorn configuration
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Use Redis hooks
when_ready = redis_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
```

### Benefits of Redis Backend

1. **No File System Dependencies**: Eliminates multiproc directory requirements
2. **Better Scalability**: Redis handles concurrent access efficiently
3. **Storage-Compute Separation**: Metrics storage independent of application servers
4. **Centralized Aggregation**: All metrics accessible from a single Redis instance
5. **Automatic Cleanup**: Dead process keys are automatically cleaned up
6. **High Performance**: Redis provides sub-millisecond latency for metric operations

### Migration from File-Based Storage

The Redis backend is designed as a drop-in replacement for file-based storage:

```python
# Before: File-based storage
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")

# After: Redis backend
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
```

No code changes are required - the same Prometheus metrics work identically with Redis storage.

## 🔧 Advanced Usage

### Custom Metrics

You can extend the exporter with custom metrics:

```python
from prometheus_client import Counter, Gauge

# Custom metrics
CUSTOM_REQUESTS = Counter('custom_requests_total', 'Custom request counter')
CUSTOM_MEMORY = Gauge('custom_memory_bytes', 'Custom memory usage')

# Use in your application
CUSTOM_REQUESTS.inc()
CUSTOM_MEMORY.set(1024)
```

### Custom Hooks

Create custom hooks for specific requirements:

```python
def custom_when_ready(server):
    """Custom hook for additional setup."""
    # Your custom logic here
    pass

def custom_worker_int(worker):
    """Custom worker initialization."""
    # Your custom logic here
    pass
```

### Error Handling

The exporter includes robust error handling:

```python
# All metrics operations are wrapped in try-catch blocks
try:
    # Metric operation
    metric.labels(**labels).inc()
except Exception as e:
    logger.error("Failed to update metric: %s", e)
```

# API Reference

Complete API reference for the Gunicorn Prometheus Exporter.

## Configuration API

### ExporterConfig

Main configuration class for the exporter.

```python
from gunicorn_prometheus_exporter.config import ExporterConfig
```

#### Constructor

```python
ExporterConfig()
```

Creates a new configuration instance. Reads environment variables and validates them.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `prometheus_metrics_port` | `int` | Port for the Prometheus metrics server |
| `prometheus_bind_address` | `str` | Bind address for metrics server |
| `prometheus_multiproc_dir` | `str` | Directory for multiprocess metrics storage |
| `gunicorn_workers` | `int` | Number of Gunicorn workers |
| `gunicorn_timeout` | `int` | Worker timeout in seconds |
| `gunicorn_keepalive` | `int` | Keep-alive connection timeout |
| `redis_enabled` | `bool` | Whether Redis forwarding is enabled |
| `redis_host` | `str` | Redis server hostname |
| `redis_port` | `int` | Redis server port |
| `redis_db` | `int` | Redis database number |
| `redis_password` | `str` | Redis authentication password |
| `redis_key_prefix` | `str` | Prefix for Redis keys |
| `redis_forward_interval` | `int` | Metrics forwarding interval in seconds |
| `cleanup_db_files` | `bool` | Whether to clean up old multiprocess files |

#### Methods

##### `validate() -> bool`

Validates the configuration and returns `True` if valid, `False` otherwise.

```python
config = ExporterConfig()
if config.validate():
    print("Configuration is valid")
else:
    print("Configuration has errors")
```

##### `print_config() -> None`

Prints the current configuration to stdout.

```python
config = ExporterConfig()
config.print_config()
```

##### `get_gunicorn_config() -> Dict[str, Any]`

Returns a dictionary with Gunicorn-specific configuration.

```python
config = ExporterConfig()
gunicorn_config = config.get_gunicorn_config()
```

##### `get_prometheus_config() -> Dict[str, Any]`

Returns a dictionary with Prometheus-specific configuration.

```python
config = ExporterConfig()
prometheus_config = config.get_prometheus_config()
```

## Worker API

### PrometheusWorker

Custom Gunicorn worker class that collects metrics.

```python
from gunicorn_prometheus_exporter.plugin import PrometheusWorker
```

#### Constructor

```python
PrometheusWorker(age, ppid, sockets, app, timeout, cfg, log)
```

Creates a new Prometheus worker instance.

#### Methods

##### `handle_request(listener, req, client, addr) -> List[str]`

Handles an incoming request and collects metrics.

```python
# Called automatically by Gunicorn
worker.handle_request(listener, req, client, addr)
```

##### `handle_error(req, client, addr, exc) -> None`

Handles request errors and collects error metrics.

```python
# Called automatically by Gunicorn
worker.handle_error(req, client, addr, exc)
```

##### `update_worker_metrics() -> None`

Updates worker-specific metrics (CPU, memory, uptime).

```python
# Called automatically by Gunicorn
worker.update_worker_metrics()
```

##### `handle_quit(signum, frame) -> None`

Handles worker quit signal and updates state metrics.

```python
# Called automatically by Gunicorn
worker.handle_quit(signum, frame)
```

##### `handle_abort(signum, frame) -> None`

Handles worker abort signal and updates state metrics.

```python
# Called automatically by Gunicorn
worker.handle_abort(signum, frame)
```

##### `_clear_old_metrics() -> None`

Cleans up metrics from old worker processes.

```python
# Called automatically by Gunicorn
worker._clear_old_metrics()
```

## Master API

### PrometheusMaster

Custom Gunicorn master class that handles worker restarts and signals.

```python
from gunicorn_prometheus_exporter.master import PrometheusMaster
```

#### Constructor

```python
PrometheusMaster(age, ppid, sockets, app, timeout, cfg, log)
```

Creates a new Prometheus master instance.

#### Methods

##### `_setup_master_metrics() -> None`

Initializes master-specific metrics.

```python
# Called automatically by Gunicorn
master._setup_master_metrics()
```

##### `signal(signum, frame) -> None`

Handles signals and updates metrics.

```python
# Called automatically by Gunicorn
master.signal(signum, frame)
```

##### `handle_hup(signum, frame) -> None`

Handles HUP signal (reload configuration).

```python
# Called automatically by Gunicorn
master.handle_hup(signum, frame)
```

##### `handle_ttin(signum, frame) -> None`

Handles TTIN signal (increase worker count).

```python
# Called automatically by Gunicorn
master.handle_ttin(signum, frame)
```

##### `handle_ttou(signum, frame) -> None`

Handles TTOU signal (decrease worker count).

```python
# Called automatically by Gunicorn
master.handle_ttou(signum, frame)
```

##### `handle_chld(signum, frame) -> None`

Handles CHLD signal (child process status change).

```python
# Called automatically by Gunicorn
master.handle_chld(signum, frame)
```

##### `handle_usr1(signum, frame) -> None`

Handles USR1 signal (reopen log files).

```python
# Called automatically by Gunicorn
master.handle_usr1(signum, frame)
```

##### `handle_usr2(signum, frame) -> None`

Handles USR2 signal (reload application).

```python
# Called automatically by Gunicorn
master.handle_usr2(signum, frame)
```

##### `init_signals() -> None`

Initializes signal handlers.

```python
# Called automatically by Gunicorn
master.init_signals()
```

## Hooks API

### Gunicorn Hooks

Pre-built hook functions for Gunicorn integration.

```python
from gunicorn_prometheus_exporter import (
    default_on_starting,
    default_when_ready,
    default_worker_int,
    default_on_exit,
    redis_when_ready
)
```

#### `default_on_starting(server) -> None`

Hook called when the master process starts.

```python
# In gunicorn.conf.py
on_starting = "gunicorn_prometheus_exporter.default_on_starting"
```

#### `default_when_ready(server) -> None`

Hook called when the server is ready to accept connections.

```python
# In gunicorn.conf.py
when_ready = "gunicorn_prometheus_exporter.default_when_ready"
```

#### `default_worker_int(worker) -> None`

Hook called when a worker receives an interrupt signal.

```python
# In gunicorn.conf.py
worker_int = "gunicorn_prometheus_exporter.default_worker_int"
```

#### `default_on_exit(server) -> None`

Hook called when the server exits.

```python
# In gunicorn.conf.py
on_exit = "gunicorn_prometheus_exporter.default_on_exit"
```

#### `redis_when_ready(server) -> None`

Hook called when the server is ready, with Redis forwarding enabled.

```python
# In gunicorn.conf.py
when_ready = "gunicorn_prometheus_exporter.redis_when_ready"
```

## Metrics API

### Metrics Classes

Custom metric classes for Gunicorn monitoring.

```python
from gunicorn_prometheus_exporter.metrics import (
    WorkerRequests,
    WorkerRequestDuration,
    WorkerMemory,
    WorkerCPU,
    WorkerUptime,
    WorkerFailedRequests,
    WorkerErrorHandling,
    WorkerState,
    MasterWorkerRestarts
)
```

#### WorkerRequests

Counter metric for tracking total requests per worker.

```python
# Usage
worker_requests = WorkerRequests()
worker_requests.inc(worker_id="worker_1")
```

#### WorkerRequestDuration

Histogram metric for tracking request duration.

```python
# Usage
request_duration = WorkerRequestDuration()
request_duration.observe(0.5, worker_id="worker_1")
```

#### WorkerMemory

Gauge metric for tracking worker memory usage.

```python
# Usage
worker_memory = WorkerMemory()
worker_memory.set(52428800, worker_id="worker_1")  # 50MB in bytes
```

#### WorkerCPU

Gauge metric for tracking worker CPU usage.

```python
# Usage
worker_cpu = WorkerCPU()
worker_cpu.set(2.5, worker_id="worker_1")  # 2.5%
```

#### WorkerUptime

Gauge metric for tracking worker uptime.

```python
# Usage
worker_uptime = WorkerUptime()
worker_uptime.set(3600, worker_id="worker_1")  # 1 hour in seconds
```

#### WorkerFailedRequests

Counter metric for tracking failed requests.

```python
# Usage
failed_requests = WorkerFailedRequests()
failed_requests.inc(
    worker_id="worker_1",
    method="GET",
    endpoint="/api/users",
    status_code="404"
)
```

#### WorkerErrorHandling

Counter metric for tracking error handling.

```python
# Usage
error_handling = WorkerErrorHandling()
error_handling.inc(
    worker_id="worker_1",
    method="POST",
    endpoint="/api/data",
    error_type="ValueError"
)
```

#### WorkerState

Gauge metric for tracking worker state.

```python
# Usage
worker_state = WorkerState()
worker_state.set(
    1.0,
    worker_id="worker_1",
    state="running",
    timestamp="1640995200.123"
)
```

#### MasterWorkerRestarts

Counter metric for tracking worker restarts.

```python
# Usage
worker_restarts = MasterWorkerRestarts()
worker_restarts.inc()
```

## Utils API

### Utility Functions

Helper functions for common operations.

```python
from gunicorn_prometheus_exporter.utils import (
    get_multiprocess_dir,
    ensure_multiprocess_dir
)
```

#### `get_multiprocess_dir() -> Optional[str]`

Gets the multiprocess directory from environment variables.

```python
mp_dir = get_multiprocess_dir()
if mp_dir:
    print(f"Multiprocess directory: {mp_dir}")
else:
    print("Multiprocess directory not set")
```

#### `ensure_multiprocess_dir(mp_dir: str) -> bool`

Ensures the multiprocess directory exists and is writable.

```python
mp_dir = "/tmp/prometheus_multiproc"
if ensure_multiprocess_dir(mp_dir):
    print("Multiprocess directory is ready")
else:
    print("Failed to create multiprocess directory")
```

## Forwarder API

### Redis Forwarder

Redis-based metrics forwarding for distributed setups.

```python
from gunicorn_prometheus_exporter.forwarder import (
    create_redis_forwarder,
    get_forwarder_manager
)
```

#### `create_redis_forwarder() -> RedisForwarder`

Creates a new Redis forwarder instance.

```python
forwarder = create_redis_forwarder()
```

#### `get_forwarder_manager() -> ForwarderManager`

Gets the global forwarder manager instance.

```python
manager = get_forwarder_manager()
```

### ForwarderManager

Manages multiple forwarder instances.

```python
from gunicorn_prometheus_exporter.forwarder.manager import ForwarderManager
```

#### Methods

##### `add_forwarder(name: str, forwarder: BaseForwarder) -> None`

Adds a forwarder to the manager.

```python
manager = ForwarderManager()
manager.add_forwarder("redis", redis_forwarder)
```

##### `start_forwarder(name: str) -> None`

Starts a specific forwarder.

```python
manager.start_forwarder("redis")
```

##### `stop_forwarder(name: str) -> None`

Stops a specific forwarder.

```python
manager.stop_forwarder("redis")
```

##### `start_all() -> None`

Starts all forwarders.

```python
manager.start_all()
```

##### `stop_all() -> None`

Stops all forwarders.

```python
manager.stop_all()
```

##### `get_status() -> Dict[str, Dict[str, Any]]`

Gets status of all forwarders.

```python
status = manager.get_status()
```

## Registry API

### Shared Registry

Access to the shared Prometheus registry.

```python
from gunicorn_prometheus_exporter.metrics import get_shared_registry
```

#### `get_shared_registry() -> CollectorRegistry`

Gets the shared Prometheus registry instance.

```python
registry = get_shared_registry()
```

## Error Handling

### Common Exceptions

#### `ConfigurationError`

Raised when configuration validation fails.

```python
from gunicorn_prometheus_exporter.config import ConfigurationError

try:
    config = ExporterConfig()
    if not config.validate():
        raise ConfigurationError("Invalid configuration")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

#### `MetricsError`

Raised when metrics operations fail.

```python
from gunicorn_prometheus_exporter.metrics import MetricsError

try:
    # Metrics operation
    pass
except MetricsError as e:
    print(f"Metrics error: {e}")
```

## Best Practices

### Configuration

1. **Validate Configuration Early**
   ```python
   config = ExporterConfig()
   if not config.validate():
       sys.exit(1)
   ```

2. **Use Environment Variables**
   ```bash
   export PROMETHEUS_METRICS_PORT=9091
   export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
   ```

3. **Handle Errors Gracefully**
   ```python
   try:
       # API operation
       pass
   except Exception as e:
       logger.error(f"Operation failed: {e}")
   ```

### Metrics

1. **Use Appropriate Metric Types**
   - Use `Counter` for cumulative values
   - Use `Gauge` for current values
   - Use `Histogram` for distributions

2. **Label Cardinality**
   - Keep label values limited
   - Avoid high-cardinality labels
   - Use aggregation when possible

3. **Clean Up Old Metrics**
   ```python
   worker._clear_old_metrics()
   ```

## Related Documentation

- [Installation Guide](installation.md)
- [Configuration Reference](configuration.md)
- [Metrics Documentation](metrics.md)
- [Troubleshooting](troubleshooting.md)

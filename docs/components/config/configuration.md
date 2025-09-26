# Configuration Guide

Complete configuration guide for the Gunicorn Prometheus Exporter with all options and scenarios.

## Configuration Architecture

The Gunicorn Prometheus Exporter uses a **ConfigManager pattern** with lifecycle management that follows software engineering best practices for configuration management. This ensures consistent, centralized configuration across the entire application.

### ConfigManager Pattern Benefits

- **Lifecycle Management**: Proper initialization, validation, and cleanup states
- **State Tracking**: Clear state transitions and error handling
- **Thread Safety**: Safe concurrent access with proper locking mechanisms
- **Validation Control**: Centralized validation with detailed error reporting
- **Resource Management**: Proper cleanup and resource management
- **Single Source of Truth**: One configuration instance for the entire application

### Configuration Loading Flow

```mermaid
flowchart TD
    A[Application Startup] --> B[initialize_config() called]
    B --> C[ConfigManager.initialize()]
    C --> D[State: INITIALIZING]
    D --> E[Set environment variables]
    E --> F[Create ExporterConfig instance]
    F --> G[Validate configuration]
    G --> H{Validation successful?}

    H -->|No| I[State: ERROR]
    H -->|Yes| J[State: INITIALIZED]

    I --> K[Raise exception]
    J --> L[Configuration ready]

    L --> M[Property Access - Lazy Loading]
    M --> N[Environment variables read with validation]
    N --> O[CLI Updates via EnvironmentManager]
    O --> P[Runtime Usage - Properties read current values]

    P --> Q[Application Shutdown]
    Q --> R[cleanup_config() called]
    R --> S[ConfigManager.cleanup()]
    S --> T[State: CLEANUP]

    style A fill:#e1f5fe
    style C fill:#f3e5f5
    style M fill:#e8f5e8
    style P fill:#fff3e0
    style T fill:#ffebee
```

### Configuration Access Patterns

#### **ConfigManager Access**
```python
# Import the config manager functions
from gunicorn_prometheus_exporter.config import get_config, initialize_config

# Initialize configuration (typically done once at startup)
initialize_config(
    PROMETHEUS_METRICS_PORT="9091",
    PROMETHEUS_BIND_ADDRESS="0.0.0.0",
    GUNICORN_WORKERS="2"
)

# Get the configuration instance
config = get_config()
port = config.prometheus_metrics_port
redis_enabled = config.redis_enabled
```

#### **Direct ConfigManager Access**
```python
# Import the ConfigManager class
from gunicorn_prometheus_exporter.config import ConfigManager

# Create and manage configuration
manager = ConfigManager()
manager.initialize(
    PROMETHEUS_METRICS_PORT="9091",
    PROMETHEUS_BIND_ADDRESS="0.0.0.0",
    GUNICORN_WORKERS="2"
)

# Get configuration
config = manager.get_config()
port = config.prometheus_metrics_port
```

#### **Module-Level Access**
```python
# Import config from the main module
from gunicorn_prometheus_exporter import get_config

# Access configuration values
config = get_config()
port = config.prometheus_metrics_port
```

### Environment Variable Processing

The configuration system processes environment variables in multiple phases:

#### **Phase 1: Module-Level Defaults**
```python
# config.py - Module level (read at import time)
PROMETHEUS_MULTIPROC_DIR = os.environ.get("PROMETHEUS_MULTIPROC_DIR", _default_prometheus_dir)
GUNICORN_TIMEOUT = os.environ.get("GUNICORN_TIMEOUT", 30)
GUNICORN_KEEPALIVE = os.environ.get("GUNICORN_KEEPALIVE", 2)
```

#### **Phase 2: Singleton Initialization**
```python
# config.py - Global singleton creation
config = ExporterConfig()  # Creates global instance

def __init__(self):
    """Initialize configuration with environment variables and defaults."""
    self._setup_multiproc_dir()  # Sets up multiprocess directory

def _setup_multiproc_dir(self):
    """Set up the Prometheus multiprocess directory."""
    if not os.environ.get(self.ENV_PROMETHEUS_MULTIPROC_DIR):
        os.environ[self.ENV_PROMETHEUS_MULTIPROC_DIR] = self.PROMETHEUS_MULTIPROC_DIR
```

#### **Phase 3: Lazy Property Access**
```python
@property
def prometheus_metrics_port(self) -> int:
    """Get the Prometheus metrics server port."""
    value = os.environ.get(self.ENV_PROMETHEUS_METRICS_PORT, self.PROMETHEUS_METRICS_PORT)
    if value is None:
        raise ValueError(f"Environment variable {self.ENV_PROMETHEUS_METRICS_PORT} must be set in production.")
    return int(value)

@property
def redis_enabled(self) -> bool:
    """Check if Redis storage is enabled."""
    return os.environ.get(self.ENV_REDIS_ENABLED, "").lower() in ("true", "1", "yes", "on")
```

#### **Phase 4: CLI Integration**
```python
# hooks.py - EnvironmentManager class
def update_from_cli(self, cfg: Any) -> None:
    """Update environment variables from CLI configuration."""
    self._update_workers_env(cfg)
    self._update_bind_env(cfg)
    self._update_worker_class_env(cfg)

def _update_workers_env(self, cfg: Any) -> None:
    """Update GUNICORN_WORKERS environment variable from CLI."""
    if hasattr(cfg, "workers") and cfg.workers:
        os.environ["GUNICORN_WORKERS"] = str(cfg.workers)
```

### Configuration Validation

The configuration system includes comprehensive validation:

#### **Required Variables Validation**
```python
@property
def prometheus_metrics_port(self) -> int:
    value = os.environ.get(self.ENV_PROMETHEUS_METRICS_PORT, self.PROMETHEUS_METRICS_PORT)
    if value is None:
        raise ValueError(
            f"Environment variable {self.ENV_PROMETHEUS_METRICS_PORT} "
            f"must be set in production. "
            f"Example: export {self.ENV_PROMETHEUS_METRICS_PORT}=9091"
        )
    return int(value)
```

#### **Type Conversion and Validation**
```python
@property
def gunicorn_timeout(self) -> int:
    """Get the Gunicorn worker timeout."""
    return int(
        os.environ.get(self.ENV_GUNICORN_TIMEOUT, str(self.GUNICORN_TIMEOUT))
    )

@property
def redis_ttl_seconds(self) -> int:
    """Get Redis TTL in seconds for metric keys."""
    return int(
        os.environ.get(self.ENV_REDIS_TTL_SECONDS, "300")
    )  # 5 minutes default
```

### Configuration Categories

#### **Required (Production)**
- `PROMETHEUS_METRICS_PORT` - Metrics server port
- `PROMETHEUS_BIND_ADDRESS` - Metrics server bind address
- `GUNICORN_WORKERS` - Number of workers

#### **Optional (Defaults)**
- `PROMETHEUS_MULTIPROC_DIR` - Multiprocess directory (defaults to `~/.gunicorn_prometheus`)
- `GUNICORN_TIMEOUT` - Worker timeout (defaults to 30)
- `GUNICORN_KEEPALIVE` - Keepalive setting (defaults to 2)

#### **Redis Configuration**
- `REDIS_ENABLED` - Enable Redis storage
- `REDIS_HOST` - Redis host (defaults to 127.0.0.1)
- `REDIS_PORT` - Redis port (defaults to 6379)
- `REDIS_DB` - Redis database (defaults to 0)
- `REDIS_PASSWORD` - Redis password
- `REDIS_KEY_PREFIX` - Key prefix (defaults to "gunicorn")
- `REDIS_TTL_SECONDS` - TTL for keys (defaults to 300)
- `REDIS_TTL_DISABLED` - Disable TTL

#### **SSL/TLS Configuration**
- `PROMETHEUS_SSL_CERTFILE` - SSL certificate file
- `PROMETHEUS_SSL_KEYFILE` - SSL key file
- `PROMETHEUS_SSL_CLIENT_CAFILE` - Client CA file
- `PROMETHEUS_SSL_CLIENT_CAPATH` - Client CA path
- `PROMETHEUS_SSL_CLIENT_AUTH_REQUIRED` - Require client auth

## 🔧 Environment Variables Reference

### Required Variables

| Variable                   | Type    | Default                     | Description                        | Example                         |
| -------------------------- | ------- | --------------------------- | ---------------------------------- | ------------------------------- |
| `PROMETHEUS_MULTIPROC_DIR` | String  | `/tmp/prometheus_multiproc` | Directory for multiprocess metrics | `/var/tmp/prometheus_multiproc` |
| `PROMETHEUS_METRICS_PORT`  | Integer | `9090`                      | Port for metrics endpoint          | `9091`                          |
| `PROMETHEUS_BIND_ADDRESS`  | String  | `0.0.0.0`                   | Bind address for metrics server    | `127.0.0.1`                     |
| `GUNICORN_WORKERS`         | Integer | `1`                         | Number of workers for metrics      | `4`                             |

### Optional Variables

| Variable             | Type    | Default | Description               | Example |
| -------------------- | ------- | ------- | ------------------------- | ------- |
| `GUNICORN_KEEPALIVE` | Integer | `2`     | Keep-alive timeout        | `5`     |
| `CLEANUP_DB_FILES`   | Boolean | `false` | Clean up old metric files | `true`  |

### Redis Variables

#### Redis Storage (No Files Created)

| Variable         | Type    | Default     | Description                                  | Example             |
| ---------------- | ------- | ----------- | -------------------------------------------- | ------------------- |
| `REDIS_ENABLED`  | Boolean | `false`     | Enable Redis storage (replaces file storage) | `true`              |
| `REDIS_HOST`     | String  | `localhost` | Redis server host                            | `redis.example.com` |
| `REDIS_PORT`     | Integer | `6379`      | Redis server port                            | `6380`              |
| `REDIS_DB`       | Integer | `0`         | Redis database number                        | `1`                 |
| `REDIS_PASSWORD` | String  | `None`      | Redis password                               | `secret123`         |

## Redis Backend Configuration

The Redis backend provides a sophisticated architecture for metrics storage with two main components:

### Architecture Components

#### `backend.service` - High-Level Management

- **`RedisStorageManager`**: Centralized lifecycle management
- **`setup_redis_metrics()`**: Initialize Redis storage
- **`teardown_redis_metrics()`**: Clean shutdown
- **`get_redis_storage_manager()`**: Global manager access

#### `backend.core` - Low-Level Operations

- **`RedisStorageClient`**: Main Redis operations client
- **`RedisStorageDict`**: Dictionary-like Redis interface
- **`RedisValue`**: Redis-backed metric values
- **`RedisMultiProcessCollector`**: Metrics collection from Redis
- **`RedisDict`**: Low-level Redis operations

### Redis Backend Setup

**Use Case:** Production deployment with Redis storage backend.

```python
# gunicorn_redis_backend.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Redis backend configuration
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("REDIS_PASSWORD", "")
os.environ.setdefault("REDIS_KEY_PREFIX", "gunicorn")

# Import Redis hooks
from gunicorn_prometheus_exporter.hooks import (
    redis_when_ready,
    default_on_starting,
    default_worker_int,
    default_on_exit,
)

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5

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

## Configuration Scenarios

### Basic Setup

**Use Case:** Simple monitoring for a single Gunicorn instance.

```python
# gunicorn_basic.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
```

**Environment Variables:**

```bash
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
export PROMETHEUS_METRICS_PORT="9090"
export PROMETHEUS_BIND_ADDRESS="0.0.0.0"
export GUNICORN_WORKERS="2"
```

### High-Performance Setup

**Use Case:** High-traffic application with optimized settings.

```python
# gunicorn_high_performance.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "8")
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")
os.environ.setdefault("CLEANUP_DB_FILES", "true")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 8
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
worker_connections = 2000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5
preload_app = True
```

### Async Application Setup

**Use Case:** Async application using eventlet workers.

```python
# gunicorn_async.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
```

### Production Setup

**Use Case:** Production environment with security and reliability.

```python
# gunicorn_production.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/var/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # Bind to localhost only
os.environ.setdefault("GUNICORN_WORKERS", "4")
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")
os.environ.setdefault("CLEANUP_DB_FILES", "true")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5
preload_app = True
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
```

### Redis Storage Setup

**Use Case:** Distributed setup with Redis storage (no files created).

```python
# gunicorn_redis_storage.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9092")  # Different port for Redis storage
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Redis storage configuration (no files created)
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("REDIS_PASSWORD", "")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5
```

### Development Setup

**Use Case:** Development environment with debugging enabled.

```python
# gunicorn_development.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
reload = True
reload_extra_files = ["app.py", "config.py"]
accesslog = "-"
errorlog = "-"
loglevel = "debug"
```

## 🔧 Worker Type Configurations

### Sync Worker

```python
# gunicorn_sync.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
```

**Best for:** CPU-bound applications, simple setups.

### Thread Worker

```python
# gunicorn_thread.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"
threads = 4
```

**Best for:** I/O-bound applications, better concurrency.

### Eventlet Worker

```python
# gunicorn_eventlet.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
worker_connections = 1000
```

**Best for:** Async applications, high concurrency.

### Gevent Worker

```python
# gunicorn_gevent.conf.py
import os

# Environment variables must be set before imports
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"
worker_connections = 1000
```

**Best for:** Async applications, high concurrency.

## 🔧 Advanced Configuration

### Hooks Architecture

The exporter uses a modular, class-based hooks architecture for managing Gunicorn lifecycle events:

#### **Manager Classes**

- **`HookManager`**: Centralized logging and execution management
- **`EnvironmentManager`**: CLI-to-environment variable mapping
- **`MetricsServerManager`**: Prometheus server lifecycle with retry logic
- **`WorkerManager`**: Worker metrics and graceful shutdown
- **`ProcessManager`**: Process cleanup and termination

#### **Benefits**

- **Modular Design**: Each responsibility isolated in its own manager
- **Lazy Initialization**: Managers created on-demand to avoid import issues
- **Enhanced Error Handling**: Comprehensive exception handling with fallbacks
- **Better Testability**: Each manager can be tested independently
- **Backward Compatible**: All existing hook functions continue to work

### Custom Hooks

#### **Basic Custom Hooks**

```python
# gunicorn_custom_hooks.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "4")

# Custom hooks
def on_starting(server):
    """Custom startup hook."""
    print("Starting Gunicorn with Prometheus exporter...")

def when_ready(server):
    """Custom ready hook."""
    from gunicorn_prometheus_exporter.hooks import default_when_ready
    default_when_ready(server)
    print("Gunicorn is ready to accept connections")

def worker_int(worker):
    """Custom worker initialization hook."""
    from gunicorn_prometheus_exporter.hooks import default_worker_int
    default_worker_int(worker)
    print(f"Worker {worker.pid} initialized")

def on_exit(server):
    """Custom exit hook."""
    from gunicorn_prometheus_exporter.hooks import default_on_exit
    default_on_exit(server)
    print("Gunicorn shutting down...")
```

#### **Advanced Custom Hooks with Managers**

```python
# gunicorn_advanced_hooks.conf.py
import os
import logging

# Environment variables (set before imports)
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")

from gunicorn_prometheus_exporter.hooks import (
    HookContext,
    HookManager,
    EnvironmentManager,
    MetricsServerManager,
    WorkerManager,
    ProcessManager,
    default_on_starting,
    default_when_ready,
    default_worker_int,
    default_on_exit,
    default_post_fork,
)

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
timeout = 300

# Custom hook with manager usage
def custom_when_ready(server):
    """Custom when_ready hook using managers directly."""
    logger = logging.getLogger(__name__)

    # Create context
    context = HookContext(server=server, logger=logger)

    # Use metrics manager for custom setup
    metrics_manager = MetricsServerManager(logger)
    result = metrics_manager.setup_server()

    if result:
        port, registry = result
        logger.info(f"Custom metrics server setup on port {port}")

        # Start with custom retry logic
        if metrics_manager.start_server(port, registry):
            logger.info("Custom metrics server started successfully")
        else:
            logger.error("Custom metrics server failed to start")
    else:
        logger.warning("Custom metrics server setup failed")

# Use custom hooks
when_ready = custom_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork
```

### CLI Options and Post-Fork Hook

Some Gunicorn CLI options like `--timeout`, `--workers`, `--bind`, and `--worker-class` do not automatically populate environment variables. The `post_fork` hook ensures these CLI options are properly configured and consistent with environment-based settings.

#### **Why use post_fork hook for CLI options:**

- CLI options like `--timeout` don't automatically set environment variables
- The post_fork hook runs after each worker is forked and can access Gunicorn's configuration
- It ensures consistency between CLI and environment-based configuration
- It logs worker-specific configuration for debugging
- Uses `EnvironmentManager` to handle CLI-to-environment mapping

#### **What the post_fork hook does:**

1. **Configuration Logging**: Logs detailed worker configuration for debugging
2. **Environment Updates**: Updates environment variables with CLI values
3. **CLI Option Detection**: Detects and processes CLI options like:
   - `--workers`: Number of worker processes
   - `--bind`: Bind address and port
   - `--worker-class`: Worker class to use
4. **Consistency Check**: Ensures CLI and environment settings are consistent

#### **Example with post_fork hook:**

```python
# gunicorn_with_cli.conf.py
import os

# Environment variables (set before imports)
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")

from gunicorn_prometheus_exporter.hooks import (
    default_on_starting,
    default_when_ready,
    default_worker_int,
    default_on_exit,
    default_post_fork,
)

# Gunicorn settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
timeout = 300

# Use pre-built hooks including post_fork
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork  # Configure CLI options after worker fork
```

#### **CLI usage with post_fork hook:**

```bash
# Override timeout from CLI
gunicorn -c gunicorn_with_cli.conf.py app:app --timeout 600

# Override workers from CLI
gunicorn -c gunicorn_with_cli.conf.py app:app --workers 8

# Override bind address from CLI
gunicorn -c gunicorn_with_cli.conf.py app:app --bind 0.0.0.0:9000

# Override worker class from CLI
gunicorn -c gunicorn_with_cli.conf.py app:app --worker-class gunicorn_prometheus_exporter.PrometheusWorker
```

#### **Environment Variable Updates**

The post_fork hook automatically updates these environment variables based on CLI options:

```bash
# CLI: --workers 8
# Sets: GUNICORN_WORKERS=8

# CLI: --bind 0.0.0.0:9000
# Sets: GUNICORN_BIND=0.0.0.0:9000

# CLI: --worker-class gunicorn_prometheus_exporter.PrometheusWorker
# Sets: GUNICORN_WORKER_CLASS=gunicorn_prometheus_exporter.PrometheusWorker
```

### 🔍 Debugging Hooks

#### **Enable Debug Logging**

```python
# gunicorn_debug.conf.py
import logging

# Enable debug logging for hooks
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ... rest of configuration
```

#### **Hook Debugging Features**

The hooks system provides detailed logging for debugging:

- **Configuration Updates**: Logs when environment variables are updated
- **Server Lifecycle**: Logs server startup, ready, and shutdown events
- **Worker Events**: Logs worker initialization and shutdown
- **Error Conditions**: Logs errors with detailed context
- **Recovery Actions**: Logs fallback and recovery attempts

#### **Example Debug Output**

```
2024-01-15 10:30:00 - gunicorn_prometheus_exporter.hooks - INFO - Server starting - initializing PrometheusMaster metrics
2024-01-15 10:30:01 - gunicorn_prometheus_exporter.hooks - INFO - Updated GUNICORN_WORKERS from CLI: 4
2024-01-15 10:30:01 - gunicorn_prometheus_exporter.hooks - INFO - Updated GUNICORN_BIND from CLI: 0.0.0.0:8000
2024-01-15 10:30:02 - gunicorn_prometheus_exporter.hooks - INFO - Starting Prometheus multiprocess metrics server on :9090
2024-01-15 10:30:02 - gunicorn_prometheus_exporter.hooks - INFO - Metrics server started successfully on port 9090
2024-01-15 10:30:03 - gunicorn_prometheus_exporter.hooks - INFO - Worker 12345 received interrupt signal
2024-01-15 10:30:03 - gunicorn_prometheus_exporter.hooks - INFO - Server shutting down - cleaning up Prometheus metrics server
```

### Error Handling

#### **Graceful Degradation**

All hooks include comprehensive error handling:

```python
# Example of error handling in custom hooks
def custom_hook(server):
    try:
        # Your custom logic
        pass
    except Exception as e:
        logger.error(f"Custom hook failed: {e}")
        # Continue with fallback behavior
```

#### **Common Error Scenarios**

1. **Missing Configuration**: Hooks handle missing environment variables gracefully
2. **Port Conflicts**: Metrics server retry logic handles port conflicts
3. **Process Cleanup**: Comprehensive cleanup handles orphaned processes
4. **Worker Shutdown**: Graceful shutdown with fallback mechanisms

#### **Recovery Mechanisms**

- **Lazy Initialization**: Prevents import-time configuration issues
- **Retry Logic**: Automatic retry for transient failures
- **Fallback Options**: Alternative approaches when primary methods fail
- **Timeout Handling**: Prevents hanging operations

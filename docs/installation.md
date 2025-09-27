# Installation Guide

This guide provides comprehensive installation instructions for the Gunicorn Prometheus Exporter, including all configuration options and environment variables.

## Installation Options

The following sections describe different installation methods and their respective features.

### Basic Installation

Install the core package with sync and thread worker support:

```bash
pip install gunicorn-prometheus-exporter
```

*Includes:*

- Sync worker (`PrometheusWorker`)
- Thread worker (`PrometheusThreadWorker`)
- Basic Prometheus metrics collection
- Multiprocess support

### Async Worker Installation

Install with support for async worker types:

```bash
# Install all async workers
pip install gunicorn-prometheus-exporter[async]

# Or install specific worker types
pip install gunicorn-prometheus-exporter[eventlet]  # Eventlet workers
pip install gunicorn-prometheus-exporter[gevent]    # Gevent workers
```

### Redis Integration

Install with Redis storage capabilities:

```bash
pip install gunicorn-prometheus-exporter[redis]
```

*Includes:*

- All basic features
- Redis storage (no files created)
- Redis connection management
- Metrics aggregation

### Development Installation

Install with development dependencies:

```bash
pip install gunicorn-prometheus-exporter[dev]
```

*Includes:*

- All basic features
- Testing dependencies (pytest, coverage)
- Linting tools (ruff, mypy)
- Documentation tools (mkdocs)

### Complete Installation

Install with all features and dependencies:

```bash
pip install gunicorn-prometheus-exporter[all]
```

*Includes:*

- All async worker types
- Redis integration
- Development tools
- Documentation

### Installation from Source

```bash
# Clone the repository
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter.git
cd gunicorn-prometheus-exporter

# Install in development mode
pip install -e ".[dev]"

# Or install with specific features
pip install -e ".[async,redis]"
```

## Environment Variables

This section documents all environment variables used by the Gunicorn Prometheus Exporter.

### Required Environment Variables

The following environment variables must be configured for proper operation.

#### `PROMETHEUS_MULTIPROC_DIR`

*Description:* Directory for storing multiprocess Prometheus metrics files.

**Type:** String (path)

**Default:** `/tmp/prometheus_multiproc`

**Example:**

```bash
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
```

**Usage in configuration:**

```python
import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
```

**Requirements:**

- Directory must be writable by the Gunicorn process
- Directory should be cleaned up periodically
- Must be unique per Gunicorn instance

#### `PROMETHEUS_METRICS_PORT`

*Description:* Port number for the Prometheus metrics HTTP server.

**Type:** Integer

**Default:** `9090`

**Range:** 1-65535

**Example:**

```bash
export PROMETHEUS_METRICS_PORT="9090"
```

**Usage in configuration:**

```python
import os
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
```

**Requirements:**

- Port must be available (not in use by another process)
- Port must be accessible for metrics collection
- Consider firewall rules for production environments

#### `PROMETHEUS_BIND_ADDRESS`

*Description:* Bind address for the Prometheus metrics HTTP server.

**Type:** String (IP address)

**Default:** `0.0.0.0`

**Example:**

```bash
export PROMETHEUS_BIND_ADDRESS="0.0.0.0"
```

**Usage in configuration:**

```python
import os
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
```

**Common values:**

- `0.0.0.0` - Bind to all interfaces (default)
- `127.0.0.1` - Bind to localhost only
- `192.168.1.100` - Bind to specific IP address

#### `GUNICORN_WORKERS`

*Description:* Number of Gunicorn workers for metrics calculation.

**Type:** Integer

**Default:** `1`

**Range:** 1-1000

**Example:**

```bash
export GUNICORN_WORKERS="4"
```

**Usage in configuration:**

```python
import os
os.environ.setdefault("GUNICORN_WORKERS", "4")
```

**Recommendations:**

- Set to match your actual worker count
- Used for metrics aggregation and calculation
- Should match the `workers` setting in Gunicorn config

### Optional Environment Variables

These environment variables provide additional configuration options.

#### `GUNICORN_KEEPALIVE`

*Description:* Keep-alive connection timeout in seconds.

**Type:** Integer

**Default:** `2`

**Range:** 0-300

**Example:**

```bash
export GUNICORN_KEEPALIVE="5"
```

**Usage in configuration:**

```python
import os
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")
```

#### `CLEANUP_DB_FILES`

*Description:* Whether to clean up old multiprocess files.

**Type:** Boolean

**Default:** `false`

**Values:** `true`, `false`

**Example:**

```bash
export CLEANUP_DB_FILES="true"
```

**Usage in configuration:**

```python
import os
os.environ.setdefault("CLEANUP_DB_FILES", "true")
```

### Redis Environment Variables

This section covers Redis-specific configuration options for distributed metrics storage.

#### Redis Storage Variables

The following variables configure Redis-based metrics storage (eliminates file system dependencies).

#### `REDIS_ENABLED`

*Description:* Enable Redis storage (replaces file storage).

**Type:** Boolean

**Default:** `false`

**Values:** `true`, `false`

**Example:**

```bash
export REDIS_ENABLED="true"
```

**Usage in configuration:**

```python
import os
os.environ.setdefault("REDIS_ENABLED", "true")
```

## Package Dependencies

This section lists all required and optional dependencies for the Gunicorn Prometheus Exporter.

### Core Dependencies

The following packages are required for basic functionality.

| Package             | Version    | Purpose                       |
| ------------------- | ---------- | ----------------------------- |
| `prometheus-client` | `>=0.16.0` | Prometheus metrics collection |
| `psutil`            | `>=5.8.0`  | System metrics (CPU, memory)  |
| `gunicorn`          | `>=20.1.0` | WSGI server integration       |

### Optional Dependencies

The following packages provide additional functionality and are installed with specific extras.

#### Async Worker Dependencies

These packages enable support for asynchronous worker types.

| Package    | Version    | Worker Type                                                 |
| ---------- | ---------- | ----------------------------------------------------------- |
| `eventlet` | `>=0.30.0` | Eventlet worker                                             |
| `gevent`   | `>=21.8.0` | Gevent worker                                               |

#### Redis Dependencies

This package enables Redis-based metrics storage.

| Package | Version   | Purpose      |
| ------- | --------- | ------------ |
| `redis` | `>=4.0.0` | Redis client |

#### Development Dependencies

These packages are required for development, testing, and documentation.

| Package           | Version   | Purpose                |
| ----------------- | --------- | ---------------------- |
| `pytest`          | `>=7.0.0` | Testing framework      |
| `pytest-cov`      | `>=4.0.0` | Coverage reporting     |
| `ruff`            | `>=0.1.0` | Linting and formatting |
| `mypy`            | `>=1.0.0` | Type checking          |
| `mkdocs`          | `>=1.4.0` | Documentation          |
| `mkdocs-material` | `>=9.0.0` | Documentation theme    |

## Configuration Examples

This section provides practical configuration examples for different deployment scenarios.

### Basic Configuration

A minimal configuration for development and testing environments.

```python
# gunicorn_basic.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

### Async Worker Configuration

Configuration for applications using asynchronous worker types.

```python
# gunicorn_async.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
worker_connections = 1000

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")
```

### Redis Storage Configuration

Configuration for Redis-based metrics storage (recommended for production).

```python
# gunicorn_redis_storage.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

import os
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9092")  # Different port for Redis storage
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Redis storage configuration (no files created)
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("REDIS_PASSWORD", "")
```

### Production Configuration

A comprehensive configuration optimized for production environments.

```python
# gunicorn_production.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/var/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "127.0.0.1")  # Bind to localhost only
os.environ.setdefault("GUNICORN_WORKERS", "4")
os.environ.setdefault("GUNICORN_KEEPALIVE", "5")
os.environ.setdefault("CLEANUP_DB_FILES", "true")

# Redis configuration for production
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "redis.production.com")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("REDIS_PASSWORD", "production_password")
os.environ.setdefault("REDIS_KEY_PREFIX", "prod_gunicorn_metrics")
```

## Installation Verification

This section provides methods to verify that the installation was successful.

### Check Installation

Verify that the package and its components are properly installed.

```bash
# Verify package installation
pip show gunicorn-prometheus-exporter

# Check available worker classes
python -c "from gunicorn_prometheus_exporter import PrometheusWorker; print('Sync worker available')"
python -c "from gunicorn_prometheus_exporter import PrometheusThreadWorker; print('Thread worker available')"
```

### Test Async Workers

Verify that asynchronous worker dependencies are available.

```bash
# Test eventlet worker
python -c "import eventlet; print('Eventlet available')" 2>/dev/null && echo "Eventlet worker ready" || echo "Install eventlet: pip install gunicorn-prometheus-exporter[eventlet]"

# Test gevent worker
python -c "import gevent; print('Gevent available')" 2>/dev/null && echo "Gevent worker ready" || echo "Install gevent: pip install gunicorn-prometheus-exporter[gevent]"
```

### Test Redis Integration

Verify that Redis integration is properly configured.

```bash
# Test Redis connection
python -c "import redis; print('Redis available')" 2>/dev/null && echo "Redis integration ready" || echo "Install Redis: pip install gunicorn-prometheus-exporter[redis]"
```

## Troubleshooting Installation

This section addresses common problems encountered during installation.

### Common Installation Issues

The following issues are frequently encountered and their solutions are provided below.

#### Missing Dependencies

*Error:* `ModuleNotFoundError: No module named 'eventlet'`

**Solution:**

```bash
# Install missing dependency
pip install gunicorn-prometheus-exporter[eventlet]
```

#### Version Conflicts

*Error:* `ImportError: cannot import name 'X' from 'Y'`

**Solution:**

```bash
# Upgrade to latest version
pip install --upgrade gunicorn-prometheus-exporter

# Or install specific version
pip install gunicorn-prometheus-exporter==0.1.3
```

### Environment Variable Issues

Problems related to environment variable configuration.

#### Variables Not Set

*Error:* `ValueError: Environment variable X must be set`

**Solution:**

```bash
# Set required variables
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
export PROMETHEUS_METRICS_PORT="9090"
export PROMETHEUS_BIND_ADDRESS="0.0.0.0"
export GUNICORN_WORKERS="2"
```

#### Invalid Values

*Error:* `ValueError: Invalid port number`

**Solution:**

```bash
# Use valid port range (1-65535)
export PROMETHEUS_METRICS_PORT="9090"  # Valid
export PROMETHEUS_METRICS_PORT="99999"  # Invalid
```

## Next Steps

After successful installation, proceed with the following configuration steps:

1. **Configure Gunicorn**: Set up your `gunicorn.conf.py` file
2. **Set Environment Variables**: Configure required environment variables
3. **Test Installation**: Run a test server and verify metrics
4. **Configure Prometheus**: Set up Prometheus to scrape metrics
5. **Monitor Application**: Start monitoring your Gunicorn application

For detailed configuration examples, see the [Configuration Guide](components/config/configuration.md).

For troubleshooting, see the [Troubleshooting Guide](troubleshooting.md).

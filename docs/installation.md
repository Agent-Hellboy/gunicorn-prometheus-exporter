# Installation Guide

Complete installation guide for the Gunicorn Prometheus Exporter with all options and environment variables.

## 🚀 Installation Options

### Basic Installation

Install the core package with sync and thread worker support:

```bash
pip install gunicorn-prometheus-exporter
```

**Includes:**
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

### Redis Integration

Install with Redis forwarding capabilities:

```bash
pip install gunicorn-prometheus-exporter[redis]
```

**Includes:**
- All basic features
- Redis metrics forwarding
- Redis connection management
- Metrics aggregation

### Development Installation

Install with development dependencies:

```bash
pip install gunicorn-prometheus-exporter[dev]
```

**Includes:**
- All basic features
- Testing dependencies (pytest, coverage)
- Linting tools (ruff, mypy)
- Documentation tools (mkdocs)

### Complete Installation

Install with all features and dependencies:

```bash
pip install gunicorn-prometheus-exporter[all]
```

**Includes:**
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

## 🔧 Environment Variables

### Required Environment Variables

#### `PROMETHEUS_MULTIPROC_DIR`

**Description:** Directory for storing multiprocess Prometheus metrics files.

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

**Description:** Port number for the Prometheus metrics HTTP server.

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

**Description:** Bind address for the Prometheus metrics HTTP server.

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

**Description:** Number of Gunicorn workers for metrics calculation.

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

#### `GUNICORN_KEEPALIVE`

**Description:** Keep-alive connection timeout in seconds.

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

**Description:** Whether to clean up old multiprocess files.

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

#### `REDIS_ENABLED`

**Description:** Enable Redis metrics forwarding.

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

#### `REDIS_HOST`

**Description:** Redis server hostname.

**Type:** String

**Default:** `localhost`

**Example:**
```bash
export REDIS_HOST="redis.example.com"
```

**Usage in configuration:**
```python
import os
os.environ.setdefault("REDIS_HOST", "redis.example.com")
```

#### `REDIS_PORT`

**Description:** Redis server port.

**Type:** Integer

**Default:** `6379`

**Range:** 1-65535

**Example:**
```bash
export REDIS_PORT="6379"
```

**Usage in configuration:**
```python
import os
os.environ.setdefault("REDIS_PORT", "6379")
```

#### `REDIS_DB`

**Description:** Redis database number.

**Type:** Integer

**Default:** `0`

**Range:** 0-15

**Example:**
```bash
export REDIS_DB="1"
```

**Usage in configuration:**
```python
import os
os.environ.setdefault("REDIS_DB", "1")
```

#### `REDIS_PASSWORD`

**Description:** Redis authentication password.

**Type:** String

**Default:** `None` (no authentication)

**Example:**
```bash
export REDIS_PASSWORD="your_redis_password"
```

**Usage in configuration:**
```python
import os
os.environ.setdefault("REDIS_PASSWORD", "your_redis_password")
```

#### `REDIS_KEY_PREFIX`

**Description:** Prefix for Redis keys.

**Type:** String

**Default:** `gunicorn_metrics`

**Example:**
```bash
export REDIS_KEY_PREFIX="myapp_metrics"
```

**Usage in configuration:**
```python
import os
os.environ.setdefault("REDIS_KEY_PREFIX", "myapp_metrics")
```

#### `REDIS_FORWARD_INTERVAL`

**Description:** Metrics forwarding interval in seconds.

**Type:** Integer

**Default:** `30`

**Range:** 1-3600

**Example:**
```bash
export REDIS_FORWARD_INTERVAL="60"
```

**Usage in configuration:**
```python
import os
os.environ.setdefault("REDIS_FORWARD_INTERVAL", "60")
```

## 📦 Package Dependencies

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `prometheus-client` | `>=0.16.0` | Prometheus metrics collection |
| `psutil` | `>=5.8.0` | System metrics (CPU, memory) |
| `gunicorn` | `>=20.1.0` | WSGI server integration |

### Optional Dependencies

#### Async Worker Dependencies

| Package | Version | Worker Type |
|---------|---------|-------------|
| `eventlet` | `>=0.30.0` | Eventlet worker |
| `gevent` | `>=21.8.0` | Gevent worker |
| `tornado` | `>=6.1.0` | Tornado worker (⚠️ Not recommended - see compatibility issues) |

#### Redis Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `redis` | `>=4.0.0` | Redis client |

#### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | `>=7.0.0` | Testing framework |
| `pytest-cov` | `>=4.0.0` | Coverage reporting |
| `ruff` | `>=0.1.0` | Linting and formatting |
| `mypy` | `>=1.0.0` | Type checking |
| `mkdocs` | `>=1.4.0` | Documentation |
| `mkdocs-material` | `>=9.0.0` | Documentation theme |

## 🔧 Configuration Examples

### Basic Configuration

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

### Redis Integration Configuration

```python
# gunicorn_redis.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Redis configuration
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
os.environ.setdefault("REDIS_PASSWORD", "")
os.environ.setdefault("REDIS_KEY_PREFIX", "gunicorn_metrics")
os.environ.setdefault("REDIS_FORWARD_INTERVAL", "30")
```

### Production Configuration

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
os.environ.setdefault("REDIS_FORWARD_INTERVAL", "60")
```

## 🧪 Installation Verification

### Check Installation

```bash
# Verify package installation
pip show gunicorn-prometheus-exporter

# Check available worker classes
python -c "from gunicorn_prometheus_exporter import PrometheusWorker; print('Sync worker available')"
python -c "from gunicorn_prometheus_exporter import PrometheusThreadWorker; print('Thread worker available')"
```

### Test Async Workers

```bash
# Test eventlet worker
python -c "import eventlet; print('Eventlet available')" 2>/dev/null && echo "Eventlet worker ready" || echo "Install eventlet: pip install gunicorn-prometheus-exporter[eventlet]"

# Test gevent worker
python -c "import gevent; print('Gevent available')" 2>/dev/null && echo "Gevent worker ready" || echo "Install gevent: pip install gunicorn-prometheus-exporter[gevent]"

# Test tornado worker (⚠️ Not recommended - see compatibility issues)
python -c "import tornado; print('Tornado available')" 2>/dev/null && echo "Tornado worker available (⚠️ Not recommended)" || echo "Install tornado: pip install gunicorn-prometheus-exporter[tornado] (⚠️ Not recommended)"
```

### Test Redis Integration

```bash
# Test Redis connection
python -c "import redis; print('Redis available')" 2>/dev/null && echo "Redis integration ready" || echo "Install Redis: pip install gunicorn-prometheus-exporter[redis]"
```

## 🔍 Troubleshooting Installation

### Common Installation Issues

#### Missing Dependencies

**Error:** `ModuleNotFoundError: No module named 'eventlet'`

**Solution:**
```bash
# Install missing dependency
pip install gunicorn-prometheus-exporter[eventlet]
```

#### Version Conflicts

**Error:** `ImportError: cannot import name 'X' from 'Y'`

**Solution:**
```bash
# Upgrade to latest version
pip install --upgrade gunicorn-prometheus-exporter

# Or install specific version
pip install gunicorn-prometheus-exporter==0.1.3
```

### Environment Variable Issues

#### Variables Not Set

**Error:** `ValueError: Environment variable X must be set`

**Solution:**
```bash
# Set required variables
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
export PROMETHEUS_METRICS_PORT="9090"
export PROMETHEUS_BIND_ADDRESS="0.0.0.0"
export GUNICORN_WORKERS="2"
```

#### Invalid Values

**Error:** `ValueError: Invalid port number`

**Solution:**
```bash
# Use valid port range (1-65535)
export PROMETHEUS_METRICS_PORT="9090"  # Valid
export PROMETHEUS_METRICS_PORT="99999"  # Invalid
```

## 📚 Next Steps

After installation:

1. **Configure Gunicorn**: Set up your `gunicorn.conf.py` file
2. **Set Environment Variables**: Configure required environment variables
3. **Test Installation**: Run a test server and verify metrics
4. **Configure Prometheus**: Set up Prometheus to scrape metrics
5. **Monitor Application**: Start monitoring your Gunicorn application

For detailed configuration examples, see the [Configuration Guide](configuration.md).

For troubleshooting, see the [Troubleshooting Guide](troubleshooting.md).

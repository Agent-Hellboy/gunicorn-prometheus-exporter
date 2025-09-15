# Gunicorn Prometheus Exporter

A comprehensive Prometheus metrics exporter for Gunicorn WSGI servers with support for multiple worker types and advanced monitoring capabilities.

## Redis Storage Innovation

### Extended Prometheus Python Client

We've **extended the Prometheus Python client** to support Redis-based storage, creating a new architecture that separates storage from compute:

#### **Traditional Prometheus Multiprocess**
```python
# Standard approach - files only
from prometheus_client import multiprocess
multiprocess.MultiProcessCollector(registry)
# Creates files in /tmp/prometheus_multiproc/
```

#### **Our Redis Storage Extension**
```python
# Our innovation - Redis storage
from gunicorn_prometheus_exporter.storage import get_redis_storage_manager
manager = get_redis_storage_manager()
collector = manager.get_collector()
registry.register(collector)
# Stores metrics in Redis: gunicorn:*:metric:*
```

### **Architecture Benefits**

| Aspect | Traditional | Redis Storage |
|--------|-------------|---------------|
| **Storage** | Local files | Redis server |
| **Scalability** | Single instance | Multiple instances |
| **Separation** | Coupled | Separated |
| **Performance** | File I/O overhead | Direct Redis access |
| **Availability** | Server-dependent | Redis-backed |

## Quick Start

### Installation

```bash
# Basic installation
pip install gunicorn-prometheus-exporter

# With async worker support
pip install gunicorn-prometheus-exporter[async]

# With Redis storage
pip install gunicorn-prometheus-exporter[redis]

# Complete installation with all features
pip install gunicorn-prometheus-exporter[all]
```

### Basic Usage

1. **Set up environment variables**:
```bash
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
export PROMETHEUS_METRICS_PORT="9091"
export PROMETHEUS_BIND_ADDRESS="0.0.0.0"
export GUNICORN_WORKERS="2"
```

2. **Create a Gunicorn configuration file** (`gunicorn.conf.py`):
```python
# Basic Gunicorn settings
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Prometheus configuration
import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

3. **Start Gunicorn**:
```bash
gunicorn -c gunicorn.conf.py your_app:app
```

4. **Access metrics**:
```bash
curl http://0.0.0.0:9091/metrics
```

## Supported Worker Types

| Worker Type | Installation | Usage |
|-------------|-------------|-------|
| **Sync Worker** | `pip install gunicorn-prometheus-exporter` | `worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"` |
| **Thread Worker** | `pip install gunicorn-prometheus-exporter` | `worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"` |
| **Eventlet Worker** | `pip install gunicorn-prometheus-exporter[eventlet]` | `worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"` |
| **Gevent Worker** | `pip install gunicorn-prometheus-exporter[gevent]` | `worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"` |
| **Tornado Worker** | `pip install gunicorn-prometheus-exporter[tornado]` (Not recommended) | `worker_class = "gunicorn_prometheus_exporter.PrometheusTornadoWorker"` (Not recommended) |

## 📈 Available Metrics

### Worker Metrics
- `gunicorn_worker_requests_total` - Total requests handled by each worker
- `gunicorn_worker_request_duration_seconds` - Request duration histogram
- `gunicorn_worker_memory_bytes` - Memory usage per worker
- `gunicorn_worker_cpu_percent` - CPU usage per worker
- `gunicorn_worker_uptime_seconds` - Worker uptime
- `gunicorn_worker_state` - Worker state with timestamp
- `gunicorn_worker_failed_requests_total` - Failed requests with method/endpoint labels

### Master Metrics
- `gunicorn_master_worker_restarts_total` - Total worker restarts
- `gunicorn_master_signals_total` - Signal handling metrics

### Error Metrics
- `gunicorn_worker_error_handling_total` - Error tracking with method and endpoint labels

## 🧪 Testing Status

All worker types have been thoroughly tested and validated:

| Worker Type | Status | Metrics | Master Signals | Load Distribution |
|-------------|--------|---------|----------------|-------------------|
| **Sync Worker** | Working | All metrics | HUP, USR1, CHLD | Balanced |
| **Thread Worker** | Working | All metrics | HUP, USR1, CHLD | Balanced |
| **Eventlet Worker** | Working | All metrics | HUP, USR1, CHLD | Balanced |
| **Gevent Worker** | Working | All metrics | HUP, USR1, CHLD | Balanced |
| **Tornado Worker** | Not recommended | Metrics endpoint issues | HUP, USR1, CHLD | Balanced |

### Validation Includes:
- Request counting and distribution across workers
- Memory and CPU usage tracking
- Error handling with method/endpoint labels
- Master process signal tracking (HUP, USR1, CHLD)
- Worker state management with timestamps
- Multiprocess metrics collection
- Load balancing verification

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus_multiproc` | Directory for multiprocess metrics |
| `PROMETHEUS_METRICS_PORT` | `9091` | Port for metrics endpoint |
| `PROMETHEUS_BIND_ADDRESS` | `0.0.0.0` | Bind address for metrics server |
| `GUNICORN_WORKERS` | `1` | Number of workers for metrics calculation |

### Redis Configuration (Optional)

#### Redis Storage (No Files Created)
```bash
# Enable Redis storage (replaces file storage)
export REDIS_ENABLED="true"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"
```

#### Redis Forwarding (Files + Redis)
```bash
# Enable Redis forwarding (keeps files + forwards to Redis)
export REDIS_FORWARD_ENABLED="true"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"
export REDIS_FORWARD_INTERVAL="30"
```

## 🌐 Understanding the Three URLs

When deploying with Gunicorn Prometheus Exporter, you'll work with three distinct URLs:

| Service | URL | Purpose |
|---------|-----|---------|
| **Prometheus UI** | `http://localhost:9090` | Prometheus web interface for querying and visualizing metrics |
| **Your Application** | `http://localhost:8200` | Your actual web application (Gunicorn server) |
| **Metrics Endpoint** | `http://127.0.0.1:9091/metrics` | Raw metrics data for Prometheus to scrape |

> **Note**: The metrics endpoint URL is configurable through environment variables. The default port is 9091 to avoid conflicts with Prometheus UI (9090).

## 📝 Examples

### Basic Configuration
```python
# gunicorn_basic.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
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
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

### Redis Storage Configuration
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
```

## Development

### Setup
```bash
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter.git
cd gunicorn-prometheus-exporter
pip install -e ".[dev]"
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/gunicorn_prometheus_exporter --cov-report=html

# Run specific test file
pytest tests/test_plugin.py
```

### Code Quality
```bash
# Linting
ruff check src/ tests/

# Formatting
ruff format src/ tests/

```

## 📚 Documentation

For detailed documentation, visit our [documentation site](https://agent-hellboy.github.io/gunicorn-prometheus-exporter/).

### Framework-Specific Guides
- [Django Integration](examples/django-integration.md)
- [FastAPI Integration](examples/fastapi-integration.md)
- [Flask Integration](examples/flask-integration.md)
- [Pyramid Integration](examples/pyramid-integration.md)
- [Custom WSGI App](examples/custom-wsgi-app.md)

### Deployment Guides
- [Deployment Guide](examples/deployment-guide.md) - Comprehensive guide for Docker, Kubernetes, and production deployments

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](contributing.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Gunicorn team for the excellent WSGI server
- Prometheus team for the monitoring ecosystem

---

**Made with dedication for the Python community**

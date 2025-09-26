# Gunicorn Prometheus Exporter

A comprehensive Prometheus metrics exporter for Gunicorn WSGI servers with support for multiple worker types and advanced monitoring capabilities, featuring innovative Redis-based storage and advanced signal handling.

## Why This Exporter is Different

This isn't just another Prometheus exporter. I've implemented several innovative features that set this apart:

### *Redis-Based Storage Innovation*
Unlike traditional file-based multiprocess metrics, I've implemented a **Redis-backed storage system** that:
- Eliminates file system bottlenecks and race conditions
- Provides distributed metrics storage across multiple servers
- Implements automatic TTL-based cleanup for stale metrics
- Offers better performance and scalability for high-traffic applications

### *Advanced Signal Handling Architecture*
I've solved the complex challenge of capturing Gunicorn master process signals by:
- **Patching the Arbiter class** to intercept all signal handling
- Implementing **asynchronous signal capture** with thread-safe metrics updates
- Providing comprehensive master process monitoring (HUP, USR1, USR2, CHLD signals)
- Maintaining full compatibility with standard Gunicorn usage

### *Prometheus Spec Implementation*
My implementation goes beyond basic metrics collection:
- **Full Prometheus multiprocess protocol** compliance
- **Custom RedisValue class** that replaces MmapedValue for distributed storage
- **RedisMultiProcessCollector** that aggregates metrics across processes
- **Automatic metric registration** with proper cleanup and lifecycle management

### *Production-Ready Features*
- **Zero-configuration** metrics server with automatic port binding
- **Comprehensive error tracking** with method and endpoint labels
- **Resource monitoring** (CPU, memory, uptime) per worker
- **Automatic fallback** to file-based storage when Redis is unavailable
- **SSL/TLS support** for secure metrics endpoints

## Technical Highlights

### *Core Innovations*

1. **Redis Storage Backend**: Complete replacement of file-based multiprocess metrics with Redis
2. **Arbiter Patching**: Deep integration with Gunicorn's core architecture for signal capture
3. **PrometheusMixin**: Reusable mixin that adds metrics to any Gunicorn worker type
4. **Automatic Lifecycle Management**: Smart cleanup and resource management
5. **Multi-Worker Support**: Sync, Thread, Eventlet, and Gevent workers with metrics

### *Architecture Benefits*

- **No File System Dependencies**: Redis eliminates file-based race conditions
- **Distributed Ready**: Metrics can be shared across multiple application instances
- **Memory Efficient**: TTL-based cleanup prevents memory leaks
- **High Performance**: Redis operations are faster than file I/O
- **Automatic Fallback**: Seamlessly falls back to file storage when Redis is unavailable
- **Production Tested**: Handles high-traffic scenarios with ease

## Quick Start

### Installation

For detailed installation instructions, see the [Installation Guide](installation.md).

```bash
# Basic installation
pip install gunicorn-prometheus-exporter

# With Redis support
pip install gunicorn-prometheus-exporter[redis]

# With all features (Redis + async workers)
pip install gunicorn-prometheus-exporter[all]
```

### Basic Usage

#### *Traditional File-Based Setup*

```bash
# Set up environment variables
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
export PROMETHEUS_METRICS_PORT="9091"
export PROMETHEUS_BIND_ADDRESS="0.0.0.0"
export GUNICORN_WORKERS="2"

# Create gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Start Gunicorn
gunicorn -c gunicorn.conf.py your_app:app

# Access metrics
curl http://0.0.0.0:9091/metrics
```

#### *Redis-Based Setup (Recommended)*

```bash
# Enable Redis storage
export REDIS_ENABLED="true"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"
export PROMETHEUS_METRICS_PORT="9091"
export PROMETHEUS_BIND_ADDRESS="0.0.0.0"
export GUNICORN_WORKERS="2"

# Create gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

# Start Gunicorn
gunicorn -c gunicorn.conf.py your_app:app

# Access metrics
curl http://0.0.0.0:9091/metrics
```

> **Note**: Redis setup eliminates file system dependencies and provides better performance for production environments. If Redis is not available, the system automatically falls back to file-based storage.

### Understanding the Three URLs

When deploying with Gunicorn Prometheus Exporter, you'll work with three distinct URLs:

| Service              | URL                             | Purpose                                                       |
| -------------------- | ------------------------------- | ------------------------------------------------------------- |
| **Prometheus UI**    | `http://localhost:9090`         | Prometheus web interface for querying and visualizing metrics |
| **Your Application** | `http://localhost:8200`         | Your actual web application (Gunicorn server)                 |
| **Metrics Endpoint** | `http://127.0.0.1:9091/metrics` | Raw metrics data for Prometheus to scrape                     |

> **Note**: The metrics endpoint URL is configurable through environment variables. The default port is 9091 to avoid conflicts with Prometheus UI (9090).

## Documentation

### Core Documentation

- [Installation Guide](installation.md) - Detailed installation instructions
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions

### Components

#### [Metrics Component](components/metrics/)
- [Metrics Overview](components/metrics/index.md) - Metrics collection overview
- [Worker Types](components/metrics/worker-types.md) - Supported worker types
- [API Reference](components/metrics/api-reference.md) - Metrics API documentation

#### [Backend Component](components/backend/)
- [Backend Overview](components/backend/index.md) - Storage and data management
- [Redis Backend](components/backend/redis-backend.md) - Redis storage implementation
- [Architecture](components/backend/architecture.md) - System architecture details
- [API Reference](components/backend/api-reference.md) - Backend API documentation

#### [Configuration Component](components/config/)
- [Configuration Overview](components/config/index.md) - Configuration management
- [Configuration Guide](components/config/configuration.md) - Complete configuration documentation
- [API Reference](components/config/api-reference.md) - Configuration API documentation

#### [Hooks Component](components/hooks/)
- [Hooks Overview](components/hooks/index.md) - Gunicorn hooks and lifecycle management
- [API Reference](components/hooks/api-reference.md) - Hooks API documentation

#### [Plugin Component](components/plugin/)
- [Plugin Overview](components/plugin/index.md) - Prometheus-enabled worker classes
- [API Reference](components/plugin/api-reference.md) - Plugin API documentation

### Advanced Features

- [Backend Architecture](components/backend/architecture.md) - System architecture details

### Framework Integration

- [Django Integration](examples/django-integration.md)
- [FastAPI Integration](examples/fastapi-integration.md)
- [Flask Integration](examples/flask-integration.md)
- [Pyramid Integration](examples/pyramid-integration.md)
- [Custom WSGI App](examples/custom-wsgi-app.md)
- [Deployment Guide](examples/deployment-guide.md)

### Development

- [Contributing Guide](contributing.md) - How to contribute to the project
- [Development Setup](development.md) - Setting up development environment

## What Makes This Different

### *The Problem We Solved*

Traditional Prometheus exporters for Gunicorn face several limitations:
- **File-based multiprocess metrics** create race conditions and performance bottlenecks
- **No master process signal tracking** - critical for understanding server behavior
- **Limited worker type support** - only basic sync workers
- **Complex configuration** - requires extensive setup and maintenance
- **No fallback mechanism** - fails completely when storage is unavailable

### *My Solution*

I've built a comprehensive solution that addresses all these issues:

1. **Redis-Based Storage**: Eliminates file system bottlenecks with distributed storage
2. **Arbiter Patching**: Captures all master process signals for complete visibility
3. **Universal Worker Support**: Works with sync, thread, eventlet, and gevent workers
4. **Zero-Configuration**: Works out of the box with sensible defaults
5. **Automatic Fallback**: Seamlessly falls back to file storage when Redis is unavailable
6. **Production Ready**: Handles high-traffic scenarios with automatic cleanup

### *Technical Deep Dive*

- **RedisValue Class**: Custom implementation that replaces Prometheus' MmapedValue
- **RedisMultiProcessCollector**: Aggregates metrics across processes using Redis
- **PrometheusMaster**: Extended Arbiter class with signal handling and metrics
- **PrometheusMixin**: Reusable mixin for adding metrics to any worker type
- **Automatic Lifecycle Management**: Smart cleanup and resource management

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Gunicorn team for the excellent WSGI server
- Prometheus team for the monitoring ecosystem
- Redis team for the high-performance storage backend

---

**Made with dedication for the Python community**

# Gunicorn Prometheus Exporter

A comprehensive Prometheus metrics exporter for Gunicorn WSGI servers with support for multiple worker types and advanced monitoring capabilities, featuring innovative Redis-based storage, YAML configuration support, and advanced signal handling.

## Overview

The Gunicorn Prometheus Exporter provides enterprise-grade monitoring capabilities for Gunicorn applications, offering both traditional file-based and modern Redis-based metrics storage solutions, with flexible YAML-based configuration management.

## Why This Exporter is Different

This is a comprehensive Prometheus exporter that implements several innovative features:

### *Redis-Based Storage Innovation*

Unlike traditional file-based multiprocess metrics, the system implements a *Redis-backed storage system* that:

- Eliminates file system bottlenecks and race conditions
- Provides distributed metrics storage across multiple servers
- Implements automatic TTL-based cleanup for stale metrics
- Offers better performance and scalability for high-traffic applications

### *Advanced Signal Handling Architecture*

The system addresses the complex challenge of capturing Gunicorn master process signals through:

- *Patching the Arbiter class* to intercept all signal handling
- Implementing *asynchronous signal capture* with thread-safe metrics updates
- Providing comprehensive master process monitoring (HUP, USR1, USR2, CHLD signals)
- Maintaining full compatibility with standard Gunicorn usage

### *Prometheus Spec Implementation*

The implementation provides comprehensive metrics collection capabilities:

- *Full Prometheus multiprocess protocol* compliance
- *Custom RedisValue class* that replaces MmapedValue for distributed storage
- *RedisMultiProcessCollector* that aggregates metrics across processes
- *Automatic metric registration* with proper cleanup and lifecycle management

### *YAML Configuration Support*

The system provides flexible YAML-based configuration management that:

- *Structured Configuration* - Clean, readable YAML files for all settings
- *Environment Variable Override* - YAML configs can be overridden by environment variables
- *Validation and Error Handling* - Comprehensive validation with clear error messages
- *Multiple Configuration Sources* - Support for basic, Redis, SSL, and production configurations
- *Backward Compatibility* - Full compatibility with existing environment variable configuration

### *Production-Ready Features*

- *Zero-configuration* metrics server with automatic port binding
- *Comprehensive error tracking* with method and endpoint labels
- *Resource monitoring* (CPU, memory, uptime) per worker
- *Automatic fallback* to file-based storage when Redis setup fails
- *SSL/TLS support* for secure metrics endpoints

## Technical Highlights

### *Core Innovations*

1. *Redis Storage Backend*: Complete replacement of file-based multiprocess metrics with Redis
2. *YAML Configuration System*: Flexible, structured configuration management with validation
3. *Arbiter Patching*: Deep integration with Gunicorn's core architecture for signal capture
4. *PrometheusMixin*: Reusable mixin that adds metrics to any Gunicorn worker type
5. *Automatic Lifecycle Management*: Smart cleanup and resource management
6. *Multi-Worker Support*: Sync, Thread, Eventlet, and Gevent workers with metrics

### *Architecture Benefits*

- *No File System Dependencies*: Redis eliminates file-based race conditions
- *Distributed Ready*: Metrics can be shared across multiple application instances
- *Memory Efficient*: TTL-based cleanup prevents memory leaks
- *High Performance*: Redis operations are faster than file I/O
- *Automatic Fallback*: Continues with file-based storage when Redis setup fails
- *Production Tested*: Handles high-traffic scenarios with ease

## Quick Start

### Option 1: Direct Installation

For detailed setup instructions, see the [Setup Guide](setup.md).

```bash
# Install
pip install gunicorn-prometheus-exporter

# Basic setup
gunicorn -c gunicorn.conf.py your_app:app

# Access metrics at http://localhost:9091/metrics
```

> *Note*: See the [Setup Guide](setup.md) for complete configuration examples including Redis setup, Prometheus integration, and production deployment.

### Option 2: Docker Sidecar (Recommended for Production)

Pre-built Docker images are available for sidecar deployment:

```bash
# Quick test with Docker Compose
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter.git
cd gunicorn-prometheus-exporter
docker-compose up --build

# Or pull pre-built images (pin versions for reproducibility)
docker pull princekrroshan01/gunicorn-prometheus-exporter:0.2.2
docker pull princekrroshan01/gunicorn-app:0.2.2
```

**Available Services:**
- Application: http://localhost:8000
- Metrics (Sidecar): http://localhost:9091/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

**Features:**
- Multi-architecture support (AMD64, ARM64)
- Production-ready security contexts
- Automated CI/CD with GitHub Actions
- Complete monitoring stack included

> *Production requirement*: Redis-backed storage (`REDIS_ENABLED=true` and `PROMETHEUS_MULTIPROC_DIR=""`) is **required** for all containerized deployments. The provided Docker Compose and Kubernetes manifests use Redis-only mode by default. Multiprocess files are incompatible with containerized environments.

See [Docker README](../docker/README.md) and [Kubernetes Guide](../k8s/README.md) for deployment details.

### Understanding the Three URLs

When deploying with Gunicorn Prometheus Exporter, you'll work with three distinct URLs:

| Service              | URL                             | Purpose                                                       |
| -------------------- | ------------------------------- | ------------------------------------------------------------- |
| *Prometheus UI*    | `http://localhost:9090`         | Prometheus web interface for querying and visualizing metrics |
| *Your Application* | `http://localhost:8000`         | Your actual web application (Gunicorn server)                 |
| *Metrics Endpoint* | `http://127.0.0.1:9091/metrics` | Raw metrics data for Prometheus to scrape                     |

> *Note*: The metrics endpoint URL is configurable through environment variables. The default port is 9091 to avoid conflicts with Prometheus UI (9090).

## Documentation

### Core Documentation

- [Installation Guide](installation.md) - Detailed installation instructions
- [Setup Guide](setup.md) - Quick setup and getting started
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
- [YAML Configuration Guide](components/config/yaml-configuration.md) - YAML-based configuration guide
- [API Reference](components/config/api-reference.md) - Configuration API documentation

#### [Hooks Component](components/hooks/)
- [Hooks Overview](components/hooks/index.md) - Gunicorn hooks and lifecycle management
- [API Reference](components/hooks/api-reference.md) - Hooks API documentation

#### [Plugin Component](components/plugin/)
- [Plugin Overview](components/plugin/index.md) - Prometheus-enabled worker classes
- [API Reference](components/plugin/api-reference.md) - Plugin API documentation

### Advanced Features

- [Backend Architecture](components/backend/architecture.md) - System architecture details

### Deployment

- [Deployment Guide](examples/deployment-guide.md) - Production deployment strategies
- [Kubernetes Deployment](examples/kubernetes-deployment.md) - Complete K8s sidecar guide
- [DaemonSet Deployment](examples/daemonset-deployment.md) - Cluster-wide infrastructure monitoring
- [Docker Sidecar Setup](../docker/README.md) - Docker Compose deployment
- [Kubernetes Manifests](../k8s/README.md) - Complete K8s manifests

### Framework Integration

- [Django Integration](examples/django-integration.md)
- [FastAPI Integration](examples/fastapi-integration.md)
- [Flask Integration](examples/flask-integration.md)
- [Pyramid Integration](examples/pyramid-integration.md)
- [Custom WSGI App](examples/custom-wsgi-app.md)

### Development

- [Contributing Guide](contributing.md) - How to contribute to the project
- [Development Setup](development.md) - Setting up development environment

## Key Benefits

- **Redis-based storage** eliminates file system bottlenecks and race conditions
- **YAML configuration** provides structured, readable configuration management
- **Universal worker support** for sync, thread, eventlet, and gevent workers
- **Zero-configuration** setup with sensible defaults
- **Production-ready** with automatic fallback and cleanup
- **Comprehensive metrics** including request rates, response times, and resource usage

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Gunicorn team for the excellent WSGI server
- Prometheus team for the monitoring ecosystem
- Redis team for the high-performance storage backend

---

*Developed for the Python community*

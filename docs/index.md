# Gunicorn Prometheus Exporter

**Universal Gunicorn Monitoring - Works with Django, FastAPI, Flask, and any WSGI framework**

A lightweight, zero-dependency Prometheus metrics exporter for Gunicorn that works with any web framework. Monitor your Gunicorn workers, requests, and application performance without framework-specific dependencies.

## Key Features

- **Framework Agnostic**: Works with Django, FastAPI, Flask, Pyramid, Bottle, and any WSGI framework
- **Zero Framework Dependencies**: Pure Gunicorn integration
- **Drop-in Solution**: Same setup process regardless of your web framework
- **Comprehensive Metrics**: Worker performance, request tracking, error monitoring
- **Redis Support**: Optional metrics forwarding for distributed setups
- **Production Ready**: Battle-tested with retry logic and error handling

## Quick Start

### 1. Install the Package

```bash
pip install gunicorn-prometheus-exporter
```

### 2. Create Gunicorn Configuration

Create a `gunicorn.conf.py` file:

```python
# Basic configuration
bind = "0.0.0.0:8000"
workers = 4

# Prometheus exporter configuration
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
master_class = "gunicorn_prometheus_exporter.PrometheusMaster"

# Environment variables
raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc",
    "GUNICORN_WORKERS=4"
]

# Hooks for metrics setup
when_ready = "gunicorn_prometheus_exporter.default_when_ready"
on_starting = "gunicorn_prometheus_exporter.default_on_starting"
worker_int = "gunicorn_prometheus_exporter.default_worker_int"
on_exit = "gunicorn_prometheus_exporter.default_on_exit"
```

### 3. Start Your Application

```bash
gunicorn -c gunicorn.conf.py your_app:app
```

### 4. Access Metrics

Visit your configured metrics endpoint to see your Prometheus metrics!

## Available Metrics

- **Worker Metrics**: CPU, memory, uptime, request count
- **Request Metrics**: Duration, success/failure rates
- **Error Tracking**: Detailed error categorization
- **Master Metrics**: Worker restarts, signal handling

## Framework Examples

This exporter works with any framework that uses Gunicorn:

- [Django Integration](examples/django-integration.md)
- [FastAPI Integration](examples/fastapi-integration.md)
- [Flask Integration](examples/flask-integration.md)
- [Pyramid Integration](examples/pyramid-integration.md)
- [Custom WSGI App](examples/custom-wsgi-app.md)

## Why Framework Agnostic?

Unlike framework-specific monitoring solutions, this exporter:

- **Works Everywhere**: Same setup for Django, FastAPI, Flask, etc.
- **No Framework Lock-in**: Switch frameworks without changing monitoring
- **Simplified DevOps**: One monitoring solution for all your Python web apps
- **Gunicorn Native**: Leverages Gunicorn's built-in hooks and worker system

## Production Features

- **Multiprocess Support**: Handles multiple Gunicorn workers
- **Redis Forwarding**: Optional metrics aggregation
- **Signal Handling**: Graceful worker restarts and upgrades
- **Error Recovery**: Automatic retry logic for port conflicts
- **Performance Optimized**: Minimal overhead on your application

## Next Steps

- [Installation Guide](installation.md) - Detailed setup instructions
- [Configuration Reference](configuration.md) - All available options
- [Metrics Documentation](metrics.md) - Complete metrics reference
- [API Reference](api-reference.md) - Programmatic usage
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](contributing.md) for details.

---

**Ready to monitor your Gunicorn applications?** [Get started with installation →](installation.md)

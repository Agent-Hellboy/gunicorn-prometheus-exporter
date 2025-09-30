# Installation Guide

This guide provides quick installation instructions for the Gunicorn Prometheus Exporter.

## Quick Start

Install the basic package:

```bash
pip install gunicorn-prometheus-exporter
```

This includes:
- Sync and thread worker support
- Basic Prometheus metrics collection
- Multiprocess support

## Installation Options

### Basic Installation

```bash
pip install gunicorn-prometheus-exporter
```

### With Async Workers

```bash
# All async workers
pip install gunicorn-prometheus-exporter[async]

# Specific worker types
pip install gunicorn-prometheus-exporter[eventlet]  # Eventlet workers
pip install gunicorn-prometheus-exporter[gevent]    # Gevent workers
```

### With Redis Storage

```bash
pip install gunicorn-prometheus-exporter[redis]
```

### Development Installation

```bash
pip install gunicorn-prometheus-exporter[dev]
```

### Complete Installation

```bash
pip install gunicorn-prometheus-exporter[all]
```

### From Source

```bash
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter.git
cd gunicorn-prometheus-exporter
pip install -e ".[dev]"
```

## Verify Installation

```bash
# Check package installation
pip show gunicorn-prometheus-exporter

# Test basic import
python -c "from gunicorn_prometheus_exporter import PrometheusWorker; print('Installation successful')"
```

## Next Steps

1. **Configure Gunicorn**: Set up your `gunicorn.conf.py` file
2. **Set Environment Variables**: Configure required environment variables
3. **Test Installation**: Run a test server and verify metrics

For detailed configuration, see the [Configuration Guide](components/config/configuration.md).

# Gunicorn Prometheus Exporter Examples

This directory contains practical examples demonstrating how to use the `gunicorn-prometheus-exporter` with different worker types and configurations.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run a basic example:**
   ```bash
   gunicorn --config gunicorn_simple.conf.py app:app
   ```

3. **Access metrics:**
   ```bash
   curl http://localhost:9090/metrics
   ```

## Available Examples

### Basic Configuration
- **`gunicorn_simple.conf.py`** - Basic sync worker with Prometheus metrics
  ```bash
  gunicorn --config gunicorn_simple.conf.py app:app
  ```

### Worker Type Examples
- **`gunicorn_thread_worker.conf.py`** - Thread-based workers
  ```bash
  gunicorn --config gunicorn_thread_worker.conf.py app:app
  ```

- **`gunicorn_eventlet_async.conf.py`** - Eventlet workers with async app
  ```bash
  gunicorn --config gunicorn_eventlet_async.conf.py async_app:app
  ```

- **`gunicorn_gevent_async.conf.py`** - Gevent workers with async app
  ```bash
  gunicorn --config gunicorn_gevent_async.conf.py async_app:app
  ```

- **`gunicorn_tornado_async.conf.py`** - Tornado workers with async app (⚠️ Not recommended)
  ```bash
  gunicorn --config gunicorn_tornado_async.conf.py async_app:app
  ```

### Advanced Configuration
- **`gunicorn_redis_based.conf.py`** - Redis forwarding enabled
  ```bash
  gunicorn --config gunicorn_redis_based.conf.py app:app
  ```

## Applications

- **`app.py`** - Standard Flask application for sync/thread workers
- **`async_app.py`** - Async-compatible Flask application for eventlet/gevent workers

## Configuration

- **`prometheus.yml`** - Prometheus server configuration for scraping metrics
- **`requirements.txt`** - Python dependencies for the examples

## Metrics Endpoints

Each configuration exposes Prometheus metrics on different ports:

| Configuration | App Port | Metrics Port | Worker Type |
|---------------|----------|--------------|-------------|
| `gunicorn_simple.conf.py` | 8200 | 9090 | Sync |
| `gunicorn_thread_worker.conf.py` | 8001 | 9091 | Thread |
| `gunicorn_eventlet_async.conf.py` | 8005 | 9095 | Eventlet |
| `gunicorn_gevent_async.conf.py` | 8006 | 9096 | Gevent |
| `gunicorn_tornado_async.conf.py` | 8007 | 9097 | Tornado (⚠️ Not recommended) |
| `gunicorn_redis_based.conf.py` | 8008 | 9098 | Sync + Redis |

## Testing

1. **Start a server:**
   ```bash
   gunicorn --config gunicorn_simple.conf.py app:app
   ```

2. **Generate traffic:**
   ```bash
   curl http://localhost:8200/
   ```

3. **Check metrics:**
   ```bash
   curl http://localhost:9090/metrics | grep gunicorn
   ```

## Worker Types Supported

| Worker Class | Concurrency Model | Use Case |
|--------------|-------------------|----------|
| `PrometheusWorker` | Pre-fork | Simple, reliable, 1 request per worker |
| `PrometheusThreadWorker` | Threads | Multi-threaded, good for I/O-bound apps |
| `PrometheusEventletWorker` | Greenlets | Async, cooperative I/O |
| `PrometheusGeventWorker` | Greenlets | Async, cooperative I/O |
| `PrometheusTornadoWorker` | Async IOLoop | Tornado-based async workers (⚠️ Not recommended) |

## Features Demonstrated

- ✅ **Worker Metrics:** Request counts, duration, memory, CPU, uptime
- ✅ **Master Metrics:** Worker restart tracking, signal handling
- ✅ **Multi-worker Support:** All Gunicorn worker types
- ✅ **Redis Forwarding:** Metrics aggregation across processes
- ✅ **Async Compatibility:** Works with async applications
- ✅ **Production Ready:** Proper error handling and cleanup

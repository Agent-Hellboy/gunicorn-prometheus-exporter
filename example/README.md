# Gunicorn Prometheus Exporter - Configuration Examples

This directory contains different configuration approaches for storing Prometheus metrics with Gunicorn.

## Redis Storage Innovation

### Extended Prometheus Python Client

This project **extends the Prometheus Python client** to support Redis-based storage, creating a new architecture that separates storage from compute:

#### **Traditional Approach**
```python
# Standard Prometheus multiprocess - files only
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

### **Key Innovation: Storage-Compute Separation**

| Feature | Traditional | Redis Storage |
|---------|-------------|---------------|
| **Storage** | Local files | Redis server |
| **Scalability** | Single server | Multiple servers |
| **File I/O** | High overhead | No file I/O |
| **Shared Metrics** | No | Yes |
| **Architecture** | Coupled | Separated |

## Configuration Files

### 1. `gunicorn_basic.conf.py` - File-Based Storage
**Standard Prometheus multiprocess storage using files.**

- **Storage**: Files in `/tmp/prometheus_multiproc/`
- **Metrics Endpoint**: `http://localhost:9091/metrics`
- **Use Case**: Simple deployments, single server
- **Pros**: Standard, reliable, no external dependencies
- **Cons**: Files only, not shared across servers

**Usage:**
```bash
gunicorn --config gunicorn_basic.conf.py app:app
```

### 2. `gunicorn_redis_integration.conf.py` - Redis Storage
**Pure Redis-based storage (no files created).**

- **Storage**: Redis keys `gunicorn:*:metric:*` and `gunicorn:*:meta:*`
- **Metrics Endpoint**: `http://localhost:9092/metrics` (reads from Redis)
- **Use Case**: Distributed deployments, multiple servers
- **Pros**: Shared across servers, no files, scalable
- **Cons**: Requires Redis server

**Redis Flags:**
- `REDIS_ENABLED=true`: Enable Redis integration
- `REDIS_HOST`: Redis server host (default: 127.0.0.1)
- `REDIS_PORT`: Redis server port (default: 6379)
- `REDIS_DB`: Redis database number (default: 0)

**Usage:**
```bash
gunicorn --config gunicorn_redis_integration.conf.py app:app
```

## Quick Start

1. **Basic Setup (Files Only):**
   ```bash
   gunicorn --config gunicorn_basic.conf.py app:app
   ```

2. **Redis Storage (No Files):**
   ```bash
   # Start Redis server first
   redis-server
   
   # Start Gunicorn with Redis storage
   gunicorn --config gunicorn_redis_integration.conf.py app:app
   ```

## Testing Metrics

After starting any configuration, test the metrics:

```bash
# Test application (basic config)
curl http://localhost:8200/

# Test application (Redis config)
curl http://localhost:8008/

# Test metrics endpoint (basic config)
curl http://localhost:9091/metrics

# Test metrics endpoint (Redis config)
curl http://localhost:9092/metrics

# Check Redis keys (for Redis configurations)
redis-cli keys '*'
```

## Environment Variables

All configurations support these common flags:

- `PROMETHEUS_METRICS_PORT`: Metrics endpoint port (default: 9091)
- `PROMETHEUS_BIND_ADDRESS`: Metrics endpoint bind address (default: 127.0.0.1)
- `PROMETHEUS_MULTIPROC_DIR`: Directory for file-based storage (default: /tmp/prometheus_multiproc)
- `GUNICORN_WORKERS`: Number of Gunicorn workers (default: 2)

## Which Configuration Should I Use?

- **Single Server**: Use `gunicorn_basic.conf.py` (file-based storage)
- **Multiple Servers**: Use `gunicorn_redis_integration.conf.py` (Redis storage)
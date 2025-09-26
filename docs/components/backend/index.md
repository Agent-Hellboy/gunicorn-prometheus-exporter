# Backend Component

The backend component provides storage and data management capabilities for metrics collection.

## Overview

The backend component handles:

- Metrics storage and retrieval
- Multiprocess data coordination
- Redis-based distributed storage
- Data persistence and cleanup

## Storage Options

### File-Based Storage (Default)

Uses the standard Prometheus multiprocess file storage:

```python
# Standard approach - files only
from prometheus_client import multiprocess
multiprocess.MultiProcessCollector(registry)
# Creates files in /tmp/prometheus_multiproc/
```

### Redis Storage Backend

Advanced Redis-based storage for distributed environments:

```python
# Redis storage implementation
from gunicorn_prometheus_exporter.backend.service import get_redis_storage_manager
manager = get_redis_storage_manager()
collector = manager.get_collector()
registry.register(collector)
```

## Documentation

- [Redis Backend](redis-backend.md) - Complete Redis storage implementation
- [Architecture](architecture.md) - System architecture details
- [API Reference](api-reference.md) - Backend API documentation

## Configuration

### File Storage Configuration

```bash
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
```

### Redis Storage Configuration

```bash
export REDIS_ENABLED="true"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"
```

For detailed configuration options, see the [Configuration Guide](../config/configuration.md).

## Architecture Components

1. **`RedisStorageClient`** - Main client for Redis operations
2. **`RedisStorageDict`** - Storage abstraction implementing Prometheus multiprocess protocols
3. **`RedisMultiProcessCollector`** - Collector that aggregates metrics from Redis across processes
4. **`RedisValue`** - Redis-backed value implementation for individual metrics
5. **`RedisStorageManager`** - Service layer managing Redis connections and lifecycle

## Examples

See the [Examples](../examples/) for backend configuration examples.

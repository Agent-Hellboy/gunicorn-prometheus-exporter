# Backend Component

The backend component provides storage and data management capabilities for metrics collection.

## Overview

The backend component handles:

- Metrics storage and retrieval
- Multiprocess data coordination
- Redis-based distributed storage
- Data persistence and cleanup

## Design Pattern Choice: Adapter

### Why Adapter Pattern for Backend?

We chose the **Adapter pattern** for the backend component because:

1. **Interface Compatibility**: Prometheus expects a specific storage interface, Redis has a different interface
2. **Seamless Integration**: Allows Redis to work as a drop-in replacement for file-based storage
3. **Protocol Compliance**: Implements Prometheus multiprocess specification using Redis
4. **Abstraction**: Hides Redis implementation details from Prometheus client
5. **Flexibility**: Can easily add other storage backends (MongoDB, PostgreSQL, etc.)

### Alternative Patterns Considered

- **Factory Pattern**: Not suitable since we're adapting interfaces, not creating objects
- **Strategy Pattern**: Overkill since we have a clear interface to adapt to
- **Facade Pattern**: Too simplistic for the complex interface adaptation needed

### Implementation Benefits

```python
class RedisStorageDict:
    """Redis-backed dictionary for storing metric values with thread safety."""

    def read_value(self, key: str, metric_type: str = "counter", multiprocess_mode: str = "") -> Tuple[float, float]:
        # Adapt Redis interface to Prometheus interface
        metric_key = self._get_metric_key(key, metric_type, multiprocess_mode)
        value_data = self._redis.hget(metric_key, "value")
        timestamp_data = self._redis.hget(metric_key, "timestamp")
        return _safe_parse_float(value_data), _safe_parse_float(timestamp_data)

    def write_value(self, key: str, value: float, timestamp: float, metric_type: str = "counter", multiprocess_mode: str = "") -> None:
        # Adapt Prometheus interface to Redis interface
        metric_key = self._get_metric_key(key, metric_type, multiprocess_mode)
        self._redis.hset(metric_key, mapping={
            "value": value,
            "timestamp": timestamp,
            "updated_at": self._redis_now(),
        })
```

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

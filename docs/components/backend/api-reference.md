# Backend API Reference

This document provides detailed API reference for the backend component.

## Core Classes

### RedisStorageManager

Main service layer managing Redis connections and lifecycle.

```python
class RedisStorageManager:
    """Service layer managing Redis connections and lifecycle."""

    def __init__(self, host='localhost', port=6379, db=0, password=None, ssl=False):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.ssl = ssl
        self._client = None
        self._collector = None
```

**Methods:**

- `get_client()` - Get Redis client instance
- `get_collector()` - Get Redis multiprocess collector
- `is_connected()` - Check Redis connection status
- `close()` - Close Redis connections
- `health_check()` - Perform health check

### RedisStorageClient

Main client for Redis operations.

```python
class RedisStorageClient:
    """Main client for Redis operations."""

    def __init__(self, host='localhost', port=6379, db=0, password=None, ssl=False):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.ssl = ssl
        self._redis = None
```

**Methods:**

- `connect()` - Establish Redis connection
- `disconnect()` - Close Redis connection
- `ping()` - Test Redis connection
- `get(key)` - Get value by key
- `set(key, value, ttl=None)` - Set value with optional TTL
- `delete(key)` - Delete key
- `exists(key)` - Check if key exists
- `keys(pattern)` - Get keys matching pattern
- `flushdb()` - Flush current database

### RedisStorageDict

Storage abstraction implementing Prometheus multiprocess protocols.

```python
class RedisStorageDict:
    """Storage abstraction implementing Prometheus multiprocess protocols."""

    def __init__(self, client, prefix='gunicorn'):
        self.client = client
        self.prefix = prefix
```

**Methods:**

- `__getitem__(key)` - Get item by key
- `__setitem__(key, value)` - Set item by key
- `__delitem__(key)` - Delete item by key
- `__contains__(key)` - Check if key exists
- `__iter__()` - Iterate over keys
- `__len__()` - Get number of items
- `keys()` - Get all keys
- `values()` - Get all values
- `items()` - Get all key-value pairs
- `clear()` - Clear all items
- `update(other)` - Update with other dict

### FactoryUtilsMixin

Mixin class providing factory utilities for Redis value classes.

```python
class FactoryUtilsMixin:
    """Mixin class for factory utilities."""

    def create_redis_value_class(self, redis_client, redis_key_prefix=None):
        """Create a RedisValue class configured with Redis client.

        Args:
            redis_client: Redis client instance
            redis_key_prefix: Prefix for Redis keys (defaults to config.redis_key_prefix)

        Returns:
            Configured RedisValue class
        """
```

**Methods:**

- `create_redis_value_class(redis_client, redis_key_prefix=None)` - Create configured RedisValue class

### CleanupUtilsMixin

Mixin class providing cleanup utilities for Redis operations.

```python
class CleanupUtilsMixin:
    """Mixin class for cleanup utilities."""

    def cleanup_process_keys(self, pid, redis_client, redis_key_prefix=None):
        """Clean up Redis keys for a specific process.

        Args:
            pid: Process ID to clean up
            redis_client: Redis client instance
            redis_key_prefix: Prefix for Redis keys (defaults to config.redis_key_prefix)
        """
```

**Methods:**

- `cleanup_process_keys(pid, redis_client, redis_key_prefix=None)` - Clean up process-specific Redis keys

### RedisMultiProcessCollector

Collector that aggregates metrics from Redis across processes.

```python
class RedisMultiProcessCollector:
    """Collector that aggregates metrics from Redis across processes."""

    def __init__(self, storage_dict, registry=None):
        self.storage_dict = storage_dict
        self.registry = registry or CollectorRegistry()
```

**Methods:**

- `collect()` - Collect metrics from Redis
- `describe()` - Describe metrics
- `register(metric)` - Register metric
- `unregister(metric)` - Unregister metric

### RedisValue

Redis-backed value implementation for individual metrics.

```python
class RedisValue:
    """Redis-backed value implementation for individual metrics."""

    def __init__(self, client, key, value_type='float'):
        self.client = client
        self.key = key
        self.value_type = value_type
```

**Methods:**

- `get()` - Get current value
- `set(value)` - Set value
- `inc(value=1)` - Increment value
- `dec(value=1)` - Decrement value
- `reset()` - Reset to default value

## Key Management

### Key Format

Redis keys follow a structured format:

```
{prefix}:{metric_type}_{mode}:{pid}:{data_type}:{hash}
```

**Components:**

- `prefix` - Key prefix (default: 'gunicorn')
- `metric_type` - Type of metric (counter, gauge, histogram, summary)
- `mode` - Multiprocess mode (all, liveall, max, min, sum, mostrecent)
- `pid` - Process ID
- `data_type` - Data type (metric, meta, samples)
- `hash` - Hash of metric name and labels

### Key Examples

```
gunicorn:gauge_all:12345:metric:abc123
gunicorn:counter:12345:meta:def456
gunicorn:histogram:12345:metric:ghi789
```

## Multiprocess Modes

### Mode Types

| Mode | Description | Use Case |
|------|-------------|----------|
| `all` | All processes (including dead ones) | Per-worker monitoring with PID labels |
| `liveall` | All live processes | Current process monitoring |
| `max` | Maximum value across processes | Peak resource usage |
| `min` | Minimum value across processes | Minimum resource usage |
| `sum` | Sum of values across processes | Total resource consumption |
| `mostrecent` | Most recent value | Latest metric values |

### Mode Implementation

```python
def aggregate_metrics(mode, values):
    """Aggregate metrics based on mode."""
    if mode == 'all':
        return values
    elif mode == 'liveall':
        return [v for v in values if is_process_alive(v.pid)]
    elif mode == 'max':
        return max(values, key=lambda x: x.value)
    elif mode == 'min':
        return min(values, key=lambda x: x.value)
    elif mode == 'sum':
        return sum(v.value for v in values)
    elif mode == 'mostrecent':
        return max(values, key=lambda x: x.timestamp)
```

## Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_ENABLED` | bool | `false` | Enable Redis storage backend |
| `REDIS_HOST` | str | `localhost` | Redis server hostname |
| `REDIS_PORT` | int | `6379` | Redis server port |
| `REDIS_DB` | int | `0` | Redis database number |
| `REDIS_KEY_PREFIX` | str | `gunicorn` | Prefix for Redis keys |
| `REDIS_TTL_SECONDS` | int | `300` | Key expiration time in seconds |
| `REDIS_PASSWORD` | str | - | Redis password (if required) |
| `REDIS_SSL` | bool | `false` | Enable SSL connection to Redis |

### Configuration Loading

```python
def load_redis_config():
    """Load Redis configuration from environment."""
    return {
        'enabled': os.getenv('REDIS_ENABLED', 'false').lower() == 'true',
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', '6379')),
        'db': int(os.getenv('REDIS_DB', '0')),
        'prefix': os.getenv('REDIS_KEY_PREFIX', 'gunicorn'),
        'ttl': int(os.getenv('REDIS_TTL_SECONDS', '300')),
        'password': os.getenv('REDIS_PASSWORD'),
        'ssl': os.getenv('REDIS_SSL', 'false').lower() == 'true'
    }
```

## Error Handling

### Connection Errors

```python
class RedisConnectionError(Exception):
    """Redis connection error."""
    pass

class RedisTimeoutError(Exception):
    """Redis timeout error."""
    pass

class RedisAuthenticationError(Exception):
    """Redis authentication error."""
    pass
```

### Error Recovery

```python
def with_retry(func, max_retries=3, delay=1):
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except (RedisConnectionError, RedisTimeoutError) as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay * (2 ** attempt))
```

## Utility Functions

### redis_key

Utility function for generating consistent Redis keys.

```python
def redis_key(
    metric_name: str,
    name: str,
    labelnames: List[str],
    labelvalues: List[str],
    help_text: str,
) -> str:
    """Format a key for use in Redis, similar to mmap_key.

    Args:
        metric_name: Name of the metric
        name: Sample name
        labelnames: List of label names
        labelvalues: List of label values
        help_text: Help text for the metric

    Returns:
        JSON-formatted key string for Redis storage
    """
```

**Usage:**

```python
from gunicorn_prometheus_exporter.backend.core.dict import redis_key

key = redis_key(
    metric_name="gunicorn_requests_total",
    name="requests_total",
    labelnames=["method", "status"],
    labelvalues=["GET", "200"],
    help_text="Total number of requests"
)
# Returns: '["gunicorn_requests_total", "requests_total", {"method": "GET", "status": "200"}, "Total number of requests"]'
```

## Performance Optimization

### Connection Pooling

```python
class RedisConnectionPool:
    """Redis connection pool for better performance."""

    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.pool = []
        self.in_use = set()
```

### Batch Operations

```python
def batch_set(client, items, ttl=None):
    """Set multiple items in batch."""
    pipe = client.pipeline()
    for key, value in items:
        pipe.set(key, value, ex=ttl)
    return pipe.execute()
```

## Monitoring

### Health Checks

```python
def health_check(manager):
    """Perform comprehensive health check."""
    try:
        # Test connection
        client = manager.get_client()
        client.ping()

        # Test write/read
        test_key = f"{manager.prefix}:health_check"
        client.set(test_key, "ok", ex=60)
        value = client.get(test_key)
        client.delete(test_key)

        return value == b"ok"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
```

## Conditional Imports and Fallback Behavior

### Redis Availability Detection

The backend uses conditional imports to handle cases where Redis is not available:

```python
# Conditional Redis import - only import when needed
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
```

### Collector Availability

The Redis collector is conditionally imported based on Redis availability:

```python
# Conditional import of Redis collector
try:
    from .collector import RedisMultiProcessCollector
    REDIS_COLLECTOR_AVAILABLE = True
except ImportError:
    RedisMultiProcessCollector = None
    REDIS_COLLECTOR_AVAILABLE = False
```

### Fallback Behavior

When Redis is not available, the system gracefully falls back to file-based storage:

```python
def _get_default_redis_client(self):
    """Get default Redis client from environment variables."""
    redis_url = os.environ.get("PROMETHEUS_REDIS_URL")
    if redis_url:
        try:
            return redis.from_url(redis_url)
        except redis.ConnectionError:
            logger.warning("Redis connection failed, falling back to file storage")
            return None
    return None
```

### Error Handling Patterns

The backend implements comprehensive error handling:

```python
def _redis_now(self) -> float:
    """Get current timestamp using Redis server time for coherence."""
    try:
        sec, usec = self._redis.time()
        return sec + usec / 1_000_000.0
    except Exception as e:
        logger.debug("Failed to get Redis time, falling back to local time: %s", e)
        return time.time()
```

### Metrics

The backend provides additional metrics for monitoring:

- `redis_connections_total` - Total Redis connections
- `redis_operations_total` - Total Redis operations
- `redis_operation_duration_seconds` - Redis operation duration
- `redis_errors_total` - Total Redis errors

## Related Documentation

- [Redis Backend](redis-backend.md) - Complete Redis storage implementation
- [Backend Architecture](../backend-architecture.md) - System architecture details
- [Configuration Guide](../configuration.md) - Configuration options

# Backend API Reference

This document provides detailed API reference for the backend component.

## Core Classes

### RedisStorageDict

Dictionary-like interface for Redis storage implementing the `StorageDictProtocol`.

```python
class RedisStorageDict:
    """Dictionary-like interface for Redis storage."""

    def __init__(self, redis_client, key_prefix=''):
        self.redis_client = redis_client
        self.key_prefix = key_prefix
```

**Methods:**

- `read_value(key)` - Read value from Redis
- `write_value(key, value)` - Write value to Redis
- `cleanup_dead_worker(pid)` - Clean up keys for dead worker process
- `__getitem__(key)` - Get value by key
- `__setitem__(key, value)` - Set key-value pair
- `__delitem__(key)` - Delete key
- `__contains__(key)` - Check if key exists
- `__iter__()` - Iterate over keys
- `__len__()` - Get number of items
- `keys()` - Get all keys
- `values()` - Get all values
- `items()` - Get all key-value pairs
- `clear()` - Clear all items
- `update(other)` - Update with other dict

### RedisStorageManager

The main manager class for Redis-based metrics storage with proper lifecycle management.

```python
class RedisStorageManager:
    """Manages Redis-based metrics storage with proper lifecycle management."""

    def __init__(self, redis_client_factory=None, value_class_factory=None):
        """Initialize Redis storage manager.

        Args:
            redis_client_factory: Factory function to create Redis client (for testing)
            value_class_factory: Factory function to create value class (for testing)
        """
```

**Key Methods:**

- `setup() -> bool` - Set up Redis-based metrics storage
- `teardown() -> None` - Teardown Redis storage and restore original behavior
- `is_enabled() -> bool` - Check if Redis storage is enabled and working
- `get_client() -> Optional[RedisClientProtocol]` - Get the Redis client instance
- `cleanup_keys() -> None` - Clean up Redis keys for dead processes
- `get_collector()` - Get Redis-based collector for metrics collection

**Note**: The mixin classes (`FactoryUtilsMixin`, `CleanupUtilsMixin`) are internal implementation details and not part of the public API.

### RedisMultiProcessCollector

Collector that aggregates metrics from Redis across processes.

```python
class RedisMultiProcessCollector:
    """Collector for Redis-based multi-process mode."""

    def __init__(self, registry, redis_client=None, redis_key_prefix=None):
        """Initialize Redis multi-process collector.

        Args:
            registry: Prometheus registry to register with
            redis_client: Redis client instance (optional)
            redis_key_prefix: Key prefix for Redis keys (optional)
        """
```

**Key Methods:**

- `collect()` - Collect metrics from Redis
- `merge_from_redis(redis_client, redis_key_prefix=None, accumulate=True)` - Static method to merge metrics from Redis

**Note**: The collector requires a registry parameter and does not default to `CollectorRegistry()`. It also requires either a `redis_client` parameter or `PROMETHEUS_REDIS_URL` environment variable to be set.

### RedisValue

Redis-backed value implementation for individual metrics. This class is not instantiated directly by users but is used internally by the Prometheus client when Redis storage is enabled.

```python
class RedisValue:
    """A float backed by Redis for multi-process mode.

    This replaces MmapedValue for storing metrics in Redis instead of files.
    """

    def __init__(
        self,
        typ,
        metric_name,
        name,
        labelnames,
        labelvalues,
        help_text,
        multiprocess_mode="",
        redis_client=None,
        redis_key_prefix=None,
        **kwargs,
    ):
        """Initialize RedisValue with Redis client and key prefix.

        Args:
            typ: Metric type (counter, gauge, histogram, summary)
            metric_name: Name of the metric
            name: Sample name
            labelnames: Label names
            labelvalues: Label values
            help_text: Help text for the metric
            multiprocess_mode: Multiprocess mode for gauge metrics
            redis_client: Redis client instance (required)
            redis_key_prefix: Prefix for Redis keys
        """
```

**Key Methods:**

- `get()` - Get current value
- `set(value, timestamp=None)` - Set value and optional timestamp
- `inc(amount=1)` - Increment value by amount
- `get_timestamp()` - Get current timestamp
- `set_exemplar(_exemplar)` - Set exemplar (not implemented for Redis yet)
- `get_exemplar()` - Get exemplar (not implemented for Redis yet)

**Note**: Users do not instantiate `RedisValue` directly. It is created automatically by the Prometheus client when Redis storage is enabled via `RedisStorageManager.setup()`.

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

The actual aggregation logic is implemented in `RedisMultiProcessCollector._accumulate_metrics()` and handles:

- **Worker lifetime management**: Dead PID cleanup and process tracking
- **Histogram bucket accumulation**: Proper bucket value aggregation
- **Metric wrapper handling**: Works with `MetricWrapperBase` instances, not simple value/timestamp pairs
- **Complex aggregation rules**: Implements Prometheus multiprocess specification

**Note**: The aggregation logic is internal to the collector and not exposed as a public API. For custom aggregation needs, refer to the `RedisMultiProcessCollector` implementation in `backend/core/collector.py`.

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

### Configuration

Configuration is driven by the `ExporterConfig` singleton and environment variables. See [Configuration Guide](../config/configuration.md) for complete details.

**Key Configuration Properties:**
- `config.redis_enabled` - Enable/disable Redis storage
- `config.redis_host` - Redis server host
- `config.redis_port` - Redis server port
- `config.redis_db` - Redis database number
- `config.redis_key_prefix` - Key prefix for Redis keys
- `config.redis_ttl_seconds` - TTL for Redis keys
- `config.redis_password` - Redis password
- `config.redis_ssl` - Enable SSL/TLS

**Example:**
```python
from gunicorn_prometheus_exporter.config import config

# Check if Redis is enabled
if config.redis_enabled:
    print(f"Redis host: {config.redis_host}:{config.redis_port}")
    print(f"Key prefix: {config.redis_key_prefix}")
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

**Note**: The `redis_key` function is located in `backend/core/dict.py` and returns a JSON string, not a tuple.

## Performance Optimization

The Redis backend uses the standard Redis Python client with built-in connection pooling and health checks:

```python
# Redis client configuration with performance optimizations
redis.from_url(
    redis_url,
    decode_responses=False,
    socket_timeout=5.0,  # 5 second timeout for socket operations
    socket_connect_timeout=5.0,  # 5 second timeout for connection
    retry_on_timeout=True,  # Retry on timeout
    health_check_interval=30,  # Health check every 30 seconds
)
```

**Note**: The backend doesn't provide custom connection pooling or batch operations. It uses the standard Redis client's built-in features for optimal performance.

## Monitoring

### Health Checks

The Redis storage manager provides built-in health checking through its setup process:

```python
def check_redis_health():
    """Check Redis storage health using the manager."""
    from gunicorn_prometheus_exporter.backend import get_redis_storage_manager

    manager = get_redis_storage_manager()

    # Check if Redis is enabled and working
    if not manager.is_enabled():
        return False

    # Get client and test connection
    client = manager.get_client()
    if client is None:
        return False

    try:
        # Test Redis connection
        client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False
```

**Note**: The `RedisStorageManager` doesn't have a `prefix` attribute or `get_client()` method that returns a raw Redis connection. Use `manager.get_client()` to get the Redis client protocol instance.

## Conditional Imports and Fallback Behavior

### Redis Availability Detection

The backend uses conditional imports in `backend/core/__init__.py` to handle Redis availability:

```python
# Conditional import of Redis collector
try:
    from .collector import RedisMultiProcessCollector
    REDIS_COLLECTOR_AVAILABLE = True
except ImportError:
    RedisMultiProcessCollector = None
    REDIS_COLLECTOR_AVAILABLE = False
```

### Redis Client Configuration

The `RedisMultiProcessCollector` provides a default Redis client factory:

```python
def _get_default_redis_client(self):
    """Get default Redis client from environment variables."""
    redis_url = os.environ.get("PROMETHEUS_REDIS_URL")
    if redis_url:
        return redis.from_url(
            redis_url,
            decode_responses=False,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            health_check_interval=30,
        )

    # Try to connect to local Redis
    try:
        return redis.Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=False,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    except redis.ConnectionError:
        return None
```

### Error Handling Patterns

The `RedisStorageDict` implements timestamp fallback:

```python
def _redis_now(self) -> float:
    """Get current timestamp using Redis server time for coherence.

    Falls back to local time if Redis time is not available.
    """
    try:
        sec, usec = self._redis.time()  # returns (seconds, microseconds)
        return sec + usec / 1_000_000.0
    except Exception as e:
        logger.debug("Failed to get Redis time, falling back to local time: %s", e)
        return time.time()
```

### Fallback Mechanism

When Redis setup fails, the system continues with file-based storage:

```python
def setup(self) -> bool:
    """Set up Redis-based metrics storage."""
    if not config.redis_enabled:
        logger.debug("Redis is not enabled, skipping Redis metrics setup")
        return False

    try:
        # Create Redis client and test connection
        self._redis_client = self._redis_client_factory()
        self._redis_client.ping()
        # ... setup Redis storage ...
        return True
    except Exception as e:
        logger.error("Failed to setup Redis metrics: %s", e)
        self._cleanup()
        return False
```

**Note**: The fallback to file-based storage is automatic when Redis setup fails. The Prometheus client library continues using its default file-based multiprocess storage mechanism.

### Redis Metrics

**Important**: The backend does not expose Redis-specific metrics like `redis_operations_total` or `redis_errors_total`. The Redis backend is a storage mechanism for existing Gunicorn metrics, not a source of additional metrics.

The Redis backend stores the same metrics that are available with file-based storage:
- All Gunicorn worker metrics (requests, duration, memory, CPU, etc.)
- All Gunicorn master metrics (worker restarts, etc.)

The only difference is the storage mechanism (Redis vs files), not the metrics themselves.

## Global Functions

The backend provides several global convenience functions for managing Redis storage:

### Storage Management Functions

```python
def get_redis_storage_manager() -> RedisStorageManager:
    """Get or create global Redis storage manager."""
```

```python
def setup_redis_metrics() -> bool:
    """Set up Redis-based metrics storage."""
```

```python
def teardown_redis_metrics() -> None:
    """Teardown Redis-based metrics storage."""
```

```python
def is_redis_enabled() -> bool:
    """Check if Redis metrics are enabled and working."""
```

### Client and Collector Functions

```python
def get_redis_client():
    """Get the Redis client instance."""
```

```python
def cleanup_redis_keys() -> None:
    """Clean up Redis keys for dead processes."""
```

```python
def get_redis_collector():
    """Get Redis-based collector for metrics collection."""
```

## Related Documentation

- [Redis Backend](redis-backend.md) - Complete Redis storage implementation
- [Backend Architecture](../backend-architecture.md) - System architecture details
- [Configuration Guide](../configuration.md) - Configuration options

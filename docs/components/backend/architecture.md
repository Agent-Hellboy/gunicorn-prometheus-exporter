# Backend Architecture

## Overview

The Gunicorn Prometheus Exporter implements a complete **Redis-based storage backend** that extends the Prometheus Python client to support distributed metrics storage. This implementation follows Prometheus multiprocess specifications while providing enhanced scalability and separation of concerns.

## Architecture Components

### Core Components

Our backend consists of several key components that work together to provide seamless Redis integration:

#### 1. **RedisStorageClient** (`backend/core/client.py`)

The main client for Redis operations, providing:

- **Connection Management**: Handles Redis connections with pooling and error handling
- **Key Generation**: Creates structured Redis keys with embedded process information
- **Value Operations**: Implements read/write operations for metric data
- **Metadata Management**: Handles metric metadata storage and retrieval
- **TTL Support**: Automatic key expiration for cleanup

```python
class RedisStorageClient:
    def __init__(self, redis_client: RedisClientProtocol, key_prefix: str = "gunicorn"):
        self._redis_client = redis_client
        self._key_prefix = key_prefix
        self._redis_dict = RedisStorageDict(redis_client, key_prefix)
```

#### 2. **RedisStorageDict** (`backend/core/client.py`)

Storage abstraction layer implementing Prometheus multiprocess protocols:

- **Protocol Compliance**: Implements `StorageDictProtocol` for Prometheus compatibility
- **Multiprocess Mode Support**: Handles all Prometheus multiprocess modes
- **Atomic Operations**: Thread-safe metric updates using Redis transactions
- **Error Handling**: Graceful fallback mechanisms

```python
class RedisStorageDict:
    def read_value(self, key: str, metric_type: str = "counter", multiprocess_mode: str = "") -> Tuple[float, float]:
        # Returns (value, timestamp) tuple

    def write_value(self, key: str, value: float, timestamp: float, metric_type: str = "counter", multiprocess_mode: str = "") -> None:
        # Writes metric value with timestamp
```

#### 3. **RedisMultiProcessCollector** (`backend/core/collector.py`)

Collector that aggregates metrics from Redis across multiple processes:

- **Metric Aggregation**: Implements Prometheus multiprocess aggregation logic
- **Process Discovery**: Scans Redis for metric keys from all processes
- **Mode Handling**: Correctly processes different multiprocess modes
- **Label Preservation**: Maintains all metric labels and metadata

```python
class RedisMultiProcessCollector:
    def collect(self) -> Generator[Metric, None, None]:
        # Yields aggregated metrics from Redis

    def _read_metrics_from_redis(self) -> Dict[str, Any]:
        # Reads all metrics from Redis storage
```

#### 4. **RedisValue** (`backend/core/values.py`)

Redis-backed value implementation for individual metrics:

- **Value Storage**: Stores individual metric values in Redis
- **Timestamp Management**: Tracks metric timestamps
- **Exemplar Support**: Handles exemplar data for tracing
- **Process Cleanup**: Supports process-specific cleanup operations

```python
class RedisValue:
    def inc(self, amount: float = 1.0) -> None:
        # Increment counter value

    def set(self, value: float) -> None:
        # Set gauge value

    def get(self) -> float:
        # Get current value
```

#### 5. **RedisStorageManager** (`backend/service/manager.py`)

Service layer managing Redis connections and lifecycle:

- **Connection Management**: Creates and manages Redis connections
- **Value Class Factory**: Creates Redis-backed value classes
- **Collector Management**: Provides Redis-based collectors
- **Lifecycle Management**: Handles setup and teardown operations

```python
class RedisStorageManager:
    def setup(self) -> None:
        # Initialize Redis storage backend

    def get_collector(self) -> RedisMultiProcessCollector:
        # Returns Redis-based collector

    def teardown(self) -> None:
        # Clean up Redis resources
```

## Redis Key Architecture

### Key Structure

We use a structured key format that embeds process information and multiprocess modes:

```
gunicorn:{metric_type}_{mode}:{pid}:{data_type}:{hash}
```

### Key Components

- **`gunicorn`**: Fixed prefix for all keys
- **`{metric_type}_{mode}`**: Metric type and multiprocess mode (e.g., `gauge_all`, `counter`)
- **`{pid}`**: Process ID for process isolation
- **`{data_type}`**: Either `metric` or `meta` for data vs metadata
- **`{hash}`**: MD5 hash of the original metric key for stability

### Examples

```
gunicorn:gauge_all:12345:metric:abc123def456
gunicorn:counter:12345:meta:def456ghi789
gunicorn:histogram:12345:metric:ghi789jkl012
```

### Key Generation

Keys are generated using deterministic hashing:

```python
def _get_metric_key(self, key: str, metric_type: str = "counter", multiprocess_mode: str = "") -> str:
    import os
    import hashlib

    pid = os.getpid()
    key_hash = hashlib.md5(key.encode("utf-8"), usedforsecurity=False).hexdigest()

    # Include multiprocess mode in key structure for gauge metrics
    if metric_type == "gauge" and multiprocess_mode:
        type_with_mode = f"{metric_type}_{multiprocess_mode}"
    else:
        type_with_mode = metric_type

    return f"{self._key_prefix}:{type_with_mode}:{pid}:metric:{key_hash}"
```

## Data Storage Format

### Metric Data Storage

Metrics are stored as Redis hashes with the following structure:

```redis
HSET gunicorn:gauge_all:12345:metric:abc123def456
  value "42.5"
  timestamp "1640995200.123"
  updated_at "1640995200.123"
```

### Metadata Storage

Metadata is stored separately for efficient querying:

```redis
HSET gunicorn:gauge_all:12345:meta:abc123def456
  multiprocess_mode "all"
  metric_name "gunicorn_worker_memory_bytes"
  labelnames "worker_id,pid"
  help_text "Memory usage per worker"
  original_key "[\"gunicorn_worker_memory_bytes\",\"memory\",{\"worker_id\":\"worker_1_1640995200\",\"pid\":\"12345\"},\"Memory usage per worker\"]"
```

## Prometheus Specification Compliance

### Multiprocess Mode Support

Our implementation correctly handles all Prometheus multiprocess modes:

| Mode | Description | Implementation |
|------|-------------|----------------|
| `all` | All processes (including dead ones) | Stores all metric instances with PID labels |
| `liveall` | All live processes | Filters out dead processes during collection |
| `live` | Only live processes (default) | Same as liveall for our use case |
| `max` | Maximum value across processes | Aggregates using Redis MAX operations |
| `min` | Minimum value across processes | Aggregates using Redis MIN operations |
| `sum` | Sum of values across processes | Aggregates using Redis SUM operations |
| `mostrecent` | Most recent value | Uses timestamp-based selection |

### Metric Type Handling

Full support for all Prometheus metric types:

- **Counters**: Monotonic increasing values
- **Gauges**: Values that can go up and down
- **Histograms**: Distribution of values in buckets
- **Summaries**: Quantile-based aggregations

### Label Preservation

All metric labels and metadata are preserved:

- **Label Names**: Stored in metadata for reconstruction
- **Label Values**: Embedded in Redis keys and metadata
- **Help Text**: Preserved for metric documentation
- **Metric Names**: Maintained for proper identification

## Performance Optimizations

### Batch Operations

Groups Redis operations for efficiency:

```python
def read_all_values(self) -> Dict[str, Tuple[float, float]]:
    # Uses pipeline for batch operations
    with self._redis.pipeline() as pipe:
        for metric_key in self._redis.scan_iter(match=pattern, count=100):
            pipe.hgetall(metric_key)
        results = pipe.execute()
```

### Streaming Collection

Processes metrics in batches to avoid memory overload:

```python
def _read_metrics_from_redis(self) -> Dict[str, Any]:
    # Processes keys in batches of 100
    for metric_key in redis_client.scan_iter(match=pattern, count=100):
        # Process each key individually
```

### Lock-Free Reads

Uses Redis `scan_iter` for non-blocking key iteration:

```python
# Non-blocking key iteration
for metric_key in self._redis.scan_iter(match=pattern, count=100):
    with self._lock:  # Only lock per key, not entire scan
        # Process individual key
```

### Metadata Caching

Reduces Redis lookups for frequently accessed metadata:

```python
def _get_multiprocess_mode_from_metadata(self, key: str, metric_type: str) -> str:
    # Caches metadata lookups to reduce Redis calls
```

## Error Handling and Fallback

### Graceful Degradation

The system gracefully handles Redis unavailability:

```python
def _get_default_redis_client(self) -> Optional[RedisClientProtocol]:
    try:
        return redis.Redis.from_url(redis_url)
    except redis.ConnectionError:
        logger.warning("Redis connection failed, falling back to file storage")
        return None
```

### Connection Retry Logic

Implements retry logic for transient failures:

```python
def _redis_now(self) -> float:
    try:
        # Try Redis server time first
        return self._redis.time()[0]
    except Exception:
        # Fallback to local time
        return time.time()
```

### Comprehensive Error Handling

The backend implements multiple layers of error handling:

#### 1. **Import-Level Error Handling**

```python
# Conditional Redis import - only import when needed
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
```

#### 2. **Connection-Level Error Handling**

```python
def setup(self) -> bool:
    """Set up Redis-based metrics storage."""
    if not config.redis_enabled:
        logger.debug("Redis is not enabled, skipping Redis metrics setup")
        return False

    try:
        # Create Redis client
        self._redis_client = self._redis_client_factory()

        # Test connection
        self._redis_client.ping()
        logger.debug("Connected to Redis successfully")
        return True

    except Exception as e:
        logger.error("Failed to setup Redis metrics: %s", e)
        self._cleanup()
        return False
```

#### 3. **Operation-Level Error Handling**

```python
def _safe_parse_float(data: Union[bytes, bytearray, str, None], default: float = 0.0) -> float:
    """Safely parse bytes/string to float with error handling."""
    if data is None:
        return default

    try:
        if isinstance(data, (bytes, bytearray)):
            return float(data.decode("utf-8"))
        return float(data)
    except (ValueError, UnicodeDecodeError):
        logger.debug("Failed to parse float value: %s, using default: %s", data, default)
        return default
```

#### 4. **Timeout and Retry Logic**

```python
def _redis_operation_with_retry(self, operation, max_retries=3, delay=0.1):
    """Execute Redis operation with retry logic."""
    for attempt in range(max_retries):
        try:
            return operation()
        except (redis.ConnectionError, redis.TimeoutError) as e:
            if attempt == max_retries - 1:
                logger.error("Redis operation failed after %d attempts: %s", max_retries, e)
                raise
            logger.warning("Redis operation failed (attempt %d/%d): %s", attempt + 1, max_retries, e)
            time.sleep(delay * (2 ** attempt))
```

#### 5. **Fallback Mechanisms**

```python
def _get_multiprocess_mode_from_metadata(self, key: str, metric_type: str) -> str:
    """Get multiprocess mode from metadata with fallback."""
    try:
        metadata_key = self._get_metadata_key(key, metric_type)
        metadata = self._redis.hgetall(metadata_key)
        if metadata:
            return _safe_decode_bytes(metadata.get(b"multiprocess_mode", b"")).decode("utf-8")
    except Exception as e:
        logger.debug("Failed to get multiprocess mode from metadata: %s", e)

    # Fallback to default mode
    return "all" if metric_type == "gauge" else ""
```

### Error Recovery Strategies

#### 1. **Automatic Fallback to File Storage**

When Redis is unavailable, the system automatically falls back to file-based storage:

```python
def _create_redis_client(self) -> RedisClientProtocol:
    """Create Redis client with fallback to file storage."""
    try:
        redis_url = f"redis://{config.redis_host}:{config.redis_port}/{config.redis_db}"
        if config.redis_password:
            redis_url = f"redis://:{config.redis_password}@{config.redis_host}:{config.redis_port}/{config.redis_db}"

        client = redis.from_url(redis_url)
        client.ping()  # Test connection
        return client

    except Exception as e:
        logger.warning("Redis connection failed, falling back to file storage: %s", e)
        return None
```

#### 2. **Graceful Degradation of Features**

```python
def is_redis_enabled(self) -> bool:
    """Check if Redis is enabled and available."""
    return (
        config.redis_enabled and
        REDIS_AVAILABLE and
        self._redis_client is not None
    )
```

#### 3. **Resource Cleanup on Failure**

```python
def _cleanup(self) -> None:
    """Clean up Redis resources."""
    try:
        if self._redis_client:
            self._redis_client.close()
    except Exception as e:
        logger.debug("Error during Redis cleanup: %s", e)
    finally:
        self._redis_client = None
        self._redis_value_class = None
```

## Integration Points

### Prometheus Client Integration

The backend integrates seamlessly with the Prometheus Python client:

```python
# Replace default multiprocess collector
from gunicorn_prometheus_exporter.backend.service import get_redis_storage_manager

manager = get_redis_storage_manager()
collector = manager.get_collector()
registry.register(collector)
```

### Gunicorn Integration

Hooks into Gunicorn's lifecycle for automatic setup:

```python
def redis_when_ready(server):
    """Setup Redis storage when Gunicorn is ready."""
    from gunicorn_prometheus_exporter.backend.service import setup_redis_metrics
    setup_redis_metrics()
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_ENABLED` | `false` | Enable Redis storage backend |
| `REDIS_HOST` | `127.0.0.1` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis database number |
| `REDIS_PASSWORD` | *(none)* | Redis password (optional) |
| `REDIS_KEY_PREFIX` | `gunicorn` | Prefix for Redis keys |
| `REDIS_TTL_SECONDS` | `300` | Key expiration time |

### Programmatic Configuration

```python
from gunicorn_prometheus_exporter.backend.service import RedisStorageManager

manager = RedisStorageManager(
    redis_host="localhost",
    redis_port=6379,
    redis_db=0,
    key_prefix="myapp",
    ttl_seconds=600
)
```

## Testing and Validation

### Unit Tests

Comprehensive unit tests cover all components:

- **Storage Operations**: Read/write operations
- **Key Generation**: Proper key structure and hashing
- **Multiprocess Modes**: All mode implementations
- **Error Handling**: Graceful failure scenarios
- **Performance**: Batch operations and streaming

### Integration Tests

System tests validate complete functionality:

- **Redis Integration**: End-to-end Redis storage
- **Multi-Process**: Multiple worker processes
- **Metric Collection**: All metric types
- **Prometheus Scraping**: Metrics endpoint functionality

### Performance Benchmarks

Validates performance characteristics:

- **Throughput**: Metrics per second
- **Latency**: Read/write operation times
- **Memory Usage**: Memory consumption patterns
- **Scalability**: Multi-instance performance

## Future Enhancements

### Planned Features

- **Redis Cluster Support**: Distributed Redis deployment
- **Compression**: Metric data compression for storage efficiency
- **Encryption**: Encrypted metric storage
- **Advanced Aggregation**: Custom aggregation functions
- **Metrics Export**: Export to other monitoring systems

### Extensibility

The architecture is designed for extensibility:

- **Custom Storage Backends**: Pluggable storage implementations
- **Custom Aggregators**: User-defined aggregation logic
- **Custom Collectors**: Specialized metric collectors
- **Custom Protocols**: Alternative storage protocols

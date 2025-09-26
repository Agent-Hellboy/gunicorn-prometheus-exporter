# Redis Storage Backend

A complete Redis-based storage implementation that extends the Prometheus Python client to support distributed metrics storage. This implementation follows Prometheus multiprocess specifications while providing enhanced scalability and separation of concerns.

## Architecture Overview

### Complete Redis-Based Storage Implementation

We've implemented a **complete Redis storage backend** that extends the Prometheus Python client to support distributed metrics storage. This implementation follows Prometheus multiprocess specifications while providing enhanced scalability and separation of concerns.

#### Architecture Components

Our backend consists of several key components:

1. **`RedisStorageClient`** - Main client for Redis operations
2. **`RedisStorageDict`** - Storage abstraction implementing Prometheus multiprocess protocols
3. **`RedisMultiProcessCollector`** - Collector that aggregates metrics from Redis across processes
4. **`RedisValue`** - Redis-backed value implementation for individual metrics
5. **`RedisStorageManager`** - Service layer managing Redis connections and lifecycle

## Traditional vs Redis Storage

### Traditional Prometheus Multiprocess

```python
# Standard approach - files only
from prometheus_client import multiprocess
multiprocess.MultiProcessCollector(registry)
# Creates files in /tmp/prometheus_multiproc/
```

### Our Redis Storage Implementation

```python
# Our innovation - direct Redis storage
from gunicorn_prometheus_exporter.backend.service import get_redis_storage_manager
manager = get_redis_storage_manager()
collector = manager.get_collector()
registry.register(collector)
# Stores metrics in Redis: gunicorn:{type}_{mode}:{pid}:{data_type}:{hash}
```

## Redis Key Architecture

We use a structured key format that embeds process information and multiprocess modes:

```
gunicorn:{metric_type}_{mode}:{pid}:{data_type}:{hash}
```

**Examples:**
- `gunicorn:gauge_all:12345:metric:abc123` - Gauge metric with "all" mode
- `gunicorn:counter:12345:meta:def456` - Counter metadata
- `gunicorn:histogram:12345:metric:ghi789` - Histogram metric data

## Architecture Benefits

| Aspect           | Traditional       | Redis Storage       |
| ---------------- | ----------------- | ------------------- |
| **Storage**      | Local files       | Redis server        |
| **Scalability**  | Single instance   | Multiple instances  |
| **Separation**   | Coupled           | Separated           |
| **Performance**  | File I/O overhead | Direct Redis access |
| **Availability** | Server-dependent  | Redis-backed        |

## Configuration

### Redis Storage Backend (No Files Created)

```bash
# Enable Redis storage (replaces file storage completely)
export REDIS_ENABLED="true"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"
export REDIS_KEY_PREFIX="gunicorn"
export REDIS_TTL_SECONDS="300"  # Optional: key expiration
```

### Gunicorn Configuration

```python
# gunicorn_redis_storage.conf.py
bind = "0.0.0.0:8000"
workers = 2
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"

import os
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9092")  # Different port for Redis storage
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")

# Redis storage configuration (no files created)
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
```

## Multiprocess Mode Support

Our Redis backend implements all Prometheus multiprocess modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| `all` | All processes (including dead ones) | Per-worker monitoring with PID labels |
| `liveall` | All live processes | Current process monitoring |
| `max` | Maximum value across processes | Peak resource usage |
| `min` | Minimum value across processes | Minimum resource usage |
| `sum` | Sum of values across processes | Total resource consumption |
| `mostrecent` | Most recent value | Latest metric values |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_ENABLED` | `false` | Enable Redis storage backend |
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis database number |
| `REDIS_KEY_PREFIX` | `gunicorn` | Prefix for Redis keys |
| `REDIS_TTL_SECONDS` | `300` | Key expiration time in seconds |
| `REDIS_PASSWORD` | - | Redis password (if required) |
| `REDIS_SSL` | `false` | Enable SSL connection to Redis |

## Usage Examples

### Basic Redis Setup

```python
# Enable Redis storage
import os
os.environ["REDIS_ENABLED"] = "true"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"

# Use with Gunicorn
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
```

### Production Redis Configuration

```python
# Production settings
os.environ["REDIS_ENABLED"] = "true"
os.environ["REDIS_HOST"] = "redis-cluster.example.com"
os.environ["REDIS_PORT"] = "6379"
os.environ["REDIS_DB"] = "0"
os.environ["REDIS_KEY_PREFIX"] = "prod-gunicorn"
os.environ["REDIS_TTL_SECONDS"] = "600"
os.environ["REDIS_PASSWORD"] = "your-redis-password"
os.environ["REDIS_SSL"] = "true"
```

## Performance Considerations

### Redis Performance

- **Memory Usage**: Redis stores metrics in memory for fast access
- **Network Latency**: Consider Redis server location relative to application
- **Connection Pooling**: Automatic connection management
- **Key Expiration**: Configurable TTL prevents memory bloat

### Scaling Considerations

- **Multiple Instances**: Redis allows multiple Gunicorn instances to share metrics
- **Load Balancing**: Metrics are aggregated across all instances
- **High Availability**: Use Redis Cluster or Sentinel for production

## Monitoring Redis Backend

### Redis Metrics

The Redis backend provides additional metrics for monitoring:

- Connection status
- Key count and memory usage
- Operation latency
- Error rates

### Health Checks

```python
# Check Redis connectivity
from gunicorn_prometheus_exporter.backend.service import get_redis_storage_manager

manager = get_redis_storage_manager()
if manager.is_connected():
    print("Redis backend is healthy")
else:
    print("Redis backend connection failed")
```

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check Redis server status and network connectivity
2. **Authentication Errors**: Verify Redis password and SSL settings
3. **Memory Issues**: Monitor Redis memory usage and adjust TTL settings
4. **Performance Issues**: Check Redis server performance and network latency

### Debug Mode

```bash
# Enable debug logging
export REDIS_DEBUG="true"
export PROMETHEUS_DEBUG="true"
```

## Migration from File Storage

### Switching to Redis

1. **Install Redis**: Ensure Redis server is running
2. **Configure Environment**: Set Redis environment variables
3. **Update Configuration**: Modify Gunicorn configuration
4. **Restart Services**: Restart Gunicorn with new configuration

### Backward Compatibility

The Redis backend is designed to be a drop-in replacement for file-based storage. No changes to your application code are required.

## Security Considerations

### Redis Security

- **Authentication**: Use Redis AUTH for password protection
- **SSL/TLS**: Enable SSL for encrypted connections
- **Network Security**: Restrict Redis access to trusted networks
- **Key Isolation**: Use different Redis databases for different environments

### Best Practices

- Use dedicated Redis instances for metrics storage
- Implement Redis monitoring and alerting
- Regular backup of Redis data (if persistence is required)
- Monitor Redis memory usage and performance

## API Reference

For detailed API documentation, see the [API Reference](api-reference.md#redis-backend-architecture).

## Related Documentation

- [Backend Architecture](backend-architecture.md) - System architecture details
- [Configuration Guide](configuration.md) - Complete configuration options
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions

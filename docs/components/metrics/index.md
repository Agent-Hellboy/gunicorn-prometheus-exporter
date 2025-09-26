# Metrics Component

The metrics component provides comprehensive monitoring capabilities for Gunicorn applications.

## Overview

The metrics component collects and exposes various metrics about your Gunicorn application, including:

- Worker performance metrics
- Request handling statistics
- Resource usage monitoring
- Error tracking
- Master process monitoring

## Available Metrics

### Worker Metrics

- `gunicorn_worker_requests_total` - Total requests handled by each worker
- `gunicorn_worker_request_duration_seconds` - Request duration histogram
- `gunicorn_worker_memory_bytes` - Memory usage per worker
- `gunicorn_worker_cpu_percent` - CPU usage per worker
- `gunicorn_worker_uptime_seconds` - Worker uptime
- `gunicorn_worker_state` - Worker state with timestamp
- `gunicorn_worker_failed_requests_total` - Failed requests with method/endpoint labels

### Master Metrics

- `gunicorn_master_worker_restarts_total` - Total worker restarts
- `gunicorn_master_signals_total` - Signal handling metrics

### Error Metrics

- `gunicorn_worker_error_handling_total` - Error tracking with method and endpoint labels

## Documentation

- [Worker Types](worker-types.md) - Supported worker types and their metrics
- [API Reference](api-reference.md) - Metrics API documentation

## Configuration

Metrics collection is automatically enabled when using the Prometheus worker classes. No additional configuration is required for basic metrics.

For advanced configuration, see the [Configuration Guide](../config/configuration.md).

## Examples

See the [Examples](../examples/) for configuration examples and usage patterns.

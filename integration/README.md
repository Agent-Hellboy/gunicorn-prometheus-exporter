# Integration Tests

This directory contains integration tests for the Gunicorn Prometheus Exporter. These tests verify that the exporter works correctly when integrated with Gunicorn and different storage backends.

## What is Integration Testing?

Integration tests sit in the middle of the Test Pyramid:

```
┌─────────────────────────────────────┐
│  E2E Tests (e2e/)                   │  ← Full deployment with containers
├─────────────────────────────────────┤
│  Integration Tests (integration/)   │  ← Component integration ⭐ YOU ARE HERE
├─────────────────────────────────────┤
│  Unit Tests (tests/)                │  ← Individual functions
└─────────────────────────────────────┘
```

*Integration tests verify that multiple components work together correctly*, without the complexity of full containerization or orchestration. They test three different integration patterns:

- ✅ **Redis Storage Integration** (`test_redis_integ.sh`): Exporter + Gunicorn + Redis backend
- ✅ **File-Based Storage Integration** (`test_basic.sh`): Exporter + Gunicorn + file-based multiprocess storage
- ✅ **YAML Configuration Integration** (`test_yaml_config.sh`): Configuration parsing and validation with different worker types

These tests verify:
- ✅ Exporter + Gunicorn worker integration
- ✅ Storage backend functionality (Redis or file-based)
- ✅ Metrics collection and aggregation
- ✅ Configuration parsing and validation
- ✅ Multi-worker coordination
- ✅ Signal handling and cleanup

## Integration Test Patterns

The integration tests cover three different integration scenarios:

### `test_basic.sh`

Tests the exporter with **file-based multiprocess storage integration**.

*What it tests:*
- Exporter plugin integration with Gunicorn
- File-based multiprocess metrics storage (`/tmp/prometheus_multiproc/`)
- Worker metrics collection (CPU, memory, requests)
- Prometheus metrics endpoint exposure
- Multi-worker metrics aggregation
- Graceful shutdown and cleanup

*Storage:* File-based (`MmapedDict`)
*Dependencies:* None (Redis not required)

*Usage:*
```bash
./test_basic.sh              # Full test
./test_basic.sh --quick      # Quick test (fewer requests)
./test_basic.sh --ci         # CI-optimized test
```

### `test_redis_integ.sh`

Tests the exporter with **Redis-based storage integration**.

*What it tests:*
- Exporter plugin integration with Gunicorn
- Redis-based metrics storage (`RedisStorageDict`)
- Worker metrics shared across processes
- Redis key management and TTL (30s)
- Prometheus scraping from Redis
- Multi-worker coordination via Redis
- Redis connection handling

*Storage:* Redis-based (`RedisStorageDict`)
*Dependencies:* Redis server (can auto-start or use existing)

*Usage:*
```bash
./test_redis_integ.sh                    # Full test (auto-starts Redis)
./test_redis_integ.sh --quick            # Quick test
./test_redis_integ.sh --no-redis         # Use existing Redis
./test_redis_integ.sh --force            # Kill existing processes
./test_redis_integ.sh --ci               # CI-optimized test
```

### `test_yaml_config.sh`

Tests **YAML-based configuration integration** parsing and validation.

*What it tests:*
- YAML configuration file parsing
- Environment variable overrides
- Configuration defaults
- Invalid configuration handling
- Multiple worker types (sync, gevent, eventlet, gthread)
- Configuration validation

*Storage:* File-based
*Dependencies:* None

*Usage:*
```bash
./test_yaml_config.sh              # Full test
./test_yaml_config.sh --quick      # Quick test
./test_yaml_config.sh --docker     # Run in Docker container
```

## Running Integration Tests

From the project root:

```bash
# Run integration tests via e2e Makefile
cd e2e
make basic-test       # File-based storage integration test
make system-test      # Redis storage integration test (auto-starts Redis)
make quick-test       # Quick Redis test (requires Redis running)
make yaml-test        # YAML configuration integration test
```

Or run them directly from the integration directory:

```bash
cd integration
./test_basic.sh       # File-based multiprocess storage integration
./test_redis_integ.sh # Redis storage integration
./test_yaml_config.sh # YAML configuration integration
```

## CI/CD Integration

These integration tests run automatically in GitHub Actions:

- **Workflow**: `.github/workflows/system-test.yml`
- **Jobs**:
  - `redis_integration_test` (Redis storage integration)
  - `basic_file_based_test` (File-based multiprocess storage integration)
  - `yaml_config_test` (YAML configuration integration)

## Test Requirements

### Local Requirements
- Python 3.8+
- pip (for installing dependencies)
- Redis (for Redis integration test)

### Test Installs
Tests will automatically install:
- gunicorn
- flask (sample WSGI app)
- redis (Python client, for Redis tests)
- requests (for HTTP testing)
- psutil (for system metrics)

## Debugging

### Enable Verbose Output

All test scripts support verbose mode via environment variables:

```bash
export VERBOSE=1
./test_redis_integ.sh
```

### Check Logs

Test logs are written to:
- `prometheus.log` - Prometheus server logs
- Gunicorn outputs to stdout/stderr

### Manual Testing

You can run tests step-by-step by examining the test scripts and running commands manually:

```bash
# Example: Manual file-based storage integration test
cd integration

# Install dependencies
pip install gunicorn flask requests psutil

# Run Gunicorn with exporter (file-based storage)
gunicorn --config ../example/gunicorn_basic.conf.py app:app

# Test metrics endpoint
curl http://localhost:9093/metrics

# Cleanup
pkill gunicorn

# Example: Manual Redis storage integration test
# Start Redis
redis-server &

# Run Gunicorn with exporter (Redis storage)
gunicorn --config ../example/gunicorn_redis_integration.conf.py app:app

# Test metrics endpoint
curl http://localhost:9093/metrics

# Cleanup
pkill gunicorn
pkill redis-server
```

## What Makes These "Integration" Tests?

These tests are *integration tests* (not unit tests or E2E tests) because:

1. **Multiple Components**: They test the interaction between:
   - Gunicorn worker process
   - Prometheus exporter plugin
   - Storage backend (file or Redis)
   - Metrics collection system

2. **No Containers**: They run directly on the host system without Docker or Kubernetes complexity

3. **Real Dependencies**: They use real Gunicorn, real Redis, real Prometheus (not mocks)

4. **Component Boundaries**: They focus on testing component interfaces and integration points

5. **Not Full E2E**: They don't test:
   - Container images
   - Orchestration systems
   - Network policies
   - Production-like deployments

## Integration Test Types vs E2E Tests

| Test Type | Purpose | Scope | Dependencies | Speed |
|-----------|---------|-------|--------------|-------|
| **File-based** (`test_basic.sh`) | File multiprocess storage integration | Exporter + Gunicorn + file storage | Gunicorn, file system | ~30s |
| **Redis** (`test_redis_integ.sh`) | Redis storage integration | Exporter + Gunicorn + Redis backend | Gunicorn, Redis server | ~60s |
| **YAML Config** (`test_yaml_config.sh`) | Configuration integration | YAML parsing + worker types | Configuration files | ~45s |
| **E2E** (`e2e/`) | Full deployment testing | Complete system in containers/K8s | Docker/Kubernetes | ~2-5min |

## Contributing

When adding new integration tests:

1. Follow the existing test structure
2. Use consistent naming (`test_*.sh`)
3. Support `--quick`, `--ci`, and `--force` flags
4. Clean up processes and files on exit
5. Use trap for cleanup (handle signals)
6. Add documentation to this README

## Related Documentation

- [`../tests/README.md`](../tests/README.md) - Unit tests
- [`../e2e/README.md`](../e2e/README.md) - End-to-end tests
- [`../README.md`](../README.md) - Project overview

# Testing Guide

This guide covers the comprehensive testing strategy for Gunicorn Prometheus Exporter, following the Test Pyramid.

## Test Pyramid

The project uses a three-tier testing approach:

```
┌─────────────────────────────────────┐
│  e2e/ (End-to-End Tests)            │  ← Slow, expensive, few tests
│  • Docker deployment                │
│  • Kubernetes orchestration         │
│  • Production-like environments     │
├─────────────────────────────────────┤
│  integration/ (Integration Tests)   │  ← Medium speed, moderate cost
│  • Exporter + Gunicorn + Storage    │
│  • Component interaction            │
│  • No containers                    │
├─────────────────────────────────────┤
│  tests/ (Unit Tests)                │  ← Fast, cheap, many tests
│  • Individual functions             │
│  • pytest-based                     │
│  • Mocked dependencies              │
└─────────────────────────────────────┘
```

## Unit Tests (`tests/`)

### Purpose

Unit tests verify individual functions and methods in isolation.

### Characteristics

- *Fast*: Run in seconds
- *Isolated*: Use mocks for dependencies
- *Focused*: Test single units of code
- *Coverage*: Aim for high coverage (80%+)

### Running Unit Tests

```bash
# Run all unit tests
pytest

# Run with coverage
pytest --cov=src/gunicorn_prometheus_exporter --cov-report=html

# Run specific test file
pytest tests/test_metrics.py

# Run specific test function
pytest tests/test_metrics.py::test_worker_requests

# Run in parallel
pytest -n auto
```

### Using tox

```bash
# Run all Python versions
tox

# Run specific Python version
tox -e py312

# Run with coverage
tox -e py312 -- --cov=gunicorn_prometheus_exporter --cov-report=html
```

### Writing Unit Tests

```python
import pytest
from gunicorn_prometheus_exporter.metrics import WorkerMetrics

def test_worker_metrics_initialization():
    """Test WorkerMetrics initializes correctly."""
    # Arrange
    worker_id = 1

    # Act
    metrics = WorkerMetrics(worker_id)

    # Assert
    assert metrics.worker_id == worker_id
    assert metrics.requests_total.describe() is not None
```

### Best Practices

1. *Use descriptive test names* that explain what is being tested
2. *Follow AAA pattern*: Arrange, Act, Assert
3. *Mock external dependencies* (Redis, files, network)
4. *Use fixtures* for common setup
5. *Test edge cases* and error conditions

## Integration Tests (`integration/`)

### Purpose

Integration tests verify that components work together correctly without containers.

### Characteristics

- *Medium speed*: Run in 30-60 seconds
- *Real dependencies*: Use actual Redis, Gunicorn
- *No containers*: Run directly on host
- *Component interaction*: Test exporter + Gunicorn + storage

### Running Integration Tests

```bash
cd e2e

# File-based storage test
make basic-test                 # Full test
make basic-quick-test           # Quick test

# Redis integration test
make integration-test                # Redis integration test (auto-starts Redis)
make quick-test                 # Requires Redis running
make ci-test                    # CI-optimized

# YAML configuration test
make yaml-test                  # Full test
make yaml-quick-test            # Quick test
```

### Available Integration Tests

#### 1. File-Based Storage (`integration/test_basic.sh`)

Tests the exporter with file-based multiprocess storage:

- Gunicorn worker startup
- Metrics collection in files
- Multi-worker coordination
- Metrics endpoint exposure
- Graceful shutdown

*Requirements*: None (no Redis needed)

#### 2. Redis Storage (`integration/test_redis_integ.sh`)

Tests the exporter with Redis-based storage:

- Redis connection and storage
- Multi-worker metrics sharing
- Redis key management and TTL
- Prometheus scraping from Redis
- Graceful cleanup

*Requirements*: Redis (auto-started or use `--no-redis`)

#### 3. YAML Configuration (`integration/test_yaml_config.sh`)

Tests YAML-based configuration:

- Configuration file parsing
- Environment variable overrides
- Validation and error handling
- Multiple worker types

*Requirements*: None

### Writing Integration Tests

Integration tests are bash scripts that:

1. Start dependencies (Redis, if needed)
2. Run Gunicorn with the exporter
3. Generate test requests
4. Verify metrics
5. Clean up processes

See `integration/README.md` for detailed guidelines.

## End-to-End Tests (`e2e/`)

### Purpose

E2E tests verify the complete system in production-like environments.

### Characteristics

- *Slow*: Run in 2-5 minutes
- *Full stack*: Docker containers, Kubernetes clusters
- *Production-like*: Network policies, service discovery
- *Complete flow*: Build → Deploy → Test → Verify

### Running E2E Tests

```bash
cd e2e

# Docker tests
bash docker/test_docker_compose.sh        # Docker Compose stack
bash docker/test_sidecar_redis.sh         # Sidecar with Redis
bash docker/test_standalone_images.sh     # Image validation

# Kubernetes tests
bash kubernetes/test_sidecar_deployment.sh    # Sidecar pattern
bash kubernetes/test_daemonset_deployment.sh  # DaemonSet pattern

# Or use Make targets
make docker-test        # Run Docker tests via workflows
```

### Available E2E Tests

#### Docker Tests (`e2e/docker/`)

1. *Docker Compose* (`test_docker_compose.sh`):
   - Multi-container orchestration
   - Sidecar pattern validation
   - Prometheus + Grafana integration
   - Complete monitoring stack

2. *Sidecar with Redis* (`test_sidecar_redis.sh`):
   - Container networking
   - Redis connectivity
   - Sidecar communication

3. *Standalone Images* (`test_standalone_images.sh`):
   - Image build validation
   - Entrypoint modes testing
   - Health checks

#### Kubernetes Tests (`e2e/kubernetes/`)

1. *Sidecar Deployment* (`test_sidecar_deployment.sh`):
   - Standard K8s deployment
   - Service discovery
   - Pod communication

2. *DaemonSet Deployment* (`test_daemonset_deployment.sh`):
   - Multi-node Kind cluster
   - DaemonSet to all nodes
   - Node-level monitoring
   - Comprehensive metrics validation

### Writing E2E Tests

E2E tests are bash scripts that:

1. Set up infrastructure (Kind cluster, Docker network)
2. Build and load images
3. Deploy manifests or Compose files
4. Wait for readiness
5. Generate traffic
6. Verify metrics and behavior
7. Clean up infrastructure

See `e2e/README.md` for detailed guidelines.

## CI/CD Testing

### GitHub Actions Workflows

The project uses three main testing workflows:

1. *Unit Tests* (`.github/workflows/ci.yml`):
   - Runs on every push/PR
   - Tests Python 3.9-3.12
   - Checks linting and formatting
   - Generates coverage reports

2. *Integration Tests* (`.github/workflows/system-test.yml`):
   - Tests Redis integration
   - Tests file-based storage
   - Tests YAML configuration
   - Runs in Docker containers

3. *Smoke Tests - Docker* (`.github/workflows/docker-test.yml`):
   - Tests Docker image builds
   - Tests Docker Compose
   - Tests sidecar functionality
   - Validates Kubernetes manifests

4. *Smoke Tests - Kubernetes* (`.github/workflows/kubernetes-test.yml`):
   - Tests Kubernetes deployments
   - Tests DaemonSet pattern
   - Tests Sidecar pattern
   - Validates metrics collection

### Running CI Tests Locally

```bash
# Unit tests (same as CI)
tox

# Integration tests (Docker-based, same as CI)
cd e2e
docker build -f fixtures/dockerfiles/default.Dockerfile -t test ..
docker run --rm test

# E2E tests (requires Docker/Kind)
bash e2e/docker/test_docker_compose.sh
bash e2e/kubernetes/test_daemonset_deployment.sh
```

## Test Coverage

### Checking Coverage

```bash
# Unit test coverage
pytest --cov=src/gunicorn_prometheus_exporter --cov-report=html
open htmlcov/index.html

# With tox
tox -e py312 -- --cov=gunicorn_prometheus_exporter --cov-report=html
```

### Coverage Goals

- *Unit tests*: 80%+ coverage
- *Integration tests*: Cover all storage backends
- *E2E tests*: Cover all deployment patterns

## Testing Best Practices

### General

1. *Follow the Test Pyramid*: Many unit tests, fewer integration tests, even fewer E2E tests
2. *Keep tests fast*: Unit tests should run in seconds
3. *Keep tests isolated*: Tests should not depend on each other
4. *Keep tests deterministic*: Tests should always produce the same result
5. *Keep tests readable*: Use descriptive names and clear assertions

### Unit Tests

- Test one thing at a time
- Use mocks for external dependencies
- Test both success and failure cases
- Use parameterized tests for multiple scenarios

### Integration Tests

- Use real dependencies
- Clean up after tests
- Test error recovery
- Verify complete workflows

### E2E Tests

- Test production-like scenarios
- Validate complete deployments
- Check metrics thoroughly
- Clean up infrastructure

## Debugging Tests

### Unit Tests

```bash
# Run with verbose output
pytest -v -s

# Run with pdb on failure
pytest --pdb

# Run specific test with print statements
pytest -v -s tests/test_metrics.py::test_worker_requests
```

### Integration Tests

```bash
# Enable verbose mode
export VERBOSE=1
cd e2e
bash ../integration/test_redis_integ.sh

# Check logs
cat prometheus.log
```

### E2E Tests

```bash
# Docker logs
docker logs <container-name>

# Kubernetes logs
kubectl logs <pod-name>
kubectl describe pod <pod-name>

# Kind cluster logs
kind export logs /tmp/kind-logs
```

## Related Documentation

- [Contributing Guide](contributing.md) - How to contribute
- [Development Setup](development.md) - Development environment
- [Integration Tests README](../integration/README.md) - Integration test details
- [E2E Tests README](../e2e/README.md) - E2E test details
- [Troubleshooting Guide](troubleshooting.md) - Common issues

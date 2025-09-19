# System Test Suite for Gunicorn Prometheus Exporter (Cross-Platform Docker)

This directory contains a comprehensive system test for the Gunicorn Prometheus Exporter with Redis integration.

## Overview

The system test validates the complete functionality of the Gunicorn Prometheus Exporter, including:

- ✅ **Dependency Installation**: Automatic setup of required packages
- ✅ **Redis Integration**: Full Redis backend functionality with TTL support
- ✅ **Gunicorn Server**: Multi-worker setup with Redis storage
- ✅ **Metrics Collection**: All metric types (counters, gauges, histograms)
- ✅ **Request Processing**: Real HTTP request handling and metrics capture
- ✅ **Prometheus Scraping**: Verification that Prometheus can scrape metrics (15 seconds)
- ✅ **Redis TTL Testing**: Automatic key expiration and cleanup (30 seconds TTL)
- ✅ **Signal Handling**: Proper shutdown and cleanup
- ✅ **CI/CD Ready**: Automated testing for continuous integration
- ✅ **Cross-Platform**: Works consistently on Mac, Windows, and Linux via Docker
- ✅ **Self-Contained**: No host machine dependencies

## Files

| File                   | Purpose                                                                                        |
| ---------------------- | ---------------------------------------------------------------------------------------------- |
| `system_test.sh`       | **Unified system test** - Complete automated test suite with multiple modes (including Docker) |
| `Dockerfile`           | **Docker image** - Container definition for consistent testing                                 |
| `docker-compose.yml`   | **Docker Compose** - Multi-service setup for testing                                           |
| `Makefile`             | **Build automation** - Easy test execution commands                                            |
| `requirements-dev.txt` | **Dependencies** - Development and testing packages                                            |
| `README.md`            | **Documentation** - This file                                                                  |

## Quick Start

### Prerequisites

1. **Docker** must be installed:
   - **Mac**: Install Docker Desktop from https://www.docker.com/products/docker-desktop
   - **Windows**: Install Docker Desktop from https://www.docker.com/products/docker-desktop
   - **Linux**: Install Docker Engine from https://docs.docker.com/engine/install/

2. **Git** (for cloning the repository)

### Running Tests

#### Option 1: Docker-based Testing (Recommended - Works on All Platforms)

```bash
# Run complete system test in Docker container
make docker-test

# Or using docker-compose
docker-compose up --build

# Or manually with Docker
docker build -f Dockerfile -t gunicorn-prometheus-exporter-test ..
docker run --rm -p 8088:8088 -p 9093:9093 -p 6379:6379 -p 9090:9090 gunicorn-prometheus-exporter-test
```

#### Option 2: Using Make (Requires Local Redis)

```bash
# Quick test (requires Redis running)
make quick-test

# Full system test (starts Redis automatically)
make system-test

# CI test (timeout-protected)
make ci-test

# Install dependencies
make install

# Clean up
make clean
```

#### Option 3: Direct Script Execution

```bash
# Docker mode (cross-platform, no host dependencies)
./system_test.sh --docker

# Quick test (requires Redis running)
./system_test.sh --quick --no-redis

# Quick test with force kill (kills existing processes)
./system_test.sh --quick --no-redis --force

# Full system test (starts Redis automatically)
./system_test.sh

# CI test (timeout-protected)
./system_test.sh --ci
```

## Test Details

### Quick Mode (`--quick --no-redis`)

**Purpose**: Fast local development testing
**Duration**: ~10 seconds
**Requirements**: Redis must be running

**What it tests**:

- ✅ Basic server startup
- ✅ HTTP endpoints (app + metrics)
- ✅ Request processing
- ✅ Key metrics collection
- ✅ Redis integration
- ✅ Prometheus scraping verification
- ✅ Redis TTL configuration
- ✅ Signal handling

**Usage**:

```bash
# Make sure Redis is running first
brew services start redis  # macOS
sudo systemctl start redis  # Linux

# Run quick test
./system_test.sh --quick --no-redis
```

### Full Mode (default)

**Purpose**: Comprehensive testing
**Duration**: ~2-3 minutes
**Requirements**: None (installs everything automatically)

**What it tests**:

- ✅ Automatic dependency installation
- ✅ Redis server startup and management
- ✅ Gunicorn server with Redis integration
- ✅ Multi-worker configuration
- ✅ Request generation and processing
- ✅ All metric types verification
- ✅ Redis key validation
- ✅ Prometheus scraping verification (15 seconds)
- ✅ Redis TTL configuration and expiration testing (30 seconds)
- ✅ Signal handling and cleanup
- ✅ Error scenarios

**Usage**:

```bash
# Run full system test (no prerequisites needed)
./system_test.sh
```

### CI Mode (`--ci`)

**Purpose**: CI/CD optimized testing
**Duration**: ~2-3 minutes with timeout protection
**Requirements**: None (installs everything automatically)

**What it tests**:

- ✅ Same as Full Mode
- ✅ Timeout protection (30 seconds max)
- ✅ Enhanced cleanup
- ✅ CI-optimized logging

**Usage**:

```bash
# CI test (timeout-protected)
./system_test.sh --ci
```

### Docker Mode (`--docker`)

**Purpose**: Run system test in Docker container (cross-platform)
**Duration**: Same as CI mode (30 seconds)
**Requirements**: Docker installed

**What it does**:

- ✅ Automatically detects Docker environment
- ✅ Skips Redis startup (handled by Docker)
- ✅ Runs in isolated container environment
- ✅ Works consistently on Mac, Windows, Linux
- ✅ No host machine dependencies

**Usage**:

```bash
# Run in Docker mode
./system_test.sh --docker

# Docker mode with CI timeout
./system_test.sh --docker --ci
```

### Force Mode (`--force`)

**Purpose**: Kill existing processes on ports 8088 and 9093
**Duration**: Same as the mode it's combined with
**Requirements**: None

**What it does**:

- ✅ Kills any existing processes on port 8088 (app)
- ✅ Kills any existing processes on port 9093 (metrics)
- ✅ Prevents port conflicts during development
- ✅ Useful when previous tests didn't clean up properly

**Usage**:

```bash
# Force kill and run quick test
./system_test.sh --quick --no-redis --force

# Force kill and run full test
./system_test.sh --force

# Force kill and run CI test
./system_test.sh --ci --force
```

## Test Configuration

### Ports Used

- **Application**: `8088`
- **Metrics**: `9093`
- **Redis**: `6379`
- **Prometheus**: `9090`

### Environment Variables

```bash
PROMETHEUS_METRICS_PORT=9093
PROMETHEUS_BIND_ADDRESS=127.0.0.1
REDIS_ENABLED=true
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_TTL_SECONDS=30          # TTL for Redis keys (30 seconds for testing)
REDIS_TTL_DISABLED=false       # Enable TTL (set to "true" to disable)
GUNICORN_WORKERS=2
```

### Test Metrics Verified

| Metric Type   | Metric Name                                | Verification          |
| ------------- | ------------------------------------------ | --------------------- |
| **Counter**   | `gunicorn_worker_requests_total`           | Request count > 0     |
| **Histogram** | `gunicorn_worker_request_duration_seconds` | Buckets + sum + count |
| **Gauge**     | `gunicorn_worker_memory_bytes`             | Memory usage > 0      |
| **Gauge**     | `gunicorn_worker_cpu_percent`              | CPU percentage        |
| **Gauge**     | `gunicorn_worker_uptime_seconds`           | Uptime > 0            |
| **Gauge**     | `gunicorn_worker_state`                    | State transitions     |
| **Counter**   | `gunicorn_master_worker_restart_total`     | Restart tracking      |

## Enhanced Testing Features

### Prometheus Scraping Verification

The system test now includes comprehensive Prometheus integration testing:

- **Target Health Check**: Verifies Prometheus can reach the metrics endpoint
- **API Accessibility**: Tests Prometheus API at `http://localhost:9090`
- **Metrics Scraping**: Confirms Prometheus successfully scrapes `gunicorn_requests_total`
- **Data Validation**: Counts scraped data points to ensure metrics are being collected
- **Timing**: 15-second wait for Prometheus to perform scraping cycles

### Redis TTL (Time To Live) Testing

Advanced Redis key lifecycle management testing:

- **TTL Configuration**: Tests 30-second TTL for Redis metric keys
- **Automatic Expiration**: Verifies Redis automatically cleans up expired keys
- **Key Lifecycle**: Monitors key creation → TTL setting → expiration → cleanup
- **No Manual Cleanup**: Confirms Redis handles cleanup without application intervention
- **Memory Management**: Prevents Redis memory from growing indefinitely

### Test Flow Timeline

```
0-15s:  Generate requests and verify metrics
15-30s: Prometheus scraping verification
30-60s: Redis TTL expiration verification
60s+:   Signal handling and cleanup
```

### Redis TTL Benefits

- **Automatic Cleanup**: No manual Redis key management needed
- **Memory Efficiency**: Prevents Redis memory bloat
- **Process Restart Safe**: Metrics persist across worker restarts
- **Prometheus Friendly**: Covers multiple scrape cycles before expiration
- **Configurable**: TTL can be adjusted via `REDIS_TTL_SECONDS` environment variable

## CI/CD Integration

The system test is integrated with GitHub Actions for automated testing:

- **Ubuntu**: Full Redis service integration
- **macOS**: Homebrew Redis installation
- **Windows**: Chocolatey Redis installation

See `.github/workflows/system-test.yml` for CI configuration.

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Kill existing processes
pkill -f "gunicorn.*redis_integration"
pkill -f "redis-server"

# Or use different ports
export PROMETHEUS_METRICS_PORT=9094
export APP_PORT=8089
```

#### 2. Redis Connection Failed

```bash
# Check Redis status
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

#### 3. Gunicorn Not Found

```bash
# Install gunicorn
pip install gunicorn

# Or use the full system test which installs dependencies
./system_test.sh
```

#### 4. Permission Denied

```bash
# Make scripts executable
chmod +x *.sh
```

#### 5. Prometheus Scraping Issues

```bash
# Check if Prometheus is running
curl -s http://localhost:9090/api/v1/targets

# Check metrics endpoint
curl -s http://localhost:9093/metrics | head -20

# Verify Prometheus configuration
curl -s http://localhost:9090/api/v1/query?query=gunicorn_requests_total
```

#### 6. Redis TTL Issues

```bash
# Check Redis TTL on sample keys
redis-cli --scan --pattern "gunicorn:*:metric:*" | head -1 | xargs redis-cli ttl

# Check if keys are expiring
redis-cli --scan --pattern "gunicorn:*" | wc -l

# Monitor Redis memory usage
redis-cli info memory | grep used_memory_human
```

### Debug Mode

Enable verbose output:

```bash
# Add debug flags
set -x  # Enable debug mode
export DEBUG=1
```

### Manual Verification

If tests fail, manually verify:

1. **Redis Keys**:

   ```bash
   redis-cli --scan --pattern "gunicorn:*" | wc -l
   ```

2. **Metrics Endpoint**:

   ```bash
   curl -s http://localhost:9093/metrics | grep "gunicorn_worker_requests_total"
   ```

3. **App Endpoint**:
   ```bash
   curl -s http://localhost:8088/
   ```

## Development

### Adding New Tests

1. **Add metric verification** in `verify_metrics()` function
2. **Add new test scenarios** in the main test functions
3. **Update expected metrics** list
4. **Test locally** with `quick_test.sh`
5. **Validate with CI** using `system_test.sh`

### Test Structure

```bash
system-test/
├── system_test.sh      # Full automated test suite
├── quick_test.sh       # Fast local testing
├── Makefile           # Build automation
├── requirements-dev.txt # Dependencies
└── README.md          # This documentation
```

## Success Criteria

A successful test run should show:

- ✅ All dependencies installed
- ✅ Redis server started
- ✅ Gunicorn server started with Redis integration
- ✅ All metric types verified
- ✅ Request metrics captured
- ✅ Redis keys created
- ✅ Prometheus scraping verified
- ✅ Redis TTL configuration working
- ✅ Redis keys expired and cleaned up automatically
- ✅ Signal handling working
- ✅ Clean shutdown

## Contributing

When adding new features:

1. **Update tests** to verify new functionality
2. **Add new metrics** to verification lists
3. **Test locally** with both quick and full tests
4. **Ensure CI passes** before submitting PR

---

**Happy Testing!** 🚀

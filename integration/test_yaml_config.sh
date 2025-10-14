#!/bin/bash

# Integration test for YAML configuration integration
# This script tests the YAML configuration functionality with actual Gunicorn processes

set -e

# Parse command line arguments
USE_DOCKER=false
QUICK_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--docker] [--quick]"
            echo "  --docker: Use Docker for testing"
            echo "  --quick: Run quick tests only"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $message"
        ((TESTS_PASSED++))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗ FAIL${NC}: $message"
        ((TESTS_FAILED++))
    elif [ "$status" = "INFO" ]; then
        echo -e "${YELLOW}ℹ INFO${NC}: $message"
    fi
}

# Test configuration
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$TEST_DIR/.." && pwd)"

# Setup environment based on mode
if [ "$USE_DOCKER" = true ]; then
    print_status "INFO" "Using Docker for testing"

    # Check if Docker is available
    if ! command -v docker > /dev/null 2>&1; then
        print_status "FAIL" "Docker not found. Please install Docker."
        exit 1
    fi

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_status "FAIL" "Docker is not running. Please start Docker."
        exit 1
    fi

    # Set Docker-specific variables
    DOCKER_IMAGE="gunicorn-prometheus-exporter-yaml-test"
    DOCKER_CONTAINER="gunicorn-prometheus-exporter-yaml-test-container"

else
    # Check if virtual environment exists
    if [ -d "$PROJECT_ROOT/test_venv" ]; then
        VENV_DIR="$PROJECT_ROOT/test_venv"
    elif [ -d "$PROJECT_ROOT/venv" ]; then
        VENV_DIR="$PROJECT_ROOT/venv"
    else
        print_status "FAIL" "No virtual environment found. Please run 'python -m venv test_venv' in project root directory"
        exit 1
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Check if gunicorn is available
    if ! command -v gunicorn > /dev/null 2>&1; then
        print_status "FAIL" "Gunicorn not found in virtual environment. Please install dependencies."
        exit 1
    fi
fi

# Test ports
GUNICORN_PORT=8089
METRICS_PORT=9094

# Function to cleanup test processes
cleanup() {
    print_status "INFO" "Cleaning up test processes..."

    if [ "$USE_DOCKER" = true ]; then
        # Docker cleanup
        docker stop "$DOCKER_CONTAINER" 2>/dev/null || true
        docker rm "$DOCKER_CONTAINER" 2>/dev/null || true
        docker rmi "$DOCKER_IMAGE" 2>/dev/null || true
    else
        # Local cleanup
        pkill -f "gunicorn.*test_app" || true
        pkill -f "python.*test_app" || true

        # Wait a moment for processes to terminate
        sleep 2

        # Force kill if still running
        pkill -9 -f "gunicorn.*test_app" || true
        pkill -9 -f "python.*test_app" || true
    fi

    print_status "INFO" "Cleanup completed"
}

# Function to wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    print_status "INFO" "Waiting for $service_name to be ready on $host:$port..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://$host:$port" > /dev/null 2>&1; then
            print_status "PASS" "$service_name is ready on $host:$port"
            return 0
        fi

        if [ $((attempt % 5)) -eq 0 ]; then
            print_status "INFO" "Still waiting for $service_name... (attempt $attempt/$max_attempts)"
        fi

        sleep 1
        ((attempt++))
    done

    print_status "FAIL" "$service_name failed to start within $max_attempts seconds"
    return 1
}

# Function to test metrics endpoint
test_metrics_endpoint() {
    local metrics_port=$1
    local test_name=$2

    print_status "INFO" "Testing metrics endpoint on port $metrics_port..."

    if curl -s "http://127.0.0.1:$metrics_port/metrics" | grep -q "gunicorn_"; then
        print_status "PASS" "$test_name - Metrics endpoint is working"
        return 0
    else
        print_status "FAIL" "$test_name - Metrics endpoint not working or no gunicorn metrics found"
        return 1
    fi
}

# Function to verify comprehensive metrics
verify_comprehensive_metrics() {
    local port=$1
    local test_name=$2

    print_status "INFO" "Verifying comprehensive metrics for $test_name..."

    local metrics_url="http://127.0.0.1:$port/metrics"
    local metrics_output=$(curl -s "$metrics_url" 2>/dev/null)

    if [ -z "$metrics_output" ]; then
        print_status "FAIL" "Failed to fetch metrics from $metrics_url"
        return 1
    fi

    # Define expected metrics
    local expected_metrics=(
        "gunicorn_worker_requests_total"
        "gunicorn_worker_request_duration_seconds"
        "gunicorn_worker_memory_bytes"
        "gunicorn_worker_cpu_percent"
        "gunicorn_worker_uptime_seconds"
        "gunicorn_worker_state"
    )

    # Optional metrics (may not have values during normal operation)
    local optional_metrics=(
        "gunicorn_master_worker_restart_total"
        "gunicorn_master_worker_restart_count_total"
        "gunicorn_worker_restart_total"
        "gunicorn_worker_restart_count_total"
    )

    local failed_checks=0

    # Check each expected metric
    for metric in "${expected_metrics[@]}"; do
        local metric_line=$(echo "$metrics_output" | grep "$metric.*[0-9]" | head -1)
        if [ ! -z "$metric_line" ]; then
            print_status "PASS" "Metric $metric: $metric_line"
        else
            print_status "FAIL" "Metric $metric has no values"
            failed_checks=$((failed_checks + 1))
        fi
    done

    # Check optional metrics (don't fail if they have no values)
    for metric in "${optional_metrics[@]}"; do
        local metric_line=$(echo "$metrics_output" | grep "$metric.*[0-9]" | head -1)
        if [ ! -z "$metric_line" ]; then
            print_status "PASS" "Optional metric $metric: $metric_line"
        else
            print_status "INFO" "Optional metric $metric has no values (this is normal)"
        fi
    done

    # Check for specific metric types
    if echo "$metrics_output" | grep -q "# TYPE.*counter"; then
        print_status "PASS" "Counter metrics found"
    else
        print_status "FAIL" "No counter metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    if echo "$metrics_output" | grep -q "# TYPE.*gauge"; then
        print_status "PASS" "Gauge metrics found"
    else
        print_status "FAIL" "No gauge metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    if echo "$metrics_output" | grep -q "# TYPE.*histogram"; then
        print_status "PASS" "Histogram metrics found"
    else
        print_status "FAIL" "No histogram metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    # Check for worker ID labels
    if echo "$metrics_output" | grep -q "worker_id="; then
        print_status "PASS" "Worker ID labels found"
    else
        print_status "FAIL" "No worker ID labels found"
        failed_checks=$((failed_checks + 1))
    fi

    # Count total metric samples
    local sample_count=$(echo "$metrics_output" | grep -c "^[^#]" || echo "0")
    print_status "INFO" "Total metric samples: $sample_count"

    if [ "$sample_count" -gt 20 ]; then
        print_status "PASS" "Sufficient metric samples found ($sample_count)"
    else
        print_status "FAIL" "Insufficient metric samples found ($sample_count)"
        failed_checks=$((failed_checks + 1))
    fi

    return $failed_checks
}

# Function to generate test requests
generate_test_requests() {
    local port=$1
    local duration=${2:-10}

    print_status "INFO" "Generating test requests for $duration seconds..."

    # Generate requests in background
    (
        for i in $(seq 1 $((duration * 2))); do
            curl -s "http://127.0.0.1:$port/" >/dev/null 2>&1 &
            curl -s "http://127.0.0.1:$port/nonexistent" >/dev/null 2>&1 &
            sleep 0.5
        done
    ) &

    local request_pid=$!

    # Show progress
    for i in $(seq 1 $duration); do
        sleep 1
        echo -n "."
    done

    echo ""

    # Wait for request generation to complete
    wait $request_pid 2>/dev/null || true

    print_status "PASS" "Generated $((duration * 4)) requests"
}

# Function to test signal handling
test_signal_handling() {
    local container_name=$1
    local metrics_port=$2

    if [ "$USE_DOCKER" != true ]; then
        print_status "INFO" "Skipping signal handling test (Docker-only)"
        return 0
    fi

    print_status "INFO" "Testing signal handling..."

    # Test different signals
    local signals_to_test=("HUP" "USR1" "USR2")

    for signal in "${signals_to_test[@]}"; do
        print_status "INFO" "Testing SIG${signal} signal..."

        # Send signal to container
        docker kill --signal="${signal}" "$container_name" 2>/dev/null || true
        sleep 3

        # Check if metrics are still working
        local metrics_url="http://127.0.0.1:$metrics_port/metrics"
        local response=$(curl -s "$metrics_url" 2>/dev/null)

        if [ ! -z "$response" ] && echo "$response" | grep -q "gunicorn_worker_requests_total"; then
            print_status "PASS" "SIG${signal} handled correctly - metrics still working"
        else
            print_status "FAIL" "SIG${signal} failed - metrics not accessible"
        fi
    done
}

# Function to verify multiprocess files
verify_multiproc_files() {
    local container_name=$1

    print_status "INFO" "Verifying multiprocess files in container..."

    # Check if multiprocess directory exists
    local multiproc_check=$(docker exec "$container_name" ls -la /tmp/prometheus_multiproc 2>/dev/null || echo "")

    if [ ! -z "$multiproc_check" ]; then
        print_status "PASS" "Multiprocess directory exists"

        # Count files in multiprocess directory
        local file_count=$(docker exec "$container_name" find /tmp/prometheus_multiproc -type f 2>/dev/null | wc -l)

        if [ "$file_count" -gt 0 ]; then
            print_status "PASS" "Found $file_count files in multiprocess directory"

            # Show sample files
            print_status "INFO" "Sample multiprocess files:"
            docker exec "$container_name" find /tmp/prometheus_multiproc -type f 2>/dev/null | head -5 | while read file; do
                local file_size=$(docker exec "$container_name" stat -c%s "$file" 2>/dev/null || echo "unknown")
                echo "  - $(basename "$file") (${file_size} bytes)"
            done

            return 0
        else
            print_status "FAIL" "No files found in multiprocess directory"
            return 1
        fi
    else
        print_status "FAIL" "Multiprocess directory not found"
        return 1
    fi
}

# Function to test basic YAML configuration
test_basic_yaml_config() {
    print_status "INFO" "Testing basic YAML configuration..."

    # Create test YAML config
    cat > "$PROJECT_ROOT/test_basic_config.yml" << EOF
exporter:
  prometheus:
    metrics_port: $METRICS_PORT
    bind_address: "127.0.0.1"
    multiproc_dir: "/tmp/prometheus_test_basic"
  gunicorn:
    workers: 1
    timeout: 30
    keepalive: 2
  redis:
    enabled: false
  cleanup:
    db_files: true
EOF

    # Create test Gunicorn config
    cat > "$PROJECT_ROOT/test_basic_gunicorn.conf.py" << EOF
import os
from gunicorn_prometheus_exporter.hooks import load_yaml_config

# Load YAML configuration
load_yaml_config("test_basic_config.yml")

from gunicorn_prometheus_exporter.hooks import (
    default_on_exit,
    default_on_starting,
    default_post_fork,
    default_when_ready,
    default_worker_int,
)

# Gunicorn settings - use 0.0.0.0 for Docker compatibility
bind = "0.0.0.0:$GUNICORN_PORT"
workers = 1
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
timeout = 30

# Use pre-built hooks
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork
EOF

    if [ "$USE_DOCKER" = true ]; then
        # Docker-based testing using docker run (like other system tests)
        print_status "INFO" "Starting Docker container for YAML testing..."

        # Build and run Docker container
        docker build -f e2e/fixtures/dockerfiles/yaml-simple.Dockerfile -t "$DOCKER_IMAGE" .. >/dev/null 2>&1

        # Run container in background with the same config as local mode
        docker run -d \
            --name "$DOCKER_CONTAINER" \
            -p 8089:8089 \
            -p 9094:9094 \
            -e PROMETHEUS_CONFIG_FILE="/app/test_basic_config.yml" \
            -v "$PROJECT_ROOT/e2e/test_configs/basic.yml:/app/test_basic_config.yml:ro" \
            -v "$PROJECT_ROOT/e2e/fixtures/apps/test_app.py:/app/e2e/fixtures/apps/test_app.py" \
            -v "$PROJECT_ROOT/e2e/fixtures/configs/gunicorn.yaml.conf.py:/app/test_basic_gunicorn.conf.py:ro" \
            "$DOCKER_IMAGE" \
            gunicorn --config /app/test_basic_gunicorn.conf.py test_app:app

        # Wait for services to be ready
        print_status "INFO" "Waiting for services to start..."
        sleep 10

        # Wait for service to be ready
        if wait_for_service "127.0.0.1" "$GUNICORN_PORT" "Gunicorn"; then
            # Generate test requests
            generate_test_requests "$GUNICORN_PORT" 10

            # Test comprehensive metrics
            if verify_comprehensive_metrics "$METRICS_PORT" "Basic YAML Config"; then
                print_status "PASS" "Basic YAML configuration test passed"
            else
                print_status "FAIL" "Basic YAML configuration test failed"
            fi

            # Test signal handling
            test_signal_handling "$DOCKER_CONTAINER" "$METRICS_PORT"

            # Verify multiprocess files
            verify_multiproc_files "$DOCKER_CONTAINER"
        else
            print_status "FAIL" "Basic YAML configuration test failed - Gunicorn did not start"
            docker logs "$DOCKER_CONTAINER"
        fi

        # Show logs for debugging
        print_status "INFO" "Container logs:"
        docker logs "$DOCKER_CONTAINER"

        # Cleanup
        docker stop "$DOCKER_CONTAINER" 2>/dev/null || true
        docker rm "$DOCKER_CONTAINER" 2>/dev/null || true

    else
        # Local testing
        print_status "INFO" "Starting Gunicorn with basic YAML configuration..."
        cd "$PROJECT_ROOT"
        gunicorn --config test_basic_gunicorn.conf.py test_app:app &
        GUNICORN_PID=$!

        # Wait for service to be ready
        if wait_for_service "127.0.0.1" "$GUNICORN_PORT" "Gunicorn"; then
            # Generate test requests
            generate_test_requests "$GUNICORN_PORT" 10

            # Test comprehensive metrics
            if verify_comprehensive_metrics "$METRICS_PORT" "Basic YAML Config"; then
                print_status "PASS" "Basic YAML configuration test passed"
            else
                print_status "FAIL" "Basic YAML configuration test failed"
            fi
        else
            print_status "FAIL" "Basic YAML configuration test failed - Gunicorn did not start"
        fi

        # Cleanup
        kill $GUNICORN_PID 2>/dev/null || true
        wait $GUNICORN_PID 2>/dev/null || true
    fi

    # Clean up test files
    rm -f "$PROJECT_ROOT/test_basic_config.yml"
    rm -f "$PROJECT_ROOT/test_basic_gunicorn.conf.py"
}

# Function to test YAML configuration with Redis integration (Docker only)
test_yaml_config_with_redis_docker() {
    print_status "INFO" "Testing YAML configuration with Redis integration (Docker)..."

    if [ "$USE_DOCKER" = true ]; then
        # Docker-based testing with Redis (simplified like other system tests)
        print_status "INFO" "Starting Docker container with Redis for YAML testing..."

        # Build and run Docker container with Redis config
        docker build -f e2e/fixtures/dockerfiles/yaml-simple.Dockerfile -t "$DOCKER_IMAGE" .. >/dev/null 2>&1

        # Run container in background with Redis config
        docker run -d \
            --name "$DOCKER_CONTAINER" \
            -p 8089:8089 \
            -p 9094:9094 \
            -e PROMETHEUS_CONFIG_FILE="/app/config/redis.yml" \
            -v "$PROJECT_ROOT/e2e/test_configs:/app/config" \
            -v "$PROJECT_ROOT/e2e/fixtures/apps/test_app.py:/app/e2e/fixtures/apps/test_app.py" \
            -v "$PROJECT_ROOT/e2e/fixtures/configs/gunicorn.yaml.conf.py:/app/e2e/fixtures/configs/gunicorn.yaml.conf.py" \
            "$DOCKER_IMAGE" \
            gunicorn --config /app/e2e/fixtures/configs/gunicorn.yaml.conf.py test_app:app

        # Wait for services to be ready
        print_status "INFO" "Waiting for services to start..."
        sleep 10

        # Wait for Gunicorn to be ready
        if wait_for_service "127.0.0.1" "$GUNICORN_PORT" "Gunicorn"; then
            # Generate test requests
            generate_test_requests "$GUNICORN_PORT" 15

            # Test comprehensive metrics
            if verify_comprehensive_metrics "$METRICS_PORT" "Redis YAML Config"; then
                print_status "PASS" "Redis YAML configuration test passed"
            else
                print_status "FAIL" "Redis YAML configuration test failed"
            fi

            # Test signal handling
            test_signal_handling "$DOCKER_CONTAINER" "$METRICS_PORT"

            # Verify multiprocess files
            verify_multiproc_files "$DOCKER_CONTAINER"
        else
            print_status "FAIL" "Redis YAML configuration test failed - Gunicorn did not start"
            docker logs "$DOCKER_CONTAINER"
        fi

        # Show logs for debugging
        print_status "INFO" "Container logs:"
        docker logs "$DOCKER_CONTAINER"

        # Cleanup
        docker stop "$DOCKER_CONTAINER" 2>/dev/null || true
        docker rm "$DOCKER_CONTAINER" 2>/dev/null || true
    else
        print_status "INFO" "Redis integration test requires Docker mode"
        print_status "FAIL" "Skipping Redis integration test (use --docker flag)"
    fi
}

# Function to test YAML configuration with environment variable overrides
test_yaml_config_with_overrides() {
    print_status "INFO" "Testing YAML configuration with environment variable overrides..."

    if [ "$USE_DOCKER" = true ]; then
        print_status "INFO" "Testing environment variable overrides with Docker..."

        # Create test YAML config with different port
        cat > "$PROJECT_ROOT/e2e/test_configs/override.yml" << EOF
exporter:
  prometheus:
    metrics_port: 9095
    bind_address: "0.0.0.0"
    multiproc_dir: "/tmp/prometheus_multiproc"
  gunicorn:
    workers: 1
    timeout: 30
    keepalive: 2
  redis:
    enabled: false
  cleanup:
    db_files: true
EOF

        # Create Gunicorn config that loads YAML and overrides with env vars
        cat > "$PROJECT_ROOT/gunicorn.override.conf.py" << EOF
import os
from gunicorn_prometheus_exporter import load_yaml_config, PrometheusWorker

# Load YAML configuration
load_yaml_config("/app/config/override.yml")

# Override with environment variables
os.environ["PROMETHEUS_METRICS_PORT"] = "9094"

bind = ["0.0.0.0:8089"]
workers = 1
worker_class = PrometheusWorker
chdir = "/app"
EOF

        # Start Docker container with override config (simplified)
        print_status "INFO" "Starting Docker container with environment variable overrides..."

        # Build and run Docker container with override config
        docker build -f e2e/fixtures/dockerfiles/yaml-simple.Dockerfile -t "$DOCKER_IMAGE" .. >/dev/null 2>&1

        # Run container in background with override config
        docker run -d \
            --name "$DOCKER_CONTAINER" \
            -p 8089:8089 \
            -p 9094:9094 \
            -e PROMETHEUS_CONFIG_FILE="/app/config/override.yml" \
            -e PROMETHEUS_METRICS_PORT="9094" \
            -v "$PROJECT_ROOT/e2e/test_configs:/app/config" \
            -v "$PROJECT_ROOT/e2e/fixtures/apps/test_app.py:/app/e2e/fixtures/apps/test_app.py" \
            -v "$PROJECT_ROOT/e2e/fixtures/configs/gunicorn.yaml.conf.py:/app/e2e/fixtures/configs/gunicorn.yaml.conf.py" \
            "$DOCKER_IMAGE" \
            gunicorn --config /app/e2e/fixtures/configs/gunicorn.yaml.conf.py test_app:app

        # Wait for services to start
        print_status "INFO" "Waiting for services to start..."
        sleep 10

        if wait_for_service "127.0.0.1" "8089" "Gunicorn"; then
            # Test metrics endpoint (should be on port 9094 due to override)
            if test_metrics_endpoint "9094" "YAML Config with Overrides"; then
                print_status "PASS" "YAML configuration with overrides test passed"
            else
                print_status "FAIL" "YAML configuration with overrides test failed"
            fi
        else
            print_status "FAIL" "YAML configuration with overrides test failed - Gunicorn did not start"
            docker logs "$DOCKER_CONTAINER"
        fi

        # Cleanup
        docker stop "$DOCKER_CONTAINER" 2>/dev/null || true
        docker rm "$DOCKER_CONTAINER" 2>/dev/null || true
        return 0
    fi

    # Create test YAML config
    cat > "$PROJECT_ROOT/test_override_config.yml" << EOF
exporter:
  prometheus:
    metrics_port: 9095
    bind_address: "127.0.0.1"
    multiproc_dir: "/tmp/prometheus_test_override"
  gunicorn:
    workers: 1
    timeout: 30
    keepalive: 2
  redis:
    enabled: false
  cleanup:
    db_files: true
EOF

    # Create test Gunicorn config with environment variable overrides
    cat > "$PROJECT_ROOT/test_override_gunicorn.conf.py" << EOF
import os
from gunicorn_prometheus_exporter.hooks import load_yaml_config

# Load YAML configuration
load_yaml_config("$PROJECT_ROOT/test_override_config.yml")

# Override with environment variables
os.environ["PROMETHEUS_METRICS_PORT"] = "$METRICS_PORT"

from gunicorn_prometheus_exporter.hooks import (
    default_on_exit,
    default_on_starting,
    default_post_fork,
    default_when_ready,
    default_worker_int,
)

# Gunicorn settings
bind = "127.0.0.1:$GUNICORN_PORT"
workers = 1
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
timeout = 30

# Use pre-built hooks
when_ready = default_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork
EOF

    # Start Gunicorn with YAML config and overrides
    print_status "INFO" "Starting Gunicorn with YAML configuration and environment variable overrides..."
    cd "$PROJECT_ROOT"
    gunicorn --config test_override_gunicorn.conf.py test_app:app &
    GUNICORN_PID=$!

    # Wait for service to be ready
    if wait_for_service "127.0.0.1" "$GUNICORN_PORT" "Gunicorn"; then
        # Test metrics endpoint
        if test_metrics_endpoint "$METRICS_PORT" "YAML Config with Overrides"; then
            print_status "PASS" "YAML configuration with overrides test passed"
        else
            print_status "FAIL" "YAML configuration with overrides test failed"
        fi
    else
        print_status "FAIL" "YAML configuration with overrides test failed - Gunicorn did not start"
    fi

    # Cleanup
    kill $GUNICORN_PID 2>/dev/null || true
    wait $GUNICORN_PID 2>/dev/null || true

    # Clean up test files
    rm -f "$PROJECT_ROOT/test_override_config.yml"
    rm -f "$PROJECT_ROOT/test_override_gunicorn.conf.py"
}

# Function to test YAML configuration with Redis
test_yaml_config_with_redis() {
    print_status "INFO" "Testing YAML configuration with Redis..."

    if [ "$USE_DOCKER" = true ]; then
        print_status "INFO" "Testing Redis YAML configuration with Docker..."

        # Create Gunicorn config that loads Redis YAML config
        cat > "$PROJECT_ROOT/gunicorn.redis.conf.py" << EOF
import os
from gunicorn_prometheus_exporter import load_yaml_config, PrometheusWorker
from gunicorn_prometheus_exporter.hooks import (
    default_on_exit,
    default_on_starting,
    default_post_fork,
    redis_when_ready,
    default_worker_int,
)

# Load Redis YAML configuration
load_yaml_config("/app/config/redis.yml")

bind = ["0.0.0.0:8089"]
workers = 1
worker_class = PrometheusWorker
chdir = "/app"

# Use Redis-enabled hooks
when_ready = redis_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork
EOF

        # Start Docker container with Redis config (simplified)
        print_status "INFO" "Starting Docker container with Redis YAML configuration..."

        # Build and run Docker container with Redis config
        docker build -f e2e/fixtures/dockerfiles/yaml-simple.Dockerfile -t "$DOCKER_IMAGE" .. >/dev/null 2>&1

        # Run container in background with Redis config
        docker run -d \
            --name "$DOCKER_CONTAINER" \
            -p 8089:8089 \
            -p 9094:9094 \
            -e PROMETHEUS_CONFIG_FILE="/app/config/redis.yml" \
            -v "$PROJECT_ROOT/e2e/test_configs:/app/config" \
            -v "$PROJECT_ROOT/e2e/fixtures/apps/test_app.py:/app/e2e/fixtures/apps/test_app.py" \
            -v "$PROJECT_ROOT/e2e/fixtures/configs/gunicorn.yaml.conf.py:/app/e2e/fixtures/configs/gunicorn.yaml.conf.py" \
            "$DOCKER_IMAGE" \
            gunicorn --config /app/e2e/fixtures/configs/gunicorn.yaml.conf.py test_app:app

        # Wait for services to start
        print_status "INFO" "Waiting for services to start..."
        sleep 10

        if wait_for_service "127.0.0.1" "8089" "Gunicorn"; then
            # Test metrics endpoint
            if test_metrics_endpoint "9094" "Redis YAML Config"; then
                print_status "PASS" "Redis YAML configuration test passed"
            else
                print_status "FAIL" "Redis YAML configuration test failed"
            fi
        else
            print_status "FAIL" "Redis YAML configuration test failed - Gunicorn did not start"
            docker logs "$DOCKER_CONTAINER"
        fi

        # Cleanup
        docker stop "$DOCKER_CONTAINER" 2>/dev/null || true
        docker rm "$DOCKER_CONTAINER" 2>/dev/null || true
        return 0
    fi

    # Check if Redis is available
    if ! command -v redis-server > /dev/null 2>&1; then
        print_status "INFO" "Redis not available, skipping Redis YAML configuration test"
        return 0
    fi

    # Start Redis server for testing
    print_status "INFO" "Starting Redis server for testing..."
    redis-server --port 6380 --daemonize yes --dir /tmp --dbfilename redis_test.rdb

    # Wait for Redis to be ready
    sleep 2

    # Create test YAML config with Redis
    cat > "$PROJECT_ROOT/test_redis_config.yml" << EOF
exporter:
  prometheus:
    metrics_port: $METRICS_PORT
    bind_address: "127.0.0.1"
    multiproc_dir: "/tmp/prometheus_test_redis"
  gunicorn:
    workers: 1
    timeout: 30
    keepalive: 2
  redis:
    enabled: true
    host: "127.0.0.1"
    port: 6380
    db: 0
    password: null
    key_prefix: "gunicorn_test"
    ttl_seconds: 300
    ttl_disabled: false
  cleanup:
    db_files: true
EOF

    # Create test Gunicorn config with Redis
    cat > "$PROJECT_ROOT/test_redis_gunicorn.conf.py" << EOF
import os
from gunicorn_prometheus_exporter.hooks import load_yaml_config

# Load YAML configuration
load_yaml_config("$PROJECT_ROOT/test_redis_config.yml")

from gunicorn_prometheus_exporter.hooks import (
    default_on_exit,
    default_on_starting,
    default_post_fork,
    redis_when_ready,
    default_worker_int,
)

# Gunicorn settings
bind = "127.0.0.1:$GUNICORN_PORT"
workers = 1
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
timeout = 30

# Use Redis-enabled hooks
when_ready = redis_when_ready
on_starting = default_on_starting
worker_int = default_worker_int
on_exit = default_on_exit
post_fork = default_post_fork
EOF

    # Start Gunicorn with Redis YAML config
    print_status "INFO" "Starting Gunicorn with Redis YAML configuration..."
    cd "$PROJECT_ROOT"
    gunicorn --config test_redis_gunicorn.conf.py test_app:app &
    GUNICORN_PID=$!

    # Wait for service to be ready
    if wait_for_service "127.0.0.1" "$GUNICORN_PORT" "Gunicorn"; then
        # Test metrics endpoint
        if test_metrics_endpoint "$METRICS_PORT" "Redis YAML Config"; then
            print_status "PASS" "Redis YAML configuration test passed"
        else
            print_status "FAIL" "Redis YAML configuration test failed"
        fi
    else
        print_status "FAIL" "Redis YAML configuration test failed - Gunicorn did not start"
    fi

    # Cleanup
    kill $GUNICORN_PID 2>/dev/null || true
    wait $GUNICORN_PID 2>/dev/null || true

    # Stop Redis server
    redis-cli -p 6380 shutdown || true

    # Clean up test files
    rm -f "$PROJECT_ROOT/test_redis_config.yml"
    rm -f "$PROJECT_ROOT/test_redis_gunicorn.conf.py"
    rm -f /tmp/redis_test.rdb
}

# Function to test invalid YAML configuration
test_invalid_yaml_config() {
    print_status "INFO" "Testing invalid YAML configuration handling..."

    if [ "$USE_DOCKER" = true ]; then
        print_status "INFO" "Testing invalid YAML configuration with Docker..."

        # Create invalid YAML config (missing required bind_address)
        cat > "$PROJECT_ROOT/e2e/test_configs/invalid.yml" << EOF
exporter:
  prometheus:
    metrics_port: 9094
    # Missing required bind_address
  gunicorn:
    workers: 1
EOF

        # Create Gunicorn config that tries to load invalid YAML
        cat > "$PROJECT_ROOT/gunicorn.invalid.conf.py" << EOF
import os
import sys
from gunicorn_prometheus_exporter import load_yaml_config, PrometheusWorker

try:
    # Load invalid YAML configuration
    load_yaml_config("/app/config/invalid.yml")
    print("ERROR: Invalid YAML configuration was accepted")
    sys.exit(1)
except Exception as e:
    print(f"SUCCESS: Invalid YAML configuration was rejected: {e}")
    sys.exit(0)
EOF

        # Test invalid YAML config in Docker
        print_status "INFO" "Testing invalid YAML configuration in Docker container..."
        cd "$PROJECT_ROOT"

        # Build the image first
        docker build -f e2e/fixtures/dockerfiles/yaml-simple.Dockerfile -t test-invalid-yaml .

        # Run the test
        if docker run --rm -v "$PROJECT_ROOT/e2e/test_configs:/app/config" -v "$PROJECT_ROOT/gunicorn.invalid.conf.py:/app/gunicorn.invalid.conf.py" test-invalid-yaml python /app/gunicorn.invalid.conf.py; then
            print_status "PASS" "Invalid YAML configuration test passed"
        else
            print_status "FAIL" "Invalid YAML configuration test failed"
        fi

        # Clean up test files
        rm -f "$PROJECT_ROOT/e2e/test_configs/invalid.yml"
        rm -f "$PROJECT_ROOT/gunicorn.invalid.conf.py"
        return 0
    fi

    # Create invalid YAML config
    cat > "$PROJECT_ROOT/test_invalid_config.yml" << EOF
exporter:
  prometheus:
    metrics_port: 9091
    # Missing required bind_address
  gunicorn:
    workers: 1
EOF

    # Create test Gunicorn config
    cat > "$PROJECT_ROOT/test_invalid_gunicorn.conf.py" << EOF
import os
import sys
from gunicorn_prometheus_exporter.hooks import load_yaml_config

try:
    # Load invalid YAML configuration
    load_yaml_config("$PROJECT_ROOT/test_invalid_config.yml")
    print("ERROR: Invalid YAML configuration was accepted")
    sys.exit(1)
except Exception as e:
    print(f"SUCCESS: Invalid YAML configuration was rejected: {e}")
    sys.exit(0)
EOF

    # Test invalid YAML config
    cd "$PROJECT_ROOT"
    if python test_invalid_gunicorn.conf.py; then
        print_status "PASS" "Invalid YAML configuration test passed"
    else
        print_status "FAIL" "Invalid YAML configuration test failed"
    fi

    # Clean up test files
    rm -f "$PROJECT_ROOT/test_invalid_config.yml"
    rm -f "$PROJECT_ROOT/test_invalid_gunicorn.conf.py"
}

# Main test execution
main() {
    print_status "INFO" "Starting YAML configuration system tests..."
    print_status "INFO" "Project root: $PROJECT_ROOT"
    print_status "INFO" "Integration test dir: $TEST_DIR"
    if [ "$USE_DOCKER" != true ] && [ -n "$VENV_DIR" ]; then
        print_status "INFO" "Virtual environment: $VENV_DIR"
    fi

    # Ensure we're in the right directory
    cd "$PROJECT_ROOT"

    # Cleanup any existing processes
    cleanup

    # Run tests based on mode
    if [ "$QUICK_MODE" = true ]; then
        print_status "INFO" "Running quick tests only..."
        test_basic_yaml_config
    else
        print_status "INFO" "Running full test suite..."
        test_basic_yaml_config
        test_yaml_config_with_overrides
        test_yaml_config_with_redis_docker
        test_yaml_config_with_redis
        test_invalid_yaml_config
    fi

    # Final cleanup
    cleanup

    # Print test results
    echo
    print_status "INFO" "Test Results Summary:"
    print_status "INFO" "Tests passed: $TESTS_PASSED"
    print_status "INFO" "Tests failed: $TESTS_FAILED"

    if [ $TESTS_FAILED -eq 0 ]; then
        print_status "PASS" "All YAML configuration system tests passed!"
        exit 0
    else
        print_status "FAIL" "Some YAML configuration system tests failed!"
        exit 1
    fi
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"

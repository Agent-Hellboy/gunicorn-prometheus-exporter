#!/bin/bash

# System Test for Gunicorn Prometheus Exporter with Redis Integration
# This script tests the complete functionality including:
# - Dependency installation
# - Redis server startup
# - Gunicorn server startup with Redis integration
# - Request generation and metrics verification
# - Cleanup
#
# Usage:
#   ./system_test.sh [--quick] [--ci] [--no-redis] [--force]
#   --quick: Quick test (shorter duration, requires Redis running)
#   --ci: CI mode (timeout protection, auto cleanup)
#   --no-redis: Skip Redis startup (assume Redis is running)
#   --force: Kill existing processes on ports 8088 and 9093

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_PORT=8088
METRICS_PORT=9093
REDIS_PORT=6379
TEST_DURATION=30
REQUESTS_PER_SECOND=5
TIMEOUT=60

# Mode flags
QUICK_MODE=false
CI_MODE=false
SKIP_REDIS=false
FORCE_KILL=false
DOCKER_MODE=false

# Detect if running in Docker
if [ -f /.dockerenv ] || [ -n "${DOCKER_CONTAINER:-}" ]; then
    DOCKER_MODE=true
    SKIP_REDIS=true  # Redis is started by Docker startup script
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            TEST_DURATION=10
            REQUESTS_PER_SECOND=2
            shift
            ;;
        --ci)
            CI_MODE=true
            TIMEOUT=30
            shift
            ;;
        --no-redis)
            SKIP_REDIS=true
            shift
            ;;
        --force)
            FORCE_KILL=true
            shift
            ;;
        --docker)
            # Run the test in Docker container instead of locally
            echo "Running system test in Docker container..."
            docker build -f Dockerfile -t gunicorn-prometheus-exporter-test .. >/dev/null 2>&1
            docker run --rm \
                --name gunicorn-prometheus-test \
                -p 8088:8088 \
                -p 9093:9093 \
                -p 6379:6379 \
                gunicorn-prometheus-exporter-test
            exit $?
            ;;
        *)
            echo "Unknown option $1"
            echo "Usage: $0 [--quick] [--ci] [--no-redis] [--force] [--docker]"
            exit 1
            ;;
    esac
done

# Process tracking
GUNICORN_PID=""
REDIS_PID=""

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Cleaning up processes...${NC}"

    # Stop Gunicorn process
    if [ ! -z "$GUNICORN_PID" ]; then
        echo "Stopping Gunicorn (PID: $GUNICORN_PID)"
        kill -TERM "$GUNICORN_PID" 2>/dev/null || true
        sleep 2
        kill -KILL "$GUNICORN_PID" 2>/dev/null || true
    fi

    # Stop Redis process
    if [ ! -z "$REDIS_PID" ]; then
        echo "Stopping Redis (PID: $REDIS_PID)"
        kill -TERM "$REDIS_PID" 2>/dev/null || true
        sleep 2
        kill -KILL "$REDIS_PID" 2>/dev/null || true
    fi

    # Clean up any remaining processes
    pkill -f "gunicorn.*redis_integration" 2>/dev/null || true
    pkill -f "redis-server" 2>/dev/null || true

    # Clean up Redis database (with error handling)
    cleanup_redis || true

    # Clean up log files
    rm -f gunicorn.log 2>/dev/null || true

    echo -e "${GREEN}Cleanup completed${NC}"
}

# Set up trap for cleanup
trap cleanup EXIT INT TERM

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to kill processes on specific ports
kill_port_processes() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null || true)

    if [ ! -z "$pids" ]; then
        print_warning "Killing processes on port $port: $pids"
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 3  # Give more time for graceful shutdown
        # Force kill if still running
        local remaining_pids=$(lsof -ti :$port 2>/dev/null || true)
        if [ ! -z "$remaining_pids" ]; then
            print_warning "Force killing remaining processes on port $port: $remaining_pids"
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
        sleep 2  # Give more time after force kill
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1

    print_status "Waiting for service at $url..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "Service is ready at $url"
            return 0
        fi

        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    print_error "Service failed to start at $url after $max_attempts attempts"
    return 1
}

# Function to check if Redis is running
check_redis() {
    if redis-cli ping >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to flush Redis database
flush_redis() {
    print_status "Flushing Redis database for clean test..."

    if command -v redis-cli >/dev/null 2>&1; then
        redis-cli FLUSHDB >/dev/null 2>&1
        print_success "Redis database flushed"
    else
        print_warning "redis-cli not available, skipping Redis flush"
    fi
}

# Function to verify Redis contains metrics
verify_redis_metrics() {
    print_status "Verifying metrics are stored in Redis..."

    if ! command -v redis-cli >/dev/null 2>&1; then
        print_warning "redis-cli not available, skipping Redis verification"
        return 0
    fi

    # Check if Redis has any keys
    local key_count=$(redis-cli DBSIZE 2>/dev/null || echo "0")

    if [ "$key_count" -eq 0 ]; then
        print_error "Redis database is empty - no metrics stored"
        return 1
    fi

    print_success "Redis contains $key_count keys"

    # Check for specific metric patterns
    local metric_keys=$(redis-cli KEYS "*metric*" 2>/dev/null | wc -l)
    local meta_keys=$(redis-cli KEYS "*meta*" 2>/dev/null | wc -l)

    if [ "$metric_keys" -gt 0 ]; then
        print_success "Found $metric_keys metric keys in Redis"
    else
        print_error "No metric keys found in Redis"
        return 1
    fi

    if [ "$meta_keys" -gt 0 ]; then
        print_success "Found $meta_keys metadata keys in Redis"
    else
        print_error "No metadata keys found in Redis"
        return 1
    fi

    # Show sample keys
    print_status "Sample Redis keys:"
    redis-cli KEYS "*" 2>/dev/null | head -5 | while read key; do
        echo "  - $key"
    done

    return 0
}

# Function to clean up Redis
cleanup_redis() {
    print_status "Cleaning up Redis database..."

    if command -v redis-cli >/dev/null 2>&1; then
        # Try to connect to Redis and flush database
        if redis-cli ping >/dev/null 2>&1; then
            redis-cli FLUSHDB >/dev/null 2>&1 || true
            print_success "Redis database cleaned"
        else
            print_warning "Redis not responding, skipping cleanup"
        fi
    else
        print_warning "redis-cli not available, skipping Redis cleanup"
    fi
}
install_dependencies() {
    print_status "Installing dependencies..."

    # Skip dependency installation in Docker mode
    if [ "$DOCKER_MODE" = true ]; then
        print_status "Skipping dependency installation (Docker mode)"
        print_success "Dependencies already installed in container"
        return 0
    fi

    # Create virtual environment if not in CI mode or if it doesn't exist
    if [ "$CI_MODE" = true ] || [ ! -d "test_venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv test_venv
    fi

    source test_venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install the package in development mode
    pip install -e ..

    # Install additional test dependencies
    pip install redis requests psutil gunicorn flask

    print_success "Dependencies installed"
}

# Function to start Redis server
start_redis() {
    if [ "$SKIP_REDIS" = true ]; then
        print_status "Skipping Redis startup (--no-redis flag)"
        if check_redis; then
            print_success "Redis is running"
            return 0
        else
            print_error "Redis is not running but --no-redis was specified"
            return 1
        fi
    fi

    print_status "Starting Redis server..."

    # Check if Redis is already running
    if check_redis; then
        print_warning "Redis is already running"
        return 0
    fi

    # Try to start Redis server
    if command -v redis-server >/dev/null 2>&1; then
        redis-server --port $REDIS_PORT --daemonize yes
        sleep 2

        if check_redis; then
            print_success "Redis server started on port $REDIS_PORT"
            REDIS_PID=$(pgrep redis-server)
        else
            print_error "Failed to start Redis server"
            return 1
        fi
    else
        print_error "Redis server not found. Please install Redis."
        return 1
    fi
}

# Function to start Gunicorn server
start_gunicorn() {
    print_status "Starting Gunicorn server with Redis integration..."

    # Kill existing processes if --force flag is used
    if [ "$FORCE_KILL" = true ]; then
        print_status "Force killing existing processes on ports $APP_PORT and $METRICS_PORT..."
        kill_port_processes $APP_PORT
        kill_port_processes $METRICS_PORT
    fi

    # Check if ports are available
    if ! check_port $APP_PORT; then
        if [ "$FORCE_KILL" = true ]; then
            print_error "Port $APP_PORT is still in use after force kill"
            return 1
        else
            print_error "Port $APP_PORT is already in use. Use --force to kill existing processes."
            return 1
        fi
    fi

    if ! check_port $METRICS_PORT; then
        if [ "$FORCE_KILL" = true ]; then
            print_error "Port $METRICS_PORT is still in use after force kill"
            return 1
        else
            print_error "Port $METRICS_PORT is already in use. Use --force to kill existing processes."
            return 1
        fi
    fi

    # Set environment variables
    export PROMETHEUS_METRICS_PORT=$METRICS_PORT
    export PROMETHEUS_BIND_ADDRESS="127.0.0.1"
    export REDIS_ENABLED="true"
    export REDIS_HOST="127.0.0.1"
    export REDIS_PORT=$REDIS_PORT
    export REDIS_DB="0"
    export GUNICORN_WORKERS="2"

    # Start Gunicorn in background
    if [ "$DOCKER_MODE" != true ]; then
        source test_venv/bin/activate
    fi
    cd ../example

    # Use different startup method based on mode
    if [ "$CI_MODE" = true ]; then
        nohup gunicorn --config gunicorn_redis_integration.conf.py app:app > ../system-test/gunicorn.log 2>&1 &
    else
        gunicorn --config gunicorn_redis_integration.conf.py app:app &
    fi

    GUNICORN_PID=$!
    cd ../system-test

    print_status "Gunicorn started with PID: $GUNICORN_PID"

    # Give Gunicorn time to fully initialize
    sleep 2

    # Wait for services to be ready
    wait_for_service "http://localhost:$APP_PORT/"
    wait_for_service "http://localhost:$METRICS_PORT/metrics"

    print_success "Gunicorn server is ready"
}

# Function to generate test requests
generate_requests() {
    print_status "Generating test requests for $TEST_DURATION seconds..."

    # Simple approach: generate requests in background and show progress
    (
        for i in $(seq 1 $((TEST_DURATION * 2))); do
            curl -s "http://localhost:$APP_PORT/" >/dev/null 2>&1 &
            curl -s "http://localhost:$APP_PORT/nonexistent" >/dev/null 2>&1 &
            sleep 0.5
        done
    ) &

    local request_pid=$!

    # Show progress dots
    for i in $(seq 1 $TEST_DURATION); do
        sleep 1
        echo -n "."
    done

    echo ""  # New line after progress dots

    # Wait for request generation to complete
    wait $request_pid 2>/dev/null || true

    print_success "Generated $((TEST_DURATION * 4)) requests"
}

# Function to verify metrics
verify_metrics() {
    print_status "Verifying metrics..."

    local metrics_url="http://localhost:$METRICS_PORT/metrics"
    local metrics_output=$(curl -s "$metrics_url")

    # Check if metrics endpoint is accessible
    if [ -z "$metrics_output" ]; then
        print_error "Failed to fetch metrics from $metrics_url"
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

    # Optional metrics (may not have values)
    local optional_metrics=(
        "gunicorn_master_worker_restart_total"
    )

    local failed_checks=0

    # Check each expected metric
    for metric in "${expected_metrics[@]}"; do
        local metric_line=$(echo "$metrics_output" | grep "$metric.*[0-9]" | head -1)
        if [ ! -z "$metric_line" ]; then
            print_success "Metric $metric: $metric_line"
        else
            print_error "Metric $metric has no values"
            failed_checks=$((failed_checks + 1))
        fi
    done

    # Check optional metrics (don't fail if they have no values)
    for metric in "${optional_metrics[@]}"; do
        local metric_line=$(echo "$metrics_output" | grep "$metric.*[0-9]" | head -1)
        if [ ! -z "$metric_line" ]; then
            print_success "Optional metric $metric: $metric_line"
        else
            print_warning "Optional metric $metric has no values (this is normal)"
        fi
    done

    # Check for specific metric types
    if echo "$metrics_output" | grep -q "# TYPE.*counter"; then
        print_success "Counter metrics found"
    else
        print_error "No counter metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    if echo "$metrics_output" | grep -q "# TYPE.*gauge"; then
        print_success "Gauge metrics found"
    else
        print_error "No gauge metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    if echo "$metrics_output" | grep -q "# TYPE.*histogram"; then
        print_success "Histogram metrics found"
    else
        print_error "No histogram metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    # Check for worker IDs
    if echo "$metrics_output" | grep -q "worker_id.*worker_"; then
        print_success "Worker ID labels found"
    else
        print_error "No worker ID labels found"
        failed_checks=$((failed_checks + 1))
    fi

    # Check Redis integration
    if echo "$metrics_output" | grep -q "gunicorn_worker_requests_total.*[1-9]"; then
        print_success "Request metrics are being captured"
    else
        print_error "Request metrics are not being captured"
        failed_checks=$((failed_checks + 1))
    fi

    # Count total metric samples
    local sample_count=$(echo "$metrics_output" | grep -c "^gunicorn.*[0-9]" || true)
    print_status "Total metric samples: $sample_count"

    if [ $sample_count -gt 10 ]; then
        print_success "Sufficient metric samples found ($sample_count)"
    else
        print_error "Insufficient metric samples ($sample_count)"
        failed_checks=$((failed_checks + 1))
    fi

    # Check Redis keys
    local redis_keys=$(redis-cli keys "gunicorn:*" | wc -l)
    print_status "Redis keys count: $redis_keys"

    if [ $redis_keys -gt 10 ]; then
        print_success "Redis integration working ($redis_keys keys)"
    else
        print_error "Redis integration not working ($redis_keys keys)"
        failed_checks=$((failed_checks + 1))
    fi

    # Test specific Redis key patterns
    local metric_keys=$(redis-cli keys "gunicorn:metric:*" | wc -l)
    local meta_keys=$(redis-cli keys "gunicorn:meta:*" | wc -l)

    print_status "Redis metric keys: $metric_keys, meta keys: $meta_keys"

    if [ $metric_keys -gt 5 ] && [ $meta_keys -gt 5 ]; then
        print_success "Redis key patterns correct"
    else
        print_error "Redis key patterns incorrect"
        failed_checks=$((failed_checks + 1))
    fi

    # Test Redis key values
    local sample_key=$(redis-cli keys "gunicorn:metric:*" | head -1)
    if [ ! -z "$sample_key" ]; then
        local key_value=$(redis-cli hget "$sample_key" "value" 2>/dev/null || echo "none")
        if [ "$key_value" != "none" ] && [ ! -z "$key_value" ]; then
            print_success "Redis key values accessible"
        else
            print_error "Redis key values not accessible"
            failed_checks=$((failed_checks + 1))
        fi
    fi

    return $failed_checks
}

# Function to test signal handling
test_signal_handling() {
    print_status "Testing signal handling (Ctrl+C simulation)..."

    # Send SIGINT to Gunicorn master process
    if [ ! -z "$GUNICORN_PID" ]; then
        kill -INT "$GUNICORN_PID"
        sleep 3

        # Check if process is still running
        if kill -0 "$GUNICORN_PID" 2>/dev/null; then
            print_warning "Process still running after SIGINT, sending SIGTERM"
            kill -TERM "$GUNICORN_PID"
            sleep 2
        fi

        if kill -0 "$GUNICORN_PID" 2>/dev/null; then
            print_error "Process did not respond to signals"
            return 1
        else
            print_success "Signal handling working correctly"
            GUNICORN_PID=""  # Clear PID since process is dead
        fi
    fi
}

# Main test execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Gunicorn Prometheus Exporter System Test${NC}"
    if [ "$DOCKER_MODE" = true ]; then
        echo -e "${BLUE}  Mode: Docker Test (Cross-Platform)${NC}"
    elif [ "$QUICK_MODE" = true ]; then
        echo -e "${BLUE}  Mode: Quick Test${NC}"
    elif [ "$CI_MODE" = true ]; then
        echo -e "${BLUE}  Mode: CI Test${NC}"
    else
        echo -e "${BLUE}  Mode: Full Test${NC}"
    fi
    echo -e "${BLUE}========================================${NC}"
    echo

    # Step 1: Install dependencies
    install_dependencies

    # Step 2: Flush Redis for clean test
    flush_redis

    # Step 3: Start Redis
    start_redis

    # Step 4: Start Gunicorn
    start_gunicorn

    # Step 5: Generate requests
    generate_requests

    # Step 6: Verify metrics
    if verify_metrics; then
        print_success "All metrics verification passed!"
    else
        print_error "Some metrics verification failed!"
        exit 1
    fi

    # Step 7: Verify Redis contains metrics
    if verify_redis_metrics; then
        print_success "Redis metrics verification passed!"
    else
        print_error "Redis metrics verification failed!"
        exit 1
    fi

    # Step 8: Test signal handling
    test_signal_handling

    # Step 9: Clean up Redis
    cleanup_redis

    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  System Test Completed Successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Run main function
main "$@"

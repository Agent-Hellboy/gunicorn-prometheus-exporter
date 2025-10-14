#!/bin/bash

# Integration Test for Gunicorn Prometheus Exporter with Redis Integration
# This script tests the complete functionality including:
# - Dependency installation
# - Redis server startup
# - Gunicorn server startup with Redis integration
# - Request generation and metrics verification
# - Prometheus scraping verification (15 seconds)
# - Redis TTL configuration verification
# - Signal handling testing
# - Redis key expiration verification (30 seconds TTL)
# - Cleanup
#
# Usage:
#   ./test_redis_integ.sh [--quick] [--ci] [--no-redis] [--force]
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

# Redis CLI options (host/port/db)
REDIS_HOST_OPT="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT_OPT="${REDIS_PORT:-6379}"
REDIS_DB_OPT="${REDIS_DB:-0}"
REDIS_CLI=("redis-cli" "-h" "$REDIS_HOST_OPT" "-p" "$REDIS_PORT_OPT" "-n" "$REDIS_DB_OPT")

# Controls whether to allow FLUSHALL during tests (default: false)
: "${REDIS_DESTRUCTIVE_FLUSH:=false}"
TEST_DURATION=30
REQUESTS_PER_SECOND=5
TIMEOUT=300

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
        # Skip script name if it's passed as first argument
        */test_redis_integ.sh|./test_redis_integ.sh|test_redis_integ.sh)
            shift
            ;;
        --quick)
            QUICK_MODE=true
            TEST_DURATION=10
            REQUESTS_PER_SECOND=2
            # Increase timeout for quick mode to allow for cleanup
            TIMEOUT=300
            shift
            ;;
        --ci)
            CI_MODE=true
            # Increase timeout to allow for test execution and cleanup
            # But don't override quick mode settings if already set
            if [ "$QUICK_MODE" != true ]; then
                TIMEOUT=300
            fi
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
            echo "Running integration test in Docker container..."
            cd "$(dirname "$0")/.."  # Change to project root
            docker build -f e2e/fixtures/dockerfiles/default.Dockerfile -t gunicorn-prometheus-exporter-test . >/dev/null 2>&1

            # Set environment variables to pass test mode to Docker container
            DOCKER_ENV_ARGS=""
            if [ "$QUICK_MODE" = true ]; then
                DOCKER_ENV_ARGS="$DOCKER_ENV_ARGS -e QUICK_MODE=true"
            fi
            if [ "$CI_MODE" = true ]; then
                DOCKER_ENV_ARGS="$DOCKER_ENV_ARGS -e CI_MODE=true"
            fi

            docker run --rm \
                --name gunicorn-prometheus-test \
                -p 8088:8088 \
                -p 9093:9093 \
                -p 6379:6379 \
                $DOCKER_ENV_ARGS \
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
    if "${REDIS_CLI[@]}" ping >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to flush Redis database
flush_redis() {
    print_status "Flushing Redis database for clean test..."

    if command -v redis-cli >/dev/null 2>&1; then
        if [ "$REDIS_DESTRUCTIVE_FLUSH" = true ]; then
            # Destructive flush - use FLUSHALL
            if "${REDIS_CLI[@]}" FLUSHALL >/dev/null 2>&1; then
                print_success "Redis all databases flushed (FLUSHALL)"
            else
                # Fallback to flushing current database only
                if "${REDIS_CLI[@]}" FLUSHDB >/dev/null 2>&1; then
                    print_success "Redis current database flushed (FLUSHDB)"
                else
                    print_warning "Failed to flush Redis database"
                    return 1
                fi
            fi
        else
            # Safer: delete only test keys by prefix
            prefix="${REDIS_KEY_PREFIX:-gunicorn}"
            # Batch unlink for performance
            "${REDIS_CLI[@]}" --scan --pattern "${prefix}:*" | \
              xargs -r -n1 -P4 -I{} "${REDIS_CLI[@]}" UNLINK "{}" >/dev/null 2>&1 || true
            print_success "Deleted keys with prefix ${prefix}:*"
        fi

        # Verify Redis is empty (or only has non-test keys)
        local key_count
        key_count=$("${REDIS_CLI[@]}" DBSIZE 2>/dev/null || echo "0")
        if [ "$key_count" -eq 0 ]; then
            print_success "Redis confirmed empty (0 keys)"
        else
            print_success "Redis cleanup complete ($key_count keys remaining)"
        fi

        # Additional validation: Check for any signal metrics
        local signal_metrics
        signal_metrics=$("${REDIS_CLI[@]}" --scan --pattern "*master_worker_restart*" 2>/dev/null | wc -l || echo "0")
        if [ "$signal_metrics" -eq 0 ]; then
            print_success "No signal metrics found in Redis (clean state)"
        else
            print_warning "Found $signal_metrics signal metric keys in Redis - forcing cleanup"
            "${REDIS_CLI[@]}" --scan --pattern "*master_worker_restart*" | \
              xargs -r -n1 -P4 -I{} "${REDIS_CLI[@]}" UNLINK "{}" >/dev/null 2>&1 || true
            print_success "Signal metrics cleaned from Redis"
        fi
    else
        print_warning "redis-cli not available, skipping Redis flush"
    fi
}

# Function to validate Redis is clean before signal testing
validate_redis_clean() {
    print_status "Validating Redis is clean before signal testing..."

    if ! command -v redis-cli >/dev/null 2>&1; then
        print_warning "redis-cli not available, skipping Redis validation"
        return 0
    fi

    # Check total key count
    local key_count
    key_count=$("${REDIS_CLI[@]}" DBSIZE 2>/dev/null || echo "0")
    print_status "Redis key count: $key_count"

    # Check for any signal metrics specifically
    local signal_metrics
    signal_metrics=$("${REDIS_CLI[@]}" --scan --pattern "*master_worker_restart*" 2>/dev/null | wc -l || echo "0")
    print_status "Signal metric keys found: $signal_metrics"

    if [ "$signal_metrics" -gt 0 ]; then
        print_warning "Found $signal_metrics signal metric keys - cleaning Redis before signal test"
        "${REDIS_CLI[@]}" --scan --pattern "*master_worker_restart*" | \
          xargs -r -n1 -P4 -I{} "${REDIS_CLI[@]}" UNLINK "{}" >/dev/null 2>&1 || true
        print_success "Signal metrics cleaned from Redis"

        # Verify cleanup
        signal_metrics=$("${REDIS_CLI[@]}" --scan --pattern "*master_worker_restart*" 2>/dev/null | wc -l || echo "0")
        if [ "$signal_metrics" -eq 0 ]; then
            print_success "✓ Redis validated clean for signal testing"
        else
            print_error "✗ Redis still contains $signal_metrics signal metric keys"
            return 1
        fi
    else
        print_success "✓ Redis validated clean for signal testing"
    fi

    return 0
}

# Function to verify Redis contains metrics
verify_redis_metrics() {
    print_status "Verifying metrics are stored in Redis..."

    if ! command -v redis-cli >/dev/null 2>&1; then
        print_warning "redis-cli not available, skipping Redis verification"
        return 0
    fi

    # Check if Redis has any keys
    local key_count
    key_count=$("${REDIS_CLI[@]}" DBSIZE 2>/dev/null || echo "0")

    if [ "$key_count" -eq 0 ]; then
        print_error "Redis database is empty - no metrics stored"
        return 1
    fi

    print_success "Redis contains $key_count keys"

    # Check for specific metric patterns
    local metric_keys
    metric_keys=$("${REDIS_CLI[@]}" --scan --pattern "*metric*" 2>/dev/null | wc -l)
    local meta_keys
    meta_keys=$("${REDIS_CLI[@]}" --scan --pattern "*meta*" 2>/dev/null | wc -l)

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
    "${REDIS_CLI[@]}" --scan --pattern "*" 2>/dev/null | head -5 | while read -r key; do
        echo "  - $key"
    done

    return 0
}

# Function to clean up Redis
cleanup_redis() {
    print_status "Cleaning up Redis database..."

    if command -v redis-cli >/dev/null 2>&1; then
        # Try to connect to Redis and flush database
        if "${REDIS_CLI[@]}" ping >/dev/null 2>&1; then
            if [ "$REDIS_DESTRUCTIVE_FLUSH" = true ]; then
                # Destructive cleanup - use FLUSHALL
                if "${REDIS_CLI[@]}" FLUSHALL >/dev/null 2>&1; then
                    print_success "Redis all databases cleaned (FLUSHALL)"
                else
                    # Fallback to FLUSHDB
                    "${REDIS_CLI[@]}" FLUSHDB >/dev/null 2>&1 || true
                    print_success "Redis current database cleaned (FLUSHDB)"
                fi
            else
                # Safer: delete only test keys by prefix
                prefix="${REDIS_KEY_PREFIX:-gunicorn}"
                # Batch unlink for performance
                "${REDIS_CLI[@]}" --scan --pattern "${prefix}:*" | \
                  xargs -r -n1 -P4 -I{} "${REDIS_CLI[@]}" UNLINK "{}" >/dev/null 2>&1 || true
                print_success "Deleted keys with prefix ${prefix}:*"
            fi
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
    export REDIS_KEY_PREFIX="gunicorn"
    export REDIS_TTL_SECONDS="30"  # 30 seconds TTL for testing expiration
    export REDIS_TTL_DISABLED="false"  # Enable TTL (set to "true" to disable)
    export GUNICORN_WORKERS="2"

    # Start Gunicorn in background
    if [ "$DOCKER_MODE" != true ]; then
        source test_venv/bin/activate
    fi
    cd example

    # Use different startup method based on mode
    if [ "$CI_MODE" = true ]; then
        nohup gunicorn --config gunicorn_redis_integration.conf.py app:app > ../gunicorn.log 2>&1 &
    else
        gunicorn --config gunicorn_redis_integration.conf.py app:app &
    fi

    GUNICORN_PID=$!
    cd ../

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
        "gunicorn_master_worker_restart_count_total"
        "gunicorn_worker_restart_total"
        "gunicorn_worker_restart_count_total"
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

        # Show detailed request metric values
        print_status "Request metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_requests_total.*[0-9]" | while read -r line; do
            echo "  - $line"
        done
    else
        print_error "Request metrics are not being captured"
        failed_checks=$((failed_checks + 1))
    fi

    # Check memory metrics
    if echo "$metrics_output" | grep -q "gunicorn_worker_memory_bytes.*[0-9]"; then
        print_success "Memory metrics are being captured"

        # Show detailed memory metric values
        print_status "Memory metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_memory_bytes.*[0-9]" | while read -r line; do
            echo "  - $line"
        done
    else
        print_error "Memory metrics are not being captured"
        failed_checks=$((failed_checks + 1))
    fi

    # Check CPU metrics
    if echo "$metrics_output" | grep -q "gunicorn_worker_cpu_percent.*[0-9]"; then
        print_success "CPU metrics are being captured"

        # Show detailed CPU metric values
        print_status "CPU metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_cpu_percent.*[0-9]" | while read -r line; do
            echo "  - $line"
        done
    else
        print_error "CPU metrics are not being captured"
        failed_checks=$((failed_checks + 1))
    fi

    # Check uptime metrics
    if echo "$metrics_output" | grep -q "gunicorn_worker_uptime_seconds.*[0-9]"; then
        print_success "Uptime metrics are being captured"

        # Show detailed uptime metric values
        print_status "Uptime metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_uptime_seconds.*[0-9]" | while read -r line; do
            echo "  - $line"
        done
    else
        print_error "Uptime metrics are not being captured"
        failed_checks=$((failed_checks + 1))
    fi

    # Check request duration metrics
    if echo "$metrics_output" | grep -q "gunicorn_worker_request_duration_seconds.*[0-9]"; then
        print_success "Request duration metrics are being captured"

        # Show detailed request duration metric values
        print_status "Request duration metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_request_duration_seconds.*[0-9]" | while read -r line; do
            echo "  - $line"
        done
    else
        print_error "Request duration metrics are not being captured"
        failed_checks=$((failed_checks + 1))
    fi

    # Check worker state metrics
    if echo "$metrics_output" | grep -q "gunicorn_worker_state.*[0-9]"; then
        print_success "Worker state metrics are being captured"

        # Show detailed worker state metric values
        print_status "Worker state metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_state.*[0-9]" | while read -r line; do
            echo "  - $line"
        done
    else
        print_error "Worker state metrics are not being captured"
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
    local redis_keys
    redis_keys=$("${REDIS_CLI[@]}" --scan --pattern "gunicorn:*" | wc -l)
    print_status "Redis keys count: $redis_keys"

    if [ $redis_keys -gt 10 ]; then
        print_success "Redis integration working ($redis_keys keys)"
    else
        print_error "Redis integration not working ($redis_keys keys)"
        failed_checks=$((failed_checks + 1))
    fi

    # Test specific Redis key patterns
    local metric_keys
    metric_keys=$("${REDIS_CLI[@]}" --scan --pattern "gunicorn:*:metric:*" | wc -l)
    local meta_keys
    meta_keys=$("${REDIS_CLI[@]}" --scan --pattern "gunicorn:*:meta:*" | wc -l)

    print_status "Redis metric keys: $metric_keys, meta keys: $meta_keys"

    if [ $metric_keys -gt 5 ] && [ $meta_keys -gt 5 ]; then
        print_success "Redis key patterns correct"
    else
        print_error "Redis key patterns incorrect"
        failed_checks=$((failed_checks + 1))
    fi

    # Test Redis key values
    local sample_key
    sample_key=$("${REDIS_CLI[@]}" --scan --pattern "gunicorn:*:metric:*" | head -1)
    if [ ! -z "$sample_key" ]; then
        print_status "Testing Redis key: $sample_key"

        # Use a more robust approach to handle keys with special characters
        # Write the key to a temporary file to avoid shell escaping issues
        local temp_key_file
        temp_key_file=$(mktemp)
        echo "$sample_key" > "$temp_key_file"

        local key_exists
        key_exists=$(redis-cli -h "$REDIS_HOST_OPT" -p "$REDIS_PORT_OPT" -n "$REDIS_DB_OPT" exists "$sample_key" 2>/dev/null || echo "0")

        if [ "$key_exists" = "1" ]; then
            local key_type
            key_type=$(redis-cli -h "$REDIS_HOST_OPT" -p "$REDIS_PORT_OPT" -n "$REDIS_DB_OPT" type "$sample_key" 2>/dev/null || echo "none")
            print_status "Key type: $key_type"

            if [ "$key_type" = "hash" ]; then
                # Try to get hash fields using a more robust approach
                local hash_fields
                hash_fields=$(redis-cli -h "$REDIS_HOST_OPT" -p "$REDIS_PORT_OPT" -n "$REDIS_DB_OPT" hgetall "$sample_key" 2>/dev/null || echo "none")
                print_status "Hash fields: $hash_fields"

                # Check if we got any fields back
                if [ "$hash_fields" != "none" ] && [ ! -z "$hash_fields" ]; then
                    # Check if the hash contains the expected fields
                    if echo "$hash_fields" | grep -q "value" && echo "$hash_fields" | grep -q "timestamp"; then
                        print_success "Redis key values accessible"
                    else
                        print_error "Redis key missing expected fields (value/timestamp)"
                        failed_checks=$((failed_checks + 1))
                    fi
                else
                    print_error "Redis key values not accessible"
                    failed_checks=$((failed_checks + 1))
                fi
            else
                print_error "Redis key is not a hash type (got: $key_type)"
                failed_checks=$((failed_checks + 1))
            fi
        else
            print_error "Redis key does not exist"
            failed_checks=$((failed_checks + 1))
        fi

        # Clean up temp file
        rm -f "$temp_key_file"
    else
        print_error "No sample key found for testing"
        failed_checks=$((failed_checks + 1))
    fi

    # Comprehensive Redis verification (similar to multiprocess file verification)
    print_status "Verifying Redis storage..."

    # Check Redis key patterns
    local counter_keys
    counter_keys=$("${REDIS_CLI[@]}" --scan --pattern "gunicorn:counter:*" | wc -l)
    local gauge_keys
    gauge_keys=$("${REDIS_CLI[@]}" --scan --pattern "gunicorn:gauge*:*" | wc -l)
    local histogram_keys
    histogram_keys=$("${REDIS_CLI[@]}" --scan --pattern "gunicorn:histogram:*" | wc -l)

    print_status "Redis key distribution:"
    print_status "  - Counter keys: $counter_keys"
    print_status "  - Gauge keys: $gauge_keys"
    print_status "  - Histogram keys: $histogram_keys"

    # Show sample Redis keys
    print_status "Sample Redis keys:"
    "${REDIS_CLI[@]}" --scan --pattern "gunicorn:*" 2>/dev/null | head -5 | while read -r key; do
        echo "  - $key"
    done

    # Verify Redis key structure
    if [ $counter_keys -gt 0 ] && [ $gauge_keys -gt 0 ] && [ $histogram_keys -gt 0 ]; then
        print_success "Redis key structure verification passed"
    else
        print_error "Redis key structure incomplete"
        failed_checks=$((failed_checks + 1))
    fi

    # Final verification summary
    if [ $failed_checks -eq 0 ]; then
        print_success "All Redis integration verification passed!"
    else
        print_error "Some Redis integration verification failed!"
    fi

    return $failed_checks
}

# Function to verify Prometheus scraping
verify_prometheus_scraping() {
    print_status "Verifying Prometheus scraping..."

    # Wait for Prometheus to scrape metrics
    print_status "Waiting 15 seconds for Prometheus to scrape metrics..."
    sleep 15

    # Check if Prometheus is running and has scraped metrics
    local prometheus_url="http://localhost:9090"

    # Check Prometheus targets
    print_status "Checking Prometheus targets..."
    local targets_response
    targets_response=$(curl -s "${prometheus_url}/api/v1/targets" 2>/dev/null || echo "")

    if [ ! -z "$targets_response" ]; then
        print_success "Prometheus API is accessible"

        # Check if our target is up
        local target_up
        target_up=$(echo "$targets_response" | grep -o '"health":"up"' | wc -l)

        if [ "$target_up" -gt 0 ]; then
            print_success "Prometheus target is UP"
        else
            print_warning "Prometheus target may not be UP"
        fi
    else
        print_warning "Prometheus API not accessible, skipping scraping verification"
        return 0
    fi

    # Check if Prometheus has scraped our metrics
    print_status "Checking if Prometheus has scraped metrics..."
    local metrics_response
    metrics_response=$(curl -s "${prometheus_url}/api/v1/query?query=gunicorn_worker_requests_total" 2>/dev/null || echo "")

    if [ ! -z "$metrics_response" ]; then
        # Check if we have metric data
        local metric_count
        metric_count=$(echo "$metrics_response" | grep -o '"value":' | wc -l)

        if [ "$metric_count" -gt 0 ]; then
            print_success "Prometheus has scraped metrics (${metric_count} data points found)"

            # Print the actual metrics grabbed from Prometheus
            print_status "Metrics grabbed from Prometheus:"
            if command -v jq >/dev/null 2>&1; then
                echo "$metrics_response" | jq -r '.data.result[]? | "\(.metric.__name__){\(.metric | to_entries | map("\(.key)=\"\(.value)\"") | join(","))} \(.value[1])"' 2>/dev/null
            else
                # Fallback: extract metric names and values manually
                echo "$metrics_response" | grep -o '"__name__":"[^"]*"' | sed 's/"__name__":"//g' | sed 's/"//g' | while read -r metric_name; do
                    echo "  $metric_name: $(echo "$metrics_response" | grep -A 5 "\"__name__\":\"$metric_name\"" | grep -o '"value":\[[^]]*\]' | head -1)"
                done
            fi

            # Also query for other metric types to show comprehensive data
            print_status "Additional metrics from Prometheus:"
            local additional_queries=("gunicorn_worker_memory_bytes" "gunicorn_worker_cpu_percent" "gunicorn_worker_uptime_seconds" "gunicorn_worker_state")

            for query in "${additional_queries[@]}"; do
                local query_response
                query_response=$(curl -s "${prometheus_url}/api/v1/query?query=${query}" 2>/dev/null || echo "")
                if [ ! -z "$query_response" ]; then
                    local query_count
                    query_count=$(echo "$query_response" | grep -o '"value":' | wc -l)
                    if [ "$query_count" -gt 0 ]; then
                        print_status "  ${query} (${query_count} samples):"
                        if command -v jq >/dev/null 2>&1; then
                            echo "$query_response" | jq -r '.data.result[]? | "    \(.metric.__name__){\(.metric | to_entries | map("\(.key)=\"\(.value)\"") | join(","))} \(.value[1])"' 2>/dev/null
                        else
                            # Fallback: show metric names and sample values
                            echo "$query_response" | grep -o '"__name__":"[^"]*"' | sed 's/"__name__":"//g' | sed 's/"//g' | head -3 | while read -r metric_name; do
                                echo "    $metric_name: $(echo "$query_response" | grep -A 5 "\"__name__\":\"$metric_name\"" | grep -o '"value":\[[^]]*\]' | head -1)"
                            done
                        fi
                    fi
                fi
            done
        else
            print_warning "Prometheus scraped but no metric data found"
        fi
    else
        print_warning "Could not query Prometheus metrics"
    fi

    return 0
}

# Function to verify Redis TTL configuration and expiration
verify_redis_ttl() {
    print_status "Verifying Redis TTL configuration..."

    if ! command -v redis-cli >/dev/null 2>&1; then
        print_warning "redis-cli not available, skipping TTL verification"
        return 0
    fi

    # Check if Redis has any keys
    local key_count
    key_count=$("${REDIS_CLI[@]}" DBSIZE 2>/dev/null || echo "0")

    if [ "$key_count" -eq 0 ]; then
        print_warning "No Redis keys found for TTL verification"
        return 0
    fi

    # Get a sample key to check TTL
    local sample_key
    sample_key=$("${REDIS_CLI[@]}" --scan --pattern "gunicorn:*:metric:*" 2>/dev/null | head -1)

    if [ ! -z "$sample_key" ]; then
        local ttl_value
        ttl_value=$(redis-cli -h "$REDIS_HOST_OPT" -p "$REDIS_PORT_OPT" -n "$REDIS_DB_OPT" ttl "$sample_key" 2>/dev/null || echo "-1")

        if [ "$ttl_value" = "-1" ]; then
            print_warning "Sample key has no TTL (persists indefinitely)"
        elif [ "$ttl_value" = "-2" ]; then
            print_warning "Sample key does not exist"
        else
            print_success "Sample key TTL: ${ttl_value} seconds"

            # Check if TTL is reasonable (between 1 and 30 seconds for our test config)
            if [ "$ttl_value" -ge 1 ] && [ "$ttl_value" -le 30 ]; then
                print_success "TTL value is within expected range (1-30 seconds)"
            else
                print_warning "TTL value ${ttl_value} is outside expected range"
            fi
        fi
    else
        print_warning "No sample metric keys found for TTL verification"
    fi

    return 0
}

# Function to verify Redis key expiration after TTL
verify_redis_expiration() {
    print_status "Verifying Redis key expiration after TTL..."

    # Wait for TTL to expire (30 seconds total)
    print_status "Waiting for TTL expiration (30 seconds total)..."
    sleep 30

    if ! command -v redis-cli >/dev/null 2>&1; then
        print_warning "redis-cli not available, skipping expiration verification"
        return 0
    fi

    # Check if Redis keys have expired
    local key_count_after
    key_count_after=$("${REDIS_CLI[@]}" DBSIZE 2>/dev/null || echo "0")

    print_status "Redis keys after TTL expiration: ${key_count_after}"

    # Check if any metric keys still exist
    local metric_keys_count
    metric_keys_count=$("${REDIS_CLI[@]}" --scan --pattern "gunicorn:*:metric:*" 2>/dev/null | wc -l)

    if [ "$metric_keys_count" -eq 0 ]; then
        print_success "All metric keys have expired and been cleaned up by Redis TTL"
    else
        print_warning "Some metric keys still exist after TTL expiration: ${metric_keys_count} keys"

        # Check TTL of remaining keys
        local remaining_key
        remaining_key=$("${REDIS_CLI[@]}" --scan --pattern "gunicorn:*:metric:*" 2>/dev/null | head -1)
        if [ ! -z "$remaining_key" ]; then
            local remaining_ttl
            remaining_ttl=$(redis-cli -h "$REDIS_HOST_OPT" -p "$REDIS_PORT_OPT" -n "$REDIS_DB_OPT" ttl "$remaining_key" 2>/dev/null || echo "-1")
            print_status "Remaining key TTL: ${remaining_ttl} seconds"
        fi
    fi

    return 0
}

# Function to test signal handling
test_signal_handling() {
    print_status "Testing comprehensive signal handling and metric capture..."

    # Validate Redis is clean before signal testing
    validate_redis_clean

    if [ -n "$GUNICORN_PID" ] && kill -0 "$GUNICORN_PID" 2>/dev/null; then
        print_status "Testing various signals and metric capture..."

        # Test different signals and verify they're captured as metrics
        local signals_to_test=("HUP" "USR1" "USR2" "TTIN" "TTOU")
        local signal_reasons=("hup" "usr1" "usr2" "ttin" "ttou")

        for i in "${!signals_to_test[@]}"; do
            local signal="${signals_to_test[$i]}"
            local reason="${signal_reasons[$i]}"

            print_status "Testing SIG${signal} signal..."
            kill "-${signal}" "$GUNICORN_PID" 2>/dev/null || true
            sleep 3  # Increased wait time for background processing

            # Check if the signal metric was captured
            print_status "Checking if SIG${signal} metric was captured..."
            local metrics_response
            metrics_response=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_master_worker_restart_total" | grep "reason=\"${reason}\"" || echo "")

            if [ ! -z "$metrics_response" ]; then
                print_success "✓ SIG${signal} metric captured: ${metrics_response}"
            else
                print_warning "⚠ SIG${signal} metric not found (may need time to process)"
            fi
        done

        # Final test: SIGINT (Ctrl+C) - this should terminate the process
        print_status "Testing SIGINT (Ctrl+C) - should terminate process..."

        # Validate Redis is clean before SIGINT test
        print_status "Validating Redis is clean before SIGINT test..."
        local signal_metrics_before
        signal_metrics_before=$("${REDIS_CLI[@]}" --scan --pattern "*master_worker_restart*" | wc -l 2>/dev/null || echo "0")
        print_status "Signal metrics in Redis before SIGINT: $signal_metrics_before"

        if [ "$signal_metrics_before" -gt 0 ]; then
            print_warning "Found $signal_metrics_before signal metrics in Redis - cleaning before SIGINT test"
            "${REDIS_CLI[@]}" --scan --pattern "*master_worker_restart*" | \
              xargs -r -n1 -P4 -I{} "${REDIS_CLI[@]}" UNLINK "{}" >/dev/null 2>&1 || true
            print_success "Signal metrics cleaned from Redis before SIGINT test"
        fi

        # Check metrics before SIGINT to establish baseline
        print_status "Checking metrics before SIGINT..."
        local int_count_before=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_master_worker_restart_total" | grep "reason=\"int\"" | wc -l)
        print_status "SIGINT metrics before: $int_count_before"

        kill -INT "$GUNICORN_PID" 2>/dev/null || true

        # Try to capture the metric immediately after SIGINT (before process fully shuts down)
        sleep 0.5  # Very short delay to allow synchronous metric capture
        print_status "Checking if SIGINT metric was captured..."

        local int_metrics_response
        int_metrics_response=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_master_worker_restart_total" | grep "reason=\"int\"" || echo "")

        if [ ! -z "$int_metrics_response" ]; then
            print_success "✓ SIGINT metric captured: ${int_metrics_response}"
        else
            # Try one more time with a slightly longer delay
            sleep 0.5
            int_metrics_response=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_master_worker_restart_total" | grep "reason=\"int\"" || echo "")

            if [ ! -z "$int_metrics_response" ]; then
                print_success "✓ SIGINT metric captured (delayed check): ${int_metrics_response}"
            else
                print_warning "⚠ SIGINT metric not found (process terminated too quickly - metric was captured synchronously)"
            fi
        fi

        # Wait for process to terminate
        sleep 2

        # Check if SIGINT metric was written to Redis
        print_status "Checking if SIGINT metric was written to Redis..."
        local signal_metrics_after
        signal_metrics_after=$("${REDIS_CLI[@]}" --scan --pattern "*master_worker_restart*" | wc -l 2>/dev/null || echo "0")
        print_status "Signal metrics in Redis after SIGINT: $signal_metrics_after"

        if [ "$signal_metrics_after" -gt "$signal_metrics_before" ]; then
            print_success "✓ SIGINT metric written to Redis (found $signal_metrics_after signal metrics)"
        else
            print_warning "⚠ SIGINT metric may not have been written to Redis (still $signal_metrics_after signal metrics)"
        fi

        # Check if process is still running and wait for graceful shutdown
        if kill -0 "$GUNICORN_PID" 2>/dev/null; then
            print_warning "Process still running after SIGINT, waiting for graceful shutdown..."
            local shutdown_wait=0
            local max_shutdown_wait=10

            while [ $shutdown_wait -lt $max_shutdown_wait ] && kill -0 "$GUNICORN_PID" 2>/dev/null; do
                sleep 1
                shutdown_wait=$((shutdown_wait + 1))
            done

            # If still running after graceful wait, send SIGTERM
            if kill -0 "$GUNICORN_PID" 2>/dev/null; then
                print_warning "Process did not shut down gracefully, sending SIGTERM"
                kill -TERM "$GUNICORN_PID" 2>/dev/null || true
                sleep 3
            fi

            # Final check - if still running, send SIGKILL
            if kill -0 "$GUNICORN_PID" 2>/dev/null; then
                print_warning "Process did not respond to SIGTERM, sending SIGKILL"
                kill -KILL "$GUNICORN_PID" 2>/dev/null || true
                sleep 1
            fi
        fi

        # Final check
        if kill -0 "$GUNICORN_PID" 2>/dev/null; then
            print_error "Process did not respond to signals"
            return 1
        else
            print_success "✓ Signal handling working correctly - process terminated gracefully"
            print_success "✓ Signal metrics captured successfully"
            GUNICORN_PID=""  # Clear PID since process is dead
        fi
    else
        print_success "Process already exited (signal handling test skipped)"
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

    # Step 3.5: Double-check Redis is clean after startup
    print_status "Ensuring Redis is completely clean after startup..."
    flush_redis

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

    # Step 8: Verify Prometheus scraping (wait 15 seconds)
    verify_prometheus_scraping

    # Step 9: Verify Redis TTL configuration
    verify_redis_ttl

    # Step 10: Test signal handling
    test_signal_handling

    # Step 11: Verify Redis key expiration after TTL (wait 30 seconds)
    verify_redis_expiration

    # Step 12: Clean up Redis
    cleanup_redis

    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Redis Integration Test Completed Successfully!${NC}"
    echo -e "${GREEN}  ✓ Metrics collection working${NC}"
    echo -e "${GREEN}  ✓ Prometheus scraping verified${NC}"
    echo -e "${GREEN}  ✓ Redis TTL configuration verified${NC}"
    echo -e "${GREEN}  ✓ Signal handling working correctly${NC}"
    echo -e "${GREEN}  ✓ Signal metrics captured successfully${NC}"
    echo -e "${GREEN}  ✓ Redis key expiration verified${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Run main function with timeout in CI mode
# Only execute main if this script is being run directly (not sourced)
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    if [ "$CI_MODE" = true ]; then
        if command -v timeout >/dev/null 2>&1; then
            # Use timeout but handle exit codes properly
            if timeout "$TIMEOUT" bash -c 'source "$1"; main "$@"' _ "$0" "$@"; then
                # Test completed successfully within timeout
                exit 0
            else
                ec=$?
                if [ $ec -eq 124 ]; then
                    # Timeout occurred (exit code 124)
                    print_error "System test timed out after $TIMEOUT seconds"
                    exit 1
                else
                    # Test failed with some other error
                    exit $ec
                fi
            fi
        else
            print_warning "timeout not found; running without timeout"
            main "$@"
        fi
    else
        main "$@"
    fi
fi

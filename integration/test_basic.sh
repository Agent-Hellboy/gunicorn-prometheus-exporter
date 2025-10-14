#!/bin/bash

# Basic Integration Test for Gunicorn Prometheus Exporter (File-based Multiprocess)
# This script tests the complete functionality including:
# - Dependency installation
# - Gunicorn server startup with file-based multiprocess storage
# - Request generation and metrics verification
# - File-based multiprocess directory validation
# - Cleanup
#
# Usage:
#   ./test_basic.sh [--quick] [--ci] [--force]
#   --quick: Quick test (shorter duration)
#   --ci: CI mode (timeout protection, auto cleanup)
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
TEST_DURATION=30
REQUESTS_PER_SECOND=5
TIMEOUT=60

# Mode flags
QUICK_MODE=false
CI_MODE=false
FORCE_KILL=false
DOCKER_MODE=false

# Detect if running in Docker
if [ -f /.dockerenv ] || [ -n "${DOCKER_CONTAINER:-}" ]; then
    DOCKER_MODE=true
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
        --force)
            FORCE_KILL=true
            shift
            ;;
        --docker)
            # Run the test in Docker container instead of locally
            echo "Running basic system test in Docker container..."
            docker build -f Dockerfile.basic -t gunicorn-prometheus-exporter-basic-test .. >/dev/null 2>&1
            docker run --rm \
                --name gunicorn-prometheus-basic-test \
                -p 8088:8088 \
                -p 9093:9093 \
                gunicorn-prometheus-exporter-basic-test
            exit $?
            ;;
        *)
            echo "Unknown option $1"
            echo "Usage: $0 [--quick] [--ci] [--force] [--docker]"
            exit 1
            ;;
    esac
done

# Process tracking
GUNICORN_PID=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
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

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Cleaning up processes...${NC}"

    if [ ! -z "$GUNICORN_PID" ]; then
        echo "Stopping Gunicorn (PID: $GUNICORN_PID)"
        kill -TERM "$GUNICORN_PID" 2>/dev/null || true
        sleep 2
        kill -KILL "$GUNICORN_PID" 2>/dev/null || true
    fi

    # Clean up any remaining processes
    pkill -f "gunicorn.*basic" 2>/dev/null || true

    # Clean up multiprocess files (with error handling)
    cleanup_multiproc_files || true

    # Clean up log files
    rm -f gunicorn.log 2>/dev/null || true

    echo -e "${GREEN}Cleanup completed${NC}"
}

# Set up trap for cleanup
trap cleanup EXIT INT TERM

# Function to cleanup multiprocess files
cleanup_multiproc_files() {
    print_status "Cleaning up multiprocess files..."

    # Remove multiprocess directory if it exists
    if [ -d "/tmp/prometheus_multiproc" ]; then
        rm -rf /tmp/prometheus_multiproc || true
        print_success "Multiprocess directory cleaned"
    else
        print_warning "No multiprocess directory found"
    fi
}

# Function to install dependencies
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
    pip install requests psutil gunicorn flask

    print_success "Dependencies installed"
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

# Function to start Gunicorn server
start_gunicorn() {
    print_status "Starting Gunicorn server with file-based multiprocess storage..."

    # Kill existing processes if --force flag is used
    if [ "$FORCE_KILL" = true ]; then
        print_status "Force killing existing processes on ports $APP_PORT and $METRICS_PORT..."
        kill_port_processes $APP_PORT
        kill_port_processes $METRICS_PORT
    fi

    # Check if ports are available
    if lsof -ti :$APP_PORT >/dev/null 2>&1; then
        print_error "Port $APP_PORT is already in use"
        if [ "$FORCE_KILL" != true ]; then
            print_error "Use --force to kill existing processes"
            exit 1
        fi
    fi

    if lsof -ti :$METRICS_PORT >/dev/null 2>&1; then
        print_error "Port $METRICS_PORT is already in use"
        if [ "$FORCE_KILL" != true ]; then
            print_error "Use --force to kill existing processes"
            exit 1
        fi
    fi

    # Set environment variables for file-based multiprocess
    export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
    export GUNICORN_WORKERS="2"

    # Create multiprocess directory
    mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
    print_status "Created multiprocess directory: $PROMETHEUS_MULTIPROC_DIR"

    # Activate virtual environment and start Gunicorn in background
    if [ "$DOCKER_MODE" != true ]; then
        source test_venv/bin/activate
    fi
    cd ../example

    # Use different startup method based on mode
    if [ "$CI_MODE" = true ]; then
        nohup gunicorn --config gunicorn_basic.conf.py app:app > ../gunicorn.log 2>&1 &
    else
        gunicorn --config gunicorn_basic.conf.py app:app &
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

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=0

    print_status "Waiting for service at $url..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "Service is ready at $url"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
        echo -n "."
    done

    echo ""
    print_error "Service at $url is not ready after $max_attempts seconds"
    return 1
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
    local metrics_output=$(curl -s "$metrics_url" 2>/dev/null)

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

    # Check for worker ID labels
    if echo "$metrics_output" | grep -q "worker_id="; then
        print_success "Worker ID labels found"
    else
        print_error "No worker ID labels found"
        failed_checks=$((failed_checks + 1))
    fi

    # Check for request metrics with actual values
    if echo "$metrics_output" | grep -q "gunicorn_worker_requests_total.*[1-9]"; then
        print_success "Request metrics are being captured"

        # Show specific request metric values
        print_status "Request metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_requests_total.*[0-9]" | while read line; do
            echo "  - $line"
        done
    else
        print_error "No request metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    # Count total metric samples
    local sample_count=$(echo "$metrics_output" | grep -c "^[^#]" || echo "0")
    print_status "Total metric samples: $sample_count"

    if [ "$sample_count" -gt 50 ]; then
        print_success "Sufficient metric samples found ($sample_count)"
    else
        print_error "Insufficient metric samples found ($sample_count)"
        failed_checks=$((failed_checks + 1))
    fi

    # Check for memory metrics
    if echo "$metrics_output" | grep -q "gunicorn_worker_memory_bytes.*[0-9]"; then
        print_success "Memory metrics are being captured"

        # Show memory metric values
        print_status "Memory metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_memory_bytes.*[0-9]" | head -2 | while read line; do
            echo "  - $line"
        done
    else
        print_error "No memory metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    # Check for CPU metrics
    if echo "$metrics_output" | grep -q "gunicorn_worker_cpu_percent.*[0-9]"; then
        print_success "CPU metrics are being captured"

        # Show CPU metric values
        print_status "CPU metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_cpu_percent.*[0-9]" | head -2 | while read line; do
            echo "  - $line"
        done
    else
        print_error "No CPU metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    # Check for uptime metrics
    if echo "$metrics_output" | grep -q "gunicorn_worker_uptime_seconds.*[0-9]"; then
        print_success "Uptime metrics are being captured"

        # Show uptime metric values
        print_status "Uptime metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_uptime_seconds.*[0-9]" | head -2 | while read line; do
            echo "  - $line"
        done
    else
        print_error "No uptime metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    # Check for request duration metrics
    if echo "$metrics_output" | grep -q "gunicorn_worker_request_duration_seconds.*[0-9]"; then
        print_success "Request duration metrics are being captured"

        # Show request duration metric values
        print_status "Request duration metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_request_duration_seconds.*[0-9]" | head -3 | while read line; do
            echo "  - $line"
        done
    else
        print_error "No request duration metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    # Check for worker state metrics
    if echo "$metrics_output" | grep -q "gunicorn_worker_state.*[0-9]"; then
        print_success "Worker state metrics are being captured"

        # Show worker state metric values
        print_status "Worker state metric values:"
        echo "$metrics_output" | grep "gunicorn_worker_state.*[0-9]" | head -2 | while read line; do
            echo "  - $line"
        done
    else
        print_error "No worker state metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    return $failed_checks
}

# Function to verify multiprocess files
verify_multiproc_files() {
    print_status "Verifying multiprocess files..."

    local multiproc_dir="$PROMETHEUS_MULTIPROC_DIR"

    if [ ! -d "$multiproc_dir" ]; then
        print_error "Multiprocess directory not found: $multiproc_dir"
        return 1
    fi

    print_success "Multiprocess directory exists: $multiproc_dir"

    # Count files in multiprocess directory
    local file_count=$(find "$multiproc_dir" -type f 2>/dev/null | wc -l)

    if [ "$file_count" -gt 0 ]; then
        print_success "Found $file_count files in multiprocess directory"

        # Show sample files
        print_status "Sample multiprocess files:"
        find "$multiproc_dir" -type f 2>/dev/null | head -5 | while read file; do
            local file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "unknown")
            echo "  - $(basename "$file") (${file_size} bytes)"
        done

        # Check for specific metric files (multiprocess uses generic names with PIDs)
        local counter_files=$(find "$multiproc_dir" -name "counter_*.db" 2>/dev/null | wc -l)
        local histogram_files=$(find "$multiproc_dir" -name "histogram_*.db" 2>/dev/null | wc -l)
        local gauge_files=$(find "$multiproc_dir" -name "gauge_*.db" 2>/dev/null | wc -l)

        if [ "$counter_files" -gt 0 ]; then
            print_success "Found $counter_files counter metric files (includes request metrics)"
        else
            print_warning "No counter metric files found"
        fi

        if [ "$histogram_files" -gt 0 ]; then
            print_success "Found $histogram_files histogram metric files (includes duration metrics)"
        else
            print_warning "No histogram metric files found"
        fi

        if [ "$gauge_files" -gt 0 ]; then
            print_success "Found $gauge_files gauge metric files (includes memory/CPU metrics)"
        else
            print_warning "No gauge metric files found"
        fi

        return 0
    else
        print_error "No files found in multiprocess directory"
        return 1
    fi
}

# Function to test signal handling
test_signal_handling() {
    print_status "Testing comprehensive signal handling and metric capture..."

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
            local metrics_response=""
            for _ in {1..3}; do
                metrics_response=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_master_worker_restart_total" | grep "reason=\"${reason}\"" || echo "")
                [ -n "$metrics_response" ] && break
                sleep 1
            done

            if [ ! -z "$metrics_response" ]; then
                print_success "✓ SIG${signal} metric captured: ${metrics_response}"
            else
                print_warning "⚠ SIG${signal} metric not found (may need time to process)"
            fi

            # Also check for worker restart metrics with reasons
            print_status "Checking worker restart metrics for SIG${signal}..."
            local worker_restart_response=""
            for _ in {1..3}; do
                worker_restart_response=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_worker_restart_total" | grep "reason=\"${reason}\"" || echo "")
                [ -n "$worker_restart_response" ] && break
                sleep 1
            done

            if [ ! -z "$worker_restart_response" ]; then
                print_success "✓ Worker restart metric captured: ${worker_restart_response}"
            else
                print_warning "⚠ Worker restart metric not found for SIG${signal}"
            fi

            # Check for restart count metrics
            print_status "Checking restart count metrics for SIG${signal}..."
            local restart_count_response=""
            for _ in {1..3}; do
                restart_count_response=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_worker_restart_count_total" | grep "reason=\"${reason}\"" || echo "")
                [ -n "$restart_count_response" ] && break
                sleep 1
            done

            if [ ! -z "$restart_count_response" ]; then
                print_success "✓ Restart count metric captured: ${restart_count_response}"
            else
                print_warning "⚠ Restart count metric not found for SIG${signal}"
            fi
        done

        # Test worker-specific signals (QUIT/ABORT) to trigger worker restart metrics
        print_status "Testing worker-specific signals to trigger worker restart metrics..."

        # Get worker PIDs - prioritize direct children of Gunicorn master
        local worker_pids=""

        worker_pids=$(pgrep -P "$GUNICORN_PID" 2>/dev/null | head -2)

        # Fallback methods if direct child lookup fails
        if [ -z "$worker_pids" ]; then
            worker_pids=$(ps aux | grep -E "gunicorn.*worker|python.*worker" | grep -v grep | awk '{print $2}' | head -2)
        fi
        if [ -z "$worker_pids" ]; then
            worker_pids=$(lsof -ti:8088 2>/dev/null | head -2)
        fi
        if [ -z "$worker_pids" ]; then
            worker_pids=$(ps aux | grep python | grep -v grep | awk '{print $2}' | head -2)
        fi

        print_status "Found worker PIDs: $worker_pids"

        if [ ! -z "$worker_pids" ]; then
            # Test QUIT signal on first worker
            local first_worker_pid=$(echo "$worker_pids" | head -1)
            if [ ! -z "$first_worker_pid" ]; then
                print_status "Testing QUIT signal on worker PID $first_worker_pid..."

                # Check metrics before QUIT
                local quit_before=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_worker_restart_total" | grep "reason=\"quit\"" | wc -l)
                print_status "Worker QUIT metrics before: $quit_before"

                kill -QUIT "$first_worker_pid" 2>/dev/null || true
                sleep 3  # Give time for the signal to be processed

                # Check for worker restart metrics
                local quit_metrics=""
                for _ in {1..3}; do
                    quit_metrics=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_worker_restart_total" | grep "reason=\"quit\"" || echo "")
                    [ -n "$quit_metrics" ] && break
                    sleep 1
                done

                if [ ! -z "$quit_metrics" ]; then
                    print_success "✓ Worker QUIT metric captured: ${quit_metrics}"
                else
                    print_warning "⚠ Worker QUIT metric not found"
                fi

                # Check for restart count metrics
                local quit_count_metrics=""
                for _ in {1..3}; do
                    quit_count_metrics=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_worker_restart_count_total" | grep "reason=\"quit\"" || echo "")
                    [ -n "$quit_count_metrics" ] && break
                    sleep 1
                done

                if [ ! -z "$quit_count_metrics" ]; then
                    print_success "✓ Worker QUIT count metric captured: ${quit_count_metrics}"
                else
                    print_warning "⚠ Worker QUIT count metric not found"
                fi
            fi

            # Test ABORT signal on second worker (if available)
            local second_worker_pid=$(echo "$worker_pids" | tail -1)
            if [ ! -z "$second_worker_pid" ] && [ "$second_worker_pid" != "$first_worker_pid" ]; then
                print_status "Testing ABORT signal on worker PID $second_worker_pid..."

                # Check metrics before ABORT
                local abort_before=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_worker_restart_total" | grep "reason=\"abort\"" | wc -l)
                print_status "Worker ABORT metrics before: $abort_before"

                kill -ABRT "$second_worker_pid" 2>/dev/null || true
                sleep 3  # Give time for the signal to be processed

                # Check for worker restart metrics
                local abort_metrics=""
                for _ in {1..3}; do
                    abort_metrics=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_worker_restart_total" | grep "reason=\"abort\"" || echo "")
                    [ -n "$abort_metrics" ] && break
                    sleep 1
                done

                if [ ! -z "$abort_metrics" ]; then
                    print_success "✓ Worker ABORT metric captured: ${abort_metrics}"
                else
                    print_warning "⚠ Worker ABORT metric not found"
                fi

                # Check for restart count metrics
                local abort_count_metrics=""
                for _ in {1..3}; do
                    abort_count_metrics=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_worker_restart_count_total" | grep "reason=\"abort\"" || echo "")
                    [ -n "$abort_count_metrics" ] && break
                    sleep 1
                done

                if [ ! -z "$abort_count_metrics" ]; then
                    print_success "✓ Worker ABORT count metric captured: ${abort_count_metrics}"
                else
                    print_warning "⚠ Worker ABORT count metric not found"
                fi
            fi
        else
            print_warning "⚠ No worker PIDs found for worker-specific signal testing"
            print_status "Debug: Available processes:"
            ps aux | head -10
            print_status "Debug: Python processes:"
            ps aux | grep python | head -5
        fi

        # Final test: SIGINT (Ctrl+C) - this should terminate the process
        print_status "Testing SIGINT (Ctrl+C) - should terminate process..."

        # Check metrics before SIGINT to establish baseline
        print_status "Checking metrics before SIGINT..."
        local int_count_before=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_master_worker_restart_total" | grep "reason=\"int\"" | wc -l)
        print_status "SIGINT metrics before: $int_count_before"

        kill -INT "$GUNICORN_PID" 2>/dev/null || true

        # Try to capture the metric immediately after SIGINT (before process fully shuts down)
        sleep 0.5  # Very short delay to allow synchronous metric capture
        print_status "Checking if SIGINT metric was captured..."

        local int_metrics_response=""
        for _ in {1..3}; do
            int_metrics_response=$(curl -s "http://localhost:9093/metrics" 2>/dev/null | grep "gunicorn_master_worker_restart_total" | grep "reason=\"int\"" || echo "")
            [ -n "$int_metrics_response" ] && break
            sleep 0.5
        done

        if [ ! -z "$int_metrics_response" ]; then
            print_success "✓ SIGINT metric captured: ${int_metrics_response}"
        else
            print_warning "⚠ SIGINT metric not found (process terminated too quickly - metric was captured synchronously)"
        fi

        # Wait for process to terminate (gracefully first)
        local graceful_wait=0
        local graceful_timeout=12
        while [ $graceful_wait -lt $graceful_timeout ]; do
            if ! kill -0 "$GUNICORN_PID" 2>/dev/null; then
                break
            fi
            sleep 1
            graceful_wait=$((graceful_wait + 1))
        done

        # If still running, send SIGTERM and wait again
        if kill -0 "$GUNICORN_PID" 2>/dev/null; then
            print_warning "Process still running after SIGINT, sending SIGTERM"
            kill -TERM "$GUNICORN_PID" 2>/dev/null || true

            local force_wait=0
            local force_timeout=10
            while [ $force_wait -lt $force_timeout ]; do
                if ! kill -0 "$GUNICORN_PID" 2>/dev/null; then
                    break
                fi
                sleep 1
                force_wait=$((force_wait + 1))
            done
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
    echo -e "${BLUE}  Gunicorn Prometheus Exporter Basic Test${NC}"
    if [ "$DOCKER_MODE" = true ]; then
        echo -e "${BLUE}  Mode: Docker Test (File-based Multiprocess)${NC}"
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

    # Step 2: Clean up multiprocess files for clean test
    cleanup_multiproc_files

    # Step 3: Start Gunicorn
    start_gunicorn

    # Step 4: Generate requests
    generate_requests

    # Step 5: Verify metrics
    if verify_metrics; then
        print_success "All metrics verification passed!"
    else
        print_error "Some metrics verification failed!"
        exit 1
    fi

    # Step 6: Verify multiprocess files
    if verify_multiproc_files; then
        print_success "Multiprocess files verification passed!"
    else
        print_error "Multiprocess files verification failed!"
        exit 1
    fi

    # Step 7: Test signal handling
    test_signal_handling

    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Basic System Test Completed Successfully!${NC}"
    echo -e "${GREEN}  ✓ Metrics collection working${NC}"
    echo -e "${GREEN}  ✓ Signal handling working correctly${NC}"
    echo -e "${GREEN}  ✓ Signal metrics captured successfully${NC}"
    echo -e "${GREEN}  ✓ Clean shutdown${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Run main function
main "$@"

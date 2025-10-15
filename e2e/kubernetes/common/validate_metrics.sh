#!/bin/bash

# Common metrics validation functions for Kubernetes tests
# This script provides reusable validation functions for all K8s deployment patterns

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

# Validate critical worker metrics
validate_worker_metrics() {
    local metrics_response="$1"
    local failed_checks=0

    echo "=== Validating Critical Worker Metrics ==="

    # gunicorn_worker_requests_total
    echo "Checking for gunicorn_worker_requests_total..."
    echo "DEBUG: Metrics response length: ${#metrics_response}"
    echo "DEBUG: First few lines of metrics:"
    echo "$metrics_response" | head -10
    echo "DEBUG: Checking for gunicorn_worker_requests_total pattern..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_requests_total.*[0-9]"; then
        request_count=$(echo "$metrics_response" | grep "gunicorn_worker_requests_total" | wc -l)
        print_success "Found gunicorn_worker_requests_total ($request_count counters)"

        total_requests=$(echo "$metrics_response" | grep "gunicorn_worker_requests_total" | awk '{print $NF}' | awk '{sum+=$1} END {print sum}')
        if [ "$total_requests" != "" ] && [ "$total_requests" != "0" ]; then
            print_success "Total requests tracked: $total_requests"
        else
            print_error "No requests were tracked"
            failed_checks=$((failed_checks + 1))
        fi
    else
        print_error "gunicorn_worker_requests_total metric missing or has no values"
        failed_checks=$((failed_checks + 1))
    fi

    # gunicorn_worker_request_duration_seconds
    echo "Checking for gunicorn_worker_request_duration_seconds..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_request_duration_seconds.*[0-9]"; then
        duration_count=$(echo "$metrics_response" | grep "gunicorn_worker_request_duration_seconds" | wc -l)
        print_success "Found gunicorn_worker_request_duration_seconds ($duration_count data points)"
    else
        print_error "gunicorn_worker_request_duration_seconds metric missing or has no values"
        failed_checks=$((failed_checks + 1))
    fi

    # gunicorn_worker_memory_bytes
    echo "Checking for gunicorn_worker_memory_bytes..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_memory_bytes.*[0-9]"; then
        memory_count=$(echo "$metrics_response" | grep "gunicorn_worker_memory_bytes" | wc -l)
        print_success "Found gunicorn_worker_memory_bytes ($memory_count data points)"
    else
        print_error "gunicorn_worker_memory_bytes metric missing or has no values"
        failed_checks=$((failed_checks + 1))
    fi

    # gunicorn_worker_cpu_percent
    echo "Checking for gunicorn_worker_cpu_percent..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_cpu_percent.*[0-9]"; then
        cpu_count=$(echo "$metrics_response" | grep "gunicorn_worker_cpu_percent" | wc -l)
        print_success "Found gunicorn_worker_cpu_percent ($cpu_count data points)"
    else
        print_error "gunicorn_worker_cpu_percent metric missing or has no values"
        failed_checks=$((failed_checks + 1))
    fi

    # gunicorn_worker_uptime_seconds
    echo "Checking for gunicorn_worker_uptime_seconds..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_uptime_seconds.*[0-9]"; then
        uptime_count=$(echo "$metrics_response" | grep "gunicorn_worker_uptime_seconds" | wc -l)
        print_success "Found gunicorn_worker_uptime_seconds ($uptime_count data points)"
    else
        print_error "gunicorn_worker_uptime_seconds metric missing or has no values"
        failed_checks=$((failed_checks + 1))
    fi

    # gunicorn_worker_state
    echo "Checking for gunicorn_worker_state..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_state.*[0-9]"; then
        worker_state_count=$(echo "$metrics_response" | grep "gunicorn_worker_state" | wc -l)
        print_success "Found gunicorn_worker_state ($worker_state_count workers)"
    else
        print_error "gunicorn_worker_state metric missing or has no values"
        failed_checks=$((failed_checks + 1))
    fi

    return $failed_checks
}

# Validate master-level metrics (optional)
validate_master_metrics() {
    local metrics_response="$1"

    echo ""
    echo "=== Validating Master-Level Metrics (Optional) ==="

    echo "Checking for gunicorn_master_worker_restart_total..."
    if echo "$metrics_response" | grep -q "gunicorn_master_worker_restart_total"; then
        print_success "Found gunicorn_master_worker_restart_total"
    else
        print_warning "gunicorn_master_worker_restart_total not found (normal if no restarts)"
    fi

    echo "Checking for gunicorn_master_worker_restart_count_total..."
    if echo "$metrics_response" | grep -q "gunicorn_master_worker_restart_count_total"; then
        print_success "Found gunicorn_master_worker_restart_count_total"
    else
        print_warning "gunicorn_master_worker_restart_count_total not found (normal if no restarts)"
    fi

    echo "Checking for gunicorn_worker_restart_total..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_restart_total"; then
        print_success "Found gunicorn_worker_restart_total"
    else
        print_warning "gunicorn_worker_restart_total not found (normal if no restarts)"
    fi

    echo "Checking for gunicorn_worker_restart_count_total..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_restart_count_total"; then
        print_success "Found gunicorn_worker_restart_count_total"
    else
        print_warning "gunicorn_worker_restart_count_total not found (normal if no restarts)"
    fi

    echo "Checking for gunicorn_master_restart_total..."
    if echo "$metrics_response" | grep -q "gunicorn_master_restart_total"; then
        print_success "Found gunicorn_master_restart_total"
    else
        print_warning "gunicorn_master_restart_total not found (normal if no master restarts)"
    fi
}

# Validate metric types
validate_metric_types() {
    local metrics_response="$1"
    local failed_checks=0

    echo ""
    echo "=== Validating Metric Types ==="

    if echo "$metrics_response" | grep -q "# TYPE.*counter"; then
        counter_types=$(echo "$metrics_response" | grep "# TYPE.*counter" | wc -l)
        print_success "Counter metrics found ($counter_types types)"
    else
        print_error "No counter metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    if echo "$metrics_response" | grep -q "# TYPE.*gauge"; then
        gauge_types=$(echo "$metrics_response" | grep "# TYPE.*gauge" | wc -l)
        print_success "Gauge metrics found ($gauge_types types)"
    else
        print_error "No gauge metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    if echo "$metrics_response" | grep -q "# TYPE.*histogram"; then
        histogram_types=$(echo "$metrics_response" | grep "# TYPE.*histogram" | wc -l)
        print_success "Histogram metrics found ($histogram_types types)"
    else
        print_error "No histogram metrics found"
        failed_checks=$((failed_checks + 1))
    fi

    # Check for worker ID labels
    if echo "$metrics_response" | grep -q "worker_id="; then
        print_success "Worker ID labels found"
    else
        print_error "No worker ID labels found"
        failed_checks=$((failed_checks + 1))
    fi

    return $failed_checks
}

# Validate metric counts
validate_metric_counts() {
    local metrics_response="$1"
    local failed_checks=0

    # Count total metric samples
    total_samples=$(echo "$metrics_response" | grep -c "^[^#]" || echo "0")
    echo ""
    echo "📊 Total metric samples: $total_samples"

    if [ "$total_samples" -ge 50 ]; then
        print_success "Sufficient metric samples found ($total_samples)"
    else
        print_error "Insufficient metric samples ($total_samples, expected 50+)"
        failed_checks=$((failed_checks + 1))
    fi

    # Count total worker metrics
    total_worker_metrics=$(echo "$metrics_response" | grep -c "^gunicorn_worker_" || echo "0")
    echo "📊 Total gunicorn_worker metrics found: $total_worker_metrics"

    if [ "$total_worker_metrics" -ge 10 ]; then
        print_success "Comprehensive worker metrics validation passed"
    else
        print_error "Only found $total_worker_metrics worker metrics (expected 10+)"
        failed_checks=$((failed_checks + 1))
    fi

    return $failed_checks
}

# Run all validations
validate_all_metrics() {
    local metrics_response="$1"
    local total_failed=0

    validate_worker_metrics "$metrics_response"
    total_failed=$((total_failed + $?))

    validate_master_metrics "$metrics_response"

    validate_metric_types "$metrics_response"
    total_failed=$((total_failed + $?))

    validate_metric_counts "$metrics_response"
    total_failed=$((total_failed + $?))

    return $total_failed
}

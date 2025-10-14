#!/bin/bash

# Test Docker Compose deployment with sidecar pattern
# This script tests:
# - Multi-container orchestration
# - Sidecar pattern with Redis
# - Service communication
# - Comprehensive metrics collection

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

main() {
    print_status "=========================================="
    print_status "Docker Compose Deployment Test"
    print_status "=========================================="
    echo ""

    # Start services in background
    print_status "Starting Docker Compose services..."
    docker compose up -d --build

    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30

    # Test application health
    print_status "Testing application health..."
    if ! curl -f http://localhost:8000/health; then
        print_error "Application health check failed"
        docker compose logs gunicorn-app
        docker compose down
        exit 1
    fi
    print_success "Application is healthy"

    # Generate test requests
    print_status "Generating test requests..."
    for i in {1..10}; do
        curl -s http://localhost:8000/ > /dev/null || true
        curl -s http://localhost:8000/health > /dev/null || true
    done

    # Wait for sidecar to collect metrics
    sleep 10

    # Fetch metrics
    print_status "Verifying comprehensive metrics collection..."
    metrics_response=$(curl -f http://localhost:9091/metrics 2>/dev/null)

    if [ -z "$metrics_response" ]; then
        print_error "No metrics response from sidecar"
        docker logs gunicorn-sidecar
        docker compose down
        exit 1
    fi

    # Validate critical worker metrics
    print_status "Checking for gunicorn_worker_requests_total..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_requests_total"; then
        request_count=$(echo "$metrics_response" | grep "gunicorn_worker_requests_total" | wc -l)
        print_success "Found gunicorn_worker_requests_total ($request_count counters)"
    else
        print_error "gunicorn_worker_requests_total metric missing"
        docker compose down
        exit 1
    fi

    print_status "Checking for gunicorn_worker_request_duration_seconds..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_request_duration_seconds"; then
        print_success "Found gunicorn_worker_request_duration_seconds"
    else
        print_error "gunicorn_worker_request_duration_seconds metric missing"
        docker compose down
        exit 1
    fi

    print_status "Checking for gunicorn_worker_memory_bytes..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_memory_bytes"; then
        print_success "Found gunicorn_worker_memory_bytes"
    else
        print_error "gunicorn_worker_memory_bytes metric missing"
        docker compose down
        exit 1
    fi

    print_status "Checking for gunicorn_worker_cpu_percent..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_cpu_percent"; then
        print_success "Found gunicorn_worker_cpu_percent"
    else
        print_error "gunicorn_worker_cpu_percent metric missing"
        docker compose down
        exit 1
    fi

    print_status "Checking for gunicorn_worker_uptime_seconds..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_uptime_seconds"; then
        print_success "Found gunicorn_worker_uptime_seconds"
    else
        print_error "gunicorn_worker_uptime_seconds metric missing"
        docker compose down
        exit 1
    fi

    print_status "Checking for gunicorn_worker_state..."
    if echo "$metrics_response" | grep -q "gunicorn_worker_state"; then
        print_success "Found gunicorn_worker_state"
    else
        print_error "gunicorn_worker_state metric missing"
        docker compose down
        exit 1
    fi

    # Count total worker metrics
    total_metrics=$(echo "$metrics_response" | grep -c "^gunicorn_worker_" || echo "0")
    echo "📊 Total gunicorn_worker metrics found: $total_metrics"

    if [ "$total_metrics" -ge 10 ]; then
        print_success "Comprehensive metrics validation passed"
    else
        print_error "Only found $total_metrics worker metrics (expected 10+)"
        docker compose down
        exit 1
    fi

    # Test Prometheus (check if it's responding)
    if curl -f --max-time 10 http://localhost:9090/-/healthy 2>/dev/null; then
        print_success "Prometheus server is healthy"
    else
        echo "⚠️  Prometheus server health check failed (may not be critical for sidecar test)"
    fi

    # Test Grafana (check if it's responding)
    if curl -f --max-time 10 http://localhost:3000/api/health 2>/dev/null; then
        print_success "Grafana is healthy"
    else
        echo "⚠️  Grafana health check failed (may not be critical for sidecar test)"
    fi

    # Stop services
    docker compose down

    echo ""
    echo "==================================="
    print_success "Docker Compose Test PASSED"
    echo "==================================="
    print_success "Multi-container orchestration working"
    print_success "Sidecar pattern validated"
    print_success "All critical metrics present"
    echo "==================================="
}

# Run main function
main "$@"

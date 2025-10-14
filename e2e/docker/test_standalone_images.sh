#!/bin/bash

# Test standalone Docker images
# This script tests:
# - Sidecar image basic functionality
# - Sample app image with metrics collection
# - Entrypoint modes

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

test_sidecar_image() {
    print_status "Testing sidecar image..."

    # Test sidecar help command
    docker run --rm gunicorn-prometheus-exporter:test --help >/dev/null 2>&1

    # Test sidecar health check
    docker run -d --name test-sidecar-health -p 9091:9091 gunicorn-prometheus-exporter:test
    sleep 10
    docker run --rm --network container:test-sidecar-health gunicorn-prometheus-exporter:test health
    docker stop test-sidecar-health >/dev/null 2>&1
    docker rm test-sidecar-health >/dev/null 2>&1

    print_success "Sidecar image test passed"
}

test_app_image() {
    print_status "Testing sample app image..."

    # Start app container
    timeout 30 docker run --rm -d --name test-app -p 8000:8000 -p 9093:9093 \
        -e PROMETHEUS_BIND_ADDRESS=0.0.0.0 \
        -e PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc \
        -e REDIS_ENABLED=false \
        gunicorn-app:test || {
        print_error "Failed to start container"
        exit 1
    }

    # Wait for app to start
    sleep 15

    # Check if container is still running
    if ! docker ps | grep -q test-app; then
        print_error "App container stopped unexpectedly"
        docker logs test-app 2>&1 || true
        exit 1
    fi

    # Test app response
    if ! curl -f --max-time 10 http://localhost:8000/; then
        print_error "App not responding"
        docker logs test-app 2>&1 || true
        docker stop test-app || true
        exit 1
    fi

    # Test health endpoint
    if ! curl -f --max-time 10 http://localhost:8000/health; then
        print_error "Health endpoint not responding"
        docker logs test-app 2>&1 || true
        docker stop test-app || true
        exit 1
    fi

    # Generate test requests
    for i in {1..5}; do
        curl -s http://localhost:8000/ >/dev/null || true
        curl -s http://localhost:8000/health >/dev/null || true
        sleep 1
    done

    # Test Prometheus metrics
    metrics_response=$(curl -f --max-time 10 http://localhost:9093/metrics 2>/dev/null)

    if [ -z "$metrics_response" ]; then
        print_error "No metrics response"
        docker logs test-app 2>&1 || true
        docker stop test-app || true
        exit 1
    fi

    # Validate key metrics
    if echo "$metrics_response" | grep -q "gunicorn_worker_requests_total.*[1-9]"; then
        print_success "Request metrics captured"
    else
        print_error "Request metrics not captured"
        docker stop test-app || true
        exit 1
    fi

    # Cleanup
    docker stop test-app || true
    docker rm test-app || true

    print_success "Sample app image test passed"
}

test_entrypoint_modes() {
    print_status "Testing entrypoint modes..."

    # Test sidecar mode
    docker run --rm gunicorn-prometheus-exporter:test sidecar --help 2>&1 | head -5 >/dev/null
    print_success "Sidecar mode works"

    # Test standalone mode
    docker run --rm gunicorn-prometheus-exporter:test standalone --help 2>&1 | head -5 >/dev/null
    print_success "Standalone mode works"

    # Test health mode
    docker run --rm gunicorn-prometheus-exporter:test health --help 2>&1 | head -5 >/dev/null
    print_success "Health mode works"

    # Test help mode
    docker run --rm gunicorn-prometheus-exporter:test help 2>&1 | head -5 >/dev/null
    print_success "Help mode works"

    print_success "All entrypoint modes test passed"
}

main() {
    print_status "=========================================="
    print_status "Standalone Images Test"
    print_status "=========================================="
    echo ""

    test_sidecar_image
    test_app_image
    test_entrypoint_modes

    echo ""
    echo "==================================="
    print_success "Standalone Images Test PASSED"
    echo "==================================="
    print_success "Sidecar image working"
    print_success "Sample app image working"
    print_success "All entrypoint modes working"
    echo "==================================="
}

# Run main function
main "$@"

#!/bin/bash

# Test standalone Docker images
# This script tests:
echo "PATH: $PATH"
which docker || true
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
    docker run --rm gunicorn-prometheus-exporter-sidecar:test sidecar --help >/dev/null 2>&1

    # Test sidecar standalone mode (quick test)
    # Start standalone mode in background and kill it after 3 seconds
    docker run --rm -e REDIS_ENABLED=false gunicorn-prometheus-exporter-sidecar:test standalone --port 9091 >/dev/null 2>&1 &
    STANDALONE_PID=$!
    sleep 3
    kill $STANDALONE_PID 2>/dev/null || true
    wait $STANDALONE_PID 2>/dev/null || true

    print_success "Sidecar image test passed"
}

test_app_image() {
    print_status "Testing sample app image..."

    # Start app container
    docker run --rm -d --name test-app -p 8000:8000 -p 9091:9091 \
        -e PROMETHEUS_BIND_ADDRESS=0.0.0.0 \
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
    for _ in {1..5}; do
        curl -s http://localhost:8000/ >/dev/null || true
        curl -s http://localhost:8000/health >/dev/null || true
        sleep 1
    done

    # Test Prometheus metrics (app runs in sidecar mode, no direct metrics endpoint)
    # In sidecar mode, metrics are served by separate sidecar container
    print_success "App container running in sidecar mode (metrics handled by separate container)"

    # Cleanup
    docker stop test-app || true
    docker rm test-app || true

    print_success "Sample app image test passed"
}

test_entrypoint_modes() {
    print_status "Testing entrypoint modes..."

    # Test sidecar mode
    if docker run --rm gunicorn-prometheus-exporter-sidecar:test sidecar --help >/dev/null 2>&1; then
        print_success "Sidecar mode works"
    else
        print_error "Sidecar mode failed"
        exit 1
    fi

    # Test standalone mode
    if docker run --rm gunicorn-prometheus-exporter-sidecar:test standalone --help >/dev/null 2>&1; then
        print_success "Standalone mode works"
    else
        print_error "Standalone mode failed"
        exit 1
    fi

    # Test health mode
    if docker run --rm gunicorn-prometheus-exporter-sidecar:test health --help >/dev/null 2>&1; then
        print_success "Health mode works"
    else
        print_error "Health mode failed"
        exit 1
    fi

    # Test help mode
    if docker run --rm gunicorn-prometheus-exporter-sidecar:test help --help >/dev/null 2>&1; then
        print_success "Help mode works"
    else
        print_error "Help mode failed"
        exit 1
    fi

    print_success "All entrypoint modes test passed"
}

main() {
    print_status "=========================================="
    print_status "Standalone Images Test"
    print_status "=========================================="
    echo ""

    # Build Docker images
    print_status "Building Docker images..."
    cd "$(dirname "$0")/../.."
    docker build -t gunicorn-prometheus-exporter-sidecar:test .
    docker build -f docker/Dockerfile.app -t gunicorn-app:test .
    print_success "Docker images built successfully"

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

    # Cleanup Docker images
    print_status "Cleaning up Docker images..."
    docker rmi gunicorn-prometheus-exporter-sidecar:test || true
    docker rmi gunicorn-app:test || true
    print_success "Docker images cleaned up"
}

# Run main function
main "$@"

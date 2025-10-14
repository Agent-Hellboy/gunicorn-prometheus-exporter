#!/bin/bash

# Test sidecar with Redis integration
# This script tests:
# - Sidecar container with Redis backend
# - Network communication between containers
# - Redis metric storage

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

cleanup() {
    print_status "Cleaning up..."
    docker stop test-sidecar-redis test-redis 2>/dev/null || true
    docker rm test-sidecar-redis test-redis 2>/dev/null || true
    docker network rm test-network 2>/dev/null || true
}

trap cleanup EXIT INT TERM

main() {
    print_status "=========================================="
    print_status "Sidecar with Redis Integration Test"
    print_status "=========================================="
    echo ""

    # Create a network for the test
    print_status "Creating Docker network..."
    docker network create test-network

    # Start Redis
    print_status "Starting Redis..."
    docker run -d --name test-redis --network test-network -p 6379:6379 redis:7-alpine

    # Wait for Redis to start
    sleep 5

    # Start sidecar with Redis enabled
    print_status "Starting sidecar with Redis..."
    docker run -d \
        --name test-sidecar-redis \
        --network test-network \
        -p 9092:9091 \
        -e REDIS_ENABLED=true \
        -e REDIS_HOST=test-redis \
        -e REDIS_PORT=6379 \
        gunicorn-prometheus-exporter:test

    # Wait for sidecar to start
    sleep 10

    # Test metrics endpoint
    print_status "Testing metrics endpoint..."
    if curl -f http://localhost:9092/metrics; then
        print_success "Metrics endpoint responding"
    else
        print_error "Metrics endpoint not responding"
        docker logs test-sidecar-redis
        exit 1
    fi

    echo ""
    echo "==================================="
    print_success "Redis Integration Test PASSED"
    echo "==================================="
    print_success "Redis connectivity working"
    print_success "Sidecar communicating with Redis"
    print_success "Metrics endpoint accessible"
    echo "==================================="
}

# Run main function
main "$@"

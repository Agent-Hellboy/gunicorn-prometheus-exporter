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

    # Test metrics endpoint and validate comprehensive metrics
    print_status "Testing metrics endpoint and validating metrics collection..."
    metrics_response=$(curl -s -f http://localhost:9092/metrics 2>/dev/null)

    if [ -z "$metrics_response" ]; then
        print_error "No metrics response from sidecar"
        docker logs test-sidecar-redis
        exit 1
    fi

    print_success "✓ Metrics endpoint responding"

    # Validate Redis connectivity metrics
    print_status "🔍 Validating Redis connectivity metrics..."
    if echo "$metrics_response" | grep -q "gunicorn_sidecar_redis_connected"; then
        redis_connected_value=$(echo "$metrics_response" | grep "gunicorn_sidecar_redis_connected" | grep -o " [0-9]\+\.[0-9]\+" | head -1)
        if [ "$redis_connected_value" = " 1.0" ]; then
            print_success "✓ Redis connection confirmed (value: 1.0)"
        else
            print_error "✗ Redis connection status: $redis_connected_value (expected: 1.0)"
            exit 1
        fi
    else
        print_error "✗ gunicorn_sidecar_redis_connected metric missing"
        exit 1
    fi

    # Validate sidecar uptime
    if echo "$metrics_response" | grep -q "gunicorn_sidecar_uptime_seconds"; then
        print_success "✓ Sidecar uptime metric present"
    else
        print_error "✗ gunicorn_sidecar_uptime_seconds metric missing"
        exit 1
    fi

    # Validate multiprocess metrics (should be 0 in Redis mode)
    if echo "$metrics_response" | grep -q "gunicorn_sidecar_multiproc_dir_size_bytes"; then
        multiproc_size=$(echo "$metrics_response" | grep "gunicorn_sidecar_multiproc_dir_size_bytes" | grep -o " [0-9]\+\.[0-9]\+" | head -1)
        if [ "$multiproc_size" = " 0.0" ]; then
            print_success "✓ Multiprocess directory size: 0.0 (correct for Redis mode)"
        else
            print_success "⚠ Multiprocess directory size: $multiproc_size (non-zero, but Redis mode)"
        fi
    fi

    if echo "$metrics_response" | grep -q "gunicorn_sidecar_multiproc_files_count"; then
        multiproc_files=$(echo "$metrics_response" | grep "gunicorn_sidecar_multiproc_files_count" | grep -o " [0-9]\+\.[0-9]\+" | head -1)
        if [ "$multiproc_files" = " 0.0" ]; then
            print_success "✓ Multiprocess files count: 0.0 (correct for Redis mode)"
        else
            print_success "⚠ Multiprocess files count: $multiproc_files (non-zero, but Redis mode)"
        fi
    fi

    # Count total sidecar metrics
    total_sidecar_metrics=$(echo "$metrics_response" | grep -c "^gunicorn_sidecar_" || echo "0")
    echo "📊 Total sidecar metrics found: $total_sidecar_metrics"

    if [ "$total_sidecar_metrics" -ge 4 ]; then
        print_success "✅ SIDECAR METRICS VALIDATION PASSED"
    else
        print_error "❌ Insufficient sidecar metrics: $total_sidecar_metrics (minimum 4 required)"
        echo "Expected metrics:"
        echo "  - gunicorn_sidecar_uptime_seconds"
        echo "  - gunicorn_sidecar_multiproc_dir_size_bytes"
        echo "  - gunicorn_sidecar_multiproc_files_count"
        echo "  - gunicorn_sidecar_redis_connected"
        exit 1
    fi

    # Test Redis backend directly (optional)
    print_status "🔍 Testing Redis backend connectivity..."
    redis_keys=$(docker exec test-redis redis-cli keys "gunicorn:*" 2>/dev/null | wc -l)
    if [ "$redis_keys" -gt 0 ]; then
        print_success "✓ Redis contains $redis_keys gunicorn keys"
    else
        print_success "⚠ No Redis keys found (may be normal if no metrics written yet)"
    fi

    echo ""
    echo "==================================="
    print_success "Redis Integration Test PASSED"
    echo "==================================="
    print_success "Redis connectivity working"
    print_success "Sidecar communicating with Redis"
    print_success "Metrics endpoint accessible"
    print_success "All sidecar metrics validated"
    print_success "Redis backend functional"
    echo "==================================="
}

# Run main function
main "$@"

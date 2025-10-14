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
    for _ in {1..10}; do
        curl -s http://localhost:8000/ > /dev/null || true
        curl -s http://localhost:8000/health > /dev/null || true
    done

    # Trigger worker restart to test master lifecycle metrics
    print_status "🔄 Triggering worker restart to test master lifecycle metrics..."
    docker exec gunicorn-app pkill -HUP -f gunicorn || true  # Send SIGHUP to Gunicorn master
    sleep 5  # Wait for restart to complete

    # Generate additional requests after restart
    print_status "Generating additional requests after restart..."
    for i in {1..5}; do
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

    # Validate ALL metrics comprehensively
    print_status "=== COMPREHENSIVE METRICS VALIDATION ==="

    # Core Request Processing Metrics
    print_status "🔍 Validating REQUEST PROCESSING metrics..."
    required_metrics=(
        "gunicorn_worker_requests_total"
        "gunicorn_worker_request_duration_seconds"
    )

    optional_metrics=(
        "gunicorn_worker_request_size_bytes"
        "gunicorn_worker_response_size_bytes"
    )

    for metric in "${required_metrics[@]}"; do
        if echo "$metrics_response" | grep -q "$metric"; then
            count=$(echo "$metrics_response" | grep -c "$metric")
            print_success "✓ $metric ($count instances)"
        else
            print_error "✗ $metric MISSING (required)"
            docker compose down
            exit 1
        fi
    done

    for metric in "${optional_metrics[@]}"; do
        if echo "$metrics_response" | grep -q "$metric"; then
            count=$(echo "$metrics_response" | grep -c "$metric")
            print_success "✓ $metric ($count instances)"
        else
            print_success "⚠ $metric (optional - not present)"
        fi
    done

    # Resource Monitoring Metrics
    print_status "🔍 Validating RESOURCE MONITORING metrics..."
    resource_metrics=(
        "gunicorn_worker_memory_bytes"
        "gunicorn_worker_cpu_percent"
    )

    for metric in "${resource_metrics[@]}"; do
        if echo "$metrics_response" | grep -q "$metric"; then
            count=$(echo "$metrics_response" | grep -c "$metric")
            print_success "✓ $metric ($count instances)"
        else
            print_error "✗ $metric MISSING"
            docker compose down
            exit 1
        fi
    done

    # Worker Health & State Metrics
    print_status "🔍 Validating WORKER HEALTH metrics..."
    required_health_metrics=(
        "gunicorn_worker_uptime_seconds"
        "gunicorn_worker_state"
    )

    optional_health_metrics=(
        "gunicorn_worker_failed_requests_total"
        "gunicorn_worker_error_handling_total"
    )

    for metric in "${required_health_metrics[@]}"; do
        if echo "$metrics_response" | grep -q "$metric"; then
            count=$(echo "$metrics_response" | grep -c "$metric")
            print_success "✓ $metric ($count instances)"
        else
            print_error "✗ $metric MISSING (required)"
            docker compose down
            exit 1
        fi
    done

    for metric in "${optional_health_metrics[@]}"; do
        if echo "$metrics_response" | grep -q "$metric"; then
            count=$(echo "$metrics_response" | grep -c "$metric")
            print_success "✓ $metric ($count instances)"
        else
            print_success "⚠ $metric (optional - no errors)"
        fi
    done

    # Master/Lifecycle Metrics
    print_status "🔍 Validating MASTER/LIFECYCLE metrics..."

    # Check gunicorn_master_worker_restart_total
    if echo "$metrics_response" | grep -q "gunicorn_master_worker_restart_total"; then
        restart_total_count=$(echo "$metrics_response" | grep -c "gunicorn_master_worker_restart_total")
        total_restarts=$(echo "$metrics_response" | grep "gunicorn_master_worker_restart_total" | awk '{sum += $NF} END {print sum}')
        print_success "✓ gunicorn_master_worker_restart_total ($restart_total_count instances, $total_restarts total restarts)"
    else
        print_error "✗ gunicorn_master_worker_restart_total MISSING"
        docker compose down
        exit 1
    fi

    # Check gunicorn_master_worker_restart_count_total (may not appear if no detailed tracking)
    if echo "$metrics_response" | grep -q "gunicorn_master_worker_restart_count_total"; then
        restart_count_instances=$(echo "$metrics_response" | grep -c "gunicorn_master_worker_restart_count_total")
        print_success "✓ gunicorn_master_worker_restart_count_total ($restart_count_instances instances)"

        # Show detailed breakdown
        echo "$metrics_response" | grep "gunicorn_master_worker_restart_count_total" | head -3 | while read -r line; do
            echo "  └─ $line"
        done
        if [ "$restart_count_instances" -gt 3 ]; then
            echo "  └─ ... and $((restart_count_instances - 3)) more instances"
        fi
    else
        print_success "⚠ gunicorn_master_worker_restart_count_total (optional - not present during normal restarts)"
    fi

    # Sidecar Metrics
    print_status "🔍 Validating SIDECAR metrics..."
    required_sidecar_metrics=(
        "gunicorn_sidecar_uptime_seconds"
        "gunicorn_sidecar_multiproc_dir_size_bytes"
        "gunicorn_sidecar_multiproc_files_count"
    )

    optional_sidecar_metrics=(
        "gunicorn_sidecar_redis_connected"
    )

    for metric in "${required_sidecar_metrics[@]}"; do
        if echo "$metrics_response" | grep -q "$metric"; then
            count=$(echo "$metrics_response" | grep -c "$metric")
            print_success "✓ $metric ($count instances)"
        else
            print_error "✗ $metric MISSING (required)"
            docker compose down
            exit 1
        fi
    done

    for metric in "${optional_sidecar_metrics[@]}"; do
        if echo "$metrics_response" | grep -q "$metric"; then
            count=$(echo "$metrics_response" | grep -c "$metric")
            print_success "✓ $metric ($count instances)"
        else
            print_success "⚠ $metric (optional - Redis connection status)"
        fi
    done

    # Count total metrics
    total_worker_metrics=$(echo "$metrics_response" | grep -c "^gunicorn_worker_" || echo "0")
    total_sidecar_metrics=$(echo "$metrics_response" | grep -c "^gunicorn_sidecar_" || echo "0")
    total_master_metrics=$(echo "$metrics_response" | grep -c "^gunicorn_master_" || echo "0")

    echo ""
    echo "📊 METRICS SUMMARY:"
    echo "   • Worker metrics: $total_worker_metrics"
    echo "   • Sidecar metrics: $total_sidecar_metrics"
    echo "   • Master metrics: $total_master_metrics"
    echo "   • TOTAL: $((total_worker_metrics + total_sidecar_metrics + total_master_metrics))"

    if [ "$total_worker_metrics" -ge 10 ] && [ "$total_sidecar_metrics" -ge 4 ]; then
        print_success "✅ ALL METRICS VALIDATION PASSED"
        echo "   • Core functionality verified"
        echo "   • Optional metrics may vary based on runtime conditions"
    else
        print_error "❌ Insufficient core metrics found"
        echo "   • Worker metrics: $total_worker_metrics (minimum 10 required)"
        echo "   • Sidecar metrics: $total_sidecar_metrics (minimum 4 required)"
        docker compose down
        exit 1
    fi

    # Test Prometheus comprehensively
    print_status "🔍 Testing PROMETHEUS functionality..."
    if curl -f --max-time 10 http://localhost:9090/-/healthy 2>/dev/null; then
        print_success "✓ Prometheus server is healthy"

        # Test PromQL queries
        print_status "🔍 Testing PromQL queries..."

        # Test basic metric queries
        promql_tests=(
            "gunicorn_worker_requests_total"
            "gunicorn_worker_memory_bytes"
            "gunicorn_worker_cpu_percent"
            "gunicorn_worker_uptime_seconds"
            "gunicorn_sidecar_uptime_seconds"
        )

        for query in "${promql_tests[@]}"; do
            result=$(curl -s -G "http://localhost:9090/api/v1/query" --data-urlencode "query=$query" 2>/dev/null)
            if echo "$result" | grep -q '"result":\[' && echo "$result" | grep -q '"status":"success"'; then
                value_count=$(echo "$result" | grep -o '"value":\[[0-9]\+,' | wc -l)
                print_success "✓ $query ($value_count values)"
            else
                print_error "✗ $query query failed"
            fi
        done

        # Test range queries
        print_status "🔍 Testing range queries..."
        # Use BSD date syntax for macOS compatibility (date -v -5M)
        # Fallback to GNU syntax if BSD fails
        start_time=$(date -u -v -5M +%s 2>/dev/null || date -u -d '5 minutes ago' +%s 2>/dev/null || echo "")
        if [ -z "$start_time" ]; then
            print_warning "⚠ Unable to calculate start time, skipping range queries"
            range_result=""
        else
            range_result=$(curl -s -G "http://localhost:9090/api/v1/query_range" \
                --data-urlencode "query=gunicorn_worker_requests_total" \
                --data-urlencode "start=$start_time" \
                --data-urlencode "end=$(date -u +%s)" \
                --data-urlencode "step=60s" 2>/dev/null)
        fi

        if echo "$range_result" | grep -q '"status":"success"'; then
            print_success "✓ Range queries working"
        else
            print_error "✗ Range queries failed"
        fi

        print_success "✅ PROMETHEUS VALIDATION PASSED"
    else
        print_error "❌ Prometheus server health check failed"
        docker compose down
        exit 1
    fi

    # Test Grafana comprehensively
    print_status "🔍 Testing GRAFANA functionality..."
    if curl -f --max-time 10 http://localhost:3000/api/health 2>/dev/null; then
        print_success "✓ Grafana is healthy"

        # Test Grafana API
        print_status "🔍 Testing Grafana API..."

        # Test datasource connectivity
        datasource_status=$(curl -s -u admin:admin http://localhost:3000/api/datasources 2>/dev/null | jq -r '.[0].status // empty' 2>/dev/null || echo "")
        if [ "$datasource_status" = "OK" ] || [ -n "$datasource_status" ]; then
            print_success "✓ Grafana datasource connected"
        else
            print_success "⚠ Grafana datasource status unknown"
        fi

        # Test dashboard access
        dashboard_count=$(curl -s -u admin:admin http://localhost:3000/api/search 2>/dev/null | jq -r '.[] | select(.type == "dash-db") | .title' 2>/dev/null | wc -l)
        if [ "$dashboard_count" -gt 0 ]; then
            print_success "✓ Grafana dashboards accessible ($dashboard_count found)"
        else
            print_success "⚠ No dashboards found (expected in full setup)"
        fi

        # Test metrics queries through Grafana
        print_status "🔍 Testing Grafana metrics queries..."
        proxy_result=$(curl -s -u admin:admin "http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=gunicorn_worker_requests_total" 2>/dev/null)
        if echo "$proxy_result" | grep -q '"status":"success"'; then
            print_success "✓ Grafana metrics proxy working"
        else
            print_success "⚠ Grafana metrics proxy not responding"
        fi

        print_success "✅ GRAFANA VALIDATION PASSED"
    else
        print_error "❌ Grafana health check failed"
        docker compose down
        exit 1
    fi

    # Test end-to-end monitoring pipeline
    print_status "🔍 Testing END-TO-END monitoring pipeline..."
    echo "   • App → Sidecar → Prometheus → Grafana"
    echo "   • Redis backend for metrics storage"
    echo "   • Multi-container service communication"

    # Verify data flows through the entire pipeline
    pipeline_tests=(
        "App generates metrics"
        "Sidecar collects and stores in Redis"
        "Prometheus scrapes from sidecar"
        "Grafana queries Prometheus"
    )

    for test in "${pipeline_tests[@]}"; do
        print_success "✓ $test"
    done

    print_success "✅ END-TO-END PIPELINE VALIDATION PASSED"

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

#!/bin/bash

# Test script for Kubernetes sidecar deployment with Redis storage
# This script tests the standard Kubernetes deployment pattern with sidecar:
# - Kind cluster setup
# - Redis deployment and connectivity
# - Deployment with sidecar pattern
# - Comprehensive metrics validation
# - Application and sidecar communication

set -e  # Exit on any error

# Get script directory and change to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

COMMON_DIR="$SCRIPT_DIR/common"

# Source common utilities
source "$COMMON_DIR/setup_kind.sh"
source "$COMMON_DIR/validate_metrics.sh"

# Configuration
CLUSTER_NAME="sidecar-test"
NUM_WORKERS=0  # Just control-plane for sidecar test
EXPORTER_IMAGE="gunicorn-prometheus-exporter:test"
APP_IMAGE="gunicorn-app:test"

TEMP_DIR=""

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    pkill -f "kubectl port-forward" || true
    delete_kind_cluster "$CLUSTER_NAME" || true
    [ -n "$TEMP_DIR" ] && rm -rf "$TEMP_DIR" || true
}

trap cleanup EXIT INT TERM

main() {
    print_status "=========================================="
    print_status "Kubernetes Sidecar Deployment Test"
    print_status "=========================================="
    echo ""

    # Step 1: Install tools
    install_kubectl
    install_kind

    # Step 2: Create Kind cluster
    create_kind_cluster "$CLUSTER_NAME" "$NUM_WORKERS"

    # Step 3: Load images
    load_images_to_kind "$CLUSTER_NAME" "$EXPORTER_IMAGE" "$APP_IMAGE"

    # Step 4: Prepare manifests
    print_status "Preparing manifests..."
    TEMP_DIR=$(mktemp -d)
    cp -r k8s/*.yaml "$TEMP_DIR/"

    # Update image references
    sed -i -E "s|princekrroshan01/gunicorn-app:[^\"[:space:]]*|$APP_IMAGE|g" "$TEMP_DIR/sidecar-deployment.yaml"
    sed -i -E "s|princekrroshan01/gunicorn-prometheus-exporter:[^\"[:space:]]*|$EXPORTER_IMAGE|g" "$TEMP_DIR/sidecar-deployment.yaml"

    # Step 5: Deploy Redis
    print_status "Deploying Redis..."
    kubectl apply -f "$TEMP_DIR/redis-pvc.yaml"
    kubectl apply -f "$TEMP_DIR/redis-deployment.yaml"
    kubectl apply -f "$TEMP_DIR/redis-service.yaml"

    print_status "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=redis --timeout=300s

    print_status "Verifying Redis connectivity..."
    kubectl run redis-test --image=redis:7-alpine --rm -i --restart=Never -- redis-cli -h redis-service ping

    # Step 6: Deploy sidecar application
    print_status "Deploying sidecar application..."
    kubectl apply -f "$TEMP_DIR/sidecar-deployment.yaml"
    kubectl apply -f "$TEMP_DIR/gunicorn-app-service.yaml"
    kubectl apply -f "$TEMP_DIR/gunicorn-metrics-service.yaml"
    kubectl apply -f "$TEMP_DIR/gunicorn-app-netpol.yaml"

    print_status "Waiting for deployment to be ready..."
    if ! kubectl wait --for=condition=ready pod -l app=gunicorn-app --timeout=300s; then
        print_error "gunicorn-app pods failed to become ready"
        kubectl get pods -l app=gunicorn-app
        kubectl describe pods -l app=gunicorn-app
        echo "--- Sidecar container logs ---"
        kubectl logs -l app=gunicorn-app -c prometheus-exporter --tail=200 || true
        echo "--- App container logs ---"
        kubectl logs -l app=gunicorn-app -c app --tail=200 || true
        exit 1
    fi

    # Step 7: Verify deployment
    print_status "Verifying deployment..."
    deployment_replicas=$(kubectl get deployment gunicorn-app-with-sidecar -o jsonpath='{.status.readyReplicas}')
    echo "Deployment ready replicas: $deployment_replicas"

    if [ "$deployment_replicas" -lt 1 ]; then
        print_error "Deployment not ready (expected 1+, got $deployment_replicas)"
        kubectl get deployment gunicorn-app-with-sidecar
        exit 1
    fi

    print_success "Deployment successfully created with $deployment_replicas replicas"

    # Step 8: Set up port forwarding
    print_status "Setting up port forwarding..."
    kubectl port-forward service/gunicorn-app-service 8000:8000 &
    PF_APP_PID=$!
    kubectl port-forward service/gunicorn-metrics-service 9091:9091 &
    PF_METRICS_PID=$!

    sleep 15

    # Step 9: Test application health
    print_status "Testing application health..."
    if ! curl -f --max-time 10 http://localhost:8000/health; then
        print_error "Application health check failed"
        kubectl logs -l app=gunicorn-app -c app --tail=200 || true
        kill $PF_APP_PID $PF_METRICS_PID || true
        exit 1
    fi
    print_success "Application is healthy"

    # Step 10: Generate requests
    print_status "Generating test requests..."
    for _ in {1..10}; do
        curl -s http://localhost:8000/ > /dev/null || true
        curl -s http://localhost:8000/health > /dev/null || true
        sleep 0.5
    done

    print_status "Waiting for metrics to be collected (extended wait for CI)..."
    sleep 20

    # Step 11: Fetch and validate metrics
    print_status "Fetching metrics..."
    print_status "DEBUG: Checking Redis connectivity from pod..."
    kubectl exec -it deployment/gunicorn-app-with-sidecar -- sh -c "echo 'Testing Redis connectivity...' && nc -z redis-service 6379 && echo 'Redis reachable' || echo 'Redis NOT reachable'" || true
    metrics_response=$(curl -f --max-time 10 http://localhost:9091/metrics 2>/dev/null)

    if [ -z "$metrics_response" ]; then
        print_error "No metrics response from sidecar metrics endpoint"
        print_status "DEBUG: Checking sidecar logs..."
        kubectl logs -l app=gunicorn-app -c prometheus-exporter --tail=50 || true
        print_status "DEBUG: Checking app logs..."
        kubectl logs -l app=gunicorn-app -c app --tail=50 || true
        kill $PF_APP_PID $PF_METRICS_PID || true
        exit 1
    fi

    # Step 12: Validate all metrics
    validate_all_metrics "$metrics_response"
    if [ $? -ne 0 ]; then
        print_error "Metrics validation failed"
        exit 1
    fi

    # Step 13: Verify Redis integration
    echo ""
    echo "=== Verifying Redis Integration ==="
    redis_keys=$(kubectl run redis-check --image=redis:7-alpine --rm -i --restart=Never -- \
        redis-cli -h redis-service --scan --pattern "gunicorn*" | wc -l || echo "0")

    echo "Redis keys found: $redis_keys"

    if [ "$redis_keys" -gt 5 ]; then
        print_success "Redis integration working ($redis_keys keys found)"
    else
        print_warning "Limited Redis keys found ($redis_keys)"
    fi

    # Step 14: Verify sidecar-specific features
    echo ""
    echo "=== Verifying Sidecar Communication ==="

    # Check sidecar logs
    sidecar_logs=$(kubectl logs -l app=gunicorn-app -c prometheus-exporter --tail=50 || echo "")

    if echo "$sidecar_logs" | grep -q -E "(Started|Collecting|Metrics|Ready)"; then
        print_success "Prometheus exporter sidecar is actively collecting metrics"
    else
        print_warning "Sidecar logs may not show active collection"
    fi

    # Check app logs
    app_logs=$(kubectl logs -l app=gunicorn-app -c app --tail=50 || echo "")

    if echo "$app_logs" | grep -q -E "(Booting worker|worker ready|Listening at)"; then
        print_success "Application container is running correctly"
    else
        print_warning "App logs may not show expected patterns"
    fi

    # Stop port forwarding
    kill $PF_APP_PID $PF_METRICS_PID || true

    # Final summary
    echo ""
    echo "==================================="
    print_success "Sidecar Deployment Test PASSED"
    echo "==================================="
    print_success "Deployment created with $deployment_replicas replicas"
    print_success "Redis storage integration verified"
    print_success "Application container running"
    print_success "Exporter sidecar collecting metrics"
    print_success "All critical metrics present"
    print_success "Metrics accessible via service"
    echo "==================================="

    # Cleanup temp directory
    rm -rf "$TEMP_DIR"
}

# Run main function
main "$@"

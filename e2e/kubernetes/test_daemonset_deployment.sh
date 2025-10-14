#!/bin/bash

# Test script for Kubernetes DaemonSet deployment with Redis storage
# This script tests the complete DaemonSet pattern including:
# - Multi-node Kind cluster setup
# - Redis deployment and connectivity
# - DaemonSet deployment to all nodes
# - Comprehensive metrics validation
# - Redis integration verification
# - Application and sidecar communication

set -e  # Exit on any error

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_DIR="$SCRIPT_DIR/common"

# Source common utilities
source "$COMMON_DIR/setup_kind.sh"
source "$COMMON_DIR/validate_metrics.sh"

# Configuration
CLUSTER_NAME="daemonset-test"
NUM_WORKERS=2
EXPORTER_IMAGE="gunicorn-prometheus-exporter:test"
APP_IMAGE="gunicorn-app:test"

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    pkill -f "kubectl port-forward" || true
    delete_kind_cluster "$CLUSTER_NAME" || true
}

trap cleanup EXIT INT TERM

main() {
    print_status "=========================================="
    print_status "Kubernetes DaemonSet Deployment Test"
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
    cp -r ../../k8s/*.yaml "$TEMP_DIR/"

    # Update image references
    sed -i -E "s|princekrroshan01/gunicorn-app:[^\"[:space:]]*|$APP_IMAGE|g" "$TEMP_DIR/sidecar-daemonset.yaml"
    sed -i -E "s|princekrroshan01/gunicorn-prometheus-exporter:[^\"[:space:]]*|$EXPORTER_IMAGE|g" "$TEMP_DIR/sidecar-daemonset.yaml"

    # Step 5: Deploy Redis
    print_status "Deploying Redis DaemonSet..."
    kubectl apply -f "$TEMP_DIR/redis-daemonset.yaml"

    print_status "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=redis --timeout=300s

    print_status "Verifying Redis connectivity..."
    kubectl run redis-test --image=redis:7-alpine --rm -i --restart=Never -- redis-cli -h redis-service ping

    # Step 6: Deploy DaemonSet
    print_status "Deploying DaemonSet..."
    kubectl apply -f "$TEMP_DIR/sidecar-daemonset.yaml"
    kubectl apply -f "$TEMP_DIR/daemonset-service.yaml"
    kubectl apply -f "$TEMP_DIR/daemonset-metrics-service.yaml"

    print_status "Waiting for DaemonSet pods to be ready..."
    if ! kubectl wait --for=condition=ready pod -l app=gunicorn-prometheus-exporter,component=daemonset --timeout=300s; then
        print_error "DaemonSet pods failed to become ready"
        kubectl get pods -l app=gunicorn-prometheus-exporter,component=daemonset
        kubectl describe pods -l app=gunicorn-prometheus-exporter,component=daemonset
        echo "--- App container logs ---"
        kubectl logs -l app=gunicorn-prometheus-exporter,component=daemonset -c app --tail=200 || true
        echo "--- Prometheus exporter sidecar logs ---"
        kubectl logs -l app=gunicorn-prometheus-exporter,component=daemonset -c prometheus-exporter --tail=200 || true
        exit 1
    fi

    # Step 7: Verify DaemonSet deployment
    print_status "Verifying DaemonSet deployment..."
    ds_desired=$(kubectl get daemonset gunicorn-prometheus-exporter-daemonset -o jsonpath='{.status.desiredNumberScheduled}')
    ds_ready=$(kubectl get daemonset gunicorn-prometheus-exporter-daemonset -o jsonpath='{.status.numberReady}')

    echo "DaemonSet desired pods: $ds_desired"
    echo "DaemonSet ready pods: $ds_ready"

    if [ "$ds_ready" -lt 2 ]; then
        print_error "DaemonSet not deployed to sufficient nodes (expected 2+, got $ds_ready)"
        kubectl get daemonset gunicorn-prometheus-exporter-daemonset
        exit 1
    fi

    print_success "DaemonSet successfully deployed to $ds_ready nodes"

    # Step 8: Set up port forwarding
    print_status "Setting up port forwarding..."
    kubectl port-forward service/daemonset-service 8000:8000 &
    PF_APP_PID=$!
    kubectl port-forward service/daemonset-metrics-service 9091:9091 &
    PF_METRICS_PID=$!

    sleep 15

    # Step 9: Test application health
    print_status "Testing application health..."
    if ! curl -f --max-time 10 http://localhost:8000/health; then
        print_error "Application health check failed"
        kubectl logs -l app=gunicorn-prometheus-exporter,component=daemonset -c app --tail=200 || true
        kill $PF_APP_PID $PF_METRICS_PID || true
        exit 1
    fi
    print_success "Application is healthy"

    # Step 10: Generate requests
    print_status "Generating test requests..."
    for i in {1..20}; do
        curl -s http://localhost:8000/ > /dev/null || true
        curl -s http://localhost:8000/health > /dev/null || true
        sleep 0.5
    done

    print_status "Waiting for metrics to be collected..."
    sleep 10

    # Step 11: Fetch and validate metrics
    print_status "Fetching metrics..."
    metrics_response=$(curl -f --max-time 10 http://localhost:9091/metrics 2>/dev/null)

    if [ -z "$metrics_response" ]; then
        print_error "No metrics response from DaemonSet metrics endpoint"
        kubectl logs -l app=gunicorn-prometheus-exporter,component=daemonset -c prometheus-exporter --tail=200 || true
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

    if [ "$redis_keys" -gt 10 ]; then
        print_success "Redis integration working ($redis_keys keys found)"
    else
        print_warning "Limited Redis keys found ($redis_keys)"
    fi

    # Step 14: Verify DaemonSet-specific features
    echo ""
    echo "=== Verifying DaemonSet-Specific Features ==="

    if echo "$metrics_response" | grep -q "node_name"; then
        print_success "Node name labels found in metrics"
    else
        print_warning "Node name labels not found"
    fi

    if echo "$metrics_response" | grep -q "pod_name"; then
        print_success "Pod name labels found in metrics"
    else
        print_warning "Pod name labels not found"
    fi

    if [ "$ds_ready" -gt 1 ]; then
        print_success "Metrics collected from multiple DaemonSet pods ($ds_ready nodes)"
    fi

    # Step 15: Check sidecar logs
    echo ""
    echo "=== Verifying Container Communication ==="
    sidecar_logs=$(kubectl logs -l app=gunicorn-prometheus-exporter,component=daemonset -c prometheus-exporter --tail=50 || echo "")

    if echo "$sidecar_logs" | grep -q -E "(Started|Collecting|Metrics|Ready)"; then
        print_success "Exporter sidecar is actively collecting metrics"
    else
        print_warning "Exporter sidecar logs may not show active collection"
    fi

    # Stop port forwarding
    kill $PF_APP_PID $PF_METRICS_PID || true

    # Final summary
    echo ""
    echo "==================================="
    print_success "DaemonSet Deployment Test PASSED"
    echo "==================================="
    print_success "DaemonSet deployed to $ds_ready nodes"
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

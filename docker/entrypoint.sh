#!/bin/bash
set -e

# Gunicorn Prometheus Exporter Sidecar Entrypoint
# This script handles the container startup and provides different modes

# Default values
DEFAULT_MODE="sidecar"
DEFAULT_PORT=9091
DEFAULT_BIND="0.0.0.0"
DEFAULT_MULTIPROC_DIR="/tmp/prometheus_multiproc"
DEFAULT_UPDATE_INTERVAL=30

# Function to print usage
usage() {
    echo "Usage: $0 [MODE] [OPTIONS]"
    echo ""
    echo "Modes:"
    echo "  sidecar     Run as sidecar container (default)"
    echo "  standalone  Run standalone metrics server"
    echo "  health      Run health check"
    echo "  help        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  PROMETHEUS_METRICS_PORT      Port for metrics endpoint (default: $DEFAULT_PORT)"
    echo "  PROMETHEUS_BIND_ADDRESS      Bind address (default: $DEFAULT_BIND)"
    echo "  PROMETHEUS_MULTIPROC_DIR     Multiprocess directory (default: $DEFAULT_MULTIPROC_DIR)"
    echo "  REDIS_ENABLED                Enable Redis storage (default: false)"
    echo "  REDIS_HOST                   Redis host (default: localhost)"
    echo "  REDIS_PORT                   Redis port (default: 6379)"
    echo "  REDIS_DB                     Redis database (default: 0)"
    echo "  REDIS_PASSWORD               Redis password (optional)"
    echo "  REDIS_KEY_PREFIX             Redis key prefix (default: gunicorn)"
    echo "  SIDECAR_UPDATE_INTERVAL      Update interval in seconds (default: $DEFAULT_UPDATE_INTERVAL)"
    echo ""
    echo "Examples:"
    echo "  $0 sidecar"
    echo "  $0 standalone --port 9092"
    echo "  $0 health"
}

# Function to run sidecar mode
run_sidecar() {
    echo "Starting Gunicorn Prometheus Exporter in sidecar mode..."

    # Set default values from environment or use defaults
    PORT=${PROMETHEUS_METRICS_PORT:-$DEFAULT_PORT}
    BIND=${PROMETHEUS_BIND_ADDRESS:-$DEFAULT_BIND}
    UPDATE_INTERVAL=${SIDECAR_UPDATE_INTERVAL:-$DEFAULT_UPDATE_INTERVAL}

    # Set multiprocess directory only for multiprocess mode
    if [ "${REDIS_ENABLED:-false}" = "false" ]; then
        MULTIPROC_DIR=${PROMETHEUS_MULTIPROC_DIR:-$DEFAULT_MULTIPROC_DIR}
        # Create multiprocess directory if it doesn't exist
        mkdir -p "$MULTIPROC_DIR"
    else
        # In Redis mode, don't use multiprocess directory
        MULTIPROC_DIR=""
    fi

    # Log configuration
    echo "Configuration:"
    echo "  Port: $PORT"
    echo "  Bind Address: $BIND"
    if [ "${REDIS_ENABLED:-false}" = "false" ]; then
        echo "  Multiprocess Directory: $MULTIPROC_DIR"
    fi
    echo "  Update Interval: $UPDATE_INTERVAL seconds"
    echo "  Redis Enabled: ${REDIS_ENABLED:-false}"

    if [ "${REDIS_ENABLED:-false}" = "true" ]; then
        echo "  Redis Host: ${REDIS_HOST:-localhost}"
        echo "  Redis Port: ${REDIS_PORT:-6379}"
        echo "  Redis DB: ${REDIS_DB:-0}"
        echo "  Redis Key Prefix: ${REDIS_KEY_PREFIX:-gunicorn}"
    fi

    # Start the sidecar
    if [ "${REDIS_ENABLED:-false}" = "false" ]; then
        exec python3 /app/sidecar.py \
            --port "$PORT" \
            --bind "$BIND" \
            --multiproc-dir "$MULTIPROC_DIR" \
            --update-interval "$UPDATE_INTERVAL"
    else
        exec python3 /app/sidecar.py \
            --port "$PORT" \
            --bind "$BIND" \
            --update-interval "$UPDATE_INTERVAL"
    fi
}

# Function to run standalone mode
run_standalone() {
    echo "Starting Gunicorn Prometheus Exporter in standalone mode..."

    # Parse additional arguments for standalone mode
    PORT=${PROMETHEUS_METRICS_PORT:-$DEFAULT_PORT}
    BIND=${PROMETHEUS_BIND_ADDRESS:-$DEFAULT_BIND}
    MULTIPROC_DIR=${PROMETHEUS_MULTIPROC_DIR:-$DEFAULT_MULTIPROC_DIR}

    # Create multiprocess directory if it doesn't exist
    mkdir -p "$MULTIPROC_DIR"

    echo "Standalone mode - serving metrics from: $MULTIPROC_DIR"
    echo "Metrics available at: http://$BIND:$PORT/metrics"

    # Start the sidecar in standalone mode
    exec python3 /app/sidecar.py \
        --port "$PORT" \
        --bind "$BIND" \
        --multiproc-dir "$MULTIPROC_DIR" \
        --update-interval 10
}

# Function to run health check
run_health() {
    echo "Running health check..."

    PORT=${PROMETHEUS_METRICS_PORT:-$DEFAULT_PORT}

    # Check if metrics endpoint is responding
    # Use 127.0.0.1 instead of BIND address since 0.0.0.0 doesn't work with curl
    if curl -f -s "http://127.0.0.1:$PORT/metrics" > /dev/null; then
        echo "Health check passed - metrics endpoint is responding"
        exit 0
    else
        echo "Health check failed - metrics endpoint is not responding"
        exit 1
    fi
}

# Function to wait for dependencies
wait_for_dependencies() {
    if [ "${REDIS_ENABLED:-false}" = "true" ]; then
        REDIS_HOST=${REDIS_HOST:-localhost}
        REDIS_PORT=${REDIS_PORT:-6379}

        echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."

        # Wait for Redis to be available
        while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
            echo "Redis not ready, waiting..."
            sleep 2
        done

        echo "Redis is ready!"
    fi
}

# Main script logic
MODE=${1:-$DEFAULT_MODE}

case "$MODE" in
    "sidecar")
        wait_for_dependencies
        run_sidecar
        ;;
    "standalone")
        wait_for_dependencies
        run_standalone
        ;;
    "health")
        run_health
        ;;
    "help"|"-h"|"--help")
        usage
        exit 0
        ;;
    *)
        echo "Unknown mode: $MODE"
        echo ""
        usage
        exit 1
        ;;
esac

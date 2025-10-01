#!/usr/bin/env python3
"""
Sample Flask application for testing Gunicorn Prometheus Exporter sidecar.
"""

import logging
import random
import time

from flask import Flask, jsonify


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global counter for requests
request_count = 0


@app.route("/")
def home():
    """Home endpoint."""
    global request_count
    request_count += 1

    return jsonify(
        {
            "message": "Hello from Gunicorn with Prometheus Exporter!",
            "request_count": request_count,
            "status": "healthy",
        }
    )


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": time.time()})


@app.route("/slow")
def slow_endpoint():
    """Slow endpoint for testing request duration metrics."""
    delay = random.uniform(1, 3)  # nosec B311
    time.sleep(delay)

    return jsonify(
        {"message": f"Slow response after {delay:.2f} seconds", "delay": delay}
    )


@app.route("/error")
def error_endpoint():
    """Error endpoint for testing error metrics."""
    raise Exception("This is a test error for metrics collection")


@app.route("/heavy")
def heavy_endpoint():
    """CPU-intensive endpoint for testing resource metrics."""
    # Simulate CPU-intensive work
    result = 0
    for i in range(1000000):
        result += i * random.random()  # nosec B311

    return jsonify({"message": "Heavy computation completed", "result": result})


@app.route("/memory")
def memory_endpoint():
    """Memory-intensive endpoint for testing memory metrics."""
    # Allocate some memory
    data = []
    for i in range(10000):
        data.append([random.random() for _ in range(100)])  # nosec B311

    return jsonify({"message": "Memory allocation completed", "data_size": len(data)})


@app.route("/metrics-info")
def metrics_info():
    """Information about available metrics."""
    return jsonify(
        {
            "message": "Gunicorn Prometheus Exporter Metrics",
            "endpoints": {
                "metrics": "/metrics (Prometheus format)",
                "health": "/health (Application health)",
                "slow": "/slow (Test request duration)",
                "error": "/error (Test error handling)",
                "heavy": "/heavy (Test CPU usage)",
                "memory": "/memory (Test memory usage)",
            },
            "sidecar_metrics_port": 9091,
            "sidecar_metrics_path": "/metrics",
        }
    )


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify(
        {"error": "Not found", "message": "The requested resource was not found"}
    ), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify(
        {"error": "Internal server error", "message": "An unexpected error occurred"}
    ), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)  # nosec B201, B104

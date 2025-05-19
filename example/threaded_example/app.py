"""
Example Flask application using Gunicorn's threaded worker with Prometheus metrics.

This example demonstrates:
1. Basic request handling
2. Error handling
3. Long-running requests
4. Memory usage
"""

import logging
import random
import time

from flask import Flask, abort, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/")
def hello():
    """Simple endpoint that returns a greeting."""
    return jsonify({"message": "Hello from threaded worker!"})


@app.route("/error")
def error():
    """Endpoint that raises an error to demonstrate error metrics."""
    abort(500, description="This is a test error")


@app.route("/slow")
def slow():
    """Endpoint that simulates a slow request."""
    time.sleep(random.uniform(0.5, 2.0))
    return jsonify({"message": "Slow request completed"})


@app.route("/memory")
def memory():
    """Endpoint that allocates some memory to demonstrate memory metrics."""
    # Allocate some memory
    data = [i for i in range(1000000)]
    time.sleep(0.1)  # Give time for metrics to update
    return jsonify({"message": "Memory allocated", "size": len(data)})


@app.route("/cpu")
def cpu():
    """Endpoint that does some CPU work."""
    # Do some CPU-intensive work
    result = sum(i * i for i in range(1000000))
    return jsonify({"message": "CPU work completed", "result": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

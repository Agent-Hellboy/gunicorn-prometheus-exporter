"""
Async-compatible WSGI application for testing eventlet and gevent workers.

This application uses async/await patterns that are compatible with:

- Eventlet workers (greenlets)
- Gevent workers (greenlets)
"""

import time

from flask import Flask, jsonify


# Create a Flask app that can work with async workers
app = Flask(__name__)


@app.route("/")
def hello():
    """Simple hello endpoint."""
    return jsonify(
        {
            "message": "Hello from async-compatible app!",
            "timestamp": time.time(),
            "worker_type": "async",
        }
    )


@app.route("/async")
def async_hello():
    """Async-compatible endpoint that simulates async I/O."""
    # Simulate async I/O with a small delay
    time.sleep(0.1)
    return jsonify(
        {
            "message": "Hello from async endpoint!",
            "timestamp": time.time(),
            "worker_type": "async",
        }
    )


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": time.time()})


if __name__ == "__main__":
    app.run(debug=False)  # nosec B201

"""
Example Flask application demonstrating Gunicorn Prometheus Exporter.

This application includes multiple endpoints to demonstrate different metrics:
- / : Simple hello world endpoint
- /slow : Endpoint that simulates slow response
- /error : Endpoint that raises an error
"""

import random
import time

from flask import Flask, abort

app = Flask(__name__)


@app.route("/")
def hello():
    """Simple endpoint returning hello world."""
    return "Hello, World!"


@app.route("/slow")
def slow():
    """Endpoint that simulates slow response time."""
    # Sleep for random time between 0.1 to 2 seconds
    time.sleep(random.uniform(0.1, 2))
    return "Slow response completed!"


@app.route("/error")
def error():
    """Endpoint that randomly raises an error."""
    if random.random() < 0.5:
        abort(500)
    return "No error this time!"


if __name__ == "__main__":
    app.run()

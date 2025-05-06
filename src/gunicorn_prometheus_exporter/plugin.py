"""
Gunicorn Prometheus Exporter - A worker plugin for Gunicorn that
exports Prometheus metrics.

This module provides a worker plugin for Gunicorn that exports Prometheus
metrics. It includes functionality to update worker metrics and handle
request durations.

It patches into the request flow cycle of the Gunicorn web server and
exposes internal telemetry (CPU, memory, request count, latency, errors)
via Prometheus-compatible metrics.

You can also subclass the Gunicorn Arbiter to capture master process events.
Refer to `test_worker.py` and `test_metrics.py` for usage and test coverage.
"""

import logging

from .workers.registry import registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def worker_class(server):
    """Return the appropriate worker class based on the server configuration."""
    return registry.get_worker_class(server.cfg.worker_class)


# # Lifecycle hooks (no changes, but can be extended if needed)
## TODO: Explore these hooks and see if we can use them to update metrics
# def on_starting(server):
#     pass

# def post_fork(server, worker):
#     pass

# def worker_int(worker):
#     pass

# def worker_abort(worker):
#     pass

# def post_worker_init(worker):
#     pass

# def pre_request(worker, req):
#     pass

# def post_request(worker, req, environ, resp):
#     pass

# def when_ready(server):
#     pass

# def worker_exit(server, worker):
#     pass

# def on_exit(server):
#     pass

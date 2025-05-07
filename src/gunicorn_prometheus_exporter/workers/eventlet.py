"""
Eventlet worker implementation for Gunicorn Prometheus Exporter.
This module provides the eventlet worker implementation
that inherits from the base worker.
"""

import logging

logger = logging.getLogger(__name__)

# Try to import EventletWorker, but don't fail if it's not available
try:
    from gunicorn.workers.geventlet import EventletWorker

    EVENTLET_AVAILABLE = True
except ImportError:
    EVENTLET_AVAILABLE = False
    EventletWorker = None
    logger.warning("EventletWorker not available. Eventlet support will be disabled.")

if EVENTLET_AVAILABLE:
    from .base import PrometheusMetricsMixin

    class PrometheusEventletWorker(PrometheusMetricsMixin, EventletWorker):
        """Eventlet worker implementation with Prometheus metrics support."""

        pass

else:
    PrometheusEventletWorker = None

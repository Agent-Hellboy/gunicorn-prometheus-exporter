"""
Gevent worker implementation for Gunicorn Prometheus Exporter.
This module provides the gevent worker implementation that
inherits from the base worker.
"""

import logging

logger = logging.getLogger(__name__)

# Try to import GeventWorker, but don't fail if it's not available
try:
    from gunicorn.workers.gevent import GeventWorker

    GEVENT_AVAILABLE = True
except ImportError:
    GEVENT_AVAILABLE = False
    GeventWorker = None
    logger.warning("GeventWorker not available. Gevent support will be disabled.")

if GEVENT_AVAILABLE:
    from .base import PrometheusMetricsMixin

    class PrometheusGeventWorker(PrometheusMetricsMixin, GeventWorker):
        """Gevent worker implementation with Prometheus metrics support."""

        pass

else:
    PrometheusGeventWorker = None

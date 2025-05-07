"""
Tornado worker implementation for Gunicorn Prometheus Exporter.
This module provides the tornado worker implementation
that inherits from the base worker.
"""

import logging

logger = logging.getLogger(__name__)

# Try to import TornadoWorker, but don't fail if it's not available
try:
    from gunicorn.workers.gtornado import TornadoWorker

    TORNADO_AVAILABLE = True
except ImportError:
    TORNADO_AVAILABLE = False
    TornadoWorker = None
    logger.warning("TornadoWorker not available. Tornado support will be disabled.")

if TORNADO_AVAILABLE:
    from .base import PrometheusMetricsMixin

    class PrometheusTornadoWorker(PrometheusMetricsMixin, TornadoWorker):
        """Tornado worker implementation with Prometheus metrics support."""

        pass

else:
    PrometheusTornadoWorker = None

"""
Thread worker implementation for Gunicorn Prometheus Exporter.
This module provides the thread worker implementation
that inherits from the base worker.
"""

import logging

logger = logging.getLogger(__name__)

# Try to import ThreadWorker, but don't fail if it's not available
try:
    from gunicorn.workers.gthread import ThreadWorker

    THREAD_AVAILABLE = True
except ImportError:
    THREAD_AVAILABLE = False
    ThreadWorker = None
    logger.warning("ThreadWorker not available. Thread support will be disabled.")

if THREAD_AVAILABLE:
    from .base import PrometheusMetricsMixin

    class PrometheusThreadWorker(PrometheusMetricsMixin, ThreadWorker):
        """Thread worker implementation with Prometheus metrics support."""

        pass

else:
    PrometheusThreadWorker = None

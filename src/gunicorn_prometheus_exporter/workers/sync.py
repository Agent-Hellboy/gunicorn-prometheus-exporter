"""
Sync worker implementation for Gunicorn Prometheus Exporter.
This module provides the sync worker implementation that inherits from the base worker.
"""

from gunicorn.workers.sync import SyncWorker

from .base import PrometheusMetricsMixin


class PrometheusSyncWorker(PrometheusMetricsMixin, SyncWorker):
    """Sync worker implementation with Prometheus metrics support."""

    pass

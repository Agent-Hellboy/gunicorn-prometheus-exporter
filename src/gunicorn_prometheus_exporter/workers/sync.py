"""
Sync worker implementation for Gunicorn Prometheus Exporter.
This module provides the sync worker implementation
that inherits from the base worker.
"""

from gunicorn.workers.sync import SyncWorker

from .base import PrometheusMetricsMixin


class PrometheusSyncWorker(PrometheusMetricsMixin, SyncWorker):
    """Sync worker implementation with Prometheus metrics support.

    This class combines the Prometheus metrics collection with Gunicorn's sync worker.
    The actual worker implementation is delegated to SyncWorker, while metrics
    collection is handled by PrometheusMetricsMixin.
    """

    pass

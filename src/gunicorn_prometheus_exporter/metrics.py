"""
Prometheus metrics for Gunicorn Prometheus Exporter.
"""

import glob
import os
from abc import ABCMeta
from typing import Dict, List, Optional, Type, Union

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, multiprocess

# === Auto setup multiprocess mode ===
DEFAULT_PROM_DIR = "/tmp/prometheus"

if not os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = DEFAULT_PROM_DIR

# Create and clean directory
try:
    os.makedirs(DEFAULT_PROM_DIR, exist_ok=True)
    for f in glob.glob(f"{DEFAULT_PROM_DIR}/*"):
        os.remove(f)
except Exception as e:
    print(f"Warning: Failed to prepare PROMETHEUS_MULTIPROC_DIR: {e}")

# Prometheus Registry
registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)


class MetricMeta(ABCMeta):
    """Metaclass for automatically registering metrics with the registry."""

    def __new__(
        mcs,
        name: str,
        bases: tuple,
        namespace: Dict,
        metric_type: Optional[Type[Union[Counter, Gauge, Histogram]]] = None,
        **kwargs,
    ) -> Type:
        """Create a new metric class and register it with the registry."""
        cls = super().__new__(mcs, name, bases, namespace)

        if metric_type is not None:
            extra_ctor_args = {}
            # Forward well‑known optional attributes
            for opt in ("buckets", "unit", "namespace", "subsystem"):
                if opt in namespace:
                    extra_ctor_args[opt] = namespace[opt]

            metric = metric_type(
                name=namespace.get("name", name.lower()),
                documentation=namespace.get("documentation", ""),
                labelnames=namespace.get("labelnames", []),
                registry=registry,
                **extra_ctor_args,
                **kwargs,
            )
            cls._metric = metric
        return cls


class BaseMetric(metaclass=MetricMeta):
    """Base class for all metrics."""

    name: str
    documentation: str
    labelnames: List[str]

    @classmethod
    def labels(cls, **kwargs):
        """Get a labeled instance of the metric."""
        return cls._metric.labels(**kwargs)

    @classmethod
    def collect(cls):
        """Collect metric samples."""
        return cls._metric.collect()

    @classmethod
    def _samples(cls):
        """Get metric samples."""
        return cls._metric._samples()

    @property
    def _name(cls):
        """Get metric name."""
        return cls._metric._name

    @property
    def _documentation(cls):
        """Get metric documentation."""
        return cls._metric._documentation

    @property
    def _labelnames(cls):
        """Get metric label names."""
        return cls._metric._labelnames

    @classmethod
    def inc(cls, **labels):
        return cls._metric.labels(**labels).inc()

    @classmethod
    def dec(cls, **labels):
        return cls._metric.labels(**labels).dec()

    @classmethod
    def set(cls, value, **labels):
        return cls._metric.labels(**labels).set(value)

    @classmethod
    def observe(cls, value, **labels):
        return cls._metric.labels(**labels).observe(value)

    @classmethod
    def describe(cls):
        return {
            "name": cls._metric._name,
            "documentation": cls._metric._documentation,
            "type": type(cls._metric).__name__,
            "labels": cls._metric._labelnames,
        }

    @classmethod
    def clear(cls):
        cls._metric._metrics.clear()


# Worker metrics
# ---------------------------------------------------------------------------------
class WorkerRequests(BaseMetric, metric_type=Counter):
    """Total number of requests handled by this worker."""

    name = "gunicorn_worker_requests"
    documentation = "Total number of requests handled by this worker"
    labelnames = ["worker_id"]


class WorkerRequestDuration(BaseMetric, metric_type=Histogram):
    """Request duration in seconds."""

    name = "gunicorn_worker_request_duration_seconds"
    documentation = "Request duration in seconds"
    labelnames = ["worker_id"]
    buckets = (0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf"))


class WorkerMemory(BaseMetric, metric_type=Gauge):
    """Memory usage of the worker process."""

    name = "gunicorn_worker_memory_bytes"
    documentation = "Memory usage of the worker process"
    labelnames = ["worker_id"]


class WorkerCPU(BaseMetric, metric_type=Gauge):
    """CPU usage of the worker process."""

    name = "gunicorn_worker_cpu_percent"
    documentation = "CPU usage of the worker process"
    labelnames = ["worker_id"]


class WorkerUptime(BaseMetric, metric_type=Gauge):
    """Uptime of the worker process."""

    name = "gunicorn_worker_uptime_seconds"
    documentation = "Uptime of the worker process"
    labelnames = ["worker_id"]


class WorkerFailedRequests(BaseMetric, metric_type=Counter):
    """Total number of failed requests handled by this worker."""

    name = "gunicorn_worker_failed_requests"
    documentation = "Total number of failed requests handled by this worker"
    labelnames = ["worker_id", "method", "endpoint", "error_type"]


class WorkerErrorHandling(BaseMetric, metric_type=Counter):
    """Total number of errors handled by this worker."""

    name = "gunicorn_worker_error_handling"
    documentation = "Total number of errors handled by this worker"
    labelnames = ["worker_id", "method", "endpoint", "error_type"]


class WorkerState(BaseMetric, metric_type=Gauge):
    """Current state of the worker."""

    name = "gunicorn_worker_state"
    documentation = "Current state of the worker (1=running, 0=stopped)"
    labelnames = ["worker_id", "state", "timestamp"]


# ---------------------------------------------------------------------------------


# Master metrics
# ---------------------------------------------------------------------------------
class MasterWorkerRestarts(BaseMetric, metric_type=Counter):
    """Total number of Gunicorn worker restarts."""

    name = "gunicorn_master_worker_restart"
    documentation = "Total number of Gunicorn worker restarts"
    labelnames = ["reason"]


# ---------------------------------------------------------------------------------

WORKER_REQUESTS = WorkerRequests
WORKER_REQUEST_DURATION = WorkerRequestDuration
WORKER_MEMORY = WorkerMemory
WORKER_CPU = WorkerCPU
WORKER_UPTIME = WorkerUptime
WORKER_FAILED_REQUESTS = WorkerFailedRequests
WORKER_ERROR_HANDLING = WorkerErrorHandling
WORKER_STATE = WorkerState
MASTER_WORKER_RESTARTS = MasterWorkerRestarts
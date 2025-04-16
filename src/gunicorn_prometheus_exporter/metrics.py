"""
Prometheus metrics for Gunicorn Prometheus Exporter.
"""

import glob
import os

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

# Worker-specific metrics
WORKER_REQUESTS = Counter(
    "gunicorn_worker_requests_total",
    "Total number of requests handled by this worker",
    ["worker_id"],
    registry=registry,
)

WORKER_REQUEST_DURATION = Histogram(
    "gunicorn_worker_request_duration_seconds",
    "Request duration in seconds",
    ["worker_id"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf")),
    registry=registry,
)

WORKER_MEMORY = Gauge(
    "gunicorn_worker_memory_bytes",
    "Memory usage of the worker process",
    ["worker_id"],
    registry=registry,
)

WORKER_CPU = Gauge(
    "gunicorn_worker_cpu_percent",
    "CPU usage of the worker process",
    ["worker_id"],
    registry=registry,
)

WORKER_UPTIME = Gauge(
    "gunicorn_worker_uptime_seconds",
    "Uptime of the worker process",
    ["worker_id"],
    registry=registry,
)

WORKER_FAILED_REQUESTS = Counter(
    "gunicorn_worker_failed_requests_total",
    "Total number of failed requests handled by this worker",
    ["worker_id"],
    registry=registry,
)

WORKER_ERROR_HANDLING = Counter(
    "gunicorn_worker_error_handling",
    "Total number of Gunicorn-level errors",
    ["worker_id", "error_type"],
    registry=registry,
)

WORKER_STATE = Gauge(
    "gunicorn_worker_state",
    "Current state of the worker exit start",
    ["worker_id", "state", "timestamp"],
    registry=registry,
)

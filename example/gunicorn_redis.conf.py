"""Gunicorn configuration with Redis forwarding enabled."""

import os


# Enable Redis forwarding
os.environ["REDIS_ENABLED"] = "true"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["REDIS_DB"] = "0"
os.environ["REDIS_KEY_PREFIX"] = "gunicorn:metrics:"
os.environ["REDIS_FORWARD_INTERVAL"] = "15"  # seconds

# Enable DB file cleanup (default: true)
os.environ["CLEANUP_DB_FILES"] = "true"

# Gunicorn configuration
bind = "127.0.0.1:8084"
workers = 2
threads = 1
timeout = 30
keepalive = 2
worker_class = "gunicorn_prometheus_exporter.plugin.PrometheusWorker"
arbiter_class = "gunicorn_prometheus_exporter.master.PrometheusMaster"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
proc_name = "gunicorn-redis-test"


# Prometheus metrics server
def when_ready(server):
    """Start Prometheus metrics server when Gunicorn is ready."""
    import threading

    from prometheus_client import CollectorRegistry, start_http_server
    from prometheus_client.multiprocess import MultiProcessCollector

    # Create registry for multiprocess mode
    registry = CollectorRegistry()
    MultiProcessCollector(registry)

    # Start metrics server
    metrics_port = int(os.environ.get("PROMETHEUS_METRICS_PORT", "9091"))
    metrics_bind = os.environ.get("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")  # nosec B104 - example config

    def start_metrics_server():
        start_http_server(metrics_port, addr=metrics_bind, registry=registry)

    metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
    metrics_thread.start()

    print(f"Prometheus metrics server started on {metrics_bind}:{metrics_port}")
    print(
        f"Redis forwarder enabled (interval: {os.environ.get('REDIS_FORWARD_INTERVAL', '15')}s)"
    )
    print(
        f"Redis connection: {os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', '6379')}"
    )

# Gunicorn Prometheus Exporter Example

This example demonstrates how to use the Gunicorn Prometheus Exporter with a simple Flask application.

## Setup


1. Install the required packages:
```bash
pip install gunicorn prometheus-client flask
```

## Running the Example

Start the example application with Gunicorn:

```bash
# 1) Clean + create metrics dir
rm -rf /tmp/metrics_test
mkdir -p /tmp/metrics_test
chmod 777 /tmp/metrics_test

# 2) Set env vars
export PROMETHEUS_MULTIPROC_DIR=/tmp/metrics_test
export PROMETHEUS_METRICS_PORT=9090

# 3) Start Gunicorn (uses your gunicorn.conf.py)
gunicorn --config gunicorn.conf.py app:app 
```

## Testing

1. The application will be available at `http://localhost:8080`
2. The metrics will be available at `http://localhost:9091/metrics`

Try these endpoints:
- `http://localhost:8080/` - Returns "Hello, World!"
- `http://localhost:8080/slow` - Simulates a slow request
- `http://localhost:9091/metrics` - View Prometheus metrics

```bash
curl -s http://localhost:9091/metrics | grep gunicorn_worker_
# Example metrics output...
```

## Setting up Prometheus UI

1. Create a `prometheus.yml` configuration file:
```yaml
global:
  scrape_interval: 15s

# Scrape our example exporter
scrape_configs:
  - job_name: 'gunicorn-prometheus-exporter'         
    metrics_path: '/metrics'       
    static_configs:
      - targets: ['127.0.0.1:9090'] # our example exporter
```

2. Run Prometheus using Docker:
```bash
docker run -d \
  --name prometheus \
  --network host \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
  prom/prometheus
```

3. Access Prometheus UI at `http://localhost:9090` to:
   - View metrics in the Graph interface
   - Use PromQL queries to analyze worker performance
   - Create graphs and dashboards
   - Set up alerts based on metric thresholds

Example PromQL queries:
```promql
# Current active workers and their uptime
gunicorn_worker_uptime_seconds{worker_id=~"worker_.*"}

# Worker memory usage (in MB)
gunicorn_worker_memory_bytes{worker_id=~"worker_.*"} / 1024 / 1024

# Request rate per worker (requests per second)
rate(gunicorn_worker_requests_total{worker_id=~"worker_.*"}[5m])

# Average request duration per worker
rate(gunicorn_worker_request_duration_seconds_sum{worker_id=~"worker_.*"}[5m]) 
/ 
rate(gunicorn_worker_request_duration_seconds_count{worker_id=~"worker_.*"}[5m])
```

## Available Metrics

The example will generate the following metrics:
- `gunicorn_worker_requests_total`: Total number of requests handled by each worker
- `gunicorn_worker_request_duration_seconds`: Request duration histogram
- `gunicorn_worker_memory_bytes`: Worker memory usage
- `gunicorn_worker_cpu_percent`: Worker CPU usage
- `gunicorn_worker_uptime_seconds`: Worker uptime
- `gunicorn_worker_failed_requests`: Failed request counts (if any)

## Notes

- The metrics server runs on port 9091 by default
- The application runs on port 8080
- The multiprocess directory is required for proper metric collection
- Make sure the multiprocess directory is writable by the Gunicorn process

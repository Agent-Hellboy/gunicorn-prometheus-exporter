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
2. The metrics will be available at `http://localhost:9090/metrics`

Try these endpoints:
- `http://localhost:8080/` - Returns "Hello, World!"
- `http://localhost:8080/slow` - Simulates a slow request
- `http://localhost:9090/metrics` - View Prometheus metrics

```bash
curl -s http://localhost:9090/metrics | grep gunicorn_worker_
# HELP gunicorn_worker_memory_bytes Memory usage of the worker process
# TYPE gunicorn_worker_memory_bytes gauge
gunicorn_worker_memory_bytes{pid="30134",worker_id="30128"} 2.54976e+07
gunicorn_worker_memory_bytes{pid="30133",worker_id="30128"} 2.54976e+07
# HELP gunicorn_worker_cpu_percent CPU usage of the worker process
# TYPE gunicorn_worker_cpu_percent gauge
gunicorn_worker_cpu_percent{pid="30134",worker_id="30128"} 0.0
gunicorn_worker_cpu_percent{pid="30133",worker_id="30128"} 0.0
# HELP gunicorn_worker_uptime_seconds Uptime of the worker process
# TYPE gunicorn_worker_uptime_seconds gauge
gunicorn_worker_uptime_seconds{pid="30134",worker_id="30128"} 26.000351667404175
gunicorn_worker_uptime_seconds{pid="30133",worker_id="30128"} 28.92296528816223
# HELP gunicorn_worker_request_duration_seconds Request duration in seconds
# TYPE gunicorn_worker_request_duration_seconds histogram
gunicorn_worker_request_duration_seconds_sum{worker_id="30128"} 0.6077625751495361
gunicorn_worker_request_duration_seconds_bucket{le="0.1",worker_id="30128"} 1.0
gunicorn_worker_request_duration_seconds_bucket{le="0.5",worker_id="30128"} 1.0
gunicorn_worker_request_duration_seconds_bucket{le="1.0",worker_id="30128"} 2.0
gunicorn_worker_request_duration_seconds_bucket{le="2.5",worker_id="30128"} 2.0
gunicorn_worker_request_duration_seconds_bucket{le="5.0",worker_id="30128"} 2.0
gunicorn_worker_request_duration_seconds_bucket{le="10.0",worker_id="30128"} 2.0
gunicorn_worker_request_duration_seconds_bucket{le="30.0",worker_id="30128"} 2.0
gunicorn_worker_request_duration_seconds_bucket{le="60.0",worker_id="30128"} 2.0
gunicorn_worker_request_duration_seconds_bucket{le="+Inf",worker_id="30128"} 2.0
gunicorn_worker_request_duration_seconds_count{worker_id="30128"} 2.0
# HELP gunicorn_worker_requests_total Total number of requests handled by this worker
# TYPE gunicorn_worker_requests_total counter
gunicorn_worker_requests_total{worker_id="30128"} 2.0
```

## Available Metrics

The example will generate the following metrics:
- Request counts and latencies
- Worker memory and CPU usage
- Worker uptime
- Failed requests (if any)

## Notes

- The metrics server runs on port 9090 by default
- The application runs on port 8080
- The multiprocess directory is required for proper metric collection
- Make sure the multiprocess directory is writable by the Gunicorn process 

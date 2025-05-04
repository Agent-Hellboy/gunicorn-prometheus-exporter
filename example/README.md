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

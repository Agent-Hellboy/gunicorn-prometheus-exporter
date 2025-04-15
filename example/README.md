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
gunicorn -c gunicorn.conf.py app:app --worker-class=gunicorn_prometheus_exporter.plugin.PrometheusWorker 
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
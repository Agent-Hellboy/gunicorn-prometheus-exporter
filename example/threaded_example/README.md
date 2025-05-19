# Gunicorn Threaded Worker Example

This example demonstrates how to use the `PrometheusGthreadWorker` with a Flask application. It includes various endpoints to showcase different types of metrics collection.

## Features

- Uses Gunicorn's threaded worker with Prometheus metrics
- Demonstrates request handling, error tracking, and resource usage metrics
- Includes endpoints for testing different scenarios:
  - `/`: Basic request handling
  - `/error`: Error handling
  - `/slow`: Long-running requests
  - `/memory`: Memory usage
  - `/cpu`: CPU-intensive work

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Example

Start the server using Gunicorn:
```bash
gunicorn -c gunicorn.conf.py app:app
```

The server will start on http://localhost:8000

## Testing the Endpoints

You can test the different endpoints using curl or a web browser:

1. Basic request:
```bash
curl http://localhost:8000/
```

2. Error endpoint:
```bash
curl http://localhost:8000/error
```

3. Slow request:
```bash
curl http://localhost:8000/slow
```

4. Memory usage:
```bash
curl http://localhost:8000/memory
```

5. CPU usage:
```bash
curl http://localhost:8000/cpu
```

## Viewing Metrics

The Prometheus metrics are available at:
```bash
curl http://localhost:8000/metrics
```

You should see metrics like:
- `gunicorn_worker_requests_total`
- `gunicorn_worker_request_duration_seconds`
- `gunicorn_worker_memory_bytes`
- `gunicorn_worker_cpu_percent`
- `gunicorn_worker_uptime_seconds`
- `gunicorn_worker_error_handling_total`

## Configuration

The example uses the following Gunicorn configuration:
- Number of workers: CPU cores * 2 + 1
- Threads per worker: 4
- Worker class: `PrometheusGthreadWorker`
- Port: 8000
- Logging: stdout/stderr

You can modify these settings in `gunicorn.conf.py`. 
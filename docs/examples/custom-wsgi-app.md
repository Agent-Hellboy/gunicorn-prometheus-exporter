# Custom WSGI App Integration

This guide shows how to integrate the Gunicorn Prometheus Exporter with custom WSGI applications.

## Quick Start

### 1. Install Dependencies

```bash
pip install gunicorn gunicorn-prometheus-exporter
```

### 2. Create Custom WSGI Application

```python
# app.py
import json
import time
from wsgiref.simple_server import make_server

def simple_app(environ, start_response):
    """Simple WSGI application."""
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')

    if path == '/' and method == 'GET':
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        return [json.dumps({"message": "Hello World"}).encode()]

    elif path == '/health' and method == 'GET':
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        return [json.dumps({"status": "healthy"}).encode()]

    elif path == '/api/users' and method == 'GET':
        status = '200 OK'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        return [json.dumps({"users": ["user1", "user2", "user3"]}).encode()]

    else:
        status = '404 Not Found'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        return [json.dumps({"error": "Not found"}).encode()]

# WSGI application object
application = simple_app

if __name__ == '__main__':
    with make_server('', 8000, application) as httpd:
        print("Serving on port 8000...")
        httpd.serve_forever()
```

### 3. Create Gunicorn Configuration

Create `gunicorn.conf.py`:

```python
# gunicorn.conf.py
import os

# Server settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
master_class = "gunicorn_prometheus_exporter.PrometheusMaster"

# Environment variables
raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc",
    "GUNICORN_WORKERS=4"
]

# Prometheus hooks
when_ready = "gunicorn_prometheus_exporter.default_when_ready"
on_starting = "gunicorn_prometheus_exporter.default_on_starting"
worker_int = "gunicorn_prometheus_exporter.default_worker_int"
on_exit = "gunicorn_prometheus_exporter.default_on_exit"

# WSGI optimizations
preload_app = True
worker_connections = 1000
```

### 4. Start Custom WSGI App with Gunicorn

```bash
gunicorn -c gunicorn.conf.py app:application
```

## 🔧 Advanced Configuration

### Production WSGI Setup

```python
# gunicorn.conf.py
import os

# Server settings
bind = "0.0.0.0:8000"
workers = 8
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
master_class = "gunicorn_prometheus_exporter.PrometheusMaster"

# Environment variables
raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/var/lib/prometheus/multiproc",
    "GUNICORN_WORKERS=8",
    "GUNICORN_TIMEOUT=30"
]

# Prometheus hooks
when_ready = "gunicorn_prometheus_exporter.default_when_ready"
on_starting = "gunicorn_prometheus_exporter.default_on_starting"
worker_int = "gunicorn_prometheus_exporter.default_worker_int"
on_exit = "gunicorn_prometheus_exporter.default_on_exit"

# Performance optimizations
preload_app = True
max_requests = 1000
max_requests_jitter = 50
worker_connections = 2000
worker_tmp_dir = "/dev/shm"

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
```

### Advanced WSGI Application with Middleware

```python
# app.py
import json
import time
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WSGIMiddleware:
    """Base middleware class for WSGI applications."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        return self.app(environ, start_response)

class LoggingMiddleware(WSGIMiddleware):
    """Middleware for request logging."""

    def __call__(self, environ, start_response):
        start_time = time.time()

        def custom_start_response(status, headers, exc_info=None):
            duration = time.time() - start_time
            logger.info(
                f"{environ.get('REQUEST_METHOD')} {environ.get('PATH_INFO')} "
                f"{status.split()[0]} {duration:.3f}s"
            )
            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)

class ErrorHandlingMiddleware(WSGIMiddleware):
    """Middleware for error handling."""

    def __call__(self, environ, start_response):
        try:
            return self.app(environ, start_response)
        except Exception as e:
            logger.error(f"Unhandled exception: {e}")
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'application/json')]
            start_response(status, headers)
            return [json.dumps({"error": "Internal server error"}).encode()]

def route(path, methods=None):
    """Decorator for route handling."""
    if methods is None:
        methods = ['GET']

    def decorator(func):
        @wraps(func)
        def wrapper(environ, start_response):
            request_path = environ.get('PATH_INFO', '/')
            request_method = environ.get('REQUEST_METHOD', 'GET')

            if request_path == path and request_method in methods:
                return func(environ, start_response)
            else:
                return None  # Continue to next handler

        return wrapper
    return decorator

class WSGIApplication:
    """Custom WSGI application with routing."""

    def __init__(self):
        self.routes = []

    def route(self, path, methods=None):
        """Add a route to the application."""
        def decorator(func):
            self.routes.append((path, methods or ['GET'], func))
            return func
        return decorator

    def __call__(self, environ, start_response):
        request_path = environ.get('PATH_INFO', '/')
        request_method = environ.get('REQUEST_METHOD', 'GET')

        # Find matching route
        for path, methods, handler in self.routes:
            if request_path == path and request_method in methods:
                return handler(environ, start_response)

        # No route found
        status = '404 Not Found'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        return [json.dumps({"error": "Not found"}).encode()]

# Create application instance
app = WSGIApplication()

@app.route('/')
def home(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'application/json')]
    start_response(status, headers)
    return [json.dumps({"message": "Hello World"}).encode()]

@app.route('/health')
def health(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'application/json')]
    start_response(status, headers)
    return [json.dumps({"status": "healthy"}).encode()]

@app.route('/api/users')
def get_users(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'application/json')]
    start_response(status, headers)
    return [json.dumps({"users": ["user1", "user2", "user3"]}).encode()]

@app.route('/api/users', methods=['POST'])
def create_user(environ, start_response):
    try:
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        body = environ['wsgi.input'].read(content_length)
        data = json.loads(body.decode())

        # Simulate user creation
        user = {"id": 1, "name": data.get('name'), "email": data.get('email')}

        status = '201 Created'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        return [json.dumps(user).encode()]
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        status = '400 Bad Request'
        headers = [('Content-Type', 'application/json')]
        start_response(status, headers)
        return [json.dumps({"error": "Invalid request"}).encode()]

# Apply middleware
application = ErrorHandlingMiddleware(LoggingMiddleware(app))
```

## 🐳 Docker Setup

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install gunicorn gunicorn-prometheus-exporter

# Copy application
COPY . .

# Create multiprocess directory
RUN mkdir -p /tmp/prometheus_multiproc

# Expose ports
EXPOSE 8000 9091

# Set environment variables
ENV PROMETHEUS_METRICS_PORT=9091
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
ENV GUNICORN_WORKERS=4

# Start with gunicorn
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:application"]
```

### requirements.txt

```txt
gunicorn>=21.2.0
gunicorn-prometheus-exporter>=0.1.5
```

### Docker Compose

```yaml
# docker-compose.yml
version: "3.8"
services:
  web:
    build: .
    ports:
      - "8000:8000"
      - "9091:9091"
    environment:
      - PROMETHEUS_METRICS_PORT=9091
      - PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
      - GUNICORN_WORKERS=4
    volumes:
      - prometheus_data:/tmp/prometheus_multiproc

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  prometheus_data:
```

## Prometheus Configuration

### prometheus.yml

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "custom-wsgi-gunicorn"
    static_configs:
      - targets: ["localhost:9091"]
    metrics_path: /metrics
    scrape_interval: 5s
```

## 🔍 Monitoring Custom WSGI Metrics

### Custom Application Metrics (Optional)

You can extend the monitoring with custom application metrics:

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Custom application metrics
app_requests_total = Counter(
    'app_requests_total',
    'Total application requests',
    ['method', 'endpoint', 'status']
)

app_request_duration = Histogram(
    'app_request_duration_seconds',
    'Application request duration',
    ['method', 'endpoint']
)

app_active_connections = Gauge(
    'app_active_connections',
    'Number of active connections'
)

class MetricsMiddleware:
    """Middleware for collecting custom metrics."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        start_time = time.time()
        app_active_connections.inc()

        def custom_start_response(status, headers, exc_info=None):
            duration = time.time() - start_time
            status_code = status.split()[0]

            app_request_duration.labels(
                method=environ.get('REQUEST_METHOD', 'GET'),
                endpoint=environ.get('PATH_INFO', '/')
            ).observe(duration)

            app_requests_total.labels(
                method=environ.get('REQUEST_METHOD', 'GET'),
                endpoint=environ.get('PATH_INFO', '/'),
                status=status_code
            ).inc()

            app_active_connections.dec()
            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)
```

Add to your WSGI app:

```python
# app.py
from metrics import MetricsMiddleware

# Apply metrics middleware
application = MetricsMiddleware(ErrorHandlingMiddleware(LoggingMiddleware(app)))
```

## 🚨 Troubleshooting

### Common WSGI Issues

1. **WSGI Application Not Found**

   ```bash
   # Ensure the application object is correctly named
   # In app.py, make sure you have: application = your_app
   ```

2. **Import Errors**

   ```bash
   # Ensure your app module is in the Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

3. **Middleware Order**
   ```python
   # Apply middleware in the correct order
   application = MetricsMiddleware(ErrorHandlingMiddleware(LoggingMiddleware(app)))
   ```

### Debug Mode

For development, you can use Python's built-in WSGI server:

```python
# debug.py
from wsgiref.simple_server import make_server
from app import application

if __name__ == '__main__':
    with make_server('', 8000, application) as httpd:
        print("Serving on port 8000...")
        httpd.serve_forever()
```

## 📈 Performance Tips

1. **Use Connection Pooling**

   ```python
   # For database connections
   import threading
   from contextlib import contextmanager

   _connections = threading.local()

   @contextmanager
   def get_connection():
       if not hasattr(_connections, 'conn'):
           _connections.conn = create_connection()
       yield _connections.conn
   ```

2. **Implement Caching**

   ```python
   import functools
   import time

   def cache(ttl=300):
       def decorator(func):
           cache_data = {}

           @functools.wraps(func)
           def wrapper(*args, **kwargs):
               key = str(args) + str(kwargs)
               now = time.time()

               if key in cache_data:
                   result, timestamp = cache_data[key]
                   if now - timestamp < ttl:
                       return result

               result = func(*args, **kwargs)
               cache_data[key] = (result, now)
               return result

           return wrapper
       return decorator
   ```

3. **Optimize Response Generation**

   ```python
   # Pre-compile JSON responses
   import json

   RESPONSES = {
       'home': json.dumps({"message": "Hello World"}).encode(),
       'health': json.dumps({"status": "healthy"}).encode(),
       'not_found': json.dumps({"error": "Not found"}).encode()
   }

   def home(environ, start_response):
       status = '200 OK'
       headers = [('Content-Type', 'application/json')]
       start_response(status, headers)
       return [RESPONSES['home']]
   ```

4. **Use Streaming Responses**

   ```python
   def streaming_response(environ, start_response):
       status = '200 OK'
       headers = [('Content-Type', 'text/plain')]
       start_response(status, headers)

       def generate():
           for i in range(1000):
               yield f"Line {i}\n".encode()

       return generate()
   ```

## 🔗 Related Documentation

- [Installation Guide](../installation.md)
- [Configuration Reference](../configuration.md)
- [Metrics Documentation](../metrics.md)
- [Django Integration](django-integration.md)
- [FastAPI Integration](fastapi-integration.md)
- [Flask Integration](flask-integration.md)
- [Pyramid Integration](pyramid-integration.md)

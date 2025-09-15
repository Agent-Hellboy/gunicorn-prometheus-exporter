# FastAPI Integration

This guide shows how to integrate the Gunicorn Prometheus Exporter with FastAPI applications.

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn gunicorn gunicorn-prometheus-exporter
```

### 2. Create FastAPI Application

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 3. Create Gunicorn Configuration

Create `gunicorn.conf.py`:

```python
# gunicorn.conf.py
import os

# Server settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"  # Sync worker
# For async applications, consider these alternatives:
# worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"  # Thread worker
# worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"  # Eventlet worker
# worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"  # Gevent worker
# worker_class = "gunicorn_prometheus_exporter.PrometheusTornadoWorker"  # Tornado worker
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

# FastAPI optimizations
preload_app = True
worker_connections = 1000
```

### 4. Start FastAPI with Gunicorn

```bash
gunicorn -c gunicorn.conf.py main:app
```

## 🔧 Advanced Configuration

### Production FastAPI Setup

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

### FastAPI Application with Middleware

```python
# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI(title="My FastAPI App", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/users")
async def get_users():
    return {"users": ["user1", "user2", "user3"]}
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
CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:app"]
```

### requirements.txt

```txt
fastapi>=0.68.0
uvicorn>=0.15.0
gunicorn>=21.2.0
gunicorn-prometheus-exporter>=0.1.0
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
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
  - job_name: 'fastapi-gunicorn'
    static_configs:
      - targets: ['localhost:9091']
    metrics_path: /metrics
    scrape_interval: 5s
```

## 🔍 Monitoring FastAPI-Specific Metrics

### Custom FastAPI Metrics (Optional)

You can extend the monitoring with FastAPI-specific metrics:

```python
# metrics.py
from prometheus_client import Counter, Histogram
from fastapi import Request
import time

# FastAPI-specific metrics
fastapi_requests_total = Counter(
    'fastapi_requests_total',
    'Total FastAPI requests',
    ['method', 'endpoint', 'status']
)

fastapi_request_duration = Histogram(
    'fastapi_request_duration_seconds',
    'FastAPI request duration',
    ['method', 'endpoint']
)

# Middleware to collect metrics
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    fastapi_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    fastapi_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    return response
```

Add to your FastAPI app:

```python
# main.py
from fastapi import FastAPI
from metrics import metrics_middleware

app = FastAPI()

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    return await metrics_middleware(request, call_next)
```

## 🚨 Troubleshooting

### Common FastAPI Issues

1. **ASGI Application Error**
   ```bash
   # Ensure you're using the correct worker class
   worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
   ```

2. **Import Errors**
   ```bash
   # Make sure your app module is in the Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

3. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   lsof -i :9091
   ```

### Debug Mode

For development, you can use uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📈 Performance Tips

1. **Use Async Operations**
   ```python
   # main.py
   import asyncio
   from fastapi import FastAPI

   app = FastAPI()

   @app.get("/async-endpoint")
   async def async_endpoint():
       await asyncio.sleep(0.1)  # Simulate async work
       return {"message": "Async response"}
   ```

2. **Database Connection Pooling**
   ```python
   # database.py
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

   engine = create_async_engine(
       "postgresql+asyncpg://user:pass@localhost/db",
       pool_size=20,
       max_overflow=30
   )
   ```

3. **Caching with Redis**
   ```python
   # cache.py
   import redis.asyncio as redis

   redis_client = redis.Redis(host='localhost', port=6379, db=0)

   @app.get("/cached-data")
   async def get_cached_data():
       cached = await redis_client.get("my_key")
       if cached:
           return {"data": cached}
       # ... fetch and cache data
   ```

## 🔗 Related Documentation

- [Installation Guide](../installation.md)
- [Configuration Reference](../configuration.md)
- [Metrics Documentation](../metrics.md)
- [Django Integration](django-integration.md)
- [Flask Integration](flask-integration.md)

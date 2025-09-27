# Pyramid Integration

This guide shows how to integrate the Gunicorn Prometheus Exporter with Pyramid applications.

## Quick Start

### 1. Install Dependencies

```bash
pip install pyramid gunicorn gunicorn-prometheus-exporter
```

### 2. Create Pyramid Application

```python
# app.py
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config

@view_config(route_name='home', renderer='json')
def home(request):
    return {"message": "Hello World"}

@view_config(route_name='health', renderer='json')
def health(request):
    return {"status": "healthy"}

@view_config(route_name='users', renderer='json')
def get_users(request):
    return {"users": ["user1", "user2", "user3"]}

def main(global_config, **settings):
    config = Configurator(settings=settings)

    config.add_route('home', '/')
    config.add_route('health', '/health')
    config.add_route('users', '/api/users')

    config.scan()
    return config.make_wsgi_app()
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

# Pyramid optimizations
preload_app = True
worker_connections = 1000
```

### 4. Start Pyramid with Gunicorn

```bash
gunicorn -c gunicorn.conf.py app:main
```

## Advanced Configuration

### Production Pyramid Setup

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

### Pyramid Application with SQLAlchemy

```python
# app.py
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(120), unique=True, nullable=False)

engine = create_engine('sqlite:///app.db')
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

@view_config(route_name='home', renderer='json')
def home(request):
    return {"message": "Hello World"}

@view_config(route_name='health', renderer='json')
def health(request):
    return {"status": "healthy"}

@view_config(route_name='users', renderer='json', request_method='GET')
def get_users(request):
    session = Session()
    users = session.query(User).all()
    result = [{"id": u.id, "name": u.name, "email": u.email} for u in users]
    session.close()
    return result

@view_config(route_name='users', renderer='json', request_method='POST')
def create_user(request):
    session = Session()
    data = request.json_body
    user = User(name=data['name'], email=data['email'])
    session.add(user)
    session.commit()
    result = {"id": user.id, "name": user.name, "email": user.email}
    session.close()
    return result

def main(global_config, **settings):
    config = Configurator(settings=settings)

    config.add_route('home', '/')
    config.add_route('health', '/health')
    config.add_route('users', '/api/users')

    config.scan()
    return config.make_wsgi_app()
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
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:main"]
```

### requirements.txt

```txt
pyramid>=2.0.0
sqlalchemy>=1.4.0
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
      - app_data:/app/data

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  prometheus_data:
  app_data:
```

## Prometheus Configuration

### prometheus.yml

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "pyramid-gunicorn"
    static_configs:
      - targets: ["localhost:9091"]
    metrics_path: /metrics
    scrape_interval: 5s
```

## Monitoring Pyramid-Specific Metrics

### Custom Pyramid Metrics (Optional)

You can extend the monitoring with Pyramid-specific metrics:

```python
# metrics.py
from prometheus_client import Counter, Histogram
from pyramid.events import subscriber, NewRequest, NewResponse
import time

# Pyramid-specific metrics
pyramid_requests_total = Counter(
    'pyramid_requests_total',
    'Total Pyramid requests',
    ['method', 'route_name', 'status']
)

pyramid_request_duration = Histogram(
    'pyramid_request_duration_seconds',
    'Pyramid request duration',
    ['method', 'route_name']
)

@subscriber(NewRequest)
def new_request(event):
    event.request.start_time = time.time()

@subscriber(NewResponse)
def new_response(event):
    if hasattr(event.request, 'start_time'):
        duration = time.time() - event.request.start_time
        route_name = event.request.matched_route.name if event.request.matched_route else 'unknown'

        pyramid_request_duration.labels(
            method=event.request.method,
            route_name=route_name
        ).observe(duration)

        pyramid_requests_total.labels(
            method=event.request.method,
            route_name=route_name,
            status=event.response.status_code
        ).inc()
```

Add to your Pyramid app:

```python
# app.py
from pyramid.config import Configurator
from metrics import new_request, new_response

def main(global_config, **settings):
    config = Configurator(settings=settings)

    # Add event subscribers
    config.add_subscriber(new_request, 'pyramid.events.NewRequest')
    config.add_subscriber(new_response, 'pyramid.events.NewResponse')

    # Add routes
    config.add_route('home', '/')
    config.add_route('health', '/health')
    config.add_route('users', '/api/users')

    config.scan()
    return config.make_wsgi_app()
```

### Pyramid-SQLAlchemy Metrics

```python
# db_metrics.py
from prometheus_client import Counter, Histogram
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

# Database metrics
db_query_count = Counter(
    'pyramid_db_query_count',
    'Number of database queries',
    ['route_name']
)

db_query_duration = Histogram(
    'pyramid_db_query_duration_seconds',
    'Database query duration',
    ['route_name']
)

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if hasattr(context, '_query_start_time'):
        duration = time.time() - context._query_start_time
        route_name = getattr(context, 'route_name', 'unknown')

        db_query_count.labels(route_name=route_name).inc()
        db_query_duration.labels(route_name=route_name).observe(duration)
```

## Troubleshooting

### Common Pyramid Issues

1. **Import Errors**

   ```bash
   # Ensure your app module is in the Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Database Connection Issues**

   ```python
   # Initialize database tables
   Base.metadata.create_all(engine)
   ```

3. **Route Configuration**
   ```python
   # Ensure routes are added before scanning
   config.add_route('home', '/')
   config.scan()  # Scan after adding routes
   ```

### Debug Mode

For development, you can use Pyramid's built-in server:

```bash
pserve development.ini --reload
```

## 📈 Performance Tips

1. **Use Pyramid Caching**

   ```python
   from pyramid_beaker import session_factory_from_settings

   session_factory = session_factory_from_settings(settings)
   config.set_session_factory(session_factory)
   ```

2. **Database Connection Pooling**

   ```python
   engine = create_engine(
       'postgresql://user:pass@localhost/db',
       pool_size=20,
       max_overflow=30,
       pool_recycle=3600
   )
   ```

3. **Use Pyramid Resources**

   ```python
   from pyramid.resource import Resource

   class UserResource(Resource):
       def __init__(self, name, parent):
           super().__init__(name, parent)
           self.name = name

   @view_config(context=UserResource, renderer='json')
   def user_view(context, request):
       return {"name": context.name}
   ```

4. **Optimize JSON Rendering**

   ```python
   from pyramid.renderers import JSON

   json_renderer = JSON()
   config.add_renderer('json', json_renderer)
   ```

## 🔗 Related Documentation

- [Installation Guide](../installation.md)
- [Configuration Reference](../config/configuration.md)
- [Metrics Documentation](../metrics/index.md)
- [Django Integration](django-integration.md)
- [FastAPI Integration](fastapi-integration.md)
- [Flask Integration](flask-integration.md)

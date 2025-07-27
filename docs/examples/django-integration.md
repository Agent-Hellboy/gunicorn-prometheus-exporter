# Django Integration

This guide shows how to integrate the Gunicorn Prometheus Exporter with Django applications.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install django gunicorn gunicorn-prometheus-exporter
```

### 2. Create Django Project (if needed)

```bash
django-admin startproject myproject
cd myproject
```

### 3. Create Gunicorn Configuration

Create `gunicorn.conf.py` in your Django project root:

```python
# gunicorn.conf.py
import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Server settings
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
master_class = "gunicorn_prometheus_exporter.PrometheusMaster"

# Environment variables
raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc",
    "GUNICORN_WORKERS=4",
    "DJANGO_SETTINGS_MODULE=myproject.settings"
]

# Prometheus hooks
when_ready = "gunicorn_prometheus_exporter.default_when_ready"
on_starting = "gunicorn_prometheus_exporter.default_on_starting"
worker_int = "gunicorn_prometheus_exporter.default_worker_int"
on_exit = "gunicorn_prometheus_exporter.default_on_exit"

# Django-specific settings
preload_app = True
```

### 4. Start Django with Gunicorn

```bash
gunicorn -c gunicorn.conf.py myproject.wsgi:application
```

## 🔧 Advanced Configuration

### Production Django Setup

```python
# gunicorn.conf.py
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

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
    "DJANGO_SETTINGS_MODULE=myproject.settings",
    "GUNICORN_TIMEOUT=30"
]

# Prometheus hooks
when_ready = "gunicorn_prometheus_exporter.default_when_ready"
on_starting = "gunicorn_prometheus_exporter.default_on_starting"
worker_int = "gunicorn_prometheus_exporter.default_worker_int"
on_exit = "gunicorn_prometheus_exporter.default_on_exit"

# Django optimizations
preload_app = True
max_requests = 1000
max_requests_jitter = 50
worker_connections = 1000

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
```

### Django Settings Configuration

Add to your `settings.py`:

```python
# settings.py

# Static files (if serving with Django)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
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

# Copy Django project
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/prometheus_multiproc
RUN mkdir -p staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose ports
EXPOSE 8000 9091

# Set environment variables
ENV PROMETHEUS_METRICS_PORT=9091
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
ENV GUNICORN_WORKERS=4
ENV DJANGO_SETTINGS_MODULE=myproject.settings

# Start with gunicorn
CMD ["gunicorn", "-c", "gunicorn.conf.py", "myproject.wsgi:application"]
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
      - DJANGO_SETTINGS_MODULE=myproject.settings
    volumes:
      - prometheus_data:/tmp/prometheus_multiproc
      - static_files:/app/staticfiles

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  prometheus_data:
  static_files:
```

## 📊 Prometheus Configuration

### prometheus.yml

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'django-gunicorn'
    static_configs:
      - targets: ['localhost:9091']
    metrics_path: /metrics
    scrape_interval: 5s
```

## 🔍 Monitoring Django-Specific Metrics

### Custom Django Metrics (Optional)

You can extend the monitoring with Django-specific metrics:

```python
# myproject/metrics.py
from prometheus_client import Counter, Histogram
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

# Django-specific metrics
django_requests_total = Counter(
    'django_requests_total',
    'Total Django requests',
    ['method', 'endpoint', 'status']
)

django_request_duration = Histogram(
    'django_request_duration_seconds',
    'Django request duration',
    ['method', 'endpoint']
)

class PrometheusMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            django_request_duration.labels(
                method=request.method,
                endpoint=request.path
            ).observe(duration)

            django_requests_total.labels(
                method=request.method,
                endpoint=request.path,
                status=response.status_code
            ).inc()

        return response
```

Add to `settings.py`:

```python
MIDDLEWARE = [
    'myproject.metrics.PrometheusMiddleware',
    # ... other middleware
]
```

## 🚨 Troubleshooting

### Common Django Issues

1. **Static Files Not Found**
   ```bash
   # Collect static files
   python manage.py collectstatic

   # Or serve with nginx/apache
   ```

2. **Database Connection Issues**
   ```python
   # Ensure database is migrated
   python manage.py migrate
   ```

3. **Settings Module Not Found**
   ```bash
   # Set the correct settings module
   export DJANGO_SETTINGS_MODULE=myproject.settings
   ```

### Debug Mode

For development, you can enable Django debug mode:

```python
# settings.py
DEBUG = True
ALLOWED_HOSTS = ['*']
```

## 📈 Performance Tips

1. **Use Database Connection Pooling**
   ```python
   # settings.py
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'mydb',
           'CONN_MAX_AGE': 600,  # 10 minutes
       }
   }
   ```

2. **Enable Caching**
   ```python
   # settings.py
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```

3. **Optimize Static Files**
   ```python
   # settings.py
   STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
   ```

## 🔗 Related Documentation

- [Installation Guide](../installation.md)
- [Configuration Reference](../configuration.md)
- [Metrics Documentation](../metrics.md)
- [FastAPI Integration](fastapi-integration.md)
- [Flask Integration](flask-integration.md)

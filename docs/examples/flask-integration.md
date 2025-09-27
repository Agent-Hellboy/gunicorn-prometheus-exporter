# Flask Integration

This guide shows how to integrate the Gunicorn Prometheus Exporter with Flask applications.

## Quick Start

### 1. Install Dependencies

```bash
pip install flask gunicorn gunicorn-prometheus-exporter
```

### 2. Create Flask Application

```python
# app.py
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Hello World"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/users')
def get_users():
    return jsonify({"users": ["user1", "user2", "user3"]})

if __name__ == '__main__':
    app.run(debug=True)
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

# Flask optimizations
preload_app = True
worker_connections = 1000
```

### 4. Start Flask with Gunicorn

```bash
gunicorn -c gunicorn.conf.py app:app
```

## Advanced Configuration

### Production Flask Setup

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

### Flask Application with Extensions

```python
# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import time

app = Flask(__name__)

# Configure Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Routes
@app.route('/')
def home():
    return jsonify({"message": "Hello World"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "name": u.name, "email": u.email} for u in users])

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    user = User(name=data['name'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "name": user.name, "email": user.email}), 201

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
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
ENV FLASK_ENV=production

# Start with gunicorn
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
```

### requirements.txt

```txt
flask>=2.0.0
flask-cors>=3.0.10
flask-sqlalchemy>=2.5.0
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
      - FLASK_ENV=production
    volumes:
      - prometheus_data:/tmp/prometheus_multiproc
      - app_data:/app/instance

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
  - job_name: "flask-gunicorn"
    static_configs:
      - targets: ["your-app-host:9091"] # Replace with your application hostname
    metrics_path: /metrics
    scrape_interval: 5s
```

## Monitoring Flask-Specific Metrics

### Custom Flask Metrics (Optional)

You can extend the monitoring with Flask-specific metrics:

```python
# metrics.py
from prometheus_client import Counter, Histogram
from flask import request, g
import time

# Flask-specific metrics
flask_requests_total = Counter(
    'flask_requests_total',
    'Total Flask requests',
    ['method', 'endpoint', 'status']
)

flask_request_duration = Histogram(
    'flask_request_duration_seconds',
    'Flask request duration',
    ['method', 'endpoint']
)

# Middleware to collect metrics
def metrics_middleware():
    g.start_time = time.time()

def after_request(response):
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        flask_request_duration.labels(
            method=request.method,
            endpoint=request.endpoint
        ).observe(duration)

        flask_requests_total.labels(
            method=request.method,
            endpoint=request.endpoint,
            status=response.status_code
        ).inc()

    return response
```

Add to your Flask app:

```python
# app.py
from flask import Flask
from metrics import metrics_middleware, after_request

app = Flask(__name__)

@app.before_request
def before_request():
    metrics_middleware()

@app.after_request
def after_request_handler(response):
    return after_request(response)
```

### Flask-SQLAlchemy Metrics

```python
# db_metrics.py
from prometheus_client import Counter, Histogram
from flask_sqlalchemy import get_debug_queries

# Database metrics
db_query_count = Counter(
    'flask_db_query_count',
    'Number of database queries',
    ['endpoint']
)

db_query_duration = Histogram(
    'flask_db_query_duration_seconds',
    'Database query duration',
    ['endpoint']
)

def collect_db_metrics():
    queries = get_debug_queries()
    for query in queries:
        db_query_count.labels(endpoint=query.endpoint).inc()
        db_query_duration.labels(endpoint=query.endpoint).observe(query.duration)

# Add to your app
@app.after_request
def after_request(response):
    collect_db_metrics()
    return response
```

## Troubleshooting

### Common Flask Issues

1. **Application Context Error**

   ```python
   # Ensure app context is available
   with app.app_context():
       # Your code here
       pass
   ```

2. **Database Connection Issues**

   ```python
   # Initialize database
   with app.app_context():
       db.create_all()
   ```

3. **Static Files Not Found**
   ```python
   # Configure static files
   app = Flask(__name__, static_folder='static', static_url_path='/static')
   ```

### Debug Mode

For development, you can use Flask's built-in server:

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
flask run --host=0.0.0.0 --port=8000
```

## 📈 Performance Tips

1. **Use Flask-Caching**

   ```python
   from flask_caching import Cache

   cache = Cache(app, config={'CACHE_TYPE': 'redis'})

   @app.route('/api/data')
   @cache.cached(timeout=300)
   def get_data():
       # Expensive operation
       return jsonify(data)
   ```

2. **Database Connection Pooling**

   ```python
   # config.py
   SQLALCHEMY_ENGINE_OPTIONS = {
       'pool_size': 20,
       'pool_recycle': 3600,
       'pool_pre_ping': True
   }
   ```

3. **Use Blueprints for Large Applications**

   ```python
   # users.py
   from flask import Blueprint

   users_bp = Blueprint('users', __name__)

   @users_bp.route('/users')
   def get_users():
       return jsonify(users)

   # app.py
   from users import users_bp
   app.register_blueprint(users_bp, url_prefix='/api')
   ```

4. **Optimize JSON Serialization**

   ```python
   from flask import jsonify
   import json

   # Use custom JSON encoder for better performance
   class CustomJSONEncoder(json.JSONEncoder):
       def default(self, obj):
           if hasattr(obj, 'to_dict'):
               return obj.to_dict()
           return super().default(obj)

   app.json_encoder = CustomJSONEncoder
   ```

## 🔗 Related Documentation

- [Installation Guide](../installation.md)
- [Configuration Reference](../config/configuration.md)
- [Metrics Documentation](../metrics/index.md)
- [Django Integration](django-integration.md)
- [FastAPI Integration](fastapi-integration.md)

# Troubleshooting Guide

Common issues and solutions when using the Gunicorn Prometheus Exporter.

## Common Issues

### 1. Port Already in Use

**Error**: `OSError: [Errno 98] Address already in use`

**Solution**:
```bash
# Check what's using the port
lsof -i :9091

# Kill the process using the port
sudo kill -9 <PID>

# Or use a different port
export PROMETHEUS_METRICS_PORT=9092
```

**Prevention**:
```python
# gunicorn.conf.py
raw_env = [
    "PROMETHEUS_METRICS_PORT=9092",  # Use different port
    # ... other env vars
]
```

### 2. Permission Denied for Multiprocess Directory

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
```bash
# Create directory with proper permissions
sudo mkdir -p /tmp/prometheus_multiproc
sudo chown $USER:$USER /tmp/prometheus_multiproc
sudo chmod 755 /tmp/prometheus_multiproc

# Or use a different directory
export PROMETHEUS_MULTIPROC_DIR=/home/$USER/prometheus_multiproc
```

**Prevention**:
```python
# gunicorn.conf.py
raw_env = [
    "PROMETHEUS_MULTIPROC_DIR=/home/user/prometheus_multiproc",
    # ... other env vars
]
```

### 3. Environment Variables Not Set

**Error**: `ValueError: Environment variable PROMETHEUS_METRICS_PORT must be set`

**Solution**:
```bash
# Set required environment variables
export PROMETHEUS_METRICS_PORT=9091
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
export GUNICORN_WORKERS=4
```

**Prevention**:
```python
# gunicorn.conf.py
raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc",
    "GUNICORN_WORKERS=4"
]
```

### 4. Metrics Not Appearing

**Issue**: No metrics visible at `/metrics` endpoint

**Diagnosis**:
```bash
# Check if metrics server is running
curl http://YOUR_BIND_ADDRESS:9091/metrics  # Replace with your configured address

# Check Gunicorn logs
tail -f gunicorn.log

# Check multiprocess directory
ls -la /tmp/prometheus_multiproc/
```

**Solutions**:

1. **Verify Configuration**:
   ```python
   from gunicorn_prometheus_exporter.config import ExporterConfig

   config = ExporterConfig()

### 5. Async Worker Issues

**Issue**: ImportError or TypeError with async workers (Eventlet, Gevent, Tornado)

**Common Errors**:
```bash
# Missing dependencies
ImportError: No module named 'eventlet'
ImportError: No module named 'gevent'
ImportError: No module named 'tornado'

# Method signature issues
TypeError: handle_request() missing required arguments
```

**Solutions**:

1. **Install Required Dependencies**:
   ```bash
   # For Eventlet workers
   pip install eventlet

   # For Gevent workers
   pip install gevent

   # For Tornado workers
   pip install tornado
   ```

2. **Verify Worker Class Configuration**:
   ```python
   # gunicorn.conf.py
   worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"  # Eventlet
   worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"    # Gevent
   worker_class = "gunicorn_prometheus_exporter.PrometheusTornadoWorker"   # Tornado
   ```

3. **Check Application Compatibility**:
   ```python
   # Ensure your app is WSGI-compatible
   # For async workers, use async_app.py from examples
   ```

4. **Verify Metrics Collection**:
   ```bash
   # Test metrics endpoint
   curl http://YOUR_BIND_ADDRESS:9091/metrics | grep worker_requests_total
   ```
   if config.validate():
       print("Configuration is valid")
   else:
       print("Configuration has errors")
   ```

2. **Check Worker Class**:
   ```python
   # gunicorn.conf.py
   worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
   master_class = "gunicorn_prometheus_exporter.PrometheusMaster"
   ```

3. **Verify Hooks**:
   ```python
   # gunicorn.conf.py
   when_ready = "gunicorn_prometheus_exporter.default_when_ready"
   on_starting = "gunicorn_prometheus_exporter.default_on_starting"
   worker_int = "gunicorn_prometheus_exporter.default_worker_int"
   on_exit = "gunicorn_prometheus_exporter.default_on_exit"
   ```

### 5. Redis Connection Issues

**Error**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
sudo systemctl start redis

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

**Configuration**:
```python
# gunicorn.conf.py
raw_env = [
    "REDIS_ENABLED=true",
    "REDIS_HOST=your-redis-host",  # Configure for your environment
    "REDIS_PORT=6379",
    "REDIS_PASSWORD=your_password",  # if needed
]
```

### 6. Worker Restart Issues

**Issue**: Workers restarting frequently

**Diagnosis**:
```bash
# Check worker logs
tail -f gunicorn.log | grep "worker"

# Check system resources
htop
free -h
df -h
```

**Solutions**:

1. **Increase Worker Timeout**:
   ```python
   # gunicorn.conf.py
   raw_env = [
       "GUNICORN_TIMEOUT=60",  # Increase timeout
   ]
   ```

2. **Reduce Worker Count**:
   ```python
   # gunicorn.conf.py
   workers = 2  # Reduce from 4 to 2
   raw_env = [
       "GUNICORN_WORKERS=2",
   ]
   ```

3. **Check Memory Usage**:
   ```bash
   # Monitor memory usage
   watch -n 1 'free -h'
   ```

### 7. Import Errors

**Error**: `ModuleNotFoundError: No module named 'gunicorn_prometheus_exporter'`

**Solution**:
```bash
# Install the package
pip install gunicorn-prometheus-exporter

# Or install from source
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter.git
cd gunicorn-prometheus-exporter
pip install -e .
```

**Verification**:
```bash
# Check if package is installed
python -c "import gunicorn_prometheus_exporter; print('Package installed')"
```

### 8. Configuration Validation Errors

**Error**: Configuration validation fails

**Diagnosis**:
```python
from gunicorn_prometheus_exporter.config import ExporterConfig

config = ExporterConfig()
config.print_config()  # Show current configuration
print(f"Valid: {config.validate()}")
```

**Common Issues**:

1. **Invalid Port**:
   ```python
   # Port must be between 1 and 65535
   export PROMETHEUS_METRICS_PORT=9091  # Valid
   export PROMETHEUS_METRICS_PORT=99999  # Invalid
   ```

2. **Invalid Worker Count**:
   ```python
   # Worker count must be positive
   export GUNICORN_WORKERS=4  # Valid
   export GUNICORN_WORKERS=0  # Invalid
   ```

3. **Invalid Directory**:
   ```python
   # Directory must be writable
   export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc  # Valid
   export PROMETHEUS_MULTIPROC_DIR=/nonexistent  # Invalid
   ```

## Debug Mode

### Enable Debug Logging

```python
# gunicorn.conf.py
loglevel = "debug"
accesslog = "-"
errorlog = "-"
```

### Verbose Configuration

```python
# gunicorn.conf.py
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Server settings
bind = "0.0.0.0:8000"
workers = 2  # Use fewer workers for debugging
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
master_class = "gunicorn_prometheus_exporter.PrometheusMaster"

# Environment variables
raw_env = [
    "PROMETHEUS_METRICS_PORT=9091",
    "PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc",
    "GUNICORN_WORKERS=2"
]

# Prometheus hooks
when_ready = "gunicorn_prometheus_exporter.default_when_ready"
on_starting = "gunicorn_prometheus_exporter.default_on_starting"
worker_int = "gunicorn_prometheus_exporter.default_worker_int"
on_exit = "gunicorn_prometheus_exporter.default_on_exit"

# Debug settings
preload_app = False  # Disable for debugging
```

### Test Configuration

```bash
# Test configuration without starting server
python -c "
from gunicorn_prometheus_exporter.config import ExporterConfig
config = ExporterConfig()
print('Configuration:')
config.print_config()
print(f'Valid: {config.validate()}')
"
```

## Monitoring and Diagnostics

### Health Check Script

```python
# health_check.py
import requests
import os
import sys

def check_metrics_endpoint():
    """Check if metrics endpoint is accessible."""
    try:
        port = os.environ.get('PROMETHEUS_METRICS_PORT', '9091')
        response = requests.get(f'http://YOUR_BIND_ADDRESS:{port}/metrics', timeout=5)  # Replace with your configured address
        if response.status_code == 200:
            print(f"✅ Metrics endpoint accessible on port {port}")
            return True
        else:
            print(f"❌ Metrics endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Metrics endpoint not accessible: {e}")
        return False

def check_multiproc_dir():
    """Check if multiprocess directory exists and is writable."""
    mp_dir = os.environ.get('PROMETHEUS_MULTIPROC_DIR', '/tmp/prometheus_multiproc')
    if os.path.exists(mp_dir) and os.access(mp_dir, os.W_OK):
        print(f"✅ Multiprocess directory {mp_dir} is writable")
        return True
    else:
        print(f"❌ Multiprocess directory {mp_dir} is not writable")
        return False

def check_environment_variables():
    """Check if required environment variables are set."""
    required_vars = [
        'PROMETHEUS_METRICS_PORT',
        'PROMETHEUS_MULTIPROC_DIR',
        'GUNICORN_WORKERS'
    ]

    all_set = True
    for var in required_vars:
        if os.environ.get(var):
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is not set")
            all_set = False

    return all_set

if __name__ == '__main__':
    print("Gunicorn Prometheus Exporter Health Check")
    print("=" * 50)

    env_ok = check_environment_variables()
    mp_dir_ok = check_multiproc_dir()
    metrics_ok = check_metrics_endpoint()

    print("\nSummary:")
    if all([env_ok, mp_dir_ok, metrics_ok]):
        print("✅ All checks passed")
        sys.exit(0)
    else:
        print("❌ Some checks failed")
        sys.exit(1)
```

### Log Analysis Script

```python
# log_analyzer.py
import re
import sys
from collections import defaultdict

def analyze_gunicorn_logs(log_file):
    """Analyze Gunicorn logs for common issues."""
    issues = defaultdict(list)

    with open(log_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            # Check for worker restarts
            if 'worker restarting' in line:
                issues['worker_restarts'].append((line_num, line.strip()))

            # Check for connection errors
            if 'connection error' in line.lower():
                issues['connection_errors'].append((line_num, line.strip()))

            # Check for timeout errors
            if 'timeout' in line.lower():
                issues['timeout_errors'].append((line_num, line.strip()))

            # Check for memory issues
            if 'memory' in line.lower() and 'error' in line.lower():
                issues['memory_errors'].append((line_num, line.strip()))

    return issues

def print_analysis(issues):
    """Print analysis results."""
    print("Gunicorn Log Analysis")
    print("=" * 50)

    for issue_type, occurrences in issues.items():
        if occurrences:
            print(f"\n❌ {issue_type.replace('_', ' ').title()}:")
            for line_num, line in occurrences[:5]:  # Show first 5
                print(f"  Line {line_num}: {line}")
            if len(occurrences) > 5:
                print(f"  ... and {len(occurrences) - 5} more")
        else:
            print(f"\n✅ No {issue_type.replace('_', ' ')} found")

if __name__ == '__main__':
    log_file = sys.argv[1] if len(sys.argv) > 1 else 'gunicorn.log'

    try:
        issues = analyze_gunicorn_logs(log_file)
        print_analysis(issues)
    except FileNotFoundError:
        print(f"❌ Log file {log_file} not found")
        sys.exit(1)
```

## Performance Optimization

### Memory Optimization

```python
# gunicorn.conf.py
# Memory optimization settings
max_requests = 1000
max_requests_jitter = 50
worker_connections = 1000
worker_tmp_dir = "/dev/shm"  # Use RAM for temporary files
```

### CPU Optimization

```python
# gunicorn.conf.py
# CPU optimization settings
workers = 4  # Match CPU cores
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
preload_app = True  # Preload application
```

### Network Optimization

```python
# gunicorn.conf.py
# Network optimization settings
keepalive = 2
worker_connections = 1000
backlog = 2048
```

## Getting Help

### Before Asking for Help

1. **Check the logs**: Look at Gunicorn and application logs
2. **Verify configuration**: Use the health check script
3. **Test minimal setup**: Try with basic configuration first
4. **Check system resources**: Monitor CPU, memory, and disk usage

### Information to Include

When reporting issues, include:

1. **Environment**:
   - Python version
   - Gunicorn version
   - Operating system
   - Package version

2. **Configuration**:
   - `gunicorn.conf.py` content
   - Environment variables
   - Application type (Django, Flask, etc.)

3. **Error Details**:
   - Full error message
   - Stack trace
   - Log files

4. **Steps to Reproduce**:
   - Installation steps
   - Configuration steps
   - Commands run

### Support Channels

- **GitHub Issues**: [Create an issue](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/issues)
- **Documentation**: Check this troubleshooting guide
- **Examples**: Review framework-specific examples

## Related Documentation

- [Installation Guide](installation.md)
- [Configuration Reference](configuration.md)
- [Metrics Documentation](metrics.md)
- [API Reference](api-reference.md)
- [Framework Examples](examples/)

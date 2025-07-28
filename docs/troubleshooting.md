# Troubleshooting Guide

Common issues and solutions for the Gunicorn Prometheus Exporter.

## 🚨 Common Issues

### Port Already in Use

**Error:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**
1. Change the metrics port in your configuration:
```python
# In gunicorn.conf.py
import os
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9091")  # Use different port
```

2. Or kill the process using the port:
```bash
# Find the process
lsof -i :9090

# Kill the process
kill -9 <PID>
```

### Permission Denied

**Error:**
```
PermissionError: [Errno 13] Permission denied
```

**Solution:**
1. Check multiprocess directory permissions:
```bash
# Create directory with proper permissions
mkdir -p /tmp/prometheus_multiproc
chmod 755 /tmp/prometheus_multiproc
```

2. Or use a different directory:
```python
# In gunicorn.conf.py
import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/var/tmp/prometheus_multiproc")
```

### Import Errors for Async Workers

**Error:**
```
ModuleNotFoundError: No module named 'eventlet'
```

**Solution:**
1. Install the required dependencies:
```bash
# For eventlet workers
pip install gunicorn-prometheus-exporter[eventlet]

# For gevent workers
pip install gunicorn-prometheus-exporter[gevent]

# For tornado workers
pip install gunicorn-prometheus-exporter[tornado]

# Or install all async dependencies
pip install gunicorn-prometheus-exporter[async]
```

2. Verify the installation:
```bash
python -c "import eventlet; print('eventlet available')"
```

### Metrics Not Updating

**Issue:** Metrics endpoint shows stale or no data.

**Solutions:**

1. **Check environment variables:**
```bash
# Verify all required variables are set
echo $PROMETHEUS_MULTIPROC_DIR
echo $PROMETHEUS_METRICS_PORT
echo $PROMETHEUS_BIND_ADDRESS
echo $GUNICORN_WORKERS
```

2. **Check multiprocess directory:**
```bash
# Verify directory exists and is writable
ls -la /tmp/prometheus_multiproc/
```

3. **Restart Gunicorn:**
```bash
# Kill existing process
pkill -f gunicorn

# Start fresh
gunicorn -c gunicorn.conf.py app:app
```

### Worker Type Errors

**Error:**
```
TypeError: 'NoneType' object is not callable
```

**Solution:**
1. Verify worker class is correctly specified:
```python
# In gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"  # Sync
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"  # Thread
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"  # Eventlet
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"  # Gevent
worker_class = "gunicorn_prometheus_exporter.PrometheusTornadoWorker"  # Tornado
```

2. Check if async dependencies are installed:
```bash
# For eventlet workers
python -c "import eventlet"

# For gevent workers
python -c "import gevent"

# For tornado workers
python -c "import tornado"
```

## 🔧 Configuration Issues

### Environment Variables Not Set

**Error:**
```
ValueError: Environment variable PROMETHEUS_METRICS_PORT must be set in production
```

**Solution:**
1. Set environment variables in your configuration:
```python
# In gunicorn.conf.py
import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.environ.setdefault("PROMETHEUS_METRICS_PORT", "9090")
os.environ.setdefault("PROMETHEUS_BIND_ADDRESS", "0.0.0.0")
os.environ.setdefault("GUNICORN_WORKERS", "2")
```

2. Or export them in your shell:
```bash
export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc"
export PROMETHEUS_METRICS_PORT="9090"
export PROMETHEUS_BIND_ADDRESS="0.0.0.0"
export GUNICORN_WORKERS="2"
```

### Redis Configuration Issues

**Error:**
```
ConnectionError: Error connecting to Redis
```

**Solution:**
1. Check Redis server is running:
```bash
redis-cli ping
```

2. Verify Redis configuration:
```python
# In gunicorn.conf.py
import os
os.environ.setdefault("REDIS_ENABLED", "true")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_DB", "0")
```

3. Test Redis connection:
```bash
redis-cli -h localhost -p 6379 ping
```

## 🐛 Debug Mode

### Enable Debug Logging

```python
# In gunicorn.conf.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set specific logger
logging.getLogger('gunicorn_prometheus_exporter').setLevel(logging.DEBUG)
```

### Verbose Gunicorn Output

```bash
# Start with verbose logging
gunicorn -c gunicorn.conf.py app:app --log-level debug
```

### Check Metrics Endpoint

```bash
# Test metrics endpoint
curl http://0.0.0.0:9090/metrics

# Check for specific metrics
curl http://0.0.0.0:9090/metrics | grep gunicorn_worker

# Check for errors
curl http://0.0.0.0:9090/metrics | grep -i error
```

## 🔍 Diagnostic Commands

### Check Process Status

```bash
# List Gunicorn processes
ps aux | grep gunicorn

# Check open ports
netstat -tlnp | grep 9090

# Check multiprocess directory
ls -la /tmp/prometheus_multiproc/
```

### Monitor Metrics

```bash
# Watch metrics in real-time
watch -n 1 'curl -s http://0.0.0.0:9090/metrics | grep gunicorn_worker_requests_total'

# Monitor specific worker
watch -n 1 'curl -s http://0.0.0.0:9090/metrics | grep "worker_id=\"worker_1\""'
```

### Test Worker Types

```bash
# Test sync worker
gunicorn --config example/gunicorn_simple.conf.py example/app:app

# Test thread worker
gunicorn --config example/gunicorn_thread_worker.conf.py example/app:app

# Test eventlet worker
gunicorn --config example/gunicorn_eventlet_async.conf.py example/async_app:app

# Test gevent worker
gunicorn --config example/gunicorn_gevent_async.conf.py example/async_app:app

# Test tornado worker
gunicorn --config example/gunicorn_tornado_async.conf.py example/async_app:app
```

## 🚨 Async Worker Issues

### Eventlet Worker Problems

**Common Issues:**
1. **Import errors**: Install `eventlet` package
2. **WSGI compatibility**: Use async-compatible application
3. **Worker connections**: Set appropriate `worker_connections`

**Solution:**
```python
# In gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
worker_connections = 1000

# Use async-compatible app
app = "example.async_app:app"
```

### Gevent Worker Problems

**Common Issues:**
1. **Import errors**: Install `gevent` package
2. **Monkey patching**: May conflict with other libraries
3. **Worker connections**: Set appropriate `worker_connections`

**Solution:**
```python
# In gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusGeventWorker"
worker_connections = 1000

# Use async-compatible app
app = "example.async_app:app"
```

### Tornado Worker Problems

**Common Issues:**
1. **Import errors**: Install `tornado` package
2. **IOLoop conflicts**: May conflict with other async libraries
3. **Application compatibility**: Requires async-compatible app

**Solution:**
```python
# In gunicorn.conf.py
worker_class = "gunicorn_prometheus_exporter.PrometheusTornadoWorker"

# Use async-compatible app
app = "example.async_app:app"
```

## 🔧 Performance Issues

### High Memory Usage

**Symptoms:**
- Memory usage increases over time
- Workers restart frequently

**Solutions:**
1. **Reduce worker count:**
```python
# In gunicorn.conf.py
workers = 2  # Reduce from default
```

2. **Enable metric cleanup:**
```python
# In gunicorn.conf.py
import os
os.environ.setdefault("CLEANUP_DB_FILES", "true")
```

3. **Monitor memory metrics:**
```bash
# Check memory usage
curl http://0.0.0.0:9090/metrics | grep gunicorn_worker_memory_bytes
```

### High CPU Usage

**Symptoms:**
- CPU usage spikes during requests
- Slow response times

**Solutions:**
1. **Use appropriate worker type:**
```python
# For I/O-bound apps
worker_class = "gunicorn_prometheus_exporter.PrometheusThreadWorker"

# For async apps
worker_class = "gunicorn_prometheus_exporter.PrometheusEventletWorker"
```

2. **Monitor CPU metrics:**
```bash
# Check CPU usage
curl http://0.0.0.0:9090/metrics | grep gunicorn_worker_cpu_percent
```

### Slow Metrics Collection

**Symptoms:**
- Metrics endpoint responds slowly
- High latency in metric updates

**Solutions:**
1. **Reduce metric collection frequency:**
```python
# Update worker metrics less frequently
def worker_int(worker):
    # Only update every 10 seconds
    if hasattr(worker, '_last_metrics_update'):
        if time.time() - worker._last_metrics_update < 10:
            return
    worker._last_metrics_update = time.time()
    worker.update_worker_metrics()
```

2. **Use Redis forwarding for aggregation:**
```python
# Enable Redis forwarding
import os
os.environ.setdefault("REDIS_ENABLED", "true")
```

## 🛠️ Recovery Procedures

### Clean Restart

```bash
# Stop all Gunicorn processes
pkill -f gunicorn

# Clean multiprocess directory
rm -rf /tmp/prometheus_multiproc/*

# Restart with fresh configuration
gunicorn -c gunicorn.conf.py app:app
```

### Emergency Recovery

```bash
# Force kill all processes
pkill -9 -f gunicorn

# Clean all temporary files
rm -rf /tmp/prometheus_multiproc/*
rm -rf /tmp/gunicorn*

# Restart with minimal configuration
gunicorn --bind 0.0.0.0:8000 --workers 1 app:app
```

### Data Recovery

```bash
# Backup metrics data
cp -r /tmp/prometheus_multiproc /backup/prometheus_multiproc_$(date +%Y%m%d_%H%M%S)

# Restore from backup
cp -r /backup/prometheus_multiproc_latest/* /tmp/prometheus_multiproc/
```

## 📞 Getting Help

### Debug Information

When reporting issues, include:

1. **Gunicorn version:**
```bash
gunicorn --version
```

2. **Python version:**
```bash
python --version
```

3. **Installed packages:**
```bash
pip list | grep gunicorn
```

4. **Configuration file:**
```bash
cat gunicorn.conf.py
```

5. **Error logs:**
```bash
gunicorn -c gunicorn.conf.py app:app --log-level debug 2>&1
```

6. **Metrics endpoint:**
```bash
curl http://0.0.0.0:9090/metrics
```

### Support Channels

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check the [API Reference](api-reference.md)
- **Examples**: See the `example/` directory for working configurations

---

**For more help, see the [Installation Guide](installation.md) and [Configuration Reference](configuration.md).**

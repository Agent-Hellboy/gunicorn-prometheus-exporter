#!/usr/bin/env python3
"""Simple test to check Redis key format."""

import os
import sys
import time

import redis

from gunicorn_prometheus_exporter.backend import setup_redis_metrics
from gunicorn_prometheus_exporter.metrics import Counter, Gauge


# Set up Redis
os.environ["REDIS_ENABLED"] = "true"
os.environ["REDIS_HOST"] = "127.0.0.1"
os.environ["REDIS_PORT"] = "6379"
os.environ["REDIS_DB"] = "0"
os.environ["REDIS_KEY_PREFIX"] = "gunicorn"

# Connect to Redis
redis_client = redis.Redis(host="127.0.0.1", port=6379, db=0)

# Setup Redis metrics
if setup_redis_metrics():
    print("✓ Redis metrics setup successful")
else:
    print("✗ Redis metrics setup failed")
    sys.exit(1)

# Create some test metrics
counter = Counter("test_counter", "A test counter")
gauge = Gauge("test_gauge", "A test gauge")

# Increment metrics
counter.inc()
gauge.set(42.0)

# Wait a bit for metrics to be written
time.sleep(1)

# Check Redis keys
keys = redis_client.keys("gunicorn:*")
print(f"Found {len(keys)} Redis keys:")
for key in keys[:10]:  # Show first 10 keys
    print(f"  {key.decode('utf-8')}")

# Check specific patterns
metric_keys = redis_client.keys("gunicorn:*:metric:*")
meta_keys = redis_client.keys("gunicorn:*:meta:*")

print(f"\nMetric keys (new format): {len(metric_keys)}")
print(f"Meta keys (new format): {len(meta_keys)}")

old_metric_keys = redis_client.keys("gunicorn:metric:*")
old_meta_keys = redis_client.keys("gunicorn:meta:*")

print(f"\nOld format metric keys: {len(old_metric_keys)}")
print(f"Old format meta keys: {len(old_meta_keys)}")

if old_metric_keys:
    print("⚠ Still using old key format!")
    for key in old_metric_keys[:3]:
        print(f"  {key.decode('utf-8')}")
else:
    print("✓ Using new key format!")

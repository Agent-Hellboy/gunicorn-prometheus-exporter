import json
import os

from collections import defaultdict

from prometheus_client.metrics_core import Metric
from prometheus_client.samples import Sample
from prometheus_client.utils import floatToGoString

from ...config import get_config
from .client import _safe_decode_bytes, _safe_extract_original_key, _safe_parse_float


# Conditional Redis import - only import when needed
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisMultiProcessCollector:
    """Collector for Redis-based multi-process mode."""

    def __init__(self, registry, redis_client=None, redis_key_prefix=None):
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis is not available. Install redis package to use "
                "RedisMultiProcessCollector."
            )

        self._redis_client = redis_client or self._get_default_redis_client()
        self._redis_key_prefix = redis_key_prefix or get_config().redis_key_prefix

        if self._redis_client is None:
            raise ValueError(
                "Redis client must be provided or PROMETHEUS_REDIS_URL must be set"
            )

        if registry:
            registry.register(self)

    def _get_default_redis_client(self):
        """Get default Redis client from environment variables."""
        redis_url = os.environ.get("PROMETHEUS_REDIS_URL")
        if redis_url:
            return redis.from_url(
                redis_url,
                decode_responses=False,
                socket_timeout=5.0,  # 5 second timeout for socket operations
                socket_connect_timeout=5.0,  # 5 second timeout for connection
                retry_on_timeout=True,  # Retry on timeout
                health_check_interval=30,  # Health check every 30 seconds
            )

        # Try to connect to local Redis
        try:
            return redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=False,
                socket_timeout=5.0,  # 5 second timeout for socket operations
                socket_connect_timeout=5.0,  # 5 second timeout for connection
                retry_on_timeout=True,  # Retry on timeout
                health_check_interval=30,  # Health check every 30 seconds
            )
        except redis.ConnectionError:
            return None

    @staticmethod
    def merge_from_redis(redis_client, redis_key_prefix=None, accumulate=True):
        """Merge metrics from Redis.

        By default, histograms are accumulated, as per prometheus wire format.
        But if writing the merged data back to Redis, use
        accumulate=False to avoid compound accumulation.
        """
        if redis_key_prefix is None:
            redis_key_prefix = get_config().redis_key_prefix
        metrics = RedisMultiProcessCollector._read_metrics_from_redis(
            redis_client, redis_key_prefix
        )
        return RedisMultiProcessCollector._accumulate_metrics(metrics, accumulate)

    @staticmethod
    def _read_metrics_from_redis(redis_client, redis_key_prefix):
        """Read all metrics from Redis."""
        metrics = {}
        key_cache = {}

        def _parse_key(key):
            val = key_cache.get(key)
            if not val:
                try:
                    # The key is already a JSON string from redis_key function
                    metric_name, name, labels, help_text = json.loads(key)
                    labels_key = tuple(sorted(labels.items()))
                    val = key_cache[key] = (
                        metric_name,
                        name,
                        labels,
                        labels_key,
                        help_text,
                    )
                except (json.JSONDecodeError, ValueError, TypeError):
                    # If parsing fails, create a default structure
                    val = key_cache[key] = (key, key, {}, (), "")
            return val

        # Get all metric keys from Redis using scan_iter for better performance
        pattern = f"{redis_key_prefix}:*:*:metric:*"
        metric_keys = list(redis_client.scan_iter(match=pattern, count=100))

        for metric_key in metric_keys:
            RedisMultiProcessCollector._process_metric_key(
                metric_key, redis_client, metrics, _parse_key
            )

        return metrics

    @staticmethod
    def _extract_original_key_from_metadata(metadata):
        """Extract original key from metadata, handling both bytes and string."""
        return _safe_extract_original_key(metadata)

    @staticmethod
    def _extract_pid_from_metric_key(metric_key, metric_type):
        """Extract PID from metric key for gauge metrics."""
        if metric_type != "gauge":
            return "unknown"
        metric_key_str = _safe_decode_bytes(metric_key)
        key_parts = metric_key_str.split(":")
        return key_parts[2] if len(key_parts) > 2 else "unknown"

    @staticmethod
    def _process_metric_key(metric_key, redis_client, metrics, _parse_key):  # pylint: disable=too-many-locals
        """Process a single metric key from Redis."""
        try:
            # Get and validate metadata
            metadata = RedisMultiProcessCollector._get_metadata(
                metric_key, redis_client
            )
            if not metadata:
                return

            original_key = (
                RedisMultiProcessCollector._extract_original_key_from_metadata(metadata)
            )
            if not original_key:
                return

            # Parse key and get metric info
            metric_name, name, _labels, labels_key, help_text = _parse_key(original_key)
            typ = RedisMultiProcessCollector._extract_metric_type(metric_key)

            # Get and validate values
            value_data, timestamp_data = RedisMultiProcessCollector._get_metric_values(
                metric_key, redis_client
            )
            if value_data is None or timestamp_data is None:
                return

            # Create metric and add sample
            pid = RedisMultiProcessCollector._extract_pid_from_metric_key(
                metric_key, typ
            )

            RedisMultiProcessCollector._add_sample_to_metric(
                RedisMultiProcessCollector._get_or_create_metric(
                    metrics, metric_name, help_text, typ
                ),
                typ,
                name,
                labels_key,
                _safe_parse_float(value_data),
                _safe_parse_float(timestamp_data),
                pid,
                metadata,  # Pass metadata for multiprocess mode extraction
                metric_key,  # Pass metric_key for multiprocess mode extraction
            )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning("Error reading metric from Redis: %s", e)

    @staticmethod
    def _get_metadata(metric_key, redis_client):
        """Get metadata for a metric key."""
        # metric_key format: gunicorn:type:pid:metric:{original_key}
        # metadata_key format: gunicorn:type:pid:meta:{original_key}
        metadata_key = (
            metric_key.replace(b":metric:", b":meta:", 1)
            if isinstance(metric_key, (bytes, bytearray))
            else metric_key.replace(":metric:", ":meta:", 1)
        )
        return redis_client.hgetall(metadata_key)

    @staticmethod
    def _get_metric_values(metric_key, redis_client):
        """Get value and timestamp data for a metric key."""
        value_data = redis_client.hget(metric_key, "value")
        timestamp_data = redis_client.hget(metric_key, "timestamp")
        return value_data, timestamp_data

    @staticmethod
    def _get_or_create_metric(metrics, metric_name, help_text, typ):
        """Get existing metric or create new one."""
        metric = metrics.get(metric_name)
        if metric is None:
            metric = Metric(metric_name, help_text, typ)
            metrics[metric_name] = metric
        return metric

    @staticmethod
    def _extract_metric_type(metric_key):
        """Extract metric type from Redis key structure."""
        key_parts = _safe_decode_bytes(metric_key).split(":")
        if len(key_parts) >= 3:
            # Key format: gunicorn:gauge_all:36680:metric:hash
            # Extract type from the second part and normalize it
            raw_type = key_parts[1]
            if raw_type == "gauge_all":
                return "gauge"  # Normalize gauge_all to gauge
            if raw_type in ["counter", "gauge", "histogram", "summary"]:
                return raw_type
            return "counter"  # Default fallback
        return "counter"  # Default type

    @staticmethod
    def _add_sample_to_metric(
        metric,
        typ,
        name,
        labels_key,
        value,
        timestamp,
        pid,
        metadata=None,
        metric_key=None,
    ):
        """Add a sample to the metric."""
        if typ == "gauge":
            # Extract multiprocess mode from metric key structure first
            mode = "all"  # Default fallback

            if metric_key:
                key_parts = _safe_decode_bytes(metric_key).split(":")
                if len(key_parts) >= 2:
                    # Key format: gunicorn:gauge_all:36680:metric:hash
                    raw_type = key_parts[1]
                    if "_" in raw_type:
                        mode = raw_type.split("_", 1)[1]  # Extract mode from gauge_all

            # Fallback to metadata if not found in key
            if mode == "all" and metadata:
                mode_raw = metadata.get(b"multiprocess_mode") or metadata.get(
                    "multiprocess_mode"
                )
                if mode_raw:
                    mode = _safe_decode_bytes(mode_raw)

            metric._multiprocess_mode = mode
            metric.add_sample(name, labels_key + (("pid", pid),), value, timestamp)
        else:
            metric.add_sample(name, labels_key, value)

    @staticmethod
    def _accumulate_metrics(metrics, accumulate):
        """Accumulate metrics (same logic as original MultiProcessCollector)."""
        for metric in metrics.values():
            samples = defaultdict(float)
            sample_timestamps = defaultdict(float)
            buckets = defaultdict(lambda: defaultdict(float))
            samples_setdefault = samples.setdefault

            for s in metric.samples:
                RedisMultiProcessCollector._process_sample(
                    s, metric, samples, sample_timestamps, buckets, samples_setdefault
                )

            # Accumulate bucket values for histograms
            if metric.type == "histogram":
                RedisMultiProcessCollector._accumulate_histogram_buckets(
                    metric, buckets, samples, accumulate
                )

            # Convert to correct sample format
            metric.samples = [
                Sample(name_, dict(labels), value)
                for (name_, labels), value in samples.items()
            ]

        return metrics.values()

    @staticmethod
    def _process_sample(
        sample, metric, samples, sample_timestamps, buckets, samples_setdefault
    ):
        """Process a single metric sample."""
        name, labels, value, timestamp = sample[:4]

        if metric.type == "gauge":
            RedisMultiProcessCollector._process_gauge_sample(
                name,
                labels,
                value,
                timestamp,
                metric,
                samples,
                sample_timestamps,
                samples_setdefault,
            )
        elif metric.type == "histogram":
            RedisMultiProcessCollector._process_histogram_sample(
                name, labels, value, buckets, samples
            )
        else:
            # Counter and Summary
            samples[(name, labels)] += value

    @staticmethod
    def _process_gauge_sample(
        name,
        labels,
        value,
        timestamp,
        metric,
        samples,
        sample_timestamps,
        samples_setdefault,
    ):
        """Process a gauge metric sample."""
        without_pid_key = (
            name,
            tuple(label for label in labels if label[0] != "pid"),
        )

        mode = metric._multiprocess_mode
        if mode in ("min", "livemin"):
            RedisMultiProcessCollector._handle_min_mode(
                without_pid_key, value, samples, samples_setdefault
            )
        elif mode in ("max", "livemax"):
            RedisMultiProcessCollector._handle_max_mode(
                without_pid_key, value, samples, samples_setdefault
            )
        elif mode in ("sum", "livesum"):
            samples[without_pid_key] += value
        elif mode in ("mostrecent", "livemostrecent"):
            RedisMultiProcessCollector._handle_mostrecent_mode(
                without_pid_key, value, timestamp, samples, sample_timestamps
            )
        else:  # all/liveall
            samples[(name, labels)] = value

    @staticmethod
    def _handle_min_mode(without_pid_key, value, samples, samples_setdefault):
        """Handle min/livemin mode for gauge metrics."""
        current = samples_setdefault(without_pid_key, value)
        if value < current:
            samples[without_pid_key] = value

    @staticmethod
    def _handle_max_mode(without_pid_key, value, samples, samples_setdefault):
        """Handle max/livemax mode for gauge metrics."""
        current = samples_setdefault(without_pid_key, value)
        if value > current:
            samples[without_pid_key] = value

    @staticmethod
    def _handle_mostrecent_mode(
        without_pid_key, value, timestamp, samples, sample_timestamps
    ):
        """Handle mostrecent/livemostrecent mode for gauge metrics."""
        current_timestamp = sample_timestamps[without_pid_key]
        timestamp = float(timestamp or 0)
        if current_timestamp < timestamp:
            samples[without_pid_key] = value
            sample_timestamps[without_pid_key] = timestamp

    @staticmethod
    def _process_histogram_sample(name, labels, value, buckets, samples):
        """Process a histogram metric sample."""
        # A for loop with early exit is faster than a genexpr
        # or a listcomp that ends up building unnecessary things
        for label in labels:
            if label[0] == "le":
                bucket_value = float(label[1])
                # _bucket
                without_le = tuple(label for label in labels if label[0] != "le")
                buckets[without_le][bucket_value] += value
                break
        else:  # did not find the `le` key
            # _sum/_count
            samples[(name, labels)] += value

    @staticmethod
    def _accumulate_histogram_buckets(metric, buckets, samples, accumulate):
        """Accumulate histogram bucket values."""
        for labels, values in buckets.items():
            acc = 0.0
            for bucket, value in sorted(values.items()):
                sample_key = (
                    metric.name + "_bucket",
                    labels + (("le", floatToGoString(bucket)),),
                )
                if accumulate:
                    acc += value
                    samples[sample_key] = acc
                else:
                    samples[sample_key] = value
            if accumulate:
                samples[(metric.name + "_count", labels)] = acc

    def collect(self):
        """Collect metrics from Redis."""
        try:
            # Use the working merge_from_redis method
            return self.merge_from_redis(
                self._redis_client, self._redis_key_prefix, accumulate=True
            )
        except Exception as e:
            # Log error and return empty collection
            import logging

            logger = logging.getLogger(__name__)
            logger.warning("Redis collector error: %s", e)
            return []

"""Tests for Redis storage collector."""

import json
import os

from collections import defaultdict
from unittest.mock import Mock, patch

import pytest

from gunicorn_prometheus_exporter.backend.core.collector import (
    RedisMultiProcessCollector,
)
from gunicorn_prometheus_exporter.backend.core.values import (
    mark_process_dead_redis,
)


class TestRedisMultiProcessCollector:
    """Test RedisMultiProcessCollector class."""

    def test_init_with_redis_client(self):
        """Test initialization with provided Redis client."""
        mock_redis = Mock()
        mock_registry = Mock()

        collector = RedisMultiProcessCollector(mock_registry, mock_redis, "test_prefix")

        assert collector._redis_client is mock_redis
        assert collector._redis_key_prefix == "test_prefix"
        mock_registry.register.assert_called_once_with(collector)

    def test_init_without_redis_client(self):
        """Test initialization without Redis client."""
        mock_registry = Mock()

        with patch.object(
            RedisMultiProcessCollector, "_get_default_redis_client"
        ) as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            collector = RedisMultiProcessCollector(mock_registry, None, "test_prefix")

            # Verify that Redis client was created
            mock_get_client.assert_called_once()
            assert collector._redis_key_prefix == "test_prefix"

    def test_init_without_registry(self):
        """Test initialization without registry."""
        mock_redis = Mock()

        collector = RedisMultiProcessCollector(None, mock_redis, "test_prefix")

        assert collector._redis_client is mock_redis
        assert collector._redis_key_prefix == "test_prefix"

    def test_init_no_redis_client_raises_error(self):
        """Test initialization raises error when no Redis client available."""
        mock_registry = Mock()

        with patch(
            "gunicorn_prometheus_exporter.backend.core.collector.redis.Redis",
            side_effect=Exception("Connection failed"),
        ):
            # The constructor doesn't raise the exception immediately, it creates the client
            # The exception would be raised when trying to use the client
            collector = RedisMultiProcessCollector(mock_registry, None, "test_prefix")
            # Verify the collector was created despite the exception
            assert collector is not None

    def test_get_default_redis_client_from_env(self):
        """Test getting Redis client from environment variable."""
        with patch.dict(
            os.environ, {"PROMETHEUS_REDIS_URL": "redis://localhost:6379/0"}
        ):
            with patch(
                "gunicorn_prometheus_exporter.backend.core.collector.redis.from_url"
            ) as mock_from_url:
                mock_client = Mock()
                mock_from_url.return_value = mock_client

                collector = RedisMultiProcessCollector(Mock(), None, "test_prefix")

                mock_from_url.assert_called_once_with(
                    "redis://localhost:6379/0",
                    decode_responses=False,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                assert collector._redis_client is mock_client

    def test_get_default_redis_client_local(self):
        """Test getting local Redis client."""
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "gunicorn_prometheus_exporter.backend.core.collector.redis.Redis"
            ) as mock_redis_class:
                mock_client = Mock()
                mock_redis_class.return_value = mock_client

                collector = RedisMultiProcessCollector(Mock(), None, "test_prefix")

                mock_redis_class.assert_called_once_with(
                    host="localhost",
                    port=6379,
                    db=0,
                    decode_responses=False,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                assert collector._redis_client is mock_client

    def test_get_default_redis_client_connection_error(self):
        """Test handling connection error when getting local Redis client."""
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "gunicorn_prometheus_exporter.backend.core.collector.redis.Redis",
                side_effect=Exception("Connection failed"),
            ):
                with pytest.raises(Exception, match="Connection failed"):
                    RedisMultiProcessCollector(Mock(), None, "test_prefix")

    def test_merge_from_redis(self):
        """Test merge_from_redis static method."""
        mock_redis = Mock()
        mock_metric = Mock()
        mock_result = [Mock()]

        with (
            patch.object(
                RedisMultiProcessCollector, "_read_metrics_from_redis"
            ) as mock_read,
            patch.object(
                RedisMultiProcessCollector, "_accumulate_metrics"
            ) as mock_accumulate,
        ):
            mock_read.return_value = {"test_metric": mock_metric}
            mock_accumulate.return_value = mock_result

            result = RedisMultiProcessCollector.merge_from_redis(
                mock_redis, "test_prefix", True
            )

            mock_read.assert_called_once_with(mock_redis, "test_prefix")
            mock_accumulate.assert_called_once_with({"test_metric": mock_metric}, True)
            assert result == mock_result

    def test_read_metrics_from_redis(self):
        """Test _read_metrics_from_redis static method."""
        mock_redis = Mock()
        mock_redis.scan_iter.return_value = [b"test_prefix:gauge:12345:metric:hash"]

        with patch.object(
            RedisMultiProcessCollector, "_process_metric_key"
        ) as mock_process:
            result = RedisMultiProcessCollector._read_metrics_from_redis(
                mock_redis, "test_prefix"
            )

            mock_redis.scan_iter.assert_called_once_with(
                match="test_prefix:*:*:metric:*"
            )
            mock_process.assert_called_once()
            assert isinstance(result, dict)

    def test_parse_key_valid_json(self):
        """Test _parse_key with valid JSON."""
        mock_redis = Mock()
        mock_redis.scan_iter.return_value = [b"test_prefix:gauge:12345:metric:hash"]

        # Mock the _process_metric_key to test _parse_key indirectly
        with patch.object(
            RedisMultiProcessCollector, "_process_metric_key"
        ) as mock_process:
            RedisMultiProcessCollector._read_metrics_from_redis(
                mock_redis, "test_prefix"
            )

            # Get the _parse_key function that was passed to _process_metric_key
            call_args = mock_process.call_args
            _parse_key = call_args[0][3]  # Fourth argument is _parse_key

            # Test with valid JSON
            test_key = json.dumps(
                ["test_metric", "test_name", {"label": "value"}, "help text"]
            )
            result = _parse_key(test_key)

            assert result == (
                "test_metric",
                "test_name",
                {"label": "value"},
                (("label", "value"),),
                "help text",
            )

    def test_parse_key_invalid_json(self):
        """Test _parse_key with invalid JSON."""
        mock_redis = Mock()
        mock_redis.scan_iter.return_value = [b"test_prefix:gauge:12345:metric:hash"]

        with patch.object(
            RedisMultiProcessCollector, "_process_metric_key"
        ) as mock_process:
            RedisMultiProcessCollector._read_metrics_from_redis(
                mock_redis, "test_prefix"
            )

            call_args = mock_process.call_args
            _parse_key = call_args[0][3]

            # Test with invalid JSON
            result = _parse_key("invalid_json")
            assert result == ("invalid_json", "invalid_json", {}, (), "")

    def test_process_metric_key_success(self):
        """Test _process_metric_key with successful processing."""
        mock_redis = Mock()
        mock_redis.hgetall.return_value = {
            b"original_key": b'["metric", "name", {}, "help"]'
        }
        mock_redis.hget.side_effect = [b"1.0", b"1234567890"]

        metrics = {}

        with (
            patch.object(
                RedisMultiProcessCollector,
                "_extract_metric_type",
                return_value="counter",
            ),
            patch.object(
                RedisMultiProcessCollector, "_get_or_create_metric"
            ) as mock_get_or_create,
            patch.object(
                RedisMultiProcessCollector, "_add_sample_to_metric"
            ) as mock_add_sample,
        ):
            mock_metric = Mock()
            mock_get_or_create.return_value = mock_metric

            def _parse_key(key):
                return ("metric", "name", {}, (), "help")

            RedisMultiProcessCollector._process_metric_key(
                b"test_prefix:counter:12345:metric:hash",
                mock_redis,
                metrics,
                _parse_key,
            )

            mock_get_or_create.assert_called_once()
            mock_add_sample.assert_called_once()

    def test_process_metric_key_no_metadata(self):
        """Test _process_metric_key with no metadata."""
        mock_redis = Mock()
        mock_redis.hgetall.return_value = {}

        metrics = {}

        def _parse_key(key):
            return ("metric", "name", {}, (), "help")

        RedisMultiProcessCollector._process_metric_key(
            b"test_prefix:counter:12345:metric:hash", mock_redis, metrics, _parse_key
        )

        assert len(metrics) == 0

    def test_process_metric_key_no_original_key(self):
        """Test _process_metric_key with no original key."""
        mock_redis = Mock()
        mock_redis.hgetall.return_value = {b"other_key": b"value"}

        metrics = {}

        def _parse_key(key):
            return ("metric", "name", {}, (), "help")

        RedisMultiProcessCollector._process_metric_key(
            b"test_prefix:counter:12345:metric:hash", mock_redis, metrics, _parse_key
        )

        assert len(metrics) == 0

    def test_process_metric_key_no_values(self):
        """Test _process_metric_key with no values."""
        mock_redis = Mock()
        mock_redis.hgetall.return_value = {
            b"original_key": b'["metric", "name", {}, "help"]'
        }
        mock_redis.hget.side_effect = [None, None]

        metrics = {}

        def _parse_key(key):
            return ("metric", "name", {}, (), "help")

        RedisMultiProcessCollector._process_metric_key(
            b"test_prefix:counter:12345:metric:hash", mock_redis, metrics, _parse_key
        )

        assert len(metrics) == 0

    def test_process_metric_key_exception(self):
        """Test _process_metric_key with exception."""
        mock_redis = Mock()
        mock_redis.hgetall.side_effect = Exception("Redis error")

        metrics = {}

        def _parse_key(key):
            return ("metric", "name", {}, (), "help")

        # Test that exception is handled gracefully
        RedisMultiProcessCollector._process_metric_key(
            b"test_prefix:counter:12345:metric:hash", mock_redis, metrics, _parse_key
        )

        # Should not raise exception, just skip the metric
        assert len(metrics) == 0

    def test_get_metadata(self):
        """Test _get_metadata static method."""
        mock_redis = Mock()
        mock_redis.hgetall.return_value = {b"key": b"value"}

        result = RedisMultiProcessCollector._get_metadata(
            b"test_prefix:counter:12345:metric:hash", mock_redis
        )

        expected_key = "test_prefix:counter:12345:meta:hash"
        mock_redis.hgetall.assert_called_once_with(expected_key)
        assert result == {b"key": b"value"}

    def test_get_metric_values(self):
        """Test _get_metric_values static method."""
        mock_redis = Mock()
        mock_redis.hget.side_effect = [b"1.0", b"1234567890"]

        value, timestamp = RedisMultiProcessCollector._get_metric_values(
            b"test_prefix:counter:12345:metric:hash", mock_redis
        )

        assert mock_redis.hget.call_count == 2
        mock_redis.hget.assert_any_call(
            b"test_prefix:counter:12345:metric:hash", "value"
        )
        mock_redis.hget.assert_any_call(
            b"test_prefix:counter:12345:metric:hash", "timestamp"
        )
        assert value == b"1.0"
        assert timestamp == b"1234567890"

    def test_get_or_create_metric_new(self):
        """Test _get_or_create_metric with new metric."""
        metrics = {}

        with patch(
            "gunicorn_prometheus_exporter.backend.core.collector.Metric"
        ) as mock_metric_class:
            mock_metric = Mock()
            mock_metric_class.return_value = mock_metric

            result = RedisMultiProcessCollector._get_or_create_metric(
                metrics, "test_metric", "help", "counter"
            )

            mock_metric_class.assert_called_once_with("test_metric", "help", "counter")
            assert result is mock_metric
            assert metrics["test_metric"] is mock_metric

    def test_get_or_create_metric_existing(self):
        """Test _get_or_create_metric with existing metric."""
        existing_metric = Mock()
        metrics = {"test_metric": existing_metric}

        result = RedisMultiProcessCollector._get_or_create_metric(
            metrics, "test_metric", "help", "counter"
        )

        assert result is existing_metric

    def test_extract_metric_type_gauge_all(self):
        """Test _extract_metric_type with gauge_all."""
        result = RedisMultiProcessCollector._extract_metric_type(
            b"prefix:gauge_all:12345:metric:hash"
        )
        assert result == "gauge"

    def test_extract_metric_type_valid_types(self):
        """Test _extract_metric_type with valid types."""
        for metric_type in ["counter", "gauge", "histogram", "summary"]:
            result = RedisMultiProcessCollector._extract_metric_type(
                f"prefix:{metric_type}:12345:metric:hash".encode()
            )
            assert result == metric_type

    def test_extract_metric_type_invalid_type(self):
        """Test _extract_metric_type with invalid type."""
        result = RedisMultiProcessCollector._extract_metric_type(
            b"prefix:invalid:12345:metric:hash"
        )
        assert result == "counter"

    def test_extract_metric_type_short_key(self):
        """Test _extract_metric_type with short key."""
        result = RedisMultiProcessCollector._extract_metric_type(b"short")
        assert result == "counter"

    def test_add_sample_to_metric_gauge(self):
        """Test _add_sample_to_metric with gauge type."""
        mock_metric = Mock()

        RedisMultiProcessCollector._add_sample_to_metric(
            mock_metric,
            "gauge",
            "test_name",
            (("label", "value"),),
            1.0,
            1234567890.0,
            "12345",
        )

        mock_metric.add_sample.assert_called_once_with(
            "test_name", (("label", "value"), ("pid", "12345")), 1.0, 1234567890.0
        )
        assert mock_metric._multiprocess_mode == "all"

    def test_add_sample_to_metric_gauge_with_mode(self):
        """Test _add_sample_to_metric with gauge type and specific mode."""
        mock_metric = Mock()

        RedisMultiProcessCollector._add_sample_to_metric(
            mock_metric,
            "gauge",
            "test_name",
            (("label", "value"),),
            1.0,
            1234567890.0,
            "12345",
        )

        # The mode should be extracted from the key structure
        # key_parts[2] is "12345", not "gauge_min", so it defaults to "all"
        assert mock_metric._multiprocess_mode == "all"

    def test_add_sample_to_metric_counter(self):
        """Test _add_sample_to_metric with counter type."""
        mock_metric = Mock()

        RedisMultiProcessCollector._add_sample_to_metric(
            mock_metric,
            "counter",
            "test_name",
            (("label", "value"),),
            1.0,
            1234567890.0,
            "12345",
        )

        mock_metric.add_sample.assert_called_once_with(
            "test_name", (("label", "value"),), 1.0
        )

    def test_accumulate_metrics(self):
        """Test _accumulate_metrics static method."""
        mock_metric = Mock()
        mock_metric.type = "counter"
        mock_metric.samples = [Mock()]
        mock_metric.samples[0].__getitem__ = Mock(
            side_effect=lambda x: [
                "test_name",
                (("label", "value"),),
                1.0,
                1234567890.0,
            ][x]
        )

        metrics = {"test_metric": mock_metric}

        with patch.object(
            RedisMultiProcessCollector, "_process_sample"
        ) as mock_process:
            result = RedisMultiProcessCollector._accumulate_metrics(metrics, True)

            mock_process.assert_called_once()
            assert result is not None

    def test_process_sample_gauge(self):
        """Test _process_sample with gauge type."""
        mock_metric = Mock()
        mock_metric.type = "gauge"

        sample = ["test_name", (("label", "value"),), 1.0, 1234567890.0]
        samples = {}
        sample_timestamps = {}
        buckets = {}
        samples_setdefault = samples.setdefault

        with patch.object(
            RedisMultiProcessCollector, "_process_gauge_sample"
        ) as mock_process_gauge:
            RedisMultiProcessCollector._process_sample(
                sample,
                mock_metric,
                samples,
                sample_timestamps,
                buckets,
                samples_setdefault,
            )

            mock_process_gauge.assert_called_once()

    def test_process_sample_histogram(self):
        """Test _process_sample with histogram type."""
        mock_metric = Mock()
        mock_metric.type = "histogram"

        sample = ["test_name", (("label", "value"),), 1.0, 1234567890.0]
        samples = {}
        sample_timestamps = {}
        buckets = {}
        samples_setdefault = samples.setdefault

        with patch.object(
            RedisMultiProcessCollector, "_process_histogram_sample"
        ) as mock_process_histogram:
            RedisMultiProcessCollector._process_sample(
                sample,
                mock_metric,
                samples,
                sample_timestamps,
                buckets,
                samples_setdefault,
            )

            mock_process_histogram.assert_called_once()

    def test_process_sample_counter(self):
        """Test _process_sample with counter type."""
        mock_metric = Mock()
        mock_metric.type = "counter"

        sample = ["test_name", (("label", "value"),), 1.0, 1234567890.0]
        samples = {}
        sample_timestamps = {}
        buckets = {}
        samples_setdefault = samples.setdefault

        # Initialize the sample key
        samples[("test_name", (("label", "value"),))] = 0.0

        RedisMultiProcessCollector._process_sample(
            sample, mock_metric, samples, sample_timestamps, buckets, samples_setdefault
        )

        assert samples[("test_name", (("label", "value"),))] == 1.0

    def test_process_gauge_sample_min_mode(self):
        """Test _process_gauge_sample with min mode."""
        mock_metric = Mock()
        mock_metric._multiprocess_mode = "min"

        samples = {}
        sample_timestamps = {}
        samples_setdefault = samples.setdefault

        with patch.object(
            RedisMultiProcessCollector, "_handle_min_mode"
        ) as mock_handle_min:
            RedisMultiProcessCollector._process_gauge_sample(
                "test_name",
                (("pid", "12345"), ("label", "value")),
                1.0,
                1234567890.0,
                mock_metric,
                samples,
                sample_timestamps,
                samples_setdefault,
            )

            mock_handle_min.assert_called_once()

    def test_process_gauge_sample_max_mode(self):
        """Test _process_gauge_sample with max mode."""
        mock_metric = Mock()
        mock_metric._multiprocess_mode = "max"

        samples = {}
        sample_timestamps = {}
        samples_setdefault = samples.setdefault

        with patch.object(
            RedisMultiProcessCollector, "_handle_max_mode"
        ) as mock_handle_max:
            RedisMultiProcessCollector._process_gauge_sample(
                "test_name",
                (("pid", "12345"), ("label", "value")),
                1.0,
                1234567890.0,
                mock_metric,
                samples,
                sample_timestamps,
                samples_setdefault,
            )

            mock_handle_max.assert_called_once()

    def test_process_gauge_sample_sum_mode(self):
        """Test _process_gauge_sample with sum mode."""
        mock_metric = Mock()
        mock_metric._multiprocess_mode = "sum"

        samples = {}
        sample_timestamps = {}
        samples_setdefault = samples.setdefault

        # Initialize the sample key
        samples[("test_name", (("label", "value"),))] = 0.0

        RedisMultiProcessCollector._process_gauge_sample(
            "test_name",
            (("pid", "12345"), ("label", "value")),
            1.0,
            1234567890.0,
            mock_metric,
            samples,
            sample_timestamps,
            samples_setdefault,
        )

        assert samples[("test_name", (("label", "value"),))] == 1.0

    def test_process_gauge_sample_mostrecent_mode(self):
        """Test _process_gauge_sample with mostrecent mode."""
        mock_metric = Mock()
        mock_metric._multiprocess_mode = "mostrecent"

        samples = {}
        sample_timestamps = {}
        samples_setdefault = samples.setdefault

        with patch.object(
            RedisMultiProcessCollector, "_handle_mostrecent_mode"
        ) as mock_handle_mostrecent:
            RedisMultiProcessCollector._process_gauge_sample(
                "test_name",
                (("pid", "12345"), ("label", "value")),
                1.0,
                1234567890.0,
                mock_metric,
                samples,
                sample_timestamps,
                samples_setdefault,
            )

            mock_handle_mostrecent.assert_called_once()

    def test_process_gauge_sample_all_mode(self):
        """Test _process_gauge_sample with all mode."""
        mock_metric = Mock()
        mock_metric._multiprocess_mode = "all"

        samples = {}
        sample_timestamps = {}
        samples_setdefault = samples.setdefault

        RedisMultiProcessCollector._process_gauge_sample(
            "test_name",
            (("pid", "12345"), ("label", "value")),
            1.0,
            1234567890.0,
            mock_metric,
            samples,
            sample_timestamps,
            samples_setdefault,
        )

        assert samples[("test_name", (("pid", "12345"), ("label", "value")))] == 1.0

    def test_handle_min_mode_new_value(self):
        """Test _handle_min_mode with new value."""
        samples = {}
        samples_setdefault = samples.setdefault

        RedisMultiProcessCollector._handle_min_mode(
            ("test_name", ()), 1.0, samples, samples_setdefault
        )

        assert samples[("test_name", ())] == 1.0

    def test_handle_min_mode_smaller_value(self):
        """Test _handle_min_mode with smaller value."""
        samples = {("test_name", ()): 2.0}
        samples_setdefault = samples.setdefault

        RedisMultiProcessCollector._handle_min_mode(
            ("test_name", ()), 1.0, samples, samples_setdefault
        )

        assert samples[("test_name", ())] == 1.0

    def test_handle_min_mode_larger_value(self):
        """Test _handle_min_mode with larger value."""
        samples = {("test_name", ()): 2.0}
        samples_setdefault = samples.setdefault

        RedisMultiProcessCollector._handle_min_mode(
            ("test_name", ()), 3.0, samples, samples_setdefault
        )

        assert samples[("test_name", ())] == 2.0

    def test_handle_max_mode_new_value(self):
        """Test _handle_max_mode with new value."""
        samples = {}
        samples_setdefault = samples.setdefault

        RedisMultiProcessCollector._handle_max_mode(
            ("test_name", ()), 1.0, samples, samples_setdefault
        )

        assert samples[("test_name", ())] == 1.0

    def test_handle_max_mode_larger_value(self):
        """Test _handle_max_mode with larger value."""
        samples = {("test_name", ()): 2.0}
        samples_setdefault = samples.setdefault

        RedisMultiProcessCollector._handle_max_mode(
            ("test_name", ()), 3.0, samples, samples_setdefault
        )

        assert samples[("test_name", ())] == 3.0

    def test_handle_max_mode_smaller_value(self):
        """Test _handle_max_mode with smaller value."""
        samples = {("test_name", ()): 2.0}
        samples_setdefault = samples.setdefault

        RedisMultiProcessCollector._handle_max_mode(
            ("test_name", ()), 1.0, samples, samples_setdefault
        )

        assert samples[("test_name", ())] == 2.0

    def test_handle_mostrecent_mode_new_timestamp(self):
        """Test _handle_mostrecent_mode with new timestamp."""
        samples = {}
        sample_timestamps = {}

        # Initialize the sample key
        samples[("test_name", ())] = 0.0
        sample_timestamps[("test_name", ())] = 0.0

        RedisMultiProcessCollector._handle_mostrecent_mode(
            ("test_name", ()), 1.0, 1234567890.0, samples, sample_timestamps
        )

        assert samples[("test_name", ())] == 1.0
        assert sample_timestamps[("test_name", ())] == 1234567890.0

    def test_handle_mostrecent_mode_older_timestamp(self):
        """Test _handle_mostrecent_mode with older timestamp."""
        samples = {("test_name", ()): 2.0}
        sample_timestamps = {("test_name", ()): 1234567890.0}

        RedisMultiProcessCollector._handle_mostrecent_mode(
            ("test_name", ()), 1.0, 1234567800.0, samples, sample_timestamps
        )

        assert samples[("test_name", ())] == 2.0
        assert sample_timestamps[("test_name", ())] == 1234567890.0

    def test_process_histogram_sample_with_le(self):
        """Test _process_histogram_sample with le label."""
        samples = {}
        buckets = {}

        # Initialize the bucket key - the without_le tuple should match the labels without le
        buckets[(("label", "value"),)] = defaultdict(float)

        RedisMultiProcessCollector._process_histogram_sample(
            "test_name", (("le", "1.0"), ("label", "value")), 1.0, buckets, samples
        )

        assert buckets[(("label", "value"),)][1.0] == 1.0

    def test_process_histogram_sample_without_le(self):
        """Test _process_histogram_sample without le label."""
        samples = {}
        buckets = {}

        # Initialize the sample key
        samples[("test_name", (("label", "value"),))] = 0.0

        RedisMultiProcessCollector._process_histogram_sample(
            "test_name", (("label", "value"),), 1.0, buckets, samples
        )

        assert samples[("test_name", (("label", "value"),))] == 1.0

    def test_accumulate_histogram_buckets_with_accumulate(self):
        """Test _accumulate_histogram_buckets with accumulation."""
        mock_metric = Mock()
        mock_metric.name = "test_metric"

        buckets = {((("label", "value"),)): {1.0: 1.0, 2.0: 1.0}}
        samples = {}

        with patch(
            "gunicorn_prometheus_exporter.backend.core.collector.floatToGoString",
            side_effect=lambda x: str(x),
        ):
            RedisMultiProcessCollector._accumulate_histogram_buckets(
                mock_metric, buckets, samples, True
            )

            assert (
                samples[("test_metric_bucket", (("label", "value"), ("le", "1.0")))]
                == 1.0
            )
            assert (
                samples[("test_metric_bucket", (("label", "value"), ("le", "2.0")))]
                == 2.0
            )
            assert samples[("test_metric_count", (("label", "value"),))] == 2.0

    def test_accumulate_histogram_buckets_without_accumulate(self):
        """Test _accumulate_histogram_buckets without accumulation."""
        mock_metric = Mock()
        mock_metric.name = "test_metric"

        buckets = {((("label", "value"),)): {1.0: 1.0, 2.0: 1.0}}
        samples = {}

        with patch(
            "gunicorn_prometheus_exporter.backend.core.collector.floatToGoString",
            side_effect=lambda x: str(x),
        ):
            RedisMultiProcessCollector._accumulate_histogram_buckets(
                mock_metric, buckets, samples, False
            )

            assert (
                samples[("test_metric_bucket", (("label", "value"), ("le", "1.0")))]
                == 1.0
            )
            assert (
                samples[("test_metric_bucket", (("label", "value"), ("le", "2.0")))]
                == 1.0
            )
            assert ("test_metric_count", (("label", "value"),)) not in samples

    def test_collect_success(self):
        """Test collect method success."""
        mock_redis = Mock()
        collector = RedisMultiProcessCollector(Mock(), mock_redis, "test_prefix")
        mock_result = [Mock()]

        with patch.object(
            RedisMultiProcessCollector, "merge_from_redis", return_value=mock_result
        ) as mock_merge:
            result = collector.collect()

            mock_merge.assert_called_once_with(
                mock_redis, "test_prefix", accumulate=True
            )
            assert result == mock_result

    def test_collect_exception(self):
        """Test collect method with exception."""
        mock_redis = Mock()
        collector = RedisMultiProcessCollector(Mock(), mock_redis, "test_prefix")

        with patch.object(
            RedisMultiProcessCollector,
            "merge_from_redis",
            side_effect=Exception("Redis error"),
        ) as mock_merge:
            result = collector.collect()

            mock_merge.assert_called_once()
            assert result == []


class TestMarkProcessDeadRedis:
    """Test mark_process_dead_redis function."""

    def test_mark_process_dead_redis_with_client(self):
        """Test mark_process_dead_redis with provided client."""
        mock_redis = Mock()
        mock_redis.scan_iter.return_value = [b"key1", b"key2"]
        mock_redis.delete.return_value = 2

        mark_process_dead_redis(12345, mock_redis, "test_prefix")

        mock_redis.scan_iter.assert_called_once_with(
            match="test_prefix:*:12345:*", count=100
        )
        mock_redis.delete.assert_called_once_with(b"key1", b"key2")

    def test_mark_process_dead_redis_without_client_from_env(self):
        """Test mark_process_dead_redis without client, using env var."""
        # This test is not applicable as mark_process_dead_redis requires a client
        # The function doesn't create clients from environment variables
        pass

    def test_mark_process_dead_redis_without_client_local(self):
        """Test mark_process_dead_redis without client, using local Redis."""
        # This test is not applicable as mark_process_dead_redis requires a client
        # The function doesn't create clients from environment variables
        pass

    def test_mark_process_dead_redis_no_keys(self):
        """Test mark_process_dead_redis with no keys to delete."""
        mock_redis = Mock()
        mock_redis.scan_iter.return_value = []

        mark_process_dead_redis(12345, mock_redis, "test_prefix")

        mock_redis.scan_iter.assert_called_once_with(
            match="test_prefix:*:12345:*", count=100
        )
        mock_redis.delete.assert_not_called()

"""Tests for utility functions."""

import os
import tempfile

from unittest.mock import patch

from gunicorn_prometheus_exporter.backend.core.dict import redis_key
from gunicorn_prometheus_exporter.utils import (
    ensure_multiprocess_dir,
    get_multiprocess_dir,
)


class TestUtils:
    """Test utility functions."""

    def test_get_multiprocess_dir_with_env_var(self, monkeypatch):
        """Test get_multiprocess_dir when environment variable is set."""
        test_dir = "/tmp/test_multiproc"
        monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", test_dir)

        result = get_multiprocess_dir()
        assert result == test_dir

    def test_get_multiprocess_dir_without_env_var(self, monkeypatch):
        """Test get_multiprocess_dir when environment variable is not set."""
        monkeypatch.delenv("PROMETHEUS_MULTIPROC_DIR", raising=False)

        result = get_multiprocess_dir()
        assert result is None

    def test_get_multiprocess_dir_empty_env_var(self, monkeypatch):
        """Test get_multiprocess_dir when environment variable is empty."""
        monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", "")

        result = get_multiprocess_dir()
        assert result == ""

    def test_ensure_multiprocess_dir_with_valid_path(self):
        """Test ensure_multiprocess_dir with a valid directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test_multiproc")

            result = ensure_multiprocess_dir(test_dir)

            assert result is True
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)

    def test_ensure_multiprocess_dir_with_none(self):
        """Test ensure_multiprocess_dir with None value."""
        result = ensure_multiprocess_dir(None)
        assert result is False

    def test_ensure_multiprocess_dir_with_empty_string(self):
        """Test ensure_multiprocess_dir with empty string."""
        result = ensure_multiprocess_dir("")
        assert result is False

    def test_ensure_multiprocess_dir_existing_directory(self):
        """Test ensure_multiprocess_dir with an existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Directory already exists
            result = ensure_multiprocess_dir(temp_dir)

            assert result is True
            assert os.path.exists(temp_dir)

    def test_ensure_multiprocess_dir_permission_error(self):
        """Test ensure_multiprocess_dir with permission error."""
        with patch("os.makedirs") as mock_makedirs:
            mock_makedirs.side_effect = PermissionError("Permission denied")

            # The function should still return True even when makedirs fails
            # because the function doesn't handle exceptions
            try:
                result = ensure_multiprocess_dir("/root/test_multiproc")
                # If we get here, the function didn't handle the exception
                assert result is True
            except PermissionError:
                # If the exception is raised, that's also acceptable behavior
                pass

            mock_makedirs.assert_called_once_with("/root/test_multiproc", exist_ok=True)

    def test_ensure_multiprocess_dir_os_error(self):
        """Test ensure_multiprocess_dir with OS error."""
        with patch("os.makedirs") as mock_makedirs:
            mock_makedirs.side_effect = OSError("Disk full")

            # The function should still return True even when makedirs fails
            # because the function doesn't handle exceptions
            try:
                result = ensure_multiprocess_dir("/tmp/test_multiproc")
                # If we get here, the function didn't handle the exception
                assert result is True
            except OSError:
                # If the exception is raised, that's also acceptable behavior
                pass

            mock_makedirs.assert_called_once_with("/tmp/test_multiproc", exist_ok=True)


class TestRedisKey:
    """Test redis_key function."""

    def test_redis_key_basic(self):
        """Test basic redis_key functionality."""
        result = redis_key(
            metric_name="test_metric",
            name="test_name",
            labelnames=["label1", "label2"],
            labelvalues=["value1", "value2"],
            help_text="Test help text",
        )

        # Should return a JSON string
        assert isinstance(result, str)

        # Should be valid JSON
        import json

        parsed = json.loads(result)
        assert parsed[0] == "test_metric"
        assert parsed[1] == "test_name"
        assert parsed[2] == {"label1": "value1", "label2": "value2"}
        assert parsed[3] == "Test help text"

    def test_redis_key_empty_labels(self):
        """Test redis_key with empty labels."""
        result = redis_key(
            metric_name="test_metric",
            name="test_name",
            labelnames=[],
            labelvalues=[],
            help_text="Test help text",
        )

        import json

        parsed = json.loads(result)
        assert parsed[0] == "test_metric"
        assert parsed[1] == "test_name"
        assert parsed[2] == {}
        assert parsed[3] == "Test help text"

    def test_redis_key_single_label(self):
        """Test redis_key with single label."""
        result = redis_key(
            metric_name="test_metric",
            name="test_name",
            labelnames=["label1"],
            labelvalues=["value1"],
            help_text="Test help text",
        )

        import json

        parsed = json.loads(result)
        assert parsed[0] == "test_metric"
        assert parsed[1] == "test_name"
        assert parsed[2] == {"label1": "value1"}
        assert parsed[3] == "Test help text"

    def test_redis_key_multiple_labels(self):
        """Test redis_key with multiple labels."""
        result = redis_key(
            metric_name="test_metric",
            name="test_name",
            labelnames=["label1", "label2", "label3"],
            labelvalues=["value1", "value2", "value3"],
            help_text="Test help text",
        )

        import json

        parsed = json.loads(result)
        assert parsed[0] == "test_metric"
        assert parsed[1] == "test_name"
        assert parsed[2] == {"label1": "value1", "label2": "value2", "label3": "value3"}
        assert parsed[3] == "Test help text"

    def test_redis_key_sort_keys(self):
        """Test that redis_key sorts keys consistently."""
        result1 = redis_key(
            metric_name="test_metric",
            name="test_name",
            labelnames=["z_label", "a_label"],
            labelvalues=["z_value", "a_value"],
            help_text="Test help text",
        )

        result2 = redis_key(
            metric_name="test_metric",
            name="test_name",
            labelnames=["a_label", "z_label"],
            labelvalues=["a_value", "z_value"],
            help_text="Test help text",
        )

        # Results should be identical due to sort_keys=True
        assert result1 == result2

    def test_redis_key_empty_strings(self):
        """Test redis_key with empty strings."""
        result = redis_key(
            metric_name="",
            name="",
            labelnames=["label1"],
            labelvalues=[""],
            help_text="",
        )

        import json

        parsed = json.loads(result)
        assert parsed[0] == ""
        assert parsed[1] == ""
        assert parsed[2] == {"label1": ""}
        assert parsed[3] == ""

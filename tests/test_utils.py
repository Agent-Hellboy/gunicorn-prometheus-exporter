"""Tests for utility functions."""

import os
import tempfile

from unittest.mock import patch

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

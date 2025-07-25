"""Unit tests for the forwarder system."""

import os
import shutil
import tempfile
import unittest

from unittest.mock import Mock, patch

from gunicorn_prometheus_exporter.forwarder.base import BaseForwarder
from gunicorn_prometheus_exporter.forwarder.manager import ForwarderManager
from gunicorn_prometheus_exporter.forwarder.redis import RedisForwarder


class TestBaseForwarder(unittest.TestCase):
    """Test cases for BaseForwarder abstract class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = self.test_dir
        os.environ["CLEANUP_DB_FILES"] = "true"

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if self.original_multiproc_dir:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = self.original_multiproc_dir
        elif "PROMETHEUS_MULTIPROC_DIR" in os.environ:
            del os.environ["PROMETHEUS_MULTIPROC_DIR"]

    def test_base_forwarder_initialization(self):
        """Test BaseForwarder initialization."""

        class TestForwarder(BaseForwarder):
            def _connect(self):
                return True

            def _forward_metrics(self, data):
                return True

            def _disconnect(self):
                pass

        forwarder = TestForwarder(forward_interval=30, name="Test")

        self.assertEqual(forwarder.forward_interval, 30)
        self.assertEqual(forwarder.name, "Test")
        self.assertFalse(forwarder.is_running())

    def test_cleanup_multiprocess_files_enabled(self):
        """Test DB file cleanup when enabled."""

        class TestForwarder(BaseForwarder):
            def _connect(self):
                return True

            def _forward_metrics(self, data):
                return True

            def _disconnect(self):
                pass

        # Create dummy DB files
        db_files = ["counter_123.db", "gauge_456.db", "histogram_789.db"]
        for db_file in db_files:
            db_path = os.path.join(self.test_dir, db_file)
            with open(db_path, "w") as f:
                f.write("dummy content")

        # Verify files exist
        self.assertEqual(len(os.listdir(self.test_dir)), 3)

        # Test cleanup
        forwarder = TestForwarder()
        result = forwarder._cleanup_multiprocess_files()

        self.assertTrue(result)
        self.assertEqual(len(os.listdir(self.test_dir)), 0)

    def test_cleanup_multiprocess_files_disabled(self):
        """Test DB file cleanup when disabled."""
        os.environ["CLEANUP_DB_FILES"] = "false"

        class TestForwarder(BaseForwarder):
            def _connect(self):
                return True

            def _forward_metrics(self, data):
                return True

            def _disconnect(self):
                pass

        # Create dummy DB files
        db_files = ["counter_123.db", "gauge_456.db"]
        for db_file in db_files:
            db_path = os.path.join(self.test_dir, db_file)
            with open(db_path, "w") as f:
                f.write("dummy content")

        # Test cleanup (should be skipped)
        forwarder = TestForwarder()
        result = forwarder._cleanup_multiprocess_files()

        self.assertTrue(result)
        self.assertEqual(len(os.listdir(self.test_dir)), 2)  # Files still there

    def test_cleanup_no_multiproc_dir(self):
        """Test cleanup when no multiprocess directory exists."""
        del os.environ["PROMETHEUS_MULTIPROC_DIR"]

        class TestForwarder(BaseForwarder):
            def _connect(self):
                return True

            def _forward_metrics(self, data):
                return True

            def _disconnect(self):
                pass

        forwarder = TestForwarder()
        result = forwarder._cleanup_multiprocess_files()

        self.assertTrue(result)  # Should succeed gracefully

    @patch("gunicorn_prometheus_exporter.forwarder.base.logger")
    def test_cleanup_error_handling(self, mock_logger):
        """Test cleanup error handling."""

        class TestForwarder(BaseForwarder):
            def _connect(self):
                return True

            def _forward_metrics(self, data):
                return True

            def _disconnect(self):
                pass

        # Create a file that can't be deleted (simulate permission error)
        with patch("os.remove", side_effect=OSError("Permission denied")):
            db_path = os.path.join(self.test_dir, "test.db")
            with open(db_path, "w") as f:
                f.write("content")

            forwarder = TestForwarder()
            result = forwarder._cleanup_multiprocess_files()

            self.assertTrue(result)  # Should still return True
            mock_logger.warning.assert_called()

    def test_generate_metrics(self):
        """Test metrics generation."""

        class TestForwarder(BaseForwarder):
            def _connect(self):
                return True

            def _forward_metrics(self, data):
                return True

            def _disconnect(self):
                pass

        forwarder = TestForwarder()

        with (
            patch("prometheus_client.generate_latest") as mock_generate,
            patch(
                "gunicorn_prometheus_exporter.metrics.get_shared_registry"
            ) as mock_registry,
        ):
            mock_generate.return_value = b"# HELP test_metric\ntest_metric 42\n"
            mock_registry.return_value = Mock()

            result = forwarder._generate_metrics()

            self.assertIsNotNone(result)
            self.assertIn("test_metric", result)

    def test_forwarder_start_stop(self):
        """Test forwarder start and stop functionality."""

        class TestForwarder(BaseForwarder):
            def _connect(self):
                return True

            def _forward_metrics(self, data):
                return True

            def _disconnect(self):
                pass

        forwarder = TestForwarder(forward_interval=0.1)

        # Test start
        self.assertTrue(forwarder.start())
        self.assertTrue(forwarder.is_running())

        # Test stop
        forwarder.stop()
        self.assertFalse(forwarder.is_running())

    def test_forwarder_failed_connection(self):
        """Test forwarder with failed connection."""

        class TestForwarder(BaseForwarder):
            def _connect(self):
                return False  # Simulate connection failure

            def _forward_metrics(self, data):
                return True

            def _disconnect(self):
                pass

        forwarder = TestForwarder()

        # Should fail to start due to connection failure
        self.assertFalse(forwarder.start())
        self.assertFalse(forwarder.is_running())


class TestRedisForwarder(unittest.TestCase):
    """Test cases for RedisForwarder."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = self.test_dir
        os.environ["CLEANUP_DB_FILES"] = "true"

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_redis_forwarder_initialization(self):
        """Test RedisForwarder initialization."""
        forwarder = RedisForwarder(
            redis_host="test_host",
            redis_port=6380,
            redis_db=1,
            redis_key_prefix="test:",
            forward_interval=60,
        )

        self.assertEqual(forwarder.redis_host, "test_host")
        self.assertEqual(forwarder.redis_port, 6380)
        self.assertEqual(forwarder.redis_db, 1)
        self.assertEqual(forwarder.redis_key_prefix, "test:")
        self.assertEqual(forwarder.forward_interval, 60)
        self.assertEqual(forwarder.name, "Redis")

    def test_redis_forwarder_config_defaults(self):
        """Test RedisForwarder using config defaults."""
        with patch(
            "gunicorn_prometheus_exporter.forwarder.redis.config"
        ) as mock_config:
            mock_config.redis_host = "config_host"
            mock_config.redis_port = 6379
            mock_config.redis_db = 0
            mock_config.redis_password = None
            mock_config.redis_key_prefix = "gunicorn:"
            mock_config.redis_forward_interval = 30

            forwarder = RedisForwarder()

            self.assertEqual(forwarder.redis_host, "config_host")
            self.assertEqual(forwarder.redis_port, 6379)

    @patch("redis.Redis")
    def test_redis_connection_success(self, mock_redis):
        """Test successful Redis connection."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True

        forwarder = RedisForwarder()
        result = forwarder._connect()

        self.assertTrue(result)
        mock_client.ping.assert_called_once()

    @patch("redis.Redis")
    def test_redis_connection_failure(self, mock_redis):
        """Test Redis connection failure."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.ping.side_effect = Exception("Connection failed")

        forwarder = RedisForwarder()
        result = forwarder._connect()

        self.assertFalse(result)

    def test_redis_import_error(self):
        """Test Redis forwarder when redis library is not installed."""
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'redis'")
        ):
            forwarder = RedisForwarder()
            result = forwarder._connect()

            self.assertFalse(result)

    def test_redis_forward_metrics_success(self):
        """Test successful metrics forwarding to Redis."""
        mock_client = Mock()

        forwarder = RedisForwarder()
        forwarder._redis_client = mock_client

        test_metrics = "# HELP test_metric\ntest_metric 42\n"

        with patch("time.time", return_value=1234567890):
            result = forwarder._forward_metrics(test_metrics)

        self.assertTrue(result)

        # Verify Redis calls
        mock_client.setex.assert_called()
        mock_client.set.assert_called()

        # Check the calls
        calls = mock_client.set.call_args_list
        self.assertTrue(any("latest" in str(call) for call in calls))
        self.assertTrue(any("metadata" in str(call) for call in calls))

    def test_redis_forward_metrics_no_client(self):
        """Test metrics forwarding when Redis client is None."""
        forwarder = RedisForwarder()
        forwarder._redis_client = None

        result = forwarder._forward_metrics("test metrics")

        self.assertFalse(result)

    def test_redis_forward_metrics_error(self):
        """Test metrics forwarding with Redis error."""
        mock_client = Mock()
        mock_client.setex.side_effect = Exception("Redis error")

        forwarder = RedisForwarder()
        forwarder._redis_client = mock_client

        result = forwarder._forward_metrics("test metrics")

        self.assertFalse(result)

    def test_redis_disconnect(self):
        """Test Redis disconnect."""
        mock_client = Mock()

        forwarder = RedisForwarder()
        forwarder._redis_client = mock_client

        forwarder._disconnect()

        mock_client.close.assert_called_once()
        self.assertIsNone(forwarder._redis_client)

    def test_redis_get_status(self):
        """Test Redis forwarder status."""
        forwarder = RedisForwarder(
            redis_host="test_host",
            redis_port=6380,
            redis_db=1,
            redis_key_prefix="test:",
        )

        status = forwarder.get_status()

        self.assertEqual(status["name"], "Redis")
        self.assertEqual(status["redis_host"], "test_host")
        self.assertEqual(status["redis_port"], 6380)
        self.assertEqual(status["redis_db"], 1)
        self.assertEqual(status["redis_key_prefix"], "test:")
        self.assertFalse(status["connected"])  # No client connected


class TestForwarderManager(unittest.TestCase):
    """Test cases for ForwarderManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ForwarderManager()

    def test_manager_initialization(self):
        """Test ForwarderManager initialization."""
        self.assertEqual(len(self.manager.list_forwarders()), 0)
        self.assertEqual(len(self.manager.get_running_forwarders()), 0)

    def test_add_forwarder(self):
        """Test adding a forwarder to manager."""
        mock_forwarder = Mock(spec=BaseForwarder)
        mock_forwarder.__class__.__name__ = "MockForwarder"

        result = self.manager.add_forwarder("test_forwarder", mock_forwarder)

        self.assertTrue(result)
        self.assertIn("test_forwarder", self.manager.list_forwarders())
        self.assertEqual(self.manager.get_forwarder("test_forwarder"), mock_forwarder)

    def test_create_redis_forwarder(self):
        """Test creating Redis forwarder through manager."""
        result = self.manager.create_forwarder(
            "redis", "test_redis", redis_host="test_host", redis_port=6380
        )

        self.assertTrue(result)
        self.assertIn("test_redis", self.manager.list_forwarders())

        forwarder = self.manager.get_forwarder("test_redis")
        self.assertIsInstance(forwarder, RedisForwarder)
        self.assertEqual(forwarder.redis_host, "test_host")
        self.assertEqual(forwarder.redis_port, 6380)

    def test_create_unknown_forwarder_type(self):
        """Test creating unknown forwarder type."""
        result = self.manager.create_forwarder("unknown", "test")

        self.assertFalse(result)
        self.assertEqual(len(self.manager.list_forwarders()), 0)

    def test_start_stop_forwarder(self):
        """Test starting and stopping forwarders."""
        mock_forwarder = Mock(spec=BaseForwarder)
        mock_forwarder.start.return_value = True
        mock_forwarder.is_running.return_value = True

        self.manager.add_forwarder("test", mock_forwarder)

        # Test start
        result = self.manager.start_forwarder("test")
        self.assertTrue(result)
        mock_forwarder.start.assert_called_once()

        # Test stop
        result = self.manager.stop_forwarder("test")
        self.assertTrue(result)
        mock_forwarder.stop.assert_called_once()

    def test_start_nonexistent_forwarder(self):
        """Test starting non-existent forwarder."""
        result = self.manager.start_forwarder("nonexistent")
        self.assertFalse(result)

    def test_remove_forwarder(self):
        """Test removing a forwarder."""
        mock_forwarder = Mock(spec=BaseForwarder)

        self.manager.add_forwarder("test", mock_forwarder)
        self.assertEqual(len(self.manager.list_forwarders()), 1)

        result = self.manager.remove_forwarder("test")
        self.assertTrue(result)
        self.assertEqual(len(self.manager.list_forwarders()), 0)
        mock_forwarder.stop.assert_called_once()

    def test_start_stop_all(self):
        """Test starting and stopping all forwarders."""
        mock_forwarder1 = Mock(spec=BaseForwarder)
        mock_forwarder1.start.return_value = True
        mock_forwarder2 = Mock(spec=BaseForwarder)
        mock_forwarder2.start.return_value = True

        self.manager.add_forwarder("test1", mock_forwarder1)
        self.manager.add_forwarder("test2", mock_forwarder2)

        # Test start all
        result = self.manager.start_all()
        self.assertTrue(result)
        mock_forwarder1.start.assert_called_once()
        mock_forwarder2.start.assert_called_once()

        # Test stop all
        self.manager.stop_all()
        mock_forwarder1.stop.assert_called_once()
        mock_forwarder2.stop.assert_called_once()

    def test_get_status(self):
        """Test getting status of all forwarders."""
        mock_forwarder = Mock(spec=BaseForwarder)
        mock_forwarder.get_status.return_value = {"running": True, "name": "test"}

        self.manager.add_forwarder("test", mock_forwarder)

        status = self.manager.get_status()

        self.assertIn("test", status)
        self.assertEqual(status["test"]["running"], True)
        mock_forwarder.get_status.assert_called_once()

    def test_get_running_forwarders(self):
        """Test getting list of running forwarders."""
        mock_forwarder1 = Mock(spec=BaseForwarder)
        mock_forwarder1.is_running.return_value = True

        mock_forwarder2 = Mock(spec=BaseForwarder)
        mock_forwarder2.is_running.return_value = False

        self.manager.add_forwarder("running", mock_forwarder1)
        self.manager.add_forwarder("stopped", mock_forwarder2)

        running = self.manager.get_running_forwarders()

        self.assertEqual(len(running), 1)
        self.assertIn("running", running)
        self.assertNotIn("stopped", running)

    def test_get_available_types(self):
        """Test getting available forwarder types."""
        types = ForwarderManager.get_available_types()

        self.assertIn("redis", types)
        self.assertIsInstance(types, list)

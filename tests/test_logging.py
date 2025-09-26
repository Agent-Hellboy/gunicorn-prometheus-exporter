"""Tests for the basic logging module."""

import logging
import tempfile
import unittest

from gunicorn_prometheus_exporter.logging import (
    LoggerMixin,
    LoggingConfig,
    configure_from_gunicorn_config,
    get_logger,
    log_configuration,
    log_error_with_context,
    log_system_info,
    setup_logging,
)


class TestLoggingConfig(unittest.TestCase):
    """Test LoggingConfig class."""

    def test_logging_config_creation(self):
        """Test creating a LoggingConfig."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format_string is not None
        assert config.log_file is None
        assert config._configured is False

    def test_setup_logging(self):
        """Test setting up logging."""
        config = LoggingConfig()
        config.setup_logging(level="DEBUG")

        assert config.level == logging.DEBUG
        assert config._configured is True

    def test_setup_logging_with_file(self):
        """Test setting up logging with file output."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            log_file = temp_file.name

        try:
            config = LoggingConfig()
            config.setup_logging(level="DEBUG", log_file=log_file)

            assert config.log_file == log_file
            assert config._configured is True
        finally:
            import os

            os.unlink(log_file)


class TestLoggerMixin(unittest.TestCase):
    """Test LoggerMixin class."""

    def test_logger_mixin_creation(self):
        """Test creating a class with LoggerMixin."""

        class TestClass(LoggerMixin):
            pass

        instance = TestClass()
        assert isinstance(instance.logger, logging.Logger)
        assert instance.logger.name == "test_logging.TestClass"

    def test_logging_methods(self):
        """Test logging methods."""

        class TestClass(LoggerMixin):
            pass

        instance = TestClass()

        # Test that logging methods exist and are callable
        assert callable(instance.log_info)
        assert callable(instance.log_debug)
        assert callable(instance.log_warning)
        assert callable(instance.log_error)
        assert callable(instance.log_critical)


class TestSetupLogging(unittest.TestCase):
    """Test setup_logging function."""

    def test_setup_logging(self):
        """Test setting up logging."""
        setup_logging(level="DEBUG")

        # Check that root logger is configured
        root_logger = logging.getLogger()
        assert root_logger.level <= logging.DEBUG
        assert len(root_logger.handlers) > 0

    def test_setup_logging_with_file(self):
        """Test setting up logging with file output."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            log_file = temp_file.name

        try:
            setup_logging(level="DEBUG", log_file=log_file)

            # Check that root logger is configured
            root_logger = logging.getLogger()
            assert root_logger.level <= logging.DEBUG
            assert len(root_logger.handlers) >= 1
        finally:
            import os

            os.unlink(log_file)


class TestGetLogger(unittest.TestCase):
    """Test get_logger function."""

    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test_logger")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""

    def test_log_configuration(self):
        """Test logging configuration."""
        config_dict = {"workers": 4, "timeout": 30}

        # This should not raise an exception
        log_configuration(config_dict)

    def test_log_error_with_context(self):
        """Test logging error with context."""
        error = ValueError("Test error")
        context = {"function": "test_func", "args": ["arg1"]}

        # This should not raise an exception
        log_error_with_context(error, context)

    def test_log_system_info(self):
        """Test logging system info."""
        # This should not raise an exception
        log_system_info()

    def test_configure_from_gunicorn_config(self):
        """Test configuring from Gunicorn config."""
        # Test with a mock config
        mock_config = {
            "loglevel": "DEBUG",
            "accesslog": "/tmp/access.log",
        }

        # This should not raise an exception
        configure_from_gunicorn_config(mock_config)


class TestIntegration(unittest.TestCase):
    """Integration tests for the logging module."""

    def test_full_workflow(self):
        """Test a complete logging workflow."""

        class TestClass(LoggerMixin):
            def test_method(self):
                self.log_info("Test info message")
                self.log_debug("Test debug message")
                self.log_warning("Test warning message")
                self.log_error("Test error message")

        instance = TestClass()

        # This should not raise an exception
        instance.test_method()

    def test_error_handling(self):
        """Test error handling in logging."""

        class TestClass(LoggerMixin):
            pass

        instance = TestClass()

        # Test error logging
        try:
            raise ValueError("Test error")
        except ValueError as e:
            instance.log_error("Test error occurred: %s", e)


if __name__ == "__main__":
    unittest.main()

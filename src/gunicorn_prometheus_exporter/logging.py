"""
Basic logging module for gunicorn-prometheus-exporter.

This module provides centralized logging configuration and utilities
for the gunicorn-prometheus-exporter project.
"""

import logging
import logging.handlers
import os
import sys

from typing import Optional, Union


class LoggingConfig:
    """Configuration class for logging setup."""

    def __init__(self):
        self.level = "INFO"
        self.format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.date_format = "%Y-%m-%d %H:%M:%S"
        self.log_file: Optional[str] = None
        self.max_bytes = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        self._configured = False

    def setup_logging(
        self,
        level: Union[str, int] = "INFO",
        log_file: Optional[str] = None,
        format_string: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ) -> None:
        """
        Setup logging configuration.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            format_string: Optional custom format string
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
        """
        # Convert string level to logging constant
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)

        self.level = level
        self.log_file = log_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        if format_string:
            self.format_string = format_string

        # Create formatter
        formatter = logging.Formatter(self.format_string, datefmt=self.date_format)

        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            try:
                # Ensure log directory exists
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)

                # Use rotating file handler
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file, maxBytes=max_bytes, backupCount=backup_count
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)

            except (OSError, PermissionError) as e:
                # If file logging fails, log to console only
                console_handler = logging.getLogger(__name__)
                console_handler.warning(
                    "Failed to setup file logging: %s. Using console only.", e
                )

        self._configured = True


# Global logging configuration instance
_logging_config = LoggingConfig()


def setup_logging(
    level: Union[str, int] = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """
    Setup logging configuration for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_string: Optional custom format string
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    _logging_config.setup_logging(
        level=level,
        log_file=log_file,
        format_string=format_string,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def get_logger_for_class(cls) -> logging.Logger:
    """
    Get a logger instance for a class.

    Args:
        cls: Class to get logger for

    Returns:
        Logger instance with class name
    """
    return logging.getLogger(f"{cls.__module__}.{cls.__name__}")


class LoggerMixin:
    """Mixin class that provides logging functionality to any class."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger_for_class(self.__class__)

    def log_info(self, message: str, *args, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, *args, **kwargs)

    def log_debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)

    def log_warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)

    def log_error(self, message: str, *args, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, *args, **kwargs)

    def log_critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)


def configure_from_gunicorn_config(gunicorn_config: dict = None) -> None:
    """
    Configure logging from Gunicorn configuration.

    This function tries to read logging configuration from the Gunicorn
    config and sets up logging accordingly.

    Args:
        gunicorn_config: Optional Gunicorn configuration dictionary
    """
    try:
        if gunicorn_config:
            # Use provided Gunicorn config
            log_level = gunicorn_config.get("loglevel", "INFO")
            # Handle mock objects gracefully
            if hasattr(log_level, "upper"):
                log_level = log_level.upper()
            else:
                log_level = str(log_level).upper()
            log_file = gunicorn_config.get("accesslog") or gunicorn_config.get(
                "errorlog"
            )
        else:
            # Fallback to our config
            from .config import config

            gunicorn_config = config.get_gunicorn_config()
            log_level = gunicorn_config.get("loglevel", "INFO").upper()
            log_file = gunicorn_config.get("accesslog") or gunicorn_config.get(
                "errorlog"
            )

        # Setup logging
        setup_logging(level=log_level, log_file=log_file)

    except (ImportError, AttributeError, ValueError, TypeError):
        # Fallback to basic logging setup
        setup_logging(level="INFO")


def log_system_info() -> None:
    """Log basic system information."""
    logger = get_logger(__name__)

    try:
        import platform

        import psutil

        logger.info("System Information:")
        logger.info("  Platform: %s", platform.platform())
        logger.info("  Python: %s", platform.python_version())
        logger.info("  CPU Count: %s", psutil.cpu_count())
        logger.info(
            "  Memory: %s MB", round(psutil.virtual_memory().total / 1024 / 1024)
        )

    except ImportError:
        logger.warning("psutil not available, skipping system info logging")


def log_configuration(config_dict: dict, logger_name: str = __name__) -> None:
    """
    Log configuration dictionary in a readable format.

    Args:
        config_dict: Configuration dictionary to log
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)

    logger.info("Configuration:")
    for key, value in sorted(config_dict.items()):
        # Mask sensitive values
        if any(
            sensitive in key.lower()
            for sensitive in ["password", "secret", "key", "token"]
        ):
            value = "***"
        logger.info("  %s: %s", key, value)


def log_error_with_context(
    error: Exception, context: dict = None, logger_name: str = __name__
) -> None:
    """
    Log an error with additional context information.

    Args:
        error: Exception to log
        context: Additional context dictionary
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)

    logger.error("Error occurred: %s", str(error))
    logger.error("Error type: %s", type(error).__name__)

    if context:
        logger.error("Context:")
        for key, value in context.items():
            logger.error("  %s: %s", key, value)


# Initialize logging on module import
# Note: We don't call configure_from_gunicorn_config() here anymore
# because we need the actual Gunicorn config which isn't available at import time
# Instead, we call it from the hooks when we have the real config

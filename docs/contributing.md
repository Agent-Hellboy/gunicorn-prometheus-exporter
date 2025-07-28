# Contributing Guide

Thank you for your interest in contributing to the Gunicorn Prometheus Exporter! This guide will help you get started with development, testing, and documentation following our established patterns.

## 🏗️ Architecture Overview

This project follows a well-structured architecture with clear separation of concerns:

### **Core Components**

- **`src/gunicorn_prometheus_exporter/plugin.py`**: Worker classes and PrometheusMixin
- **`src/gunicorn_prometheus_exporter/metrics.py`**: Prometheus metrics definitions
- **`src/gunicorn_prometheus_exporter/config.py`**: Configuration management
- **`src/gunicorn_prometheus_exporter/hooks.py`**: Pre-built Gunicorn hooks
- **`src/gunicorn_prometheus_exporter/master.py`**: Master process handling
- **`src/gunicorn_prometheus_exporter/forwarder/`**: Redis integration

### **Testing Structure**

- **`tests/conftest.py`**: Shared fixtures and test configuration
- **`tests/test_*.py`**: Comprehensive test coverage for each module
- **`tox.ini`**: Multi-environment testing configuration

## 🤝 How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug Reports**: Report issues you encounter
- **Feature Requests**: Suggest new features
- **Documentation**: Improve or add documentation
- **Code**: Fix bugs or implement features
- **Testing**: Add tests or improve test coverage
- **Examples**: Add framework-specific examples

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- pip
- tox (for testing)

### Development Setup

1. **Fork the Repository**
   ```bash
   git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter.git
   cd gunicorn-prometheus-exporter
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"
   pip install tox
   ```

4. **Run Tests**
   ```bash
   tox
   ```

## 📝 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write your code
- Add tests for new functionality
- Update documentation if needed
- Follow the coding standards

### 3. Run Tests and Checks

```bash
# Run all tests
tox

# Run specific test environments
tox -e py312
tox -e py39

# Run linting
tox -e lint

# Run formatting
tox -e format
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

### 5. Push and Create a Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## 📋 Coding Standards

### Python Code Style

We use **Ruff** for linting and formatting. Follow these guidelines:

1. **Line Length**: 88 characters maximum
2. **Indentation**: 4 spaces (no tabs)
3. **Imports**: Grouped and sorted
4. **Docstrings**: Use Google-style docstrings

### Example Code Style

Following the patterns from our source code:

```python
"""
Gunicorn Prometheus Exporter - Custom Metrics Module

This module provides custom Prometheus metrics collection following
the established patterns from the main codebase.

WHY THIS PATTERN:
================

1. COMPREHENSIVE DOCUMENTATION:
   - Detailed docstrings explaining the "why" not just "what"
   - Architecture explanations for complex decisions
   - Clear separation of concerns

2. ERROR HANDLING:
   - Extensive try/except blocks with meaningful fallbacks
   - Logging at appropriate levels
   - Graceful degradation

3. CONFIGURATION MANAGEMENT:
   - Environment variable-based configuration
   - Validation with clear error messages
   - Default values for development

4. METRICS ARCHITECTURE:
   - BaseMetric class with metaclass
   - Automatic registry registration
   - Label-based metrics
"""

import logging
import time
from typing import Dict, Optional, Union

from prometheus_client import Counter, Histogram, Gauge


class CustomMetricsCollector:
    """Collects and manages custom Prometheus metrics for Gunicorn workers.

    This class follows the established patterns from the main codebase:
    - Comprehensive error handling with fallbacks
    - Extensive logging throughout
    - Property-based configuration
    - Metaclass usage for metrics

    Args:
        registry: Prometheus registry to use for metrics
        config: Configuration instance (optional)

    Example:
        >>> collector = CustomMetricsCollector()
        >>> collector.record_request(duration=0.5, worker_id="worker_1")
    """

    def __init__(self, registry: Optional[object] = None, config: Optional[object] = None) -> None:
        """Initialize the metrics collector with comprehensive setup.

        This method follows the pattern from src/gunicorn_prometheus_exporter/plugin.py:
        - Setup logging when collector is initialized
        - Initialize metrics with proper error handling
        - Create unique identifiers using timestamps
        - Extensive error handling with fallbacks

        Args:
            registry: Prometheus registry to use for metrics
            config: Configuration instance (optional)
        """
        # Setup logging following the pattern from plugin.py
        try:
            log_level = getattr(logging, "INFO")
            logging.basicConfig(level=log_level)
        except Exception as e:
            # Fallback for testing when config is not fully set up
            logging.basicConfig(level=logging.INFO)
            logging.getLogger(__name__).warning(
                "Could not setup logging from config: %s", e
            )

        self.logger = logging.getLogger(__name__)
        self.registry = registry
        self.config = config
        self.start_time = time.time()

        # Create a unique collector ID using timestamp
        self.collector_id = f"collector_{int(self.start_time)}"

        # Initialize metrics with error handling
        self._initialize_metrics()

        self.logger.info("CustomMetricsCollector initialized with ID: %s", self.collector_id)

    def _initialize_metrics(self) -> None:
        """Initialize Prometheus metrics with comprehensive error handling.

        This method follows the pattern from src/gunicorn_prometheus_exporter/metrics.py:
        - Automatic registry registration
        - Label-based metrics
        - Proper error handling
        """
        try:
            # Initialize metrics following the BaseMetric pattern
            self.request_counter = Counter(
                'custom_requests_total',
                'Total requests processed by custom collector',
                ['worker_id', 'collector_id']
            )

            self.request_duration = Histogram(
                'custom_request_duration_seconds',
                'Request duration in seconds',
                ['worker_id', 'collector_id'],
                buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf"))
            )

            self.custom_gauge = Gauge(
                'custom_active_requests',
                'Number of active requests being processed',
                ['worker_id', 'collector_id']
            )

            self.logger.info("Successfully initialized custom metrics")

        except Exception as e:
            self.logger.error("Failed to initialize metrics: %s", e)
            # Create fallback metrics
            self.request_counter = None
            self.request_duration = None
            self.custom_gauge = None

    def record_request(self, worker_id: str, duration: float, method: str = "GET") -> None:
        """Record a request with its duration and metadata.

        This method follows the pattern from src/gunicorn_prometheus_exporter/plugin.py:
        - Comprehensive error handling
        - Extensive logging
        - Graceful degradation on errors
        - Method and endpoint tracking

        Args:
            worker_id: ID of the worker that processed the request
            duration: Request duration in seconds
            method: HTTP method used (default: "GET")
        """
        try:
            if self.request_counter is None or self.request_duration is None:
                self.logger.warning("Metrics not initialized, skipping request recording")
                return

            # Record metrics with labels
            self.request_counter.labels(
                worker_id=worker_id,
                collector_id=self.collector_id
            ).inc()

            self.request_duration.labels(
                worker_id=worker_id,
                collector_id=self.collector_id
            ).observe(duration)

            self.logger.debug(
                "Recorded request for worker %s with duration %.3f and method %s",
                worker_id, duration, method
            )

        except Exception as e:
            self.logger.error(
                "Failed to record request for worker %s: %s",
                worker_id, e
            )

    def update_active_requests(self, worker_id: str, count: int) -> None:
        """Update the active requests gauge.

        Args:
            worker_id: ID of the worker
            count: Number of active requests
        """
        try:
            if self.custom_gauge is None:
                self.logger.warning("Gauge not initialized, skipping update")
                return

            self.custom_gauge.labels(
                worker_id=worker_id,
                collector_id=self.collector_id
            ).set(count)

            self.logger.debug(
                "Updated active requests for worker %s to %d",
                worker_id, count
            )

        except Exception as e:
            self.logger.error(
                "Failed to update active requests for worker %s: %s",
                worker_id, e
            )
```

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat: add Redis metrics forwarding support

fix(worker): handle worker restart gracefully

docs: update installation guide with Docker examples

test: add comprehensive test coverage for metrics module
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
tox

# Run specific Python version
tox -e py312

# Run with coverage
tox -e py312 -- --cov=gunicorn_prometheus_exporter --cov-report=html

# Run specific test file
tox -e py312 -- tests/test_metrics.py

# Run specific test function
tox -e py312 -- tests/test_metrics.py::test_worker_requests
```

### Writing Tests

Follow these guidelines for writing tests:

1. **Test Structure**: Use pytest fixtures and classes
2. **Test Names**: Descriptive names that explain what is being tested
3. **Coverage**: Aim for high test coverage
4. **Mocking**: Use mocks for external dependencies

**Example Test**:

Following the patterns from our test files:

```python
"""
Tests for the custom metrics module.

This test file follows the established patterns from tests/test_plugin.py
and tests/test_metrics.py with comprehensive test coverage.
"""

import logging
import time
from unittest.mock import MagicMock, patch

import pytest

from gunicorn_prometheus_exporter.custom_metrics import CustomMetricsCollector


class TestCustomMetricsCollector:
    """Test cases for CustomMetricsCollector class.

    This class follows the pattern from tests/test_plugin.py:
    - Comprehensive test coverage for initialization
    - Error handling tests with fallbacks
    - Logging verification
    - Mock usage for external dependencies
    """

    def test_collector_import(self):
        """Test that CustomMetricsCollector can be imported and is a class."""
        assert hasattr(CustomMetricsCollector, "__init__")
        assert callable(CustomMetricsCollector.__init__)

    def test_collector_initialization_simple(self):
        """Test CustomMetricsCollector initialization with minimal mocking."""
        with patch("gunicorn_prometheus_exporter.custom_metrics._setup_logging") as mock_setup:
            collector = CustomMetricsCollector()

            mock_setup.assert_called_once()
            assert hasattr(collector, "start_time")
            assert hasattr(collector, "collector_id")
            assert hasattr(collector, "logger")
            assert collector.collector_id.startswith("collector_")

    def test_metrics_initialization_success(self):
        """Test successful metrics initialization."""
        with patch("prometheus_client.Counter") as mock_counter:
            with patch("prometheus_client.Histogram") as mock_histogram:
                with patch("prometheus_client.Gauge") as mock_gauge:
                    mock_counter.return_value = MagicMock()
                    mock_histogram.return_value = MagicMock()
                    mock_gauge.return_value = MagicMock()

                    collector = CustomMetricsCollector()

                    # Verify metrics were initialized
                    assert collector.request_counter is not None
                    assert collector.request_duration is not None
                    assert collector.custom_gauge is not None

    def test_metrics_initialization_exception_handling(self):
        """Test exception handling in metrics initialization."""
        with patch("prometheus_client.Counter", side_effect=Exception("Metric error")):
            with patch("logging.getLogger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                collector = CustomMetricsCollector()

                # Verify fallback behavior
                assert collector.request_counter is None
                assert collector.request_duration is None
                assert collector.custom_gauge is None
                mock_logger.error.assert_called()

    def test_record_request_success(self, monkeypatch):
        """Test successful request recording."""
        # Arrange
        collector = CustomMetricsCollector()
        worker_id = "worker_1"
        duration = 0.5
        method = "POST"

        # Mock the metrics to avoid actual Prometheus calls
        mock_counter = MagicMock()
        mock_histogram = MagicMock()
        collector.request_counter = mock_counter
        collector.request_duration = mock_histogram

        # Act
        collector.record_request(worker_id, duration, method)

        # Assert
        mock_counter.labels.assert_called_once_with(
            worker_id=worker_id,
            collector_id=collector.collector_id
        )
        mock_histogram.labels.assert_called_once_with(
            worker_id=worker_id,
            collector_id=collector.collector_id
        )

    def test_record_request_with_uninitialized_metrics(self):
        """Test request recording when metrics are not initialized."""
        collector = CustomMetricsCollector()
        collector.request_counter = None
        collector.request_duration = None

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Act
            collector.record_request("worker_1", 0.5)

            # Assert
            mock_logger.warning.assert_called_with(
                "Metrics not initialized, skipping request recording"
            )

    def test_record_request_exception_handling(self):
        """Test exception handling in request recording."""
        collector = CustomMetricsCollector()

        # Mock metrics to raise exception
        mock_counter = MagicMock()
        mock_counter.labels.side_effect = Exception("Metric error")
        collector.request_counter = mock_counter

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Act
            collector.record_request("worker_1", 0.5)

            # Assert
            mock_logger.error.assert_called()

    def test_update_active_requests_success(self):
        """Test successful active requests update."""
        collector = CustomMetricsCollector()

        # Mock the gauge
        mock_gauge = MagicMock()
        collector.custom_gauge = mock_gauge

        # Act
        collector.update_active_requests("worker_1", 5)

        # Assert
        mock_gauge.labels.assert_called_once_with(
            worker_id="worker_1",
            collector_id=collector.collector_id
        )
        mock_gauge.labels().set.assert_called_once_with(5)

    def test_update_active_requests_with_uninitialized_gauge(self):
        """Test active requests update when gauge is not initialized."""
        collector = CustomMetricsCollector()
        collector.custom_gauge = None

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Act
            collector.update_active_requests("worker_1", 5)

            # Assert
            mock_logger.warning.assert_called_with(
                "Gauge not initialized, skipping update"
            )

    @patch('gunicorn_prometheus_exporter.custom_metrics.logging')
    def test_logging_on_request_record(self, mock_logging):
        """Test that requests are logged correctly."""
        collector = CustomMetricsCollector()

        # Mock metrics
        mock_counter = MagicMock()
        mock_histogram = MagicMock()
        collector.request_counter = mock_counter
        collector.request_duration = mock_histogram

        # Act
        collector.record_request("worker_1", 0.5, "GET")

        # Assert
        collector.logger.debug.assert_called_once_with(
            "Recorded request for worker %s with duration %.3f and method %s",
            "worker_1", 0.5, "GET"
        )


class TestCustomMetricsIntegration:
    """Integration tests for custom metrics.

    This class follows the pattern from tests/test_worker.py:
    - End-to-end testing
    - Real Gunicorn integration
    - Metric validation
    """

    def test_metrics_integration_with_gunicorn(self):
        """Test that custom metrics work with actual Gunicorn workers."""
        # This would be an integration test using real Gunicorn
        # Following the pattern from tests/test_worker.py
        pass

    def test_metrics_collection_under_load(self):
        """Test metrics collection under high load conditions."""
        # This would test metrics collection during high traffic
        # Following the pattern from tests/test_worker.py
        pass
```

### Test Coverage

We aim for high test coverage. Check coverage with:

```bash
tox -e py312 -- --cov=gunicorn_prometheus_exporter --cov-report=term-missing
```

## ⚙️ Configuration Patterns

### Configuration Management

Following the patterns from `src/gunicorn_prometheus_exporter/config.py`:

```python
"""
Configuration management for custom extensions.

This module follows the established patterns from the main config.py:
- Environment variable-based configuration
- Validation with clear error messages
- Default values for development
- Production requirements clearly marked
"""

import logging
import os
from typing import Optional


class CustomExporterConfig:
    """Configuration class for custom extensions.

    This class follows the pattern from ExporterConfig:
    - Environment variable-based configuration
    - Validation with clear error messages
    - Default values for development
    - Production requirements clearly marked
    """

    # Default values (only for development/testing)
    _default_custom_dir = os.path.join(
        os.path.expanduser("~"), ".custom_gunicorn"
    )
    CUSTOM_MULTIPROC_DIR = os.environ.get(
        "CUSTOM_MULTIPROC_DIR", _default_custom_dir
    )

    # Production settings - no defaults, must be set by user
    CUSTOM_METRICS_PORT = None  # Must be set by user in production
    CUSTOM_BIND_ADDRESS = None  # Must be set by user in production
    CUSTOM_WORKERS = None  # Must be set by user in production

    # Environment variable names
    ENV_CUSTOM_MULTIPROC_DIR = "CUSTOM_MULTIPROC_DIR"
    ENV_CUSTOM_METRICS_PORT = "CUSTOM_METRICS_PORT"
    ENV_CUSTOM_BIND_ADDRESS = "CUSTOM_BIND_ADDRESS"
    ENV_CUSTOM_WORKERS = "CUSTOM_WORKERS"

    def __init__(self):
        """Initialize configuration with environment variables and defaults.

        Note: This modifies os.environ during initialization to set up
        the multiprocess directory if not already set.
        """
        self._setup_multiproc_dir()

    def _setup_multiproc_dir(self):
        """Set up the custom multiprocess directory."""
        if not os.environ.get(self.ENV_CUSTOM_MULTIPROC_DIR):
            os.environ[
                self.ENV_CUSTOM_MULTIPROC_DIR
            ] = self.CUSTOM_MULTIPROC_DIR

    @property
    def custom_multiproc_dir(self) -> str:
        """Get the custom multiprocess directory path."""
        return os.environ.get(
            self.ENV_CUSTOM_MULTIPROC_DIR, self.CUSTOM_MULTIPROC_DIR
        )

    @property
    def custom_metrics_port(self) -> int:
        """Get the custom metrics server port."""
        value = os.environ.get(
            self.ENV_CUSTOM_METRICS_PORT, self.CUSTOM_METRICS_PORT
        )
        if value is None:
            raise ValueError(
                f"Environment variable {self.ENV_CUSTOM_METRICS_PORT} "
                f"must be set in production. "
                f"Example: export {self.ENV_CUSTOM_METRICS_PORT}=9092"
            )
        return int(value)

    @property
    def custom_bind_address(self) -> str:
        """Get the custom metrics server bind address."""
        value = os.environ.get(
            self.ENV_CUSTOM_BIND_ADDRESS, self.CUSTOM_BIND_ADDRESS
        )
        if value is None:
            raise ValueError(
                f"Environment variable {self.ENV_CUSTOM_BIND_ADDRESS} "
                f"must be set in production. "
                f"Example: export {self.ENV_CUSTOM_BIND_ADDRESS}=0.0.0.0"
            )
        return value

    @property
    def custom_workers(self) -> int:
        """Get the number of custom workers."""
        value = os.environ.get(self.ENV_CUSTOM_WORKERS, self.CUSTOM_WORKERS)
        if value is None:
            raise ValueError(
                f"Environment variable {self.ENV_CUSTOM_WORKERS} "
                f"must be set in production. "
                f"Example: export {self.ENV_CUSTOM_WORKERS}=2"
            )
        return int(value)

    def validate(self) -> bool:
        """Validate the configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate required settings
            _ = self.custom_metrics_port
            _ = self.custom_bind_address
            _ = self.custom_workers

            # Validate port range
            port = self.custom_metrics_port
            if not (1024 <= port <= 65535):
                logging.error("Custom metrics port must be between 1024 and 65535")
                return False

            return True

        except ValueError as e:
            logging.error("Configuration validation failed: %s", e)
            return False
        except Exception as e:
            logging.error("Unexpected error during validation: %s", e)
            return False

    def print_config(self):
        """Print the current configuration for debugging."""
        logging.info("Custom Configuration:")
        logging.info("  Multiprocess Directory: %s", self.custom_multiproc_dir)
        logging.info("  Metrics Port: %s", self.custom_metrics_port)
        logging.info("  Bind Address: %s", self.custom_bind_address)
        logging.info("  Workers: %s", self.custom_workers)
```

## 🔌 Hook Patterns

### Custom Gunicorn Hooks

Following the patterns from `src/gunicorn_prometheus_exporter/hooks.py`:

```python
"""
Custom Gunicorn hooks for extensions.

This module provides ready-to-use hook functions that can be imported
and assigned to Gunicorn configuration variables.

Available hooks:
- custom_on_starting: Initialize custom metrics
- custom_when_ready: Start custom metrics server
- custom_worker_int: Handle custom worker interrupts
- custom_on_exit: Cleanup on server exit
"""

import logging
import time
from typing import Any, Union

from prometheus_client import start_http_server
from prometheus_client.multiprocess import MultiProcessCollector


def custom_on_starting(_server: Any) -> None:
    """Custom on_starting hook to initialize custom metrics.

    This function follows the pattern from default_on_starting:
    1. Ensures the multiprocess directory exists
    2. Initializes custom metrics
    3. Logs initialization status

    Args:
        _server: Gunicorn server instance (unused)
    """
    from .utils import ensure_multiprocess_dir, get_multiprocess_dir

    mp_dir = get_multiprocess_dir()
    if not mp_dir:
        logging.warning(
            "CUSTOM_MULTIPROC_DIR not set; skipping custom metrics initialization"
        )
        return

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Master starting - initializing CustomMaster metrics")

    # Ensure the multiprocess directory exists
    ensure_multiprocess_dir(mp_dir)
    logger.info(" Custom multiprocess directory ready: %s", mp_dir)

    logger.info(" Custom metrics initialized")


def _setup_custom_prometheus_server(logger: logging.Logger) -> Union[tuple[int, Any], None]:
    """Set up custom Prometheus multiprocess metrics server.

    This function follows the pattern from _setup_prometheus_server:
    1. Validates multiprocess directory configuration
    2. Initializes MultiProcessCollector
    3. Returns port and registry for server startup

    Args:
        logger: Logger instance for status messages

    Returns:
        Tuple of (port, registry) if successful, None if failed
    """
    from .metrics import registry
    from .utils import get_multiprocess_dir

    mp_dir = get_multiprocess_dir()
    if not mp_dir:
        logger.warning("CUSTOM_MULTIPROC_DIR not set; skipping metrics server")
        return None

    port = 9092  # Custom port

    # Initialize MultiProcessCollector
    try:
        MultiProcessCollector(registry)
        logger.info("Successfully initialized custom MultiProcessCollector")
    except Exception as e:
        logger.error("Failed to initialize custom MultiProcessCollector: %s", e)
        return None

    return port, registry


def custom_when_ready(_server: Any) -> None:
    """Custom when_ready hook with Prometheus metrics.

    This function follows the pattern from default_when_ready:
    1. Sets up Prometheus multiprocess metrics collection
    2. Starts the Prometheus metrics HTTP server with retry logic
    3. Logs status information

    Args:
        _server: Gunicorn server instance (unused)
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting custom Prometheus metrics server")

    # Set up Prometheus server
    server_info = _setup_custom_prometheus_server(logger)
    if not server_info:
        logger.error("Failed to set up custom Prometheus server")
        return

    port, registry = server_info

    # Start HTTP server with retry logic
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            start_http_server(port, registry=registry)
            logger.info(
                "Custom Prometheus metrics server started on port %d (attempt %d)",
                port, attempt + 1
            )
            return
        except Exception as e:
            logger.warning(
                "Failed to start custom metrics server on attempt %d: %s",
                attempt + 1, e
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2

    logger.error("Failed to start custom Prometheus metrics server after %d attempts", max_retries)


def custom_worker_int(worker: Any) -> None:
    """Custom worker_int hook to handle worker interrupts.

    This function follows the pattern from default_worker_int:
    1. Updates custom worker metrics
    2. Handles worker-specific cleanup
    3. Logs worker status

    Args:
        worker: Gunicorn worker instance
    """
    logger = logging.getLogger(__name__)
    logger.info("Worker interrupt received for worker %s", worker.pid)

    try:
        # Update custom worker metrics
        if hasattr(worker, 'update_custom_worker_metrics'):
            worker.update_custom_worker_metrics()
            logger.debug("Updated custom worker metrics for worker %s", worker.pid)
    except Exception as e:
        logger.error(
            "Failed to update custom worker metrics for worker %s: %s",
            worker.pid, e
        )


def custom_on_exit(_server: Any) -> None:
    """Custom on_exit hook for cleanup.

    This function follows the pattern from default_on_exit:
    1. Performs custom cleanup tasks
    2. Logs cleanup status
    3. Handles cleanup errors gracefully

    Args:
        _server: Gunicorn server instance (unused)
    """
    logger = logging.getLogger(__name__)
    logger.info("Custom cleanup starting")

    try:
        # Perform custom cleanup tasks
        logger.info("Custom cleanup completed successfully")
    except Exception as e:
        logger.error("Custom cleanup failed: %s", e)
```

## 📊 Metrics Patterns

### Custom Metrics Definition

Following the patterns from `src/gunicorn_prometheus_exporter/metrics.py`:

```python
"""
Custom Prometheus metrics for extensions.

This module follows the established patterns from the main metrics.py:
- BaseMetric class with metaclass
- Automatic registry registration
- Label-based metrics
- Comprehensive error handling
"""

import logging
from abc import ABCMeta
from typing import Dict, List, Optional, Type, Union

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram


class CustomMetricMeta(ABCMeta):
    """Metaclass for automatically registering custom metrics with the registry.

    This follows the pattern from MetricMeta in the main metrics.py.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple,
        namespace: Dict,
        metric_type: Optional[Type[Union[Counter, Gauge, Histogram]]] = None,
        **kwargs,
    ) -> Type:
        """Create a new custom metric class and register it with the registry."""
        cls = super().__new__(mcs, name, bases, namespace)

        if metric_type is not None:
            extra_ctor_args = {}
            # Forward well‑known optional attributes
            for opt in ("buckets", "unit", "namespace", "subsystem"):
                if opt in namespace:
                    extra_ctor_args[opt] = namespace[opt]

            metric = metric_type(
                name=namespace.get("name", name.lower()),
                documentation=namespace.get("documentation", ""),
                labelnames=namespace.get("labelnames", []),
                registry=registry,
                **extra_ctor_args,
                **kwargs,
            )
            cls._metric = metric
        return cls


class CustomBaseMetric(metaclass=CustomMetricMeta):
    """Base class for all custom metrics.

    This follows the pattern from BaseMetric in the main metrics.py.
    """

    name: str
    documentation: str
    labelnames: List[str]

    @classmethod
    def labels(cls, **kwargs):
        """Get a labeled instance of the metric."""
        return cls._metric.labels(**kwargs)

    @classmethod
    def collect(cls):
        """Collect metric samples."""
        return cls._metric.collect()

    @classmethod
    def inc(cls, **labels):
        """Increment the metric."""
        return cls._metric.labels(**labels).inc()

    @classmethod
    def dec(cls, **labels):
        """Decrement the metric."""
        return cls._metric.labels(**labels).dec()

    @classmethod
    def set(cls, value, **labels):
        """Set the metric value."""
        return cls._metric.labels(**labels).set(value)

    @classmethod
    def observe(cls, value, **labels):
        """Observe a value for histogram metrics."""
        return cls._metric.labels(**labels).observe(value)


class CustomWorkerRequests(CustomBaseMetric, metric_type=Counter):
    """Total number of custom requests handled by this worker."""

    name = "custom_worker_requests"
    documentation = "Total number of custom requests handled by this worker"
    labelnames = ["worker_id", "custom_type"]


class CustomWorkerRequestDuration(CustomBaseMetric, metric_type=Histogram):
    """Custom request duration in seconds."""

    name = "custom_worker_request_duration_seconds"
    documentation = "Custom request duration in seconds"
    labelnames = ["worker_id", "custom_type"]
    buckets = (0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf"))


class CustomWorkerMemory(CustomBaseMetric, metric_type=Gauge):
    """Custom memory usage of the worker process."""

    name = "custom_worker_memory_bytes"
    documentation = "Custom memory usage of the worker process"
    labelnames = ["worker_id", "custom_type"]


class CustomWorkerState(CustomBaseMetric, metric_type=Gauge):
    """Current custom state of the worker."""

    name = "custom_worker_state"
    documentation = "Current custom state of the worker (1=running, 0=stopped)"
    labelnames = ["worker_id", "state", "custom_type", "timestamp"]
```

## 🧪 Testing Patterns

### Test Structure and Organization

Following the patterns from our test files:

```python
"""
Tests for custom extensions.

This test file follows the established patterns from tests/test_plugin.py
and tests/test_metrics.py with comprehensive test coverage.

TESTING PATTERNS:
================

1. COMPREHENSIVE COVERAGE:
   - Test initialization with minimal mocking
   - Test success paths and error handling
   - Test logging verification
   - Test integration scenarios

2. FIXTURE USAGE:
   - Use pytest fixtures for common setup
   - Follow patterns from tests/conftest.py
   - Proper environment variable management

3. MOCKING STRATEGIES:
   - Mock external dependencies
   - Use MagicMock for complex objects
   - Verify mock calls and interactions

4. ERROR HANDLING:
   - Test exception scenarios
   - Verify fallback behavior
   - Check error logging
"""

import logging
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from gunicorn_prometheus_exporter.custom_metrics import CustomMetricsCollector


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment with required variables.

    This follows the pattern from tests/conftest.py.
    """
    # Set up required environment variables for testing
    os.environ.setdefault("CUSTOM_BIND_ADDRESS", "127.0.0.1")
    os.environ.setdefault("CUSTOM_METRICS_PORT", "9092")
    os.environ.setdefault("CUSTOM_WORKERS", "2")

    # Set up the custom multiprocess directory
    temp_dir = tempfile.mkdtemp()
    os.environ["CUSTOM_MULTIPROC_DIR"] = temp_dir
    yield
    os.environ.pop("CUSTOM_MULTIPROC_DIR", None)


@pytest.fixture
def custom_registry():
    """Create a fresh Prometheus registry for testing."""
    from prometheus_client import CollectorRegistry
    return CollectorRegistry()


class TestCustomMetricsCollector:
    """Test cases for CustomMetricsCollector class.

    This class follows the pattern from tests/test_plugin.py:
    - Comprehensive test coverage for initialization
    - Error handling tests with fallbacks
    - Logging verification
    - Mock usage for external dependencies
    """

    def test_collector_import(self):
        """Test that CustomMetricsCollector can be imported and is a class."""
        assert hasattr(CustomMetricsCollector, "__init__")
        assert callable(CustomMetricsCollector.__init__)

    def test_collector_initialization_simple(self):
        """Test CustomMetricsCollector initialization with minimal mocking."""
        with patch("gunicorn_prometheus_exporter.custom_metrics._setup_logging") as mock_setup:
            collector = CustomMetricsCollector()

            mock_setup.assert_called_once()
            assert hasattr(collector, "start_time")
            assert hasattr(collector, "collector_id")
            assert hasattr(collector, "logger")
            assert collector.collector_id.startswith("collector_")

    def test_metrics_initialization_success(self):
        """Test successful metrics initialization."""
        with patch("prometheus_client.Counter") as mock_counter:
            with patch("prometheus_client.Histogram") as mock_histogram:
                with patch("prometheus_client.Gauge") as mock_gauge:
                    mock_counter.return_value = MagicMock()
                    mock_histogram.return_value = MagicMock()
                    mock_gauge.return_value = MagicMock()

                    collector = CustomMetricsCollector()

                    # Verify metrics were initialized
                    assert collector.request_counter is not None
                    assert collector.request_duration is not None
                    assert collector.custom_gauge is not None

    def test_metrics_initialization_exception_handling(self):
        """Test exception handling in metrics initialization."""
        with patch("prometheus_client.Counter", side_effect=Exception("Metric error")):
            with patch("logging.getLogger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                collector = CustomMetricsCollector()

                # Verify fallback behavior
                assert collector.request_counter is None
                assert collector.request_duration is None
                assert collector.custom_gauge is None
                mock_logger.error.assert_called()

    def test_record_request_success(self, monkeypatch):
        """Test successful request recording."""
        # Arrange
        collector = CustomMetricsCollector()
        worker_id = "worker_1"
        duration = 0.5
        method = "POST"

        # Mock the metrics to avoid actual Prometheus calls
        mock_counter = MagicMock()
        mock_histogram = MagicMock()
        collector.request_counter = mock_counter
        collector.request_duration = mock_histogram

        # Act
        collector.record_request(worker_id, duration, method)

        # Assert
        mock_counter.labels.assert_called_once_with(
            worker_id=worker_id,
            collector_id=collector.collector_id
        )
        mock_histogram.labels.assert_called_once_with(
            worker_id=worker_id,
            collector_id=collector.collector_id
        )

    def test_record_request_with_uninitialized_metrics(self):
        """Test request recording when metrics are not initialized."""
        collector = CustomMetricsCollector()
        collector.request_counter = None
        collector.request_duration = None

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Act
            collector.record_request("worker_1", 0.5)

            # Assert
            mock_logger.warning.assert_called_with(
                "Metrics not initialized, skipping request recording"
            )

    def test_record_request_exception_handling(self):
        """Test exception handling in request recording."""
        collector = CustomMetricsCollector()

        # Mock metrics to raise exception
        mock_counter = MagicMock()
        mock_counter.labels.side_effect = Exception("Metric error")
        collector.request_counter = mock_counter

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Act
            collector.record_request("worker_1", 0.5)

            # Assert
            mock_logger.error.assert_called()

    @patch('gunicorn_prometheus_exporter.custom_metrics.logging')
    def test_logging_on_request_record(self, mock_logging):
        """Test that requests are logged correctly."""
        collector = CustomMetricsCollector()

        # Mock metrics
        mock_counter = MagicMock()
        mock_histogram = MagicMock()
        collector.request_counter = mock_counter
        collector.request_duration = mock_histogram

        # Act
        collector.record_request("worker_1", 0.5, "GET")

        # Assert
        collector.logger.debug.assert_called_once_with(
            "Recorded request for worker %s with duration %.3f and method %s",
            "worker_1", 0.5, "GET"
        )


class TestCustomMetricsIntegration:
    """Integration tests for custom metrics.

    This class follows the pattern from tests/test_worker.py:
    - End-to-end testing
    - Real Gunicorn integration
    - Metric validation
    """

    def test_metrics_integration_with_gunicorn(self):
        """Test that custom metrics work with actual Gunicorn workers."""
        # This would be an integration test using real Gunicorn
        # Following the pattern from tests/test_worker.py
        pass

    def test_metrics_collection_under_load(self):
        """Test metrics collection under high load conditions."""
        # This would test metrics collection during high traffic
        # Following the pattern from tests/test_worker.py
        pass
```

## 📚 Documentation

### Documentation Standards

1. **Docstrings**: Use Google-style docstrings for all public functions and classes
2. **README**: Keep the main README updated
3. **Examples**: Provide working examples for all features
4. **API Documentation**: Document all public APIs

### Building Documentation

```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Build documentation
mkdocs build

# Serve documentation locally
mkdocs serve
```

### Documentation Structure

```
docs/
├── index.md              # Home page
├── installation.md       # Installation guide
├── configuration.md      # Configuration reference
├── metrics.md           # Metrics documentation
├── examples/            # Framework examples
│   ├── django-integration.md
│   ├── fastapi-integration.md
│   └── ...
├── api-reference.md     # API documentation
├── troubleshooting.md   # Troubleshooting guide
└── contributing.md      # This file
```

## Development Tools

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
pip install pre-commit
pre-commit install
```

### Tox Configuration

The project uses tox for testing. Key environments:

- `py39`, `py310`, `py311`, `py312`: Python version testing
- `lint`: Code linting with Ruff
- `format`: Code formatting with Ruff
- `docs`: Documentation building

### IDE Configuration

**VS Code Settings** (`.vscode/settings.json`):

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": false,
    "python.formatting.provider": "none",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

## 🐛 Bug Reports

### Before Reporting a Bug

1. **Check existing issues**: Search for similar issues
2. **Reproduce the issue**: Ensure you can reproduce it consistently
3. **Test with minimal setup**: Try with basic configuration
4. **Check logs**: Include relevant log output

### Bug Report Template

```markdown
**Bug Description**
A clear description of what the bug is.

**Steps to Reproduce**
1. Install package with `pip install gunicorn-prometheus-exporter`
2. Create configuration file `gunicorn.conf.py`
3. Start server with `gunicorn -c gunicorn.conf.py app:app`
4. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- Python version: 3.9.0
- Gunicorn version: 21.2.0
- Operating system: Ubuntu 20.04
- Package version: 0.1.0

**Configuration**
```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
# ... rest of configuration
```

**Logs**
```
[2024-01-01 12:00:00] ERROR: Failed to start metrics server
```

**Additional Context**
Any other context about the problem.
```

## Feature Requests

### Feature Request Template

```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Use Case**
Why this feature would be useful.

**Proposed Implementation**
How you think this could be implemented (optional).

**Alternatives Considered**
Other approaches you've considered (optional).

**Additional Context**
Any other context about the feature request.
```

## 🔄 Pull Request Process

### Before Submitting a PR

1. **Run all tests**: Ensure all tests pass
2. **Check linting**: Ensure code follows style guidelines
3. **Update documentation**: Add/update relevant documentation
4. **Add tests**: Include tests for new functionality
5. **Update changelog**: Add entry to CHANGELOG.md if needed

### PR Template

```markdown
**Description**
Brief description of changes.

**Type of Change**
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Test addition/update
- [ ] Other (please describe)

**Testing**
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated

**Checklist**
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] Commit messages follow conventional format

**Related Issues**
Closes #123
```

### PR Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and linting
2. **Code Review**: Maintainers review the code
3. **Discussion**: Address any feedback or questions
4. **Merge**: Once approved, the PR is merged

## 🏷️ Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes (backward compatible)

### Release Checklist

1. **Update version**: Update version in `pyproject.toml`
2. **Update changelog**: Add release notes to `CHANGELOG.md`
3. **Create release**: Create GitHub release
4. **Publish package**: Publish to PyPI

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Help others learn and grow
- Provide constructive feedback
- Follow the project's coding standards

### Communication

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and discussions
- **Pull Requests**: For code contributions

## 📞 Getting Help

### Questions and Support

- **Documentation**: Check the documentation first
- **GitHub Issues**: Search existing issues
- **GitHub Discussions**: Ask questions in discussions
- **Examples**: Review framework-specific examples

### Mentorship

New contributors are welcome! Feel free to:

- Ask questions in GitHub discussions
- Start with "good first issue" labels
- Request help with your first contribution

## 🙏 Acknowledgments

Thank you for contributing to the Gunicorn Prometheus Exporter! Your contributions help make this project better for everyone.

## Related Links

- [GitHub Repository](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter)
- [Issue Tracker](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/issues)
- [Documentation](https://agent-hellboy.github.io/gunicorn-prometheus-exporter/)
- [PyPI Package](https://pypi.org/project/gunicorn-prometheus-exporter/)

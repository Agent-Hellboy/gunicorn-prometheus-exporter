# Logging Module Usage

The `gunicorn-prometheus-exporter` includes a basic logging module that provides centralized logging configuration and utilities.

## Basic Usage

### Import the logging module

```python
from gunicorn_prometheus_exporter.logging import (
    LoggerMixin,
    get_logger,
    setup_logging,
    log_configuration,
    log_error_with_context,
    log_system_info
)
```

### Setup Logging

```python
# Basic setup with default configuration
setup_logging()

# Setup with custom level
setup_logging(level="DEBUG")

# Setup with log file
setup_logging(level="INFO", log_file="/var/log/gunicorn-prometheus.log")

# Setup with custom format
setup_logging(
    level="DEBUG",
    format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Using LoggerMixin

The `LoggerMixin` class provides convenient logging methods for any class:

```python
class MyWorker(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.log_info("Worker initialized")

    def process_request(self):
        try:
            # Process request
            self.log_debug("Processing request")
        except Exception as e:
            self.log_error("Error processing request: %s", e)
```

### Getting Logger Instances

```python
# Get logger for current module
logger = get_logger(__name__)

# Get logger for a class
logger = get_logger_for_class(MyClass)

# Use the logger
logger.info("This is an info message")
logger.error("This is an error message")
```

### Utility Functions

```python
# Log configuration dictionary
config_dict = {"workers": 4, "timeout": 30}
log_configuration(config_dict)

# Log error with context
try:
    # Some operation
    pass
except Exception as e:
    log_error_with_context(e, {"function": "my_function", "args": ["arg1"]})

# Log system information
log_system_info()
```

## Integration with Gunicorn

The logging module automatically integrates with Gunicorn configuration:

```python
# This will read log level from Gunicorn config
from gunicorn_prometheus_exporter.logging import configure_from_gunicorn_config

configure_from_gunicorn_config()
```

## Features

- **Centralized Configuration**: Single place to configure logging for the entire application
- **File Rotation**: Automatic log file rotation with configurable size and backup count
- **Gunicorn Integration**: Automatically reads logging configuration from Gunicorn config
- **LoggerMixin**: Convenient mixin class for adding logging to any class
- **Utility Functions**: Helper functions for common logging tasks
- **System Information Logging**: Built-in function to log system information

## Configuration Options

- `level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_file`: Optional log file path
- `format_string`: Custom log format string
- `max_bytes`: Maximum size of log file before rotation (default: 10MB)
- `backup_count`: Number of backup files to keep (default: 5)

## Example Integration

Here's how the logging module is integrated into the existing components:

```python
# In hooks.py
class HookManager(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.log_info("Hook manager initialized")

# In plugin.py
class PrometheusMixin(LoggerMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_info("PrometheusMixin initialized with ID: %s", self.worker_id)
```

The logging module provides a clean, consistent way to handle logging throughout the gunicorn-prometheus-exporter project.

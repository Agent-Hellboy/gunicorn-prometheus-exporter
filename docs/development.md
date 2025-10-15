# Development Setup

This guide covers setting up a development environment for Gunicorn Prometheus Exporter.

## Prerequisites

- Python 3.8 or higher
- Git
- pip
- tox (for testing)

## Setup

### Clone the Repository

```bash
git clone https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter.git
cd gunicorn-prometheus-exporter
```

### Install Development Dependencies

```bash
# Install in development mode with all dependencies
pip install -e ".[dev]"

# Or install specific extras
pip install -e ".[async,redis,dev]"
```

### Development Dependencies

The `[dev]` extra includes:

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `ruff` - Linting and formatting
- `mypy` - Type checking
- `tox` - Testing across Python versions

## Running Tests

### Using pytest

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/gunicorn_prometheus_exporter --cov-report=html

# Run specific test file
pytest tests/test_plugin.py

# Run tests with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Using tox

```bash
# Run all test environments
tox

# Run specific environment
tox -e py311

# Run linting only
tox -e lint

# Run formatting only
tox -e format
```

## Code Quality

### Linting

```bash
# Check code with ruff
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/
```

### Formatting

```bash
# Format code with ruff
ruff format src/ tests/

# Check formatting without changes
ruff format --check src/ tests/
```

### Type Checking

```bash
# Run mypy type checking
mypy src/gunicorn_prometheus_exporter/
```

## Project Structure

```
gunicorn-prometheus-exporter/
├── src/
│   └── gunicorn_prometheus_exporter/
│       ├── __init__.py
│       ├── backend/           # Redis backend implementation
│       ├── config.py          # Configuration management
│       ├── hooks.py           # Gunicorn hooks
│       ├── logging.py         # Logging utilities
│       ├── master.py          # Master process monitoring
│       ├── metrics.py         # Metrics collection
│       ├── plugin.py          # Gunicorn plugin
│       └── utils.py           # Utility functions
├── tests/                     # Unit tests (pytest)
├── integration/               # Integration tests
├── e2e/                       # End-to-end tests (Docker + K8s)
├── docs/                      # Documentation
├── example/                   # Example applications
├── pyproject.toml            # Project configuration
├── tox.ini                   # Tox configuration
└── README.md
```

### Test Structure

Following the Test Pyramid:

```
┌─────────────────────────────────────┐
│  e2e/                               │  ← Docker + Kubernetes
├─────────────────────────────────────┤
│  integration/                       │  ← Component integration
├─────────────────────────────────────┤
│  tests/                             │  ← Unit tests (pytest)
└─────────────────────────────────────┘
```

- *tests/*: Unit tests using pytest
- *integration/*: Component integration tests (exporter + Gunicorn + storage)
- *e2e/*: End-to-end tests with Docker and Kubernetes deployments

## Adding New Features

### 1. Create a Feature Branch

```bash
git checkout -b feature/new-feature
```

### 2. Implement the Feature

- Add your code to the appropriate module
- Follow existing code patterns and style
- Add type hints where appropriate
- Include docstrings for public functions

### 3. Add Tests

- Create test files in the `tests/` directory
- Test both success and failure cases
- Aim for high test coverage

### 4. Update Documentation

- Update relevant documentation files
- Add examples if applicable
- Update the changelog

### 5. Run Quality Checks

```bash
# Run all quality checks
tox

# Or run individually
ruff check src/ tests/
ruff format src/ tests/
mypy src/gunicorn_prometheus_exporter/
pytest
```

## Testing Guidelines

### Unit Tests (`tests/`)

- Test individual functions and methods
- Mock external dependencies
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Run with: `pytest` or `tox`

### Integration Tests (`integration/`)

- Test component interactions (exporter + Gunicorn + storage)
- Use real dependencies (Redis, Gunicorn)
- Test error handling and edge cases
- No containers required
- Run with: `make -f e2e/Makefile integration-test-redis-quick`

### E2E Tests (`e2e/`)

- Test complete deployment workflows
- Docker containers and Kubernetes clusters
- Test with different worker types
- Verify metrics collection in production-like environments
- Run with: `make -f e2e/Makefile docker-test` or check `.github/workflows/`

## Code Style

### Python Style

- Follow PEP 8
- Use type hints
- Write descriptive docstrings
- Use meaningful variable names

### Import Organization

```python
# Standard library imports
import os
import sys

# Third-party imports
import prometheus_client
from gunicorn import util

# Local imports
from .config import Config
from .metrics import Metrics
```

### Error Handling

```python
try:
    # Risky operation
    result = risky_function()
except SpecificException as e:
    logger.error(f"Specific error occurred: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

## Debugging

### Enable Debug Logging

```bash
# Set debug environment variables
export PROMETHEUS_DEBUG="true"
export GUNICORN_DEBUG="true"
export REDIS_DEBUG="true"
```

### Using pdb

```python
import pdb; pdb.set_trace()
```

### Using logging

```python
import logging

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

## Performance Testing

### Load Testing

```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f load_test.py --host=http://localhost:8000
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler your_script.py
```

## Release Process

### 1. Update Version

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
```

### 2. Create Release

```bash
# Create and push tag
git tag v1.0.0
git push origin v1.0.0
```

### 3. Build and Publish

```bash
# Build package
python -m build

# Publish to PyPI
python -m twine upload dist/*
```

## Contributing

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

### Pull Request Guidelines

- Include a clear description
- Reference related issues
- Ensure all tests pass
- Update documentation if needed
- Keep changes focused and atomic

## Common Issues

### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e .
```

### Test Failures

```bash
# Check test environment
pytest --collect-only

# Run tests with verbose output
pytest -v -s
```

### Linting Errors

```bash
# Check specific file
ruff check src/gunicorn_prometheus_exporter/plugin.py

# Fix auto-fixable issues
ruff check --fix src/gunicorn_prometheus_exporter/plugin.py
```

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [tox Documentation](https://tox.wiki/)

## Related Documentation

- [Contributing Guide](contributing.md) - How to contribute
- [Backend API](components/backend/api-reference.md) - Backend API documentation
- [Config API](components/config/api-reference.md) - Configuration API documentation
- [Hooks API](components/hooks/api-reference.md) - Hooks API documentation
- [Metrics API](components/metrics/api-reference.md) - Metrics API documentation
- [Plugin API](components/plugin/api-reference.md) - Plugin API documentation
- [Troubleshooting Guide](troubleshooting.md) - Common issues

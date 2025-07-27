# Contributing Guide

Thank you for your interest in contributing to the Gunicorn Prometheus Exporter! This guide will help you get started.

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
   git clone https://github.com/your-username/gunicorn-prometheus-exporter.git
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

```python
"""Module for handling Prometheus metrics collection."""

import logging
from typing import Dict, Optional

from prometheus_client import Counter, Histogram


class MetricsCollector:
    """Collects and manages Prometheus metrics for Gunicorn workers.

    This class provides methods for collecting various metrics from
    Gunicorn workers including request counts, durations, and errors.

    Args:
        registry: Prometheus registry to use for metrics

    Example:
        >>> collector = MetricsCollector()
        >>> collector.record_request(duration=0.5)
    """

    def __init__(self, registry: Optional[object] = None) -> None:
        """Initialize the metrics collector.

        Args:
            registry: Prometheus registry to use for metrics
        """
        self.logger = logging.getLogger(__name__)
        self.registry = registry

        # Initialize metrics
        self.request_counter = Counter(
            'gunicorn_requests_total',
            'Total requests processed',
            ['worker_id']
        )

        self.request_duration = Histogram(
            'gunicorn_request_duration_seconds',
            'Request duration in seconds',
            ['worker_id']
        )

    def record_request(self, worker_id: str, duration: float) -> None:
        """Record a request with its duration.

        Args:
            worker_id: ID of the worker that processed the request
            duration: Request duration in seconds
        """
        self.request_counter.labels(worker_id=worker_id).inc()
        self.request_duration.labels(worker_id=worker_id).observe(duration)
        self.logger.debug(
            "Recorded request for worker %s with duration %.3f",
            worker_id, duration
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

```python
"""Tests for the metrics module."""

import pytest
from unittest.mock import Mock, patch

from gunicorn_prometheus_exporter.metrics import MetricsCollector


class TestMetricsCollector:
    """Test cases for MetricsCollector class."""

    @pytest.fixture
    def collector(self):
        """Create a MetricsCollector instance for testing."""
        return MetricsCollector()

    def test_record_request(self, collector):
        """Test that request recording works correctly."""
        # Arrange
        worker_id = "worker_1"
        duration = 0.5

        # Act
        collector.record_request(worker_id, duration)

        # Assert
        # Check that metrics were updated
        sample = next(collector.request_counter.collect())
        assert sample.samples[0].value == 1.0

        sample = next(collector.request_duration.collect())
        assert sample.samples[0].value == 0.5

    def test_record_request_with_invalid_duration(self, collector):
        """Test that invalid duration raises appropriate error."""
        with pytest.raises(ValueError, match="Duration must be positive"):
            collector.record_request("worker_1", -1.0)

    @patch('gunicorn_prometheus_exporter.metrics.logging')
    def test_logging_on_request_record(self, mock_logging, collector):
        """Test that requests are logged correctly."""
        # Act
        collector.record_request("worker_1", 0.5)

        # Assert
        collector.logger.debug.assert_called_once_with(
            "Recorded request for worker %s with duration %.3f",
            "worker_1", 0.5
        )
```

### Test Coverage

We aim for high test coverage. Check coverage with:

```bash
tox -e py312 -- --cov=gunicorn_prometheus_exporter --cov-report=term-missing
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
- [Documentation](https://gunicorn-prometheus-exporter.readthedocs.io/)
- [PyPI Package](https://pypi.org/project/gunicorn-prometheus-exporter/)

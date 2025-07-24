# Development Guide

This guide explains how to set up and use the development environment for
gunicorn-prometheus-exporter.

## Quick Setup

Run the setup script to install all development dependencies and configure
pre-commit hooks:

```bash
./setup_dev.sh
```

This will:

- Install development dependencies
- Set up pre-commit hooks
- Configure tox environments

## Development Tools

### Pre-commit Hooks

Pre-commit hooks run automatically on every commit to ensure code quality:

- **ruff**: Code formatting and basic linting
- **isort**: Import sorting
- **xenon**: Code complexity analysis
- **prospector**: Comprehensive code quality analysis
- **radon**: Cyclomatic complexity and maintainability index
- **bandit**: Security analysis
- **safety**: Dependency security check
- **markdownlint**: Markdown file formatting
- **prettier**: YAML file formatting

### Manual Pre-commit Usage

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run hooks only on staged files
pre-commit run

# Run a specific hook
pre-commit run ruff
pre-commit run xenon
pre-commit run prospector
```

### Tox Environments

Tox provides isolated testing environments for different Python versions and
tools:

```bash
# Run all linting and code quality checks
tox -e lint

# Run tests with specific Python version
tox -e py39
tox -e py310
tox -e py311
tox -e py312
tox -e py313

# Run all environments
tox

# Run with specific arguments
tox -e lint -- --help
```

## Code Quality Tools

### Ruff (Linting & Formatting)

```bash
# Check code
ruff check src tests

# Fix issues automatically
ruff check --fix src tests

# Format code
ruff format src tests

# Check formatting without changes
ruff format --check src tests
```

### Xenon (Complexity Analysis)

```bash
# Analyze code complexity
xenon src --max-absolute A --max-modules A --max-average A

# More strict analysis
xenon src --max-absolute B --max-modules B --max-average B
```

### Prospector (Code Quality)

```bash
# Full analysis
prospector src

# With specific profile
prospector src --profile strictness_high

# Output as JSON
prospector src --output-format json
```

### Radon (Complexity & Maintainability)

```bash
# Cyclomatic complexity
radon cc src -a

# Maintainability index
radon mi src

# Halstead metrics
radon hal src

# Raw metrics
radon raw src
```

### Bandit (Security)

```bash
# Security analysis
bandit -r src

# With specific severity levels
bandit -r src -ll

# Generate report
bandit -r src -f json -o bandit-report.json
```

### Safety (Dependency Security)

```bash
# Check dependencies
safety check

# Check with full report
safety check --full-report

# Check specific requirements file
safety check -r requirements.txt
```

## Code Quality Standards

### Complexity Grades

- **A**: Excellent (1-5 complexity)
- **B**: Good (6-10 complexity)
- **C**: Moderate (11-15 complexity)
- **D**: Poor (16-20 complexity)
- **E**: Very Poor (21+ complexity)

### Maintainability Index

- **A**: Highly Maintainable (85-100)
- **B**: Maintainable (65-84)
- **C**: Moderately Maintainable (45-64)
- **D**: Difficult to Maintain (25-44)
- **E**: Very Difficult to Maintain (0-24)

## Pre-commit Hook Configuration

The `.pre-commit-config.yaml` file configures all hooks. Key features:

- **Automatic fixes**: Some hooks automatically fix issues
- **File filtering**: Hooks only run on relevant file types
- **Performance**: Hooks are optimized for speed
- **Fail-fast**: Hooks stop on first failure

## Tox Configuration

The `tox.ini` file defines testing environments:

- **lint**: All code quality tools
- **py39-py313**: Test environments for different Python versions
- **Isolated builds**: Each environment is isolated
- **Coverage reporting**: XML coverage reports for CI

## Continuous Integration

The GitHub Actions workflow (`.github/workflows/code-quality.yml`) runs:

- **radon cc src -a**: Cyclomatic complexity
- **radon mi src**: Maintainability index
- **prospector src**: Code quality analysis

## Troubleshooting

### Pre-commit Issues

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Clean pre-commit cache
pre-commit clean

# Skip hooks for a commit
git commit --no-verify
```

### Tox Issues

```bash
# Recreate tox environments
tox --recreate

# Run with verbose output
tox -v

# Run specific command
tox -e lint -- prospector src
```

### Dependency Issues

```bash
# Update development dependencies
pip install -e ".[dev]" --upgrade

# Check for outdated packages
pip list --outdated
```

## Best Practices

1. **Always run pre-commit hooks** before committing
2. **Use tox for testing** to ensure consistency
3. **Keep complexity low** (A or B grades)
4. **Maintain high maintainability** (A grade)
5. **Fix security issues** immediately
6. **Update dependencies** regularly

## IDE Integration

### VS Code

Add to `.vscode/settings.json`:

```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": false,
    "python.formatting.provider": "ruff",
    "python.linting.ruffEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### PyCharm

1. Install the Ruff plugin
2. Configure Ruff as the formatter
3. Enable "Format on Save"
4. Configure "Optimize imports on save"

This setup ensures consistent code quality across all development environments and
CI/CD pipelines.

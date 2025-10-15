# Contributing Guide

Thank you for your interest in contributing to the Gunicorn Prometheus Exporter! This guide will help you get started with development, testing, and documentation.

## 📁 Project Structure

### **Core Modules**

- **`src/gunicorn_prometheus_exporter/plugin.py`**: Worker classes and PrometheusMixin
- **`src/gunicorn_prometheus_exporter/metrics.py`**: Prometheus metrics definitions
- **`src/gunicorn_prometheus_exporter/config.py`**: Configuration management
- **`src/gunicorn_prometheus_exporter/hooks.py`**: Modular hooks system with manager classes
- **`src/gunicorn_prometheus_exporter/master.py`**: Master process handling
- **`src/gunicorn_prometheus_exporter/storage/`**: Redis storage integration

### **Testing Structure**

Following the Test Pyramid:

- **`tests/`**: Unit tests (pytest-based)
  - `conftest.py`: Shared fixtures and test configuration
  - `test_*.py`: Comprehensive test coverage for each module
- **`integration/`**: Integration tests (component integration)
  - `test_file_storage_integration.sh`: File-based storage tests
  - `test_redis_integration.sh`: Redis storage tests
  - `test_yaml_config_integration.sh`: YAML configuration tests
- **`e2e/`**: End-to-end tests (Docker + Kubernetes)
  - `docker/`: Docker deployment tests
  - `kubernetes/`: Kubernetes deployment tests
  - `fixtures/`: Test resources and configurations
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

### Code Patterns

When contributing, follow the established patterns in the codebase:

1. **Error Handling**: Use comprehensive try/except blocks with meaningful fallbacks
2. **Logging**: Use appropriate log levels throughout
3. **Configuration**: Use environment variable-based configuration
4. **Metrics**: Follow the BaseMetric pattern with automatic registry registration
5. **Testing**: Use pytest fixtures and comprehensive mocking

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
feat: add Redis storage backend support

fix(worker/hooks/metric): handle worker restart gracefully

docs: update installation guide with Docker examples

test: add comprehensive test coverage for metrics module
```

## DevOps Playbook for Contributors

This project relies heavily on containerised workflows and infrastructure automation. The checklist below highlights the DevOps skills you will touch when contributing and why they matter.

### Local Container Tooling

- **Docker images**: The sidecar and sample app live under `Dockerfile` and `docker/Dockerfile.app`. Rebuild them with `docker build -f docker/Dockerfile.sidecar -t gunicorn-prometheus-exporter-sidecar:test .` and `docker build -f docker/Dockerfile.app -t gunicorn-app:test .` before running integration tests.
- **Docker Compose stack**: `docker-compose.yml` wires Redis, Gunicorn, the exporter, Prometheus, and Grafana. Use `docker compose up -d --build` for end-to-end smoke tests and `docker compose down` for cleanup.
- **Shared memory requirements**: Gunicorn expects `/dev/shm` = 1 GiB. Compose already sets `shm_size: 1gb`; if you run `docker run` manually, append `--shm-size=1g`.

### Kubernetes Hands-on

- **kind (Kubernetes in Docker)**: The CI workflow spins up a throwaway cluster. Install it locally with `brew install kind` and create a cluster via `kind create cluster --name test-cluster --wait 300s`.
- **kubectl essentials**: You will apply manifests from `k8s/`, wait for pods, and port-forward services. Common commands:
  ```bash
  kubectl apply -f k8s/sidecar-deployment.yaml
  kubectl wait --for=condition=ready pod -l app=gunicorn-app --timeout=300s
  kubectl port-forward service/gunicorn-metrics-service 9091:9091
  ```
- **Temporary manifest rewrites**: In CI we copy `k8s/*.yaml` into `/tmp/k8s-test/` and `sed` the image tags to `gunicorn-app:test` and `gunicorn-prometheus-exporter-sidecar:test`. Mirror this when testing locally so the cluster uses your freshly built images.
- **Cleanup discipline**: Delete port-forward processes (`pkill -f "kubectl port-forward"`) and clusters (`kind delete cluster --name test-cluster`) to avoid resource leaks.

### Observability Stack

- **Prometheus**: Validate metrics at `http://localhost:9091/metrics` (Docker) or `kubectl port-forward service/gunicorn-metrics-service`. CI asserts the presence of key `gunicorn_worker_*` families.
- **Grafana**: Default credentials are sourced from `GRAFANA_ADMIN_PASSWORD`. Override for production with `export GRAFANA_ADMIN_PASSWORD='strong-secret'` before `docker compose up`.
- **Redis**: Acts as the default multiprocess metrics backend. For local smoke tests set `REDIS_ENABLED=false`; for cluster and Compose scenarios ensure Redis is reachable and unsecured or seeded with secrets templates.

### CI/CD Awareness

- **GitHub Actions pipelines**: `.github/workflows/docker-test.yml` runs the full integration matrix, and `.github/workflows/docker-build.yml` handles multi-arch builds and Docker Hub publishing. Read these files when adding features to anticipate required updates.
- **Docker Hub metadata**: Release jobs rely on `docker/metadata-action` and `peter-evans/dockerhub-description`. If you change image names or tags, update the workflows and `DOCKER_HUB_README.md`.
- **Secrets and tokens**: Keep credentials out of source control. Use `.env` files locally and GitHub Action secrets (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, etc.) in CI. Document new secrets in `docs/README.md` or workflow comments.

### Automation Etiquette

- Run E2E tests before opening PRs to catch regressions early:
  ```bash
  cd e2e
  make e2e-test-redis-docker        # Docker deployment tests
  make integration-test-redis-full        # Redis integration test (auto-starts Redis)
  make integration-test-file-storage  # Integration tests with file storage
  ```
- Run unit tests with `tox` or `pytest`
- Capture diagnostic logs on failure (`docker logs <container>`, `kubectl describe pod/<pod>`). Attach snippets to issues or pull requests.
- Prefer Infrastructure as Code changes alongside documentation updates so contributors understand new operational steps.

### Environment Parity Tips

- Align local, CI, and production defaults by keeping `.env` examples in sync with the Helm or manifest defaults. Drift here is the top cause of "works locally" bugs.
- Prefer declarative config (YAML + templates) over ad-hoc `kubectl` edits. If you must hotfix a cluster, capture the change in the manifest immediately.
- Record one command to bootstrap each environment (local: `docker compose up`; CI: GitHub workflow reference; staging/prod: `kubectl apply -f`). Contributors should be able to rehearse the exact promotion path.

### Secret Management Fundamentals

- Ship secrets as templates only (`*.template`). Real secrets belong in local `.env` or secret managers (SOPS, Vault, GitHub Encrypted Secrets).
- Use `kubectl create secret generic ... --dry-run=client -o yaml` to generate manifests without leaking values.
- When adding a new secret requirement, update `k8s/README.md`, `docker-compose.yml`, and `docs/examples/` so others know how to populate it.

### CI/CD Troubleshooting Checklist

- Re-run failing jobs with `Retry` before diving deep—many Docker registry blips are transient.
- Use `::group::` logs in GitHub Actions when adding verbose debugging so the default output stays readable.
- For flaky Kubernetes tests, inspect `kind export logs` artifacts and attach them to PRs.
- If multi-arch builds error, temporarily force `platforms: linux/amd64` and log an issue so we can fix ARM64 parity deliberately.

### Release & Registry Hygiene

- Tag images with SemVer (`0.x.y`) and avoid `latest` in docs except for quick-start notes. Our release jobs automatically push `:0.x.y` and mark `:latest` only on tagged builds.
- Update `CHANGELOG.md` in the same PR as version bumps so release notes stay trustworthy.
- After merging release PRs, smoke-test the published Docker images (`docker run princekrroshan01/gunicorn-prometheus-exporter:0.x.y --help`) and link the results in the GitHub release discussion.

### Security & Compliance Basics

- Evaluate new dependencies with `pip install .[dev] && pip check`. If something pulls in a CVE, document the mitigation or seek alternatives.
- Keep containers slim: install only runtime packages and drop build tools in the final stage. Every extra binary widens the attack surface.
- Ensure RBAC, NetworkPolicies, and PodSecurity settings are updated whenever you add a new component. Copy + tweak existing patterns instead of inventing new ones.

### Performance & Reliability Testing

- Use `hey` or `wrk` inside the cluster (`kubectl run ... --image=ghcr.io/rakyll/hey`) to generate synthetic load against the app while watching metrics.
- When tuning Gunicorn worker counts or Redis settings, capture before/after metrics snapshots and document the rationale in the PR description.
- Monitor local test runs with `docker stats` or `kubectl top pod` to catch runaway resource consumption early.

## Testing

### Test Pyramid

The project follows the Test Pyramid with three levels of testing:

```
┌─────────────────────────────────────┐
│  e2e/                               │  ← Docker + Kubernetes (slowest)
├─────────────────────────────────────┤
│  integration/                       │  ← Component integration
├─────────────────────────────────────┤
│  tests/                             │  ← Unit tests (fastest)
└─────────────────────────────────────┘
```

### Running Unit Tests

```bash
# Run all unit tests
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

### Running Integration Tests

```bash
cd e2e

# File-based storage integration test
make integration-test-file-storage

# Redis integration test (auto-starts Redis)
make integration-test-redis-full

# Quick Redis integration test (requires Redis running)
make integration-test-redis-quick

# YAML configuration integration test
make integration-test-yaml-config
```

### Running E2E Tests

```bash
cd e2e

# Docker deployment tests
make docker-test

# Or run specific E2E tests
bash docker/test_docker_compose.sh
bash docker/test_sidecar_redis.sh
bash kubernetes/test_daemonset_deployment.sh
```

### Writing Tests

Follow these guidelines for writing tests:

1. **Test Structure**: Use pytest fixtures and classes for unit tests
2. **Test Names**: Descriptive names that explain what is being tested
3. **Coverage**: Aim for high test coverage (especially for unit tests)
4. **Mocking**: Use mocks for external dependencies in unit tests
5. **Real Dependencies**: Use real Redis/Gunicorn in integration tests
6. **Containers**: Use Docker/K8s in E2E tests

### Test Coverage

We aim for high test coverage. Check coverage with:

```bash
tox -e py312 -- --cov=gunicorn_prometheus_exporter --cov-report=term-missing
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

## Documentation

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

## Bug Reports

### Before Reporting a Bug

1. **Check existing issues**: Search for similar issues
2. **Reproduce the issue**: Ensure you can reproduce it consistently
3. **Test with minimal setup**: Try with basic configuration
4. **Check logs**: Include relevant log output

### Bug Report Template

````markdown
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
- Package version: 0.1.5

**Configuration**

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gunicorn_prometheus_exporter.PrometheusWorker"
# ... rest of configuration
```
````

**Logs**

```
[2024-01-01 12:00:00] ERROR: Failed to start metrics server
```

**Additional Context**
Any other context about the problem.

````

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
````

## Pull Request Process

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

## Release Process

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

## Getting Help

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

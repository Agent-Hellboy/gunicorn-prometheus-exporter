# Gunicorn Prometheus Exporter Documentation

Welcome to the Gunicorn Prometheus Exporter documentation. This comprehensive guide will help you monitor your Gunicorn applications with Prometheus metrics.

## Quick Start

1. **[Installation](installation.md)** - Install the package
2. **[Setup Guide](setup.md)** - Get started quickly
3. **[Examples](examples/)** - Framework-specific examples
4. **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## Key Features

- **Redis-based storage** - Eliminates file system bottlenecks
- **Multiple worker support** - Sync, Thread, Eventlet, and Gevent workers
- **Zero-configuration** - Works out of the box with sensible defaults
- **Production-ready** - Handles high-traffic scenarios with automatic cleanup
- **Comprehensive metrics** - Request rates, response times, resource usage, and more

## Documentation Structure

### Core Guides
- **[Installation Guide](installation.md)** - Package installation
- **[Setup Guide](setup.md)** - Quick setup and configuration
- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions

### Components
- **[Metrics](components/metrics/)** - Metrics collection and monitoring
- **[Backend](components/backend/)** - Storage and data management
- **[Configuration](components/config/)** - Configuration management
- **[Hooks](components/hooks/)** - Gunicorn lifecycle management
- **[Plugin](components/plugin/)** - Worker classes

### Examples
- **[Configuration Examples](examples/examples.md)** - Advanced configurations
- **[Framework Integration](examples/)** - Django, FastAPI, Flask, Pyramid
- **[Deployment Guide](examples/deployment-guide.md)** - Docker, Kubernetes

## Building Documentation

### Prerequisites

- Python 3.9+
- pip

### Local Development

1. **Install dependencies:**

   ```bash
   pip install mkdocs mkdocs-material mkdocs-minify-plugin
   ```

2. **Serve locally:**

   ```bash
   mkdocs serve
   ```

3. **Build for production:**
   ```bash
   mkdocs build
   ```

### Using the Development Script

We provide a convenient script for documentation development:

```bash
# Install dependencies and serve locally

./scripts/docs.sh all

# Or use individual commands
./scripts/docs.sh install  # Install dependencies
./scripts/docs.sh build    # Build documentation
./scripts/docs.sh serve    # Serve locally
./scripts/docs.sh clean    # Clean build artifacts
```

## Automatic Deployment

The documentation is automatically deployed to GitHub Pages when changes are pushed to the main branch. The deployment is handled by the GitHub Actions workflow in `.github/workflows/docs.yml`.

### Deployment Process

1. **Trigger**: Changes to `docs/`, `mkdocs.yml`, or the docs workflow
2. **Build**: MkDocs builds the documentation using Python 3.9
3. **Deploy**: Built documentation is deployed to GitHub Pages
4. **URL**: Available at `https://agent-hellboy.github.io/gunicorn-prometheus-exporter`

### Manual Deployment

If you need to manually trigger a documentation deployment:

1. Go to the GitHub repository
2. Navigate to Actions tab
3. Select "Deploy Documentation" workflow
4. Click "Run workflow"

## Related Links

- [GitHub Repository](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter)
- [Live Documentation](https://agent-hellboy.github.io/gunicorn-prometheus-exporter)
- [Issues](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/issues)
- [Pull Requests](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/pulls)

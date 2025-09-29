# Documentation

This directory contains the complete documentation for the Gunicorn Prometheus Exporter.

## Structure

- **[index.md](index.md)** - Main landing page
- **[installation.md](installation.md)** - Installation guide
- **[troubleshooting.md](troubleshooting.md)** - Troubleshooting guide
- **[contributing.md](contributing.md)** - Contributing guide
- **[development.md](development.md)** - Development setup guide

## Components

- **[components/metrics/](components/metrics/)** - Metrics collection and monitoring
- **[components/backend/](components/backend/)** - Storage and data management
- **[components/config/](components/config/)** - Configuration management
- **[components/hooks/](components/hooks/)** - Gunicorn hooks and lifecycle management
- **[components/plugin/](components/plugin/)** - Prometheus-enabled worker classes

## Examples

- **[examples/](examples/)** - Configuration examples and framework integration

## Framework Examples

- **[Django Integration](examples/django-integration.md)** - Django setup guide
- **[FastAPI Integration](examples/fastapi-integration.md)** - FastAPI setup guide
- **[Flask Integration](examples/flask-integration.md)** - Flask setup guide
- **[Pyramid Integration](examples/pyramid-integration.md)** - Pyramid setup guide
- **[Custom WSGI App](examples/custom-wsgi-app.md)** - Custom WSGI app guide

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

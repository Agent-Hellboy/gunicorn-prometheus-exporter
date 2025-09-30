# Docker Hub Publishing Guide

This guide explains how to build and publish the Gunicorn Prometheus Exporter sidecar container to Docker Hub.

## Prerequisites

1. **Docker installed** on your local machine
2. **Docker Hub account** created at [hub.docker.com](https://hub.docker.com)
3. **Git repository** with the code

## Step 1: Build the Docker Image

### Build the Sidecar Image

```bash
# Build the sidecar image
docker build -t gunicorn-prometheus-exporter:latest .

# Build with specific version tag
docker build -t gunicorn-prometheus-exporter:0.1.7 .
```

### Build the Sample Application Image

```bash
# Build the sample application image
docker build -f docker/Dockerfile.app -t gunicorn-app:latest .
```

## Step 2: Tag Images for Docker Hub

Replace `your-username` with your actual Docker Hub username:

```bash
# Tag sidecar image
docker tag gunicorn-prometheus-exporter:latest your-username/gunicorn-prometheus-exporter:latest
docker tag gunicorn-prometheus-exporter:latest your-username/gunicorn-prometheus-exporter:0.1.7

# Tag application image
docker tag gunicorn-app:latest your-username/gunicorn-app:latest
```

## Step 3: Login to Docker Hub

```bash
docker login
```

Enter your Docker Hub username and password when prompted.

## Step 4: Push Images to Docker Hub

```bash
# Push sidecar image
docker push your-username/gunicorn-prometheus-exporter:latest
docker push your-username/gunicorn-prometheus-exporter:0.1.7

# Push application image
docker push your-username/gunicorn-app:latest
```

## Step 5: Verify Upload

1. Go to [hub.docker.com](https://hub.docker.com)
2. Navigate to your repository
3. Verify that the images are available

## Automated Builds (Recommended)

### Set up Automated Builds on Docker Hub

1. **Connect GitHub Repository**:
   - Go to Docker Hub → Account Settings → Linked Accounts
   - Connect your GitHub account
   - Authorize Docker Hub to access your repositories

2. **Create Automated Build**:
   - Click "Create Repository" on Docker Hub
   - Select "Build Settings"
   - Choose "GitHub" as source
   - Select your repository: `Agent-Hellboy/gunicorn-prometheus-exporter`
   - Set build context to `/`

3. **Configure Build Rules**:
   - **Branch**: `main` → Tag: `latest`
   - **Branch**: `main` → Tag: `{{.Branch}}`
   - **Tag**: `v*` → Tag: `{{.Tag}}`

4. **Build Triggers**:
   - Enable "Build on push to source repository"
   - Enable "Build on tag push"

### Build Configuration File

Create a `.dockerignore` file to exclude unnecessary files:

```dockerignore
# Git
.git
.gitignore

# Documentation
docs/
*.md
!README.md

# Tests
tests/
test_*.py
*_test.py

# Development
.tox/
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt

# Build artifacts
build/
dist/
*.egg-info/

# System test
system-test/
example/prometheus-data/
example/venv/
```

## Multi-Architecture Builds

### Using Docker Buildx

```bash
# Create and use a new builder instance
docker buildx create --name multiarch --driver docker-container --use

# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-username/gunicorn-prometheus-exporter:latest \
  -t your-username/gunicorn-prometheus-exporter:0.1.7 \
  --push .
```

### Using GitHub Actions

The repository includes two GitHub Actions workflows:

#### 1. **Release Workflow** (`.github/workflows/docker-release.yml`)

Automatically builds and pushes Docker images when a new release is published:

```yaml
name: Build and Push Docker Images on Release

on:
  release:
    types: [published]
  push:
    tags:
      - 'v*'

env:
  REGISTRY: docker.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    - name: Log in to Docker Hub
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    - name: Build and push sidecar image
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./Dockerfile
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
```

#### 2. **Development Workflow** (`.github/workflows/docker-build.yml`)

Builds and pushes Docker images for development branches and pull requests:

```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - name: Build and push sidecar image
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: ${{ github.event_name != 'pull_request' }}
```

## Security Best Practices

### 1. Use Specific Base Images

```dockerfile
# Use specific version instead of latest
FROM python:3.11.7-slim
```

### 2. Run as Non-Root User

```dockerfile
# Create non-root user
RUN groupadd -r gunicorn && useradd -r -g gunicorn gunicorn

# Switch to non-root user
USER gunicorn
```

### 3. Use Multi-Stage Builds

```dockerfile
# Build stage
FROM python:3.11-slim as builder
# ... build dependencies

# Production stage
FROM python:3.11-slim
# ... copy only necessary files
```

### 4. Scan Images for Vulnerabilities

```bash
# Install Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# Scan image
trivy image your-username/gunicorn-prometheus-exporter:latest
```

## Image Optimization

### 1. Minimize Layers

```dockerfile
# Combine RUN commands
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*
```

### 2. Use .dockerignore

Exclude unnecessary files to reduce build context size.

### 3. Optimize Caching

```dockerfile
# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code last
COPY src/ ./src/
```

## Publishing Checklist

### Manual Publishing
- [ ] Build image locally and test
- [ ] Tag image with version number
- [ ] Login to Docker Hub
- [ ] Push image to Docker Hub
- [ ] Verify image is available
- [ ] Test pulling and running the image
- [ ] Update documentation with image references

### Automated Publishing (Recommended)
- [ ] Set up Docker Hub secrets in GitHub repository
- [ ] Create a new release on GitHub
- [ ] Verify automated build completes successfully
- [ ] Test the published images
- [ ] Update documentation with new version

### Required GitHub Secrets
Add these secrets to your GitHub repository settings:

- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password or access token

## Usage Examples

### Pull and Run

```bash
# Pull the image
docker pull your-username/gunicorn-prometheus-exporter:latest

# Run as sidecar
docker run -d \
  --name gunicorn-sidecar \
  -p 9091:9091 \
  -v /tmp/prometheus_multiproc:/tmp/prometheus_multiproc \
  your-username/gunicorn-prometheus-exporter:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  sidecar:
    image: your-username/gunicorn-prometheus-exporter:latest
    ports:
      - "9091:9091"
    environment:
      - PROMETHEUS_METRICS_PORT=9091
      - REDIS_ENABLED=true
      - REDIS_HOST=redis
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gunicorn-app-with-sidecar
spec:
  template:
    spec:
      containers:
        - name: prometheus-exporter
          image: your-username/gunicorn-prometheus-exporter:latest
          ports:
            - containerPort: 9091
```

## Troubleshooting

### Common Issues

1. **Build fails**: Check Dockerfile syntax and dependencies
2. **Push fails**: Verify Docker Hub credentials
3. **Image too large**: Optimize Dockerfile and use .dockerignore
4. **Security vulnerabilities**: Update base image and dependencies

### Debug Commands

```bash
# Check image size
docker images your-username/gunicorn-prometheus-exporter

# Inspect image layers
docker history your-username/gunicorn-prometheus-exporter:latest

# Test image locally
docker run --rm your-username/gunicorn-prometheus-exporter:latest --help
```

## Maintenance

### Regular Updates

1. **Update base images** regularly
2. **Update dependencies** in requirements.txt
3. **Rebuild and push** new versions
4. **Monitor security** vulnerabilities
5. **Update documentation** as needed

### Version Management

- Use semantic versioning (e.g., 0.1.7)
- Tag releases in Git
- Maintain compatibility between versions
- Document breaking changes

## Support

For issues and questions:

- **GitHub Issues**: [Create an issue](https://github.com/Agent-Hellboy/gunicorn-prometheus-exporter/issues)
- **Documentation**: [Read the docs](https://agent-hellboy.github.io/gunicorn-prometheus-exporter)
- **Docker Hub**: [Repository page](https://hub.docker.com/r/your-username/gunicorn-prometheus-exporter)

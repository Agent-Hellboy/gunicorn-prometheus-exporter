# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated CI/CD processes.

## Workflows

### 1. **Docker Release** (`.github/workflows/docker-release.yml`)

**Trigger**: When a new release is published or a version tag is pushed

**Purpose**: Automatically build and push Docker images to Docker Hub when a new version is released

**Features**:
- Builds both sidecar and sample app images
- Supports multi-architecture builds (AMD64, ARM64)
- Extracts version from Git tags
- Updates release notes with Docker image information
- Pushes to Docker Hub with proper tagging

**Required Secrets**:
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password or access token

**Usage**:
1. Create a new release on GitHub
2. The workflow automatically builds and pushes Docker images
3. Release notes are updated with Docker image information

### 2. **Docker Build** (`.github/workflows/docker-build.yml`)

**Trigger**: On pushes to main/develop branches and pull requests

**Purpose**: Build and test Docker images for development and continuous integration

**Features**:
- Builds Docker images for development branches
- Tests images on pull requests (without pushing)
- Pushes images to Docker Hub for main branch
- Supports multi-architecture builds
- Uses GitHub Actions cache for faster builds

**Required Secrets**:
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password or access token

**Usage**:
- Automatically runs on every push to main/develop
- Tests Docker images on pull requests
- Pushes images to Docker Hub for main branch

## Setup Instructions

### 1. **Configure GitHub Secrets**

Go to your repository settings → Secrets and variables → Actions, and add:

```
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-password-or-token
```

### 2. **Enable GitHub Actions**

1. Go to your repository settings
2. Navigate to Actions → General
3. Ensure "Allow all actions and reusable workflows" is selected
4. Save the settings

### 3. **Test the Workflows**

#### Test Development Workflow:
```bash
# Push to main branch
git push origin main

# Check GitHub Actions tab for build status
```

#### Test Release Workflow:
```bash
# Create and push a new tag
git tag v0.1.8
git push origin v0.1.8

# Create a new release on GitHub
# Go to Releases → Create a new release
# Select the tag and publish
```

## Workflow Details

### Docker Release Workflow

```yaml
on:
  release:
    types: [published]
  push:
    tags:
      - 'v*'
```

**What it does**:
1. Triggers on release publication or version tag push
2. Extracts version from Git tag (removes 'v' prefix)
3. Builds sidecar image with version tag
4. Builds sample app image with version tag
5. Pushes both images to Docker Hub
6. Updates release notes with Docker image information

**Generated Images**:
- `your-username/gunicorn-prometheus-exporter:0.1.8`
- `your-username/gunicorn-prometheus-exporter:latest`
- `your-username/gunicorn-prometheus-exporter-app:0.1.8`
- `your-username/gunicorn-prometheus-exporter-app:latest`

### Docker Build Workflow

```yaml
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
```

**What it does**:
1. Triggers on pushes to main/develop branches
2. Triggers on pull requests to main branch
3. Builds Docker images for testing
4. Pushes images to Docker Hub (except for PRs)
5. Tests images on pull requests

**Generated Images**:
- `your-username/gunicorn-prometheus-exporter:main`
- `your-username/gunicorn-prometheus-exporter:latest` (main branch only)
- `your-username/gunicorn-prometheus-exporter-app:main`
- `your-username/gunicorn-prometheus-exporter-app:latest` (main branch only)

## Troubleshooting

### Common Issues

1. **Workflow not triggering**:
   - Check if GitHub Actions are enabled
   - Verify the trigger conditions match your actions
   - Check repository permissions

2. **Docker push fails**:
   - Verify Docker Hub credentials are correct
   - Check if the repository exists on Docker Hub
   - Ensure the account has push permissions

3. **Build fails**:
   - Check the Dockerfile syntax
   - Verify all required files are present
   - Check for dependency issues

4. **Multi-architecture build fails**:
   - Ensure Docker Buildx is properly configured
   - Check if the base image supports multiple architectures
   - Verify platform specifications

### Debug Commands

```bash
# Check workflow status
gh workflow list

# View workflow runs
gh run list

# View specific run logs
gh run view <run-id>

# Rerun a failed workflow
gh run rerun <run-id>
```

### Local Testing

Test Docker builds locally before pushing:

```bash
# Build sidecar image
docker build -t gunicorn-prometheus-exporter:test .

# Build sample app image
docker build -f docker/Dockerfile.app -t gunicorn-app:test .

# Test the images
docker run --rm gunicorn-prometheus-exporter:test --help
docker run --rm gunicorn-app:test --help
```

## Best Practices

### 1. **Version Management**
- Use semantic versioning (e.g., v0.1.8)
- Tag releases consistently
- Update version in pyproject.toml before releasing

### 2. **Security**
- Use Docker Hub access tokens instead of passwords
- Regularly rotate credentials
- Limit repository permissions

### 3. **Performance**
- Use GitHub Actions cache for faster builds
- Optimize Dockerfile for smaller images
- Use multi-stage builds when possible

### 4. **Monitoring**
- Monitor workflow success rates
- Set up notifications for failures
- Review build logs regularly

## Customization

### Adding New Triggers

```yaml
on:
  push:
    branches: [ main, develop, feature/* ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM
```

### Adding New Build Arguments

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    build-args: |
      VERSION=${{ steps.version.outputs.version }}
      BUILD_DATE=${{ steps.date.outputs.date }}
      GIT_COMMIT=${{ github.sha }}
```

### Adding New Platforms

```yaml
platforms: linux/amd64,linux/arm64,linux/arm/v7
```

## Support

For issues with the workflows:

1. Check the GitHub Actions logs
2. Review the troubleshooting section
3. Create an issue in the repository
4. Check GitHub Actions documentation

## Related Documentation

- [Docker Hub Guide](../DOCKER_HUB_GUIDE.md)
- [Kubernetes Deployment](../k8s/README.md)
- [Docker Compose Setup](../docker/README.md)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

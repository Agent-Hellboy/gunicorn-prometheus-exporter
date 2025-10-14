#!/usr/bin/env python3
"""
Release Readiness Automation Script for gunicorn-prometheus-exporter.

This script automates release preparation by updating version numbers across all files,
running checks, and preparing release artifacts.
Usage: python scripts/release_readiness.py <new_version>
"""

import re
import sys

from pathlib import Path


def update_version(file_path, old_version, new_version):
    """Update version in a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Create escaped version for regex patterns
        escaped_old_version = old_version.replace(".", r"\.")
        escaped_new_version = new_version.replace(".", r"\.")

        # Replace version patterns - comprehensive coverage
        replacements = [
            # Docker image tags
            (
                f"princekrroshan01/gunicorn-prometheus-exporter:{old_version}",
                f"princekrroshan01/gunicorn-prometheus-exporter:{new_version}",
            ),
            (
                f"princekrroshan01/gunicorn-app:{old_version}",
                f"princekrroshan01/gunicorn-app:{new_version}",
            ),
            (
                f"gunicorn-prometheus-exporter:{old_version}",
                f"gunicorn-prometheus-exporter:{new_version}",
            ),
            (f"gunicorn-app:{old_version}", f"gunicorn-app:{new_version}"),
            # Version strings (both escaped and unescaped)
            (f'version = "{old_version}"', f'version = "{new_version}"'),
            (f'version="{old_version}"', f'version="{new_version}"'),
            (
                f'version = "{escaped_old_version}"',
                f'version = "{escaped_new_version}"',
            ),
            (f'version="{escaped_old_version}"', f'version="{escaped_new_version}"'),
            (f"ARG VERSION={old_version}", f"ARG VERSION={new_version}"),
            (
                f"ARG VERSION={escaped_old_version}",
                f"ARG VERSION={escaped_new_version}",
            ),
            (f'LABEL version="{old_version}"', f'LABEL version="{new_version}"'),
            (
                f'LABEL version="{escaped_old_version}"',
                f'LABEL version="{escaped_new_version}"',
            ),
            # Docker commands
            (
                f"docker pull princekrroshan01/gunicorn-prometheus-exporter:{old_version}",
                f"docker pull princekrroshan01/gunicorn-prometheus-exporter:{new_version}",
            ),
            (
                f"docker pull princekrroshan01/gunicorn-app:{old_version}",
                f"docker pull princekrroshan01/gunicorn-app:{new_version}",
            ),
            (
                f"docker build -t gunicorn-prometheus-exporter:{old_version}",
                f"docker build -t gunicorn-prometheus-exporter:{new_version}",
            ),
            (
                f"docker build -f docker/Dockerfile.app -t gunicorn-app:{old_version}",
                f"docker build -f docker/Dockerfile.app -t gunicorn-app:{new_version}",
            ),
            (
                f"docker tag gunicorn-prometheus-exporter:latest princekrroshan01/gunicorn-prometheus-exporter:{old_version}",
                f"docker tag gunicorn-prometheus-exporter:latest princekrroshan01/gunicorn-prometheus-exporter:{new_version}",
            ),
            (
                f"docker push princekrroshan01/gunicorn-prometheus-exporter:{old_version}",
                f"docker push princekrroshan01/gunicorn-prometheus-exporter:{new_version}",
            ),
            # Docker Compose and Kubernetes
            (
                f"image: princekrroshan01/gunicorn-prometheus-exporter:{old_version}",
                f"image: princekrroshan01/gunicorn-prometheus-exporter:{new_version}",
            ),
            (
                f"image: princekrroshan01/gunicorn-app:{old_version}",
                f"image: princekrroshan01/gunicorn-app:{new_version}",
            ),
            # Badge URLs
            (
                f"badgen.net/docker/size/princekrroshan01/gunicorn-prometheus-exporter/{old_version}/amd64",
                f"badgen.net/docker/size/princekrroshan01/gunicorn-prometheus-exporter/{new_version}/amd64",
            ),
            # Documentation examples
            (
                f"specific version tags (e.g., `{old_version}`)",
                f"specific version tags (e.g., `{new_version}`)",
            ),
            (
                f"semantic versioning (e.g., {old_version})",
                f"semantic versioning (e.g., {new_version})",
            ),
            # Changelog entries
            (f"## [{old_version}]", f"## [{new_version}]"),
            (
                f"Updated documentation, manifests, and guides to default to `{old_version}`",
                f"Updated documentation, manifests, and guides to default to `{new_version}`",
            ),
            # Generic patterns (be more specific to avoid false matches)
            (f":{old_version} ", f":{new_version} "),
            (f":{old_version}\n", f":{new_version}\n"),
            (f':{old_version}"', f':{new_version}"'),
            (f":{old_version}>", f":{new_version}>"),
            (f":{old_version}`", f":{new_version}`"),
            (f":{old_version})", f":{new_version})"),
            (f":{old_version}\\", f":{new_version}\\"),
        ]

        # Apply all replacements
        for old_pattern, new_pattern in replacements:
            content = content.replace(old_pattern, new_pattern)

        # Also handle the VERSION file content directly
        if Path(file_path).name == "VERSION":
            content = new_version + "\n"

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated {file_path}")
            return True
        else:
            print(f"No changes needed in {file_path}")
            return False

    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def validate_version_format(version):
    """Validate version format."""
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        print("Invalid version format. Use semantic versioning (e.g., 0.3.0)")
        return False
    return True


def read_current_version():
    """Read current version from VERSION file."""
    version_file = Path("VERSION")
    if not version_file.exists():
        print("VERSION file not found")
        return None

    with open(version_file, "r") as f:
        return f.read().strip()


def run_pre_release_checks():
    """Run pre-release validation checks."""
    print("Running pre-release checks...")

    # Check if VERSION file exists
    if not Path("VERSION").exists():
        print("ERROR: VERSION file not found")
        return False

    # Check if pyproject.toml exists
    if not Path("pyproject.toml").exists():
        print("ERROR: pyproject.toml not found")
        return False

    # Check if Dockerfile exists
    if not Path("Dockerfile").exists():
        print("ERROR: Dockerfile not found")
        return False

    print("Pre-release checks passed")
    return True


def generate_release_commands(version):
    """Generate release commands for the user."""
    print("\nRelease commands:")
    print("=" * 50)
    print("1. Update CHANGELOG.md with new features/fixes")
    print(f"2. Commit changes: git add . && git commit -m 'Bump version to {version}'")
    print(f"3. Create tag: git tag v{version}")
    print("4. Push: git push origin main --tags")
    print("5. Create GitHub release: gh release create v" + version)
    print("=" * 50)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/release_readiness.py <new_version>")
        print("Example: python scripts/release_readiness.py 0.3.0")
        sys.exit(1)

    new_version = sys.argv[1]

    print("Release Readiness Automation")
    print("=" * 40)

    # Run pre-release checks
    if not run_pre_release_checks():
        print("Pre-release checks failed. Aborting.")
        sys.exit(1)

    # Validate version format
    if not validate_version_format(new_version):
        sys.exit(1)

    # Read current version
    old_version = read_current_version()
    if not old_version:
        sys.exit(1)

    print(f"Updating version from {old_version} to {new_version}")

    # Files to update
    files_to_update = [
        "VERSION",
        "pyproject.toml",
        "Dockerfile",
        "README.md",
        "DOCKER_HUB_README.md",
        "DOCKER_HUB_GUIDE.md",
        "CHANGELOG.md",
        "docs/index.md",
        "docs/development.md",
        "docs/contributing.md",
        "docs/testing.md",
        "docs/examples/kubernetes-deployment.md",
        "docs/examples/deployment-guide.md",
        "docs/examples/daemonset-deployment.md",
        "docker/README.md",
        "k8s/README.md",
        "k8s/sidecar-deployment.yaml",
        "k8s/sidecar-daemonset.yaml",
        "integration/README.md",
        "e2e/README.md",
    ]

    # Update all files
    updated_count = 0
    for file_path in files_to_update:
        if Path(file_path).exists():
            if update_version(file_path, old_version, new_version):
                updated_count += 1
        else:
            print(f"File not found: {file_path}")

    print(f"\nUpdated {updated_count} files")

    # Generate release commands
    generate_release_commands(new_version)


if __name__ == "__main__":
    main()

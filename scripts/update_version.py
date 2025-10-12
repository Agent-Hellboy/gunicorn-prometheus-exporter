#!/usr/bin/env python3
"""
Version update script for gunicorn-prometheus-exporter.

This script updates version numbers across all files that reference them.
Usage: python scripts/update_version.py <new_version>
"""

import re
import sys

from pathlib import Path


def update_file_version(file_path, old_version, new_version):
    """Update version in a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace version patterns
        patterns = [
            # Docker image tags
            rf"princekrroshan01/gunicorn-prometheus-exporter:{re.escape(old_version)}",
            rf"princekrroshan01/gunicorn-app:{re.escape(old_version)}",
            # Version strings
            rf'version = "{re.escape(old_version)}"',
            rf'version="{re.escape(old_version)}"',
            rf"ARG VERSION={re.escape(old_version)}",
            rf'LABEL version="{re.escape(old_version)}"',
            # Docker pull commands
            rf"docker pull princekrroshan01/gunicorn-prometheus-exporter:{re.escape(old_version)}",
            rf"docker pull princekrroshan01/gunicorn-app:{re.escape(old_version)}",
            # Docker run commands
            rf"princekrroshan01/gunicorn-prometheus-exporter:{re.escape(old_version)}",
            rf"princekrroshan01/gunicorn-app:{re.escape(old_version)}",
        ]

        updated_content = content
        for pattern in patterns:
            updated_content = re.sub(
                pattern, pattern.replace(old_version, new_version), updated_content
            )

        if updated_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            print(f"✅ Updated {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed in {file_path}")
            return False

    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/update_version.py <new_version>")
        print("Example: python scripts/update_version.py 0.3.0")
        sys.exit(1)

    new_version = sys.argv[1]

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        print("❌ Invalid version format. Use semantic versioning (e.g., 0.3.0)")
        sys.exit(1)

    # Read current version from VERSION file
    version_file = Path("VERSION")
    if not version_file.exists():
        print("❌ VERSION file not found")
        sys.exit(1)

    with open(version_file, "r") as f:
        old_version = f.read().strip()

    print(f"🔄 Updating version from {old_version} to {new_version}")

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
        "docs/examples/kubernetes-deployment.md",
        "docs/examples/deployment-guide.md",
        "docker/README.md",
        "k8s/sidecar-deployment.yaml",
    ]

    updated_count = 0
    for file_path in files_to_update:
        if Path(file_path).exists():
            if update_file_version(file_path, old_version, new_version):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")

    print(f"\n🎉 Updated {updated_count} files")
    print("📝 Don't forget to:")
    print("   1. Update CHANGELOG.md with new features/fixes")
    print(
        f"   2. Commit changes: git add . && git commit -m 'Bump version to {new_version}'"
    )
    print(f"   3. Create tag: git tag v{new_version}")
    print("   4. Push: git push origin main --tags")


if __name__ == "__main__":
    main()

"""
Utility functions for gunicorn-prometheus-exporter.
"""

import logging
import os


logger = logging.getLogger(__name__)


def get_multiprocess_dir():
    """Get the multiprocess directory from environment variables."""
    return os.environ.get("PROMETHEUS_MULTIPROC_DIR")


def ensure_multiprocess_dir(mp_dir):
    """Ensure the multiprocess directory exists."""
    if mp_dir:
        os.makedirs(mp_dir, exist_ok=True)
        return True
    return False

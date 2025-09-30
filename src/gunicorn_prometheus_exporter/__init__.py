"""
Gunicorn Prometheus Exporter

This module provides Prometheus metrics for Gunicorn master and worker processes.
It works by replacing Gunicorn's Arbiter class with a custom PrometheusMaster that
tracks signal handling and worker lifecycle events.

WHY WE NEED TO PATCH THE ARBITER:
================================

1. SIGNAL HANDLING ARCHITECTURE:
   - Gunicorn's Arbiter class is responsible for managing worker processes and
     handling system signals
   - Only the master process receives and handles system signals
     (HUP, USR1, USR2, CHLD, etc.)
   - Worker processes don't receive these signals directly

2. WHY HOOKS ARE NOT SUFFICIENT:
   - Gunicorn hooks (on_starting, when_ready, child_exit, etc.) are worker-focused
   - There's no hook that gets called when the master receives HUP, USR1, USR2
     signals
   - Hooks run in worker processes or at specific lifecycle events, not during
     signal handling

3. OUR PATCHING STRATEGY:
   - Replace the entire Arbiter class with our PrometheusMaster
   - PrometheusMaster extends the original Arbiter and overrides signal handling
     methods
   - This ensures our metrics are incremented whenever signals are processed

4. SIGNAL FLOW:
   System Signal → Python Signal Handler → Gunicorn Signal Handler →
   Our PrometheusMaster.handle_*() → Parent Arbiter.handle_*() → Metrics Increment

5. WHY THIS APPROACH IS NECESSARY:
   - Transparent to users: Standard gunicorn -c gunicorn.conf.py app:app command
   - Comprehensive signal tracking: Captures all master-level signals
   - Non-intrusive: Doesn't break existing Gunicorn functionality
   - Maintainable: Clear separation of concerns

6. ALTERNATIVE APPROACHES REJECTED:
   - Wrapper scripts: Would require changing how users start Gunicorn
   - Environment variable injection: Wouldn't work for signal handling
   - Monkey patching signal handlers: Too fragile and could break Gunicorn
     internals

WHY WE ALSO PATCH BASEAPPLICATION:
==================================

GUNICORN STARTUP FLOW:
1. User runs: gunicorn -c gunicorn.conf.py app:app
2. Gunicorn creates a BaseApplication instance
3. BaseApplication loads the config file (gunicorn.conf.py)
4. Config file imports our module, triggering Arbiter replacement
5. BaseApplication.run() is called
6. BaseApplication.run() creates an Arbiter instance: Arbiter(self).run()
7. If we only patched gunicorn.arbiter.Arbiter, the import in BaseApplication
   might still use the original
8. Therefore, we also patch gunicorn.app.base.Arbiter to ensure consistency

THE PROBLEM:
- BaseApplication imports Arbiter from gunicorn.app.base
- If we only replace gunicorn.arbiter.Arbiter, BaseApplication might still
  reference the original
- This could lead to inconsistent behavior where sometimes our PrometheusMaster
  is used, sometimes not

THE SOLUTION:
- Patch both gunicorn.arbiter.Arbiter and gunicorn.app.base.Arbiter
- Also patch BaseApplication.run() as a safety measure
- This ensures our PrometheusMaster is always used regardless of import paths
"""

import logging  # noqa: I001

import gunicorn.app.base
import gunicorn.arbiter

from .config import (
    ExporterConfig,
    ConfigManager,
    ConfigState,
    get_config_manager,
    initialize_config,
    get_config,
    cleanup_config,
    load_yaml_config,
)
from .master import PrometheusMaster
from .metrics import registry
from .plugin import (
    PrometheusThreadWorker,
    PrometheusWorker,
    get_prometheus_eventlet_worker,
    get_prometheus_gevent_worker,
)
from .backend import (
    RedisStorageManager,
    get_redis_storage_manager,
    setup_redis_metrics,
    teardown_redis_metrics,
    is_redis_enabled,
)


# Import async worker classes if available
try:
    from .plugin import PrometheusEventletWorker

    EVENTLET_AVAILABLE = True
except ImportError:
    PrometheusEventletWorker = None
    EVENTLET_AVAILABLE = False

try:
    from .plugin import PrometheusGeventWorker

    GEVENT_AVAILABLE = True
except ImportError:
    PrometheusGeventWorker = None
    GEVENT_AVAILABLE = False


logger = logging.getLogger(__name__)


# Force Arbiter replacement before gunicorn starts
# This ensures that when Gunicorn's BaseApplication.run() calls
# Arbiter(self).run(), it uses our PrometheusMaster instead of the original
# Arbiter.

# Replace the Arbiter class in gunicorn.arbiter module
gunicorn.arbiter.Arbiter = PrometheusMaster

# Also patch the import in gunicorn.app.base module
# This is necessary because BaseApplication imports Arbiter from app.base
gunicorn.app.base.Arbiter = PrometheusMaster

# Patch the BaseApplication.run() method to ensure our PrometheusMaster is used
original_run = gunicorn.app.base.BaseApplication.run


def patched_run(self):
    """
    Patched version of BaseApplication.run() that ensures our PrometheusMaster
    is used.

    This is a safety measure to ensure that even if the Arbiter replacement
    above doesn't work for some reason, we still get our custom master.

    The flow is:
    1. User runs: gunicorn -c gunicorn.conf.py app:app
    2. BaseApplication is created and config is loaded
    3. Our module is imported during config loading, triggering Arbiter
       replacement
    4. BaseApplication.run() is called
    5. BaseApplication.run() calls Arbiter(self).run()
    6. With our patches, this uses PrometheusMaster instead of original Arbiter
    """
    return original_run(self)


gunicorn.app.base.BaseApplication.run = patched_run


# Build __all__ list conditionally
__all__ = [
    "PrometheusWorker",
    "PrometheusThreadWorker",
    "PrometheusMaster",
    "registry",
    "ExporterConfig",
    "ConfigManager",
    "ConfigState",
    "get_config_manager",
    "initialize_config",
    "get_config",
    "cleanup_config",
    "load_yaml_config",
    "RedisStorageManager",
    "get_redis_storage_manager",
    "setup_redis_metrics",
    "teardown_redis_metrics",
    "is_redis_enabled",
    "get_prometheus_eventlet_worker",
    "get_prometheus_gevent_worker",
]

# Add async workers if available
if EVENTLET_AVAILABLE:
    __all__.append("PrometheusEventletWorker")

if GEVENT_AVAILABLE:
    __all__.append("PrometheusGeventWorker")

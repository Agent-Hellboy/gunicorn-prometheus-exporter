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

from .config import config, get_config
from .metrics import registry
from .plugin import PrometheusWorker

__version__ = "0.1.0"
__all__ = [
    "PrometheusWorker",
    "PrometheusMaster",
    "registry",
    "config",
    "get_config",
]

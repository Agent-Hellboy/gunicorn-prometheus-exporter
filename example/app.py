"""
Example Flask application demonstrating Gunicorn Prometheus Exporter.

This application includes multiple endpoints to demonstrate different metrics:
- / : Simple hello world endpoint
- /slow : Endpoint that simulates slow response
- /error : Endpoint that raises an error
- /memory : Endpoint that consumes high memory
- /cpu : Endpoint that spikes CPU usage
- /leak : Endpoint that creates memory leaks
- /crash : Endpoint that may crash the worker
- /oom : Endpoint that may trigger OOM killer
- /stress : Endpoint that combines multiple stressors
"""

import gc
import os
import random
import time

from array import array

from flask import Flask, abort, request


app = Flask(__name__)


@app.route("/")
def hello():
    """Simple endpoint returning hello world."""
    return "Hello, World!"


@app.route("/slow")
def slow():
    """Endpoint that simulates slow response time."""
    # Sleep for random time between 0.1 to 2 seconds
    time.sleep(random.uniform(0.1, 2))  # nosec B311
    return "Slow response completed!"


@app.route("/error")
def error():
    """Endpoint that randomly raises an error."""
    if random.random() < 0.5:  # nosec B311
        abort(500)
    return "No error this time!"


@app.route("/memory")
def memory():
    """Endpoint that consumes high memory for testing memory limits."""
    # Get memory size from query parameter (default 100MB)
    size_mb = request.args.get("size", 100, type=int)
    duration = request.args.get("duration", 5, type=int)  # seconds to hold memory

    # Allocate memory (1MB = 1024 * 1024 bytes)
    memory_size = size_mb * 1024 * 1024

    try:
        # Create a large array to consume memory
        large_array = array("B", [0] * memory_size)

        # Hold the memory for specified duration
        time.sleep(duration)

        # Clean up
        del large_array
        gc.collect()

        return f"Consumed {size_mb}MB for {duration} seconds"
    except MemoryError:
        return "Memory allocation failed - system limit reached", 500


@app.route("/cpu")
def cpu():
    """Endpoint that spikes CPU usage for testing CPU limits."""
    # Get CPU intensity from query parameter (default 5 seconds)
    duration = request.args.get("duration", 5, type=int)
    intensity = request.args.get("intensity", 100, type=int)  # iterations per second

    start_time = time.time()
    end_time = start_time + duration

    # CPU-intensive loop
    while time.time() < end_time:
        # Perform CPU-intensive calculations
        for _ in range(intensity):
            _ = sum(i * i for i in range(1000))
            _ = [x * x for x in range(100)]

    return f"CPU spike completed for {duration} seconds at {intensity} intensity"


@app.route("/leak")
def leak():
    """Endpoint that creates memory leaks for testing memory leak detection."""
    # Get leak size from query parameter (default 10MB)
    leak_size_mb = request.args.get("size", 10, type=int)

    # Create a global list to hold memory (simulating a leak)
    if not hasattr(app, "memory_leak"):
        app.memory_leak = []

    # Add memory to the leak
    leak_bytes = leak_size_mb * 1024 * 1024
    # Use zero-filled array for faster allocation instead of random data
    leak_data = array("B", [0] * leak_bytes)
    app.memory_leak.append(leak_data)

    current_leak_mb = len(app.memory_leak) * leak_size_mb

    return (
        f"Memory leak created: {leak_size_mb}MB added, total leak: {current_leak_mb}MB"
    )


@app.route("/crash")
def crash():
    """Endpoint that may crash the worker process."""
    crash_probability = request.args.get("probability", 0.1, type=float)
    force_crash = request.args.get("force", "false", type=str).lower() == "true"

    if force_crash or random.random() < crash_probability:  # nosec B311
        # Simulate different types of crashes
        crash_type = request.args.get("type", "exception", type=str)

        if crash_type == "segfault":
            # Try to access invalid memory (may cause segfault)
            import ctypes

            try:
                ctypes.cast(0xDEADBEEF, ctypes.c_void_p).value
            except Exception:  # nosec B110
                pass
        elif crash_type == "exception":
            # Raise an unhandled exception
            raise RuntimeError("Simulated worker crash")
        elif crash_type == "exit":
            # Force exit the process
            os._exit(1)
        elif crash_type == "abort":
            # Abort the process
            import signal

            os.kill(os.getpid(), signal.SIGABRT)
        elif crash_type == "memory_error":
            # Trigger memory error
            raise MemoryError("Simulated memory error")

    return "Worker survived this time!"


@app.route("/oom")
def oom():
    """Endpoint that may trigger OOM killer by consuming excessive memory.
    You would see gunicorn logs like this:
    127.0.0.1 - - [23/Jul/2025:13:14:49 +0530] "GET /oom HTTP/1.1" 200 80 "-" "curl/7.68.0"
    [2025-07-23 13:15:06 +0530] [3989957] [DEBUG] GET /oom
    [2025-07-23 13:15:37 +0530] [3989949] [CRITICAL] WORKER TIMEOUT (pid:3989957)
    [2025-07-23 13:15:38 +0530] [3989949] [ERROR] Worker (pid:3989957) was sent SIGKILL! Perhaps out of memory?
    INFO:gunicorn_prometheus_exporter.plugin:PrometheusWorker initialized with ID: worker_3_1753256738

    capture metrics like this:

    # TYPE gunicorn_worker_failed_requests_total counter
    # HELP gunicorn_worker_error_handling_total Total number of errors handled by this worker
    # TYPE gunicorn_worker_error_handling_total counter
    # HELP gunicorn_worker_state Current state of the worker (1=running, 0=stopped)
    # TYPE gunicorn_worker_state gauge
    # HELP gunicorn_master_worker_restart_total Total number of Gunicorn worker restarts
    # TYPE gunicorn_master_worker_restart_total counter

    """
    # Get target memory consumption (default 1GB)
    target_mb = request.args.get("size", 1024, type=int)
    force_oom = request.args.get("force", "false", type=str).lower() == "true"

    if force_oom:
        # Force OOM by trying to allocate more memory than available
        try:
            # Try to allocate a massive amount of memory
            memory_size = target_mb * 1024 * 1024
            memory_blocks = []
            block_size = 200 * 1024 * 1024  # 200MB blocks

            for i in range(0, memory_size, block_size):
                remaining = min(block_size, memory_size - i)
                block = array("B", [0] * remaining)
                memory_blocks.append(block)

                # Small delay to allow OOM killer to act
                time.sleep(0.1)

            # Hold memory for a bit
            time.sleep(2)

            # Clean up
            del memory_blocks
            gc.collect()

            return f"Successfully allocated {target_mb}MB without OOM"

        except MemoryError:
            return "Memory allocation failed - OOM killer may have intervened", 500
        except Exception as e:
            return f"Unexpected error during OOM test: {str(e)}", 500
    else:
        # Safe OOM test - just simulate the scenario without actually triggering OOM
        try:
            # Allocate a reasonable amount of memory
            safe_size = min(target_mb, 100)  # Cap at 100MB for safety
            memory_size = safe_size * 1024 * 1024

            # Create a single large array
            large_array = array("B", [0] * memory_size)

            # Hold memory briefly
            time.sleep(1)

            # Clean up
            del large_array
            gc.collect()

            return f"OOM test simulation: allocated {safe_size}MB safely (use ?force=true to test actual OOM)"

        except MemoryError:
            return "Memory allocation failed even for safe amount", 500
        except Exception as e:
            return f"Error during OOM simulation: {str(e)}", 500


@app.route("/stress")
def stress():
    """Endpoint that combines multiple stressors for comprehensive testing."""
    # Get stress parameters
    memory_mb = request.args.get("memory", 50, type=int)
    cpu_duration = request.args.get("cpu", 3, type=int)
    leak_mb = request.args.get("leak", 5, type=int)

    results = []

    # 1. Memory stress
    try:
        memory_size = memory_mb * 1024 * 1024
        large_array = array("B", [0] * memory_size)
        results.append(f"Memory: {memory_mb}MB allocated")
    except MemoryError:
        results.append("Memory: Allocation failed")

    # 2. CPU stress
    start_time = time.time()
    end_time = start_time + cpu_duration
    while time.time() < end_time:
        _ = sum(i * i for i in range(1000))
    results.append(f"CPU: {cpu_duration}s intensive work")

    # 3. Memory leak
    if not hasattr(app, "stress_leak"):
        app.stress_leak = []

    leak_bytes = leak_mb * 1024 * 1024
    # Use zero-filled array for faster allocation instead of random data
    leak_data = array("B", [0] * leak_bytes)
    app.stress_leak.append(leak_data)
    results.append(f"Leak: {leak_mb}MB added")

    # 4. Clean up memory stress
    try:
        del large_array
    except NameError:  # noqa: E722 - Bare except is intentional for crash testing
        # large_array may not exist if memory allocation failed
        pass
    gc.collect()

    return f"Stress test completed: {'; '.join(results)}"


@app.route("/health")
def health():
    """Health check endpoint that returns current memory usage."""
    try:
        import psutil
    except ImportError:
        return {"status": "healthy", "error": "psutil not installed"}, 200

    process = psutil.Process()
    memory_info = process.memory_info()

    return {
        "status": "healthy",
        "memory_rss_mb": round(memory_info.rss / 1024 / 1024, 2),
        "memory_vms_mb": round(memory_info.vms / 1024 / 1024, 2),
        "cpu_percent": process.cpu_percent(),
        "pid": process.pid,
    }


@app.route("/cleanup")
def cleanup():
    """Cleanup endpoint to clear memory leaks."""
    cleaned = []

    # Clean up memory leaks
    if hasattr(app, "memory_leak"):
        del app.memory_leak
        app.memory_leak = []
        cleaned.append("memory_leak")

    if hasattr(app, "stress_leak"):
        del app.stress_leak
        app.stress_leak = []
        cleaned.append("stress_leak")

    # Force garbage collection
    gc.collect()

    return f"Cleanup completed: {', '.join(cleaned)}"


if __name__ == "__main__":
    app.run()

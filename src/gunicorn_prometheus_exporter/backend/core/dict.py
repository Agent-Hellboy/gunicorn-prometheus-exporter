import json

from typing import List


def redis_key(
    metric_name: str,
    name: str,
    labelnames: List[str],
    labelvalues: List[str],
    help_text: str,
) -> str:
    """Format a key for use in Redis, similar to mmap_key."""
    # Ensure labels are in consistent order for identity
    labels = dict(zip(labelnames, labelvalues))
    return json.dumps([metric_name, name, labels, help_text], sort_keys=True)

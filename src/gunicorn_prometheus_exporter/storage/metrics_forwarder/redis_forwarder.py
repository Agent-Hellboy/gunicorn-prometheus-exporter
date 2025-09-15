"""Redis forwarder implementation."""

import json
import logging
import time

from typing import Optional

from ...config import config
from .base import BaseForwarder


logger = logging.getLogger(__name__)


class RedisForwarder(BaseForwarder):
    """Redis implementation of metric forwarder."""

    def __init__(
        self,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: Optional[int] = None,
        redis_password: Optional[str] = None,
        redis_key_prefix: Optional[str] = None,
        forward_interval: Optional[int] = None,
    ):
        """Initialize Redis forwarder."""
        # Use config defaults if not provided
        self.redis_host = redis_host or config.redis_host
        self.redis_port = redis_port or config.redis_port
        self.redis_db = redis_db or config.redis_db
        self.redis_password = redis_password or config.redis_password
        self.redis_key_prefix = redis_key_prefix or config.redis_key_prefix

        interval = forward_interval or config.redis_forward_interval
        super().__init__(forward_interval=interval, name="Redis")

        # Redis connection
        self._redis_client = None

    def _connect(self) -> bool:
        """Connect to Redis."""
        try:
            import redis

            self._redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self._redis_client.ping()
            logger.info("Connected to Redis at %s:%s", self.redis_host, self.redis_port)
            return True

        except ImportError:
            logger.error("Redis library not installed. Install with: pip install redis")
            return False
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", e)
            return False

    def _forward_metrics(self, metrics_data: str) -> bool:
        """Forward metrics to Redis."""
        try:
            if not self._redis_client:
                return False

            timestamp = int(time.time())

            # Store timestamped version with expiration
            timestamped_key = f"{self.redis_key_prefix}{timestamp}"
            self._redis_client.setex(
                timestamped_key, self.forward_interval * 3, metrics_data
            )

            # Store latest version
            latest_key = f"{self.redis_key_prefix}latest"
            self._redis_client.set(latest_key, metrics_data)

            # Store metadata
            metadata = {
                "timestamp": timestamp,
                "host": self.redis_host,
                "port": self.redis_port,
                "interval": self.forward_interval,
                "forwarder": "redis",
            }
            metadata_key = f"{self.redis_key_prefix}metadata"
            self._redis_client.set(metadata_key, json.dumps(metadata))

            return True

        except Exception as e:
            logger.error("Failed to forward metrics to Redis: %s", e)
            return False

    def _disconnect(self):
        """Disconnect from Redis."""
        if self._redis_client:
            try:
                self._redis_client.close()
                self._redis_client = None
                logger.info("Disconnected from Redis")
            except Exception:  # nosec B110 - intentional silence on disconnect
                pass

    def get_status(self) -> dict:
        """Get Redis forwarder status."""
        status = super().get_status()
        status.update(
            {
                "redis_host": self.redis_host,
                "redis_port": self.redis_port,
                "redis_db": self.redis_db,
                "redis_key_prefix": self.redis_key_prefix,
                "connected": self._redis_client is not None,
            }
        )
        return status

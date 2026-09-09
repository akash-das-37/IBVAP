import json
import logging
import queue
import time
from typing import Optional, Dict, Any

logger = logging.getLogger("ibvap.queue")

class EventQueue:
    """
    Central Event Queue for IBVAP.
    Acts as a buffer between edge ingestion and downstream AI/Alert processing.
    Primary: Redis list queue ('ibvap:events').
    Fallback: Thread-safe Python in-memory queue when Redis is not running.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0", queue_name: str = "ibvap:events"):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.redis_client = None
        self.is_redis_available = False
        self._memory_queue = queue.Queue(maxsize=1000)
        self._init_connection()

    def _init_connection(self):
        try:
            import redis
            client = redis.Redis.from_url(self.redis_url, socket_timeout=1.5, socket_connect_timeout=1.5)
            client.ping()
            self.redis_client = client
            self.is_redis_available = True
            logger.info(f"Connected to Redis central event queue at {self.redis_url}")
        except Exception as e:
            self.is_redis_available = False
            self.redis_client = None
            logger.warning(
                f"Redis unavailable ({e}). Gracefully falling back to High-Performance In-Memory Event Queue. "
                "All event queuing, buffering, and processing will function normally."
            )

    def publish(self, event_data: Dict[str, Any]) -> bool:
        """
        Pushes an event item onto the queue.
        Payload includes event_id, camera_id, timestamp, event_type, priority, etc.
        """
        payload = json.dumps(event_data)

        if self.is_redis_available and self.redis_client:
            try:
                self.redis_client.rpush(self.queue_name, payload)
                return True
            except Exception as e:
                logger.warning(f"Redis write failed ({e}), using memory queue fallback.")
                self.is_redis_available = False

        # In-memory queue fallback
        try:
            self._memory_queue.put_nowait(payload)
            return True
        except queue.Full:
            logger.warning("In-memory event queue is full; dropping oldest event.")
            try:
                self._memory_queue.get_nowait()
                self._memory_queue.put_nowait(payload)
                return True
            except Exception:
                return False

    def pop(self, block: bool = True, timeout: float = 0.5) -> Optional[Dict[str, Any]]:
        """
        Pops the next event from the queue.
        """
        if self.is_redis_available and self.redis_client:
            try:
                item = self.redis_client.blpop(self.queue_name, timeout=int(timeout) if timeout >= 1 else 1)
                if item:
                    _, payload = item
                    return json.loads(payload.decode("utf-8"))
            except Exception as e:
                logger.warning(f"Redis pop failed ({e}), falling back to memory queue.")
                self.is_redis_available = False

        # In-memory queue
        try:
            payload = self._memory_queue.get(block=block, timeout=timeout)
            return json.loads(payload)
        except queue.Empty:
            return None

    def size(self) -> int:
        if self.is_redis_available and self.redis_client:
            try:
                return self.redis_client.llen(self.queue_name)
            except Exception:
                pass
        return self._memory_queue.qsize()

import json
import logging
from typing import Optional
from langchain.utilities.redis import get_client

logger = logging.getLogger(__name__)

class RedisSessionLog():
    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        key_prefix: str = "message_store:",
        ttl: Optional[int] = None,
    ):
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Could not import redis python package. "
                "Please install it with `pip install redis`."
            )

        try:
            self.redis_client = get_client(redis_url=url)
        except redis.exceptions.ConnectionError as error:
            logger.error(error)

        self.key_prefix = key_prefix
        self.ttl = ttl

    def key(self, session_id: str) -> str:
        """Construct the record key to use"""
        return self.key_prefix + session_id

    def add_message(self, session_id: str, message: dict[str, any]) -> None:
        """Append the message to the record in Redis"""
        key = self.key(session_id)
        self.redis_client.lpush(key, json.dumps(message))
        if self.ttl:
            self.redis_client.expire(key, self.ttl)

    def clear(self, session_id: str) -> None:
        """Clear session memory from Redis"""
        self.redis_client.delete(self.key(session_id))
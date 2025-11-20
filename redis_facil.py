import json
from typing import Any, Dict, Optional, List

import redis.asyncio as redis


class RedisFacil:
    """Async Redis helper for bridging Telegram client and UI.

    - Incoming messages from Telegram -> UI: stored in a Redis list
      under key "{namespace}:{topic}:incoming".
    - Outgoing messages from UI -> Telegram: read from a Redis list
      under key "{namespace}:{topic}:outgoing" via BLPOP.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        namespace: str = "tg_bridge",
        retry_on_timeout: bool = True,
        socket_keepalive: bool = True,
        health_check_interval: int = 30,
    ) -> None:
        self._redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            retry_on_timeout=retry_on_timeout,
            socket_keepalive=socket_keepalive,
            health_check_interval=health_check_interval
        )
        self._ns = namespace
        self._connected = False
    
    async def ensure_connected(self) -> None:
        """Ensure Redis connection is alive, reconnect if needed."""
        if not self._connected:
            try:
                await self._redis.ping()
                self._connected = True
            except Exception as e:
                print(f"Redis connection error: {e}")
                self._connected = False
                raise

    def _incoming_key(self, topic: str) -> str:
        return f"{self._ns}:{topic}:incoming"

    def _outgoing_key(self, topic: str) -> str:
        return f"{self._ns}:{topic}:outgoing"

    async def close(self) -> None:
        await self._redis.close()

    async def send_recvd_msg_to_ui(self, topic: str, payload: Dict[str, Any]) -> None:
        """Push a received Telegram message for the UI to consume.

        The UI can poll or BRPOP/BLPOP on the same list key.
        """
        key = self._incoming_key(topic)
        data = json.dumps(payload, ensure_ascii=False)
        await self._redis.rpush(key, data)

    async def send_user_entered_msg_to_client(
        self,
        topic: str,
        timeout: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """Block until the UI provides a message for this topic.

        Expects the UI to RPUSH JSON blobs onto the outgoing list key.
        This method BLPOPs from that list and returns the decoded dict.

        timeout=0 means block indefinitely; timeout>0 returns None if
        no message arrives within that many seconds.
        """
        key = self._outgoing_key(topic)
        item = await self._redis.blpop(key, timeout=timeout)
        if item is None:
            return None
        _k, raw = item
        try:
            return json.loads(raw)
        except Exception:
            return {"text": str(raw)}
            
    async def read_incoming_msgs(self, topic: str, batch_size: int = 10) -> List[Dict[str, Any]]:
        """Read messages from a topic's incoming list.
        
        Non-blocking, returns messages currently in the list up to batch_size.
        Messages are removed from Redis after being read.
        """
        await self.ensure_connected()
        key = self._incoming_key(topic)
        messages = []
        
        try:
            # Get messages one by one until batch_size or no more messages
            for _ in range(batch_size):
                raw = await self._redis.lpop(key)
                if raw is None:
                    break
                try:
                    messages.append(json.loads(raw))
                except Exception:
                    messages.append({"text": str(raw)})
            return messages
        except Exception as e:
            print(f"Error reading messages: {e}")
            return []

    async def write_outgoing_msg(self, topic: str, payload: Dict[str, Any]) -> bool:
        """Write a message to the outgoing topic.
        
        This is used by the UI to send messages that will be picked up
        by the Telegram client via send_user_entered_msg_to_client().
        Returns True if message was written successfully.
        """
        await self.ensure_connected()
        try:
            key = self._outgoing_key(topic)
            data = json.dumps(payload, ensure_ascii=False)
            await self._redis.rpush(key, data)
            return True
        except Exception as e:
            print(f"Error writing message: {e}")
            return False


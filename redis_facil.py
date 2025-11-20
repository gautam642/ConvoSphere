import json
from typing import Any, Dict, Optional

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
    ) -> None:
        self._redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self._ns = namespace

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

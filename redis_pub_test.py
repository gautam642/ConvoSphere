import json
import redis  # sync example for UI side

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

topic = "my_chat"
key = f"tg_bridge:telegram_chat:outgoing"  # must match RedisFacil namespace/topic
payload = {"text": "Hello from UI!"}

r.rpush(key, json.dumps(payload, ensure_ascii=False))
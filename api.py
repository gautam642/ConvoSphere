import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv

from redis_facil import RedisFacil


load_dotenv()

CHAT_DIR = Path("chats")
CHAT_DIR.mkdir(exist_ok=True)

REDIS_TOPIC = "telegram_chat"

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY environment variable is not set")

client = genai.Client(api_key=api_key)
redis_facil = RedisFacil()

app = FastAPI(title="ConvoSphere API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_chat_file_path(chat_id: str) -> Path:
    return CHAT_DIR / f"{chat_id}.json"


def load_chat(chat_id: str) -> Dict[str, Any]:
    path = get_chat_file_path(chat_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Chat not found")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("generated", [])
    data.setdefault("past", [])
    data.setdefault("messages", [])
    return data


def save_chat(chat_id: str, data: Dict[str, Any]) -> None:
    path = get_chat_file_path(chat_id)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_chat_id(base: str) -> str:
    ts = time.strftime("%Y%m%d_%H%M%S")
    base = base or "client"
    return f"{base}_start_{ts}"


def generate_gemini_response(chat: Dict[str, Any], prompt: str) -> str:
    chat["messages"].append({"role": "user", "parts": [prompt]})

    formatted_messages: List[Dict[str, Any]] = []
    for msg in chat["messages"]:
        role = msg.get("role")
        if role == "system":
            formatted_messages.append({"role": "user", "parts": [msg.get("content", "")]})
        elif role == "user":
            parts = msg.get("parts") or [msg.get("content", "")]
            formatted_messages.append({"role": "user", "parts": parts})
        elif role in ("assistant", "model"):
            parts = msg.get("parts") or [msg.get("content", "")]
            formatted_messages.append({"role": "model", "parts": parts})

    response_obj = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=formatted_messages,
    )
    response_text = response_obj.text

    chat["messages"].append({"role": "model", "parts": [response_text]})
    chat.setdefault("past", []).append(prompt)
    chat.setdefault("generated", []).append(response_text)

    now_ts = time.time()
    chat["messages"].append(
        {
            "source": "convosphere_ui",
            "direction": "outgoing",
            "text": prompt,
            "timestamp": now_ts,
        }
    )
    chat["messages"].append(
        {
            "source": "convosphere_model",
            "direction": "incoming",
            "text": response_text,
            "timestamp": now_ts,
        }
    )

    return response_text


class CreateChatRequest(BaseModel):
    client_phone: str = ""
    client_name: str = "client"
    client_details: str = ""


class ChatSummary(BaseModel):
    id: str
    metadata: Dict[str, Any]


class SendTelegramRequest(BaseModel):
    chat_id: str
    text: str


class SendGeminiRequest(BaseModel):
    chat_id: str
    text: str


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/chats", response_model=List[ChatSummary])
def list_chats() -> List[ChatSummary]:
    summaries: List[ChatSummary] = []
    if not CHAT_DIR.exists():
        return summaries
    for file in CHAT_DIR.glob("*.json"):
        try:
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("metadata", {})
            summaries.append(ChatSummary(id=file.stem, metadata=meta))
        except Exception:
            continue
    return summaries


@app.post("/api/chats")
def create_chat(req: CreateChatRequest) -> Dict[str, Any]:
    chat_id = create_chat_id(req.client_name.strip() or "client")
    ts = time.strftime("%Y%m%d_%H%M%S")
    chat = {
        "metadata": {
            "client_phone": req.client_phone.strip(),
            "client_name": req.client_name.strip() or "client",
            "client_details": req.client_details.strip(),
            "start_timestamp": ts,
        },
        "generated": [],
        "past": [],
        "messages": [],
    }
    save_chat(chat_id, chat)
    return {"id": chat_id, "chat": chat}


@app.get("/api/chats/{chat_id}")
def get_chat(chat_id: str) -> Dict[str, Any]:
    chat = load_chat(chat_id)
    return {"id": chat_id, "chat": chat}


@app.post("/api/telegram/send")
async def send_telegram(req: SendTelegramRequest) -> Dict[str, Any]:
    chat = load_chat(req.chat_id)
    payload = {"text": req.text}
    ok = await redis_facil.write_outgoing_msg(REDIS_TOPIC, payload)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to write message to Redis")

    chat["messages"].append(
        {
            "source": "telegram_ui",
            "direction": "outgoing",
            "text": req.text,
            "timestamp": time.time(),
        }
    )
    save_chat(req.chat_id, chat)
    return {"success": True}


@app.get("/api/telegram/messages")
async def poll_telegram(chat_id: str, batch_size: int = 20) -> Dict[str, Any]:
    chat = load_chat(chat_id)
    messages = await redis_facil.read_incoming_msgs(REDIS_TOPIC, batch_size=batch_size)
    new_messages_for_client: List[Dict[str, Any]] = []
    for payload in messages:
        text = payload.get("text", "") if isinstance(payload, dict) else str(payload)
        if not text:
            continue
        sender_name = "Telegram"
        if isinstance(payload, dict):
            sender_name = (
                payload.get("sender_name")
                or payload.get("sender_username")
                or sender_name
            )
        ts_msg = time.time()
        chat["messages"].append(
            {
                "source": "telegram_client",
                "direction": "incoming",
                "text": text,
                "sender": sender_name,
                "timestamp": ts_msg,
            }
        )
        new_messages_for_client.append(
            {
                "sender": sender_name,
                "text": text,
                "timestamp": ts_msg,
            }
        )

    if new_messages_for_client:
        save_chat(chat_id, chat)
    return {"messages": new_messages_for_client}


@app.post("/api/gemini/send")
def send_gemini(req: SendGeminiRequest) -> Dict[str, Any]:
    chat = load_chat(req.chat_id)
    reply = generate_gemini_response(chat, req.text)
    save_chat(req.chat_id, chat)
    return {"reply": reply, "chat": chat}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

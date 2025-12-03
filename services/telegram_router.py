import os
import asyncio
import httpx
from telethon import TelegramClient, events
from telethon.tl.functions.contacts import SearchRequest
from dotenv import load_dotenv
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase
from schemas import Message, Session
from datetime import datetime
from services.connection_manager import ConnectionManager

load_dotenv()

class TelegramRouter:
    """
    Handles sending outbound messages and listening for inbound messages via Telegram.
    """
    def __init__(self, db: AsyncIOMotorDatabase = None, manager: ConnectionManager = None):
        self.api_id = os.getenv("API_ID")
        self.api_hash = os.getenv("API_HASH")
        self.client = None
        self.db = db
        self.manager = manager # Store the connection manager
        self.session_file = str(Path(__file__).parent.parent / 'tg_user_session')

        if not self.api_id or not self.api_hash:
            print("WARNING: TELEGRAM_API_ID or TELEGRAM_API_HASH not set. Telegram functionality will be mocked.")
            self.mock_mode = True
        else:
            self.api_id = int(self.api_id)
            self.mock_mode = False
            self.client = TelegramClient(self.session_file, self.api_id, self.api_hash)

    async def _message_handler(self, event):
        """Event handler for new incoming messages."""
        if not event.is_private: # Ignore messages from groups/channels
            return
            
        print(f"--- Received new inbound message from: {event.sender_id} ---")
        
        try:
            sender = await event.get_sender()
            sender_telegram_user_id = sender.id # Telegram user ID is always available
            
            print(f"--- Sender Details: ID={sender_telegram_user_id}, Phone={getattr(sender, 'phone', 'N/A')}, Username={getattr(sender, 'username', 'N/A')} ---")

            
            # Find session by Telegram user ID first, then fallback to phone/username
            sessions_collection = self.db["sessions"]
            or_conditions = [
                {"customer.telegram_user_id": sender_telegram_user_id},
            ]
            if hasattr(sender, 'phone') and sender.phone:
                or_conditions.append({"customer.phone": f"+{sender.phone}"})
            if hasattr(sender, 'username') and sender.username:
                or_conditions.append({"customer.username": f"@{sender.username}"})

            session_doc = await sessions_collection.find_one({
                "$or": or_conditions
            })

            if session_doc:
                session_id = session_doc["_id"]
                
                # Make an API call to the add_message_to_session endpoint
                api_url = f"http://localhost:8000/api/sessions/{session_id}/messages"
                payload = {
                    "sender": "customer",
                    "text": event.raw_text,
                    "channel": "telegram",
                    "telegram_user_id": sender_telegram_user_id # Include sender's Telegram user ID
                }
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(api_url, json=payload)
                        response.raise_for_status()
                    print(f"--- Relayed inbound message to API for session {session_id} ---")
                except httpx.HTTPStatusError as e:
                    print(f"--- Failed to relay inbound message to API (HTTP Status): {e.response.status_code} ---")
                except httpx.RequestError as e:
                    print(f"--- Failed to relay inbound message to API (Request Error): {e} ---")
            else:
                print(f"--- No session found for Telegram User ID: {sender_telegram_user_id}. Cannot route message. ---")

        except Exception as e:
            print(f"--- Error in message handler: {e} ---")

    async def connect(self):
        if self.mock_mode:
            return
        if self.client is None:
            self.client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        
        if not self.client.is_connected():
            await self.client.connect()
            if not await self.client.is_user_authorized():
                print("Telegram client not authorized. Manual authentication might be needed.")
                print("Please run `python telegram_talker.py` once to authenticate if needed.")
            else:
                # Add event handler for incoming messages
                self.client.add_event_handler(self._message_handler, events.NewMessage(incoming=True))
                print("--- Telegram client connected and listening for messages. ---")

    async def send_message(self, phone_number: str, message_text: str):
        if self.mock_mode:
            print(f"[MOCK TELEGRAM] Sending message to {phone_number}: {message_text}")
            return {"status": "mock_sent", "phone": phone_number, "message": message_text}
        
        if not self.client or not self.client.is_connected():
            await self.connect()

        try:
            entity = await self.client.get_entity(phone_number)
            if not entity:
                return {"status": "error", "detail": f"Could not resolve Telegram entity for {phone_number}"}

            sent_message = await self.client.send_message(entity, message_text)
            return {
                "status": "sent", 
                "message_id": sent_message.id, 
                "phone": phone_number,
                "telegram_user_id": entity.id # Return the resolved Telegram User ID
            }
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return {"status": "error", "detail": str(e)}

    async def disconnect(self):
        if not self.mock_mode and self.client and self.client.is_connected():
            await self.client.disconnect()

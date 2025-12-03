from typing import Dict
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_session_update(self, session_id: str, session_data: dict): # session_data is a dict
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(session_data)

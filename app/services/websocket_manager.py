import json
from typing import Dict, List, Set
from fastapi import WebSocket

class WebSocketConnectionManager:
    def __init__(self):
        # Room based active connections: room_id -> Set[WebSocket]
        self.rooms: Dict[str, Set[WebSocket]] = {}
        # Global activity subscribers
        self.global_subscribers: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, room_id: str = "global"):
        await websocket.accept()
        if room_id == "global":
            self.global_subscribers.add(websocket)
        else:
            if room_id not in self.rooms:
                self.rooms[room_id] = set()
            self.rooms[room_id].add(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str = "global"):
        if room_id == "global":
            self.global_subscribers.discard(websocket)
        else:
            if room_id in self.rooms:
                self.rooms[room_id].discard(websocket)
                if not self.rooms[room_id]:
                    del self.rooms[room_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    async def broadcast_to_room(self, room_id: str, message: dict):
        if room_id in self.rooms:
            message_str = json.dumps(message)
            for connection in list(self.rooms[room_id]):
                try:
                    await connection.send_text(message_str)
                except Exception:
                    self.rooms[room_id].discard(connection)

    async def broadcast_activity(self, message: dict):
        message_str = json.dumps(message)
        for connection in list(self.global_subscribers):
            try:
                await connection.send_text(message_str)
            except Exception:
                self.global_subscribers.discard(connection)

ws_manager = WebSocketConnectionManager()

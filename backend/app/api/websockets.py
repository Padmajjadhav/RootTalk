from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/ws", tags=["Real-time WebSockets"])

@router.websocket("/activity")
async def websocket_activity_stream(websocket: WebSocket):
    """Global WebSocket activity stream broadcasting real-time preservation events."""
    await ws_manager.connect(websocket, room_id="global")
    try:
        await ws_manager.send_personal_message({
            "event": "CONNECTED",
            "message": "Connected to Regional Language Preservation Live Activity Stream"
        }, websocket)
        while True:
            # Keep connection open and receive optional ping messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, room_id="global")

@router.websocket("/dictation/{recording_id}")
async def websocket_dictation_room(websocket: WebSocket, recording_id: str):
    """Real-time collaborative dictation room for live audio transcription editing."""
    room_id = f"dictation_{recording_id}"
    await ws_manager.connect(websocket, room_id=room_id)
    try:
        await ws_manager.send_personal_message({
            "event": "ROOM_JOINED",
            "room_id": room_id,
            "message": f"Joined live collaborative dictation room for recording #{recording_id}"
        }, websocket)
        
        while True:
            data = await websocket.receive_text()
            # Broadcast edit event to all peers in the room
            await ws_manager.broadcast_to_room(room_id, {
                "event": "TRANSCRIPT_EDIT",
                "recording_id": recording_id,
                "payload": data
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, room_id=room_id)

@router.websocket("/quiz/{deck_id}")
async def websocket_quiz_room(websocket: WebSocket, deck_id: str):
    """Real-time multiplayer dialect quiz room."""
    room_id = f"quiz_{deck_id}"
    await ws_manager.connect(websocket, room_id=room_id)
    try:
        await ws_manager.send_personal_message({
            "event": "QUIZ_ROOM_JOINED",
            "deck_id": deck_id,
            "message": f"Connected to live multiplayer quiz session for deck #{deck_id}"
        }, websocket)
        
        while True:
            data = await websocket.receive_text()
            await ws_manager.broadcast_to_room(room_id, {
                "event": "QUIZ_LIVE_ACTION",
                "deck_id": deck_id,
                "payload": data
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, room_id=room_id)

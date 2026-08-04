"""Real-time event push (Section 11: WS /ws/events)."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ws_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Frontend doesn't need to send anything; just keep the socket
            # open and drain whatever it sends (e.g. pings).
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

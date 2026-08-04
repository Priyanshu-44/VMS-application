"""Broadcasts new events to connected frontend clients in real time (Section 11: WS /ws/events)."""
import asyncio
import json

from fastapi import WebSocket


class WSManager:
    def __init__(self):
        self.connections: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Detection runs on background threads; broadcasting must be
        scheduled onto the asyncio loop FastAPI/uvicorn is running on."""
        self._loop = loop

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.add(ws)

    def disconnect(self, ws: WebSocket):
        self.connections.discard(ws)

    async def _broadcast_async(self, message: dict):
        dead = []
        payload = json.dumps(message)
        for ws in list(self.connections):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def broadcast_threadsafe(self, message: dict):
        """Called from a detection background thread (not the event loop)."""
        if self._loop is None or not self.connections:
            return
        asyncio.run_coroutine_threadsafe(self._broadcast_async(message), self._loop)


ws_manager = WSManager()

"""
Envision backend entry point.

Run with:  uvicorn app.main:app --reload --port 8000   (from backend/)
Interactive API docs:  http://localhost:8000/docs
"""
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, cameras, dashboard, events, recordings, ws, zones
from app.core.config import CORS_ORIGINS
from app.core.db import db_session, init_db
from app.services.camera_manager import camera_manager
from app.services.event_pipeline import pipeline_manager
from app.services.recorder import recorder_manager
from app.services.ws_manager import ws_manager

app = FastAPI(
    title="Envision API",
    description=(
        "Video Management System with AI intrusion detection and "
        "false-alarm suppression (zones, class filter, dwell/debounce)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras.router)
app.include_router(zones.router)
app.include_router(events.router)
app.include_router(recordings.router)
app.include_router(ws.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)


@app.on_event("startup")
def on_startup():
    init_db()
    ws_manager.set_loop(asyncio.get_running_loop())

    # Start capture, recording, and detection threads for every camera
    # already registered in the DB so the whole pipeline is warm immediately.
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM cameras").fetchall()
        for row in rows:
            camera_manager.register(row["id"], row["source"], row["name"])
            recorder_manager.start(row["id"])
            pipeline_manager.start(row["id"])


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "envision-backend"}


@app.get("/health", tags=["health"])
def health():
    states = camera_manager.all_states()
    return {
        "status": "ok",
        "cameras_active": len(states),
        "cameras_online": sum(1 for s in states if s.online),
    }

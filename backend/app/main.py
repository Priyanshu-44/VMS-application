"""
Smart VMS backend entry point.

Run with:  uvicorn app.main:app --reload --port 8000   (from backend/)
Interactive API docs:  http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cameras
from app.core.config import CORS_ORIGINS
from app.core.db import db_session, init_db
from app.services.camera_manager import camera_manager

app = FastAPI(
    title="Smart VMS API",
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


@app.on_event("startup")
def on_startup():
    init_db()
    # Start capture threads for every camera already registered in the DB
    # so streams and the (future) detection pipeline are warm immediately.
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM cameras").fetchall()
        for row in rows:
            camera_manager.register(row["id"], row["source"], row["name"])


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "smart-vms-backend"}


@app.get("/health", tags=["health"])
def health():
    states = camera_manager.all_states()
    return {
        "status": "ok",
        "cameras_active": len(states),
        "cameras_online": sum(1 for s in states if s.online),
    }

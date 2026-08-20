"""Pydantic request/response models for the REST API (Section 11)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Cameras ----------
class CameraCreate(BaseModel):
    name: str
    source: str  # "0" for webcam index, or a file path / URL
    location: Optional[str] = None


class CameraOut(BaseModel):
    id: int
    name: str
    source: str
    location: Optional[str] = None
    status: str
    created_at: Optional[str] = None


# ---------- Zones ----------
class ZoneCreate(BaseModel):
    camera_id: int
    name: str
    polygon: list[list[float]] = Field(..., description="[[x,y],...] normalized 0-1")
    enabled: bool = True
    sensitivity: float = 0.5
    dwell_seconds: int = 2


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    polygon: Optional[list[list[float]]] = None
    enabled: Optional[bool] = None
    sensitivity: Optional[float] = None
    dwell_seconds: Optional[int] = None


class ZoneOut(BaseModel):
    id: int
    camera_id: int
    name: str
    polygon: list[list[float]]
    enabled: bool
    sensitivity: float
    dwell_seconds: int


# ---------- Events ----------
class EventOut(BaseModel):
    id: int
    camera_id: int
    zone_id: Optional[int] = None
    type: str
    object_class: Optional[str] = None
    confidence: Optional[float] = None
    ts: str
    clip_path: Optional[str] = None
    clip_offset: Optional[float] = None
    thumbnail_path: Optional[str] = None
    acknowledged: bool = False


# ---------- Recordings ----------
class RecordingOut(BaseModel):
    id: int
    camera_id: int
    start_ts: str
    end_ts: Optional[str] = None
    file_path: str
    size_bytes: Optional[int] = None


# ---------- Dashboard / Analytics ----------
class DashboardStats(BaseModel):
    cameras_online: int
    cameras_total: int
    recent_detections: list[EventOut]
    storage_used_bytes: int
    storage_used_readable: str
    active_alerts: int


class AnalyticsResponse(BaseModel):
    detections_per_hour: list[dict]
    detections_per_zone: list[dict]
    confirmed_vs_false: dict

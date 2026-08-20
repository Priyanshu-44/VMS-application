"""Pydantic request/response models for the REST API (Section 11)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _non_blank(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("must not be blank")
    return v


def _validate_polygon(polygon: list[list[float]]) -> list[list[float]]:
    # Zones are stored/compared in normalized [0,1] coordinates everywhere
    # else in the codebase (geometry.point_in_polygon, the detector's
    # centroid_norm) -- a point outside that range would never match
    # anything and silently make the zone dead, so reject it at the API
    # boundary instead of persisting a zone that can never fire.
    for point in polygon:
        if len(point) != 2:
            raise ValueError("each polygon point must be an [x, y] pair")
        x, y = point
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            raise ValueError(f"polygon point {point} is outside normalized [0,1] bounds")
    return polygon


# ---------- Cameras ----------
class CameraCreate(BaseModel):
    name: str
    source: str  # "0" for webcam index, or a file path / URL
    location: Optional[str] = None

    _validate_name = field_validator("name")(_non_blank)
    _validate_source = field_validator("source")(_non_blank)


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
    sensitivity: float = Field(0.5, ge=0.0, le=1.0)
    dwell_seconds: int = Field(2, ge=0)

    _validate_name = field_validator("name")(_non_blank)
    _validate_polygon = field_validator("polygon")(_validate_polygon)


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    polygon: Optional[list[list[float]]] = None
    enabled: Optional[bool] = None
    sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)
    dwell_seconds: Optional[int] = Field(None, ge=0)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v):
        return None if v is None else _non_blank(v)

    @field_validator("polygon")
    @classmethod
    def _validate_polygon(cls, v):
        return None if v is None else _validate_polygon(v)


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

"""Pydantic validation on the zone/camera request schemas -- server-side
enforcement of invariants the rest of the pipeline assumes: normalized
[0,1] coordinates (geometry.point_in_polygon, Detection.centroid_norm),
non-negative dwell time, non-blank names. See app/models/schemas.py.
"""
import pytest
from pydantic import ValidationError

from app.models.schemas import CameraCreate, ZoneCreate, ZoneUpdate

VALID_POLYGON = [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9]]


def test_valid_zone_passes_with_defaults():
    z = ZoneCreate(camera_id=1, name="Front Gate", polygon=VALID_POLYGON)
    assert z.sensitivity == 0.5
    assert z.dwell_seconds == 2
    assert z.enabled is True


@pytest.mark.parametrize(
    "field, value",
    [
        ("sensitivity", 1.5),
        ("sensitivity", -0.1),
        ("dwell_seconds", -1),
    ],
)
def test_zone_rejects_out_of_range_scalars(field, value):
    with pytest.raises(ValidationError):
        ZoneCreate(camera_id=1, name="Z", polygon=VALID_POLYGON, **{field: value})


def test_zone_rejects_polygon_point_outside_normalized_bounds():
    with pytest.raises(ValidationError):
        ZoneCreate(camera_id=1, name="Z", polygon=[[1.2, 0.1], [0.9, 0.1], [0.9, 0.9]])


def test_zone_rejects_blank_name():
    with pytest.raises(ValidationError):
        ZoneCreate(camera_id=1, name="   ", polygon=VALID_POLYGON)


def test_zone_update_allows_partial_patch():
    patch = ZoneUpdate(sensitivity=0.8)
    # exclude_unset is how zones.py's PATCH handler decides what to write --
    # only the field actually passed should show up here.
    assert patch.model_dump(exclude_unset=True) == {"sensitivity": 0.8}


def test_zone_update_still_validates_provided_fields():
    with pytest.raises(ValidationError):
        ZoneUpdate(sensitivity=3.0)
    with pytest.raises(ValidationError):
        ZoneUpdate(polygon=[[2.0, 0.1], [0.9, 0.1], [0.9, 0.9]])
    with pytest.raises(ValidationError):
        ZoneUpdate(name="   ")


def test_camera_rejects_blank_name_and_source():
    with pytest.raises(ValidationError):
        CameraCreate(name="", source="0")
    with pytest.raises(ValidationError):
        CameraCreate(name="Front Door", source="   ")


def test_camera_accepts_valid_input():
    cam = CameraCreate(name="Front Door", source="0", location="Main entrance")
    assert cam.name == "Front Door"

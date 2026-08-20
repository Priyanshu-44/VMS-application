"""geometry.point_in_polygon -- Layer 3 of the false-alarm pipeline: zone
containment. See app/core/geometry.py.
"""
from app.core.geometry import point_in_polygon

SQUARE = [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]


def test_point_clearly_inside():
    assert point_in_polygon(0.5, 0.5, SQUARE) is True


def test_point_clearly_outside():
    assert point_in_polygon(0.05, 0.05, SQUARE) is False
    assert point_in_polygon(0.95, 0.5, SQUARE) is False


def test_concave_polygon_rejects_point_in_the_cutout():
    # An L-shaped (concave) polygon. A naive "inside the bounding box" check
    # would wrongly accept a point that sits in the cut-out corner -- this
    # is the case a real ray-casting test has to get right.
    l_shape = [[0, 0], [1, 0], [1, 0.5], [0.5, 0.5], [0.5, 1], [0, 1]]
    assert point_in_polygon(0.75, 0.75, l_shape) is False  # in the cut-out
    assert point_in_polygon(0.25, 0.25, l_shape) is True   # in the solid part


def test_degenerate_polygon_returns_false():
    assert point_in_polygon(0.5, 0.5, []) is False
    assert point_in_polygon(0.5, 0.5, [[0.1, 0.1]]) is False
    assert point_in_polygon(0.5, 0.5, [[0.1, 0.1], [0.9, 0.9]]) is False  # 2 points isn't a polygon


def test_full_frame_zone_contains_center():
    # Matches the Detection.centroid_norm contract: (x, y) each in [0,1].
    full_frame = [[0, 0], [1, 0], [1, 1], [0, 1]]
    assert point_in_polygon(0.5, 0.5, full_frame) is True

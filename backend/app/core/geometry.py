"""Point-in-polygon test for zone containment (FR-15). Zones and centroids
are both stored/compared in normalized [0,1] coordinates, so this is
resolution-independent — a zone drawn on a 640x480 preview still works
against detections from a differently-sized frame.
"""


def point_in_polygon(x: float, y: float, polygon: list[list[float]]) -> bool:
    """Standard ray-casting algorithm. polygon = [[x,y], [x,y], ...]."""
    if len(polygon) < 3:
        return False
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside

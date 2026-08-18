"""Minimum Convex Polygon (MCP) calculations for tiger ranges."""
import math


def compute_mcp(points: list[tuple[float, float]]) -> dict:
    """Calculate the Minimum Convex Polygon (Convex Hull) and its area in km2."""
    if len(points) < 3:
        return {"valid": False, "area_km2": 0.0, "reason": "At least 3 points required"}

    # Remove duplicates
    unique_pts = sorted(list(set(points)))
    if len(unique_pts) < 3:
        return {"valid": False, "area_km2": 0.0, "reason": "At least 3 unique points required"}

    # Monotone Chain Algorithm (convex hull)
    lower = []
    for p in unique_pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(unique_pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    # Concatenate lower and upper, omitting last point of each list
    hull = lower[:-1] + upper[:-1]

    # Calculate area using Shoelace formula (coordinates in degrees)
    # Then convert to approximate square kilometers
    area_deg = _polygon_area(hull)
    
    # Conversions: 1 degree latitude ~ 111 km.
    # At latitude ~22.7 degrees (Pench), 1 degree longitude ~ 111 * cos(22.7 deg) ~ 102.4 km
    lat_factor = 111.0
    lon_factor = 111.0 * math.cos(math.radians(22.7))
    
    # Scale coordinates to km relative to the first point
    ref_lon, ref_lat = hull[0]
    hull_km = []
    for lon, lat in hull:
        x = (lon - ref_lon) * lon_factor
        y = (lat - ref_lat) * lat_factor
        hull_km.append((x, y))

    area_km2 = _polygon_area(hull_km)

    return {
        "valid": True,
        "area_km2": float(round(area_km2, 2)),
        "polygon_points": hull,
    }


def _cross(o, a, b):
    """2D cross product of OA and OB vectors. Returns positive for counter-clockwise turn."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _polygon_area(points: list[tuple[float, float]]) -> float:
    """Calculate area of a polygon using Shoelace formula."""
    n = len(points)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2.0

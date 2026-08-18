def centroid(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    """Simple geographic centroid; project coordinates before operational area calculations."""
    if not points: return None
    return (sum(x for x, _ in points) / len(points), sum(y for _, y in points) / len(points))

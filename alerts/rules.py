def range_shift_trigger(previous_area_km2: float, current_area_km2: float, threshold_km2: float = 15) -> bool:
    return abs(current_area_km2 - previous_area_km2) >= threshold_km2

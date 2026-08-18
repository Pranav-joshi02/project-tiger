def is_new_station(historical_station_ids: set[str], station_id: str) -> bool:
    return station_id not in historical_station_ids

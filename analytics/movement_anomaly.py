"""
Movement anomaly detection module to monitor tiger trajectories.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from datetime import datetime
import math

class MovementAnomalyType(Enum):
    CORRIDOR_DEVIATION = auto()
    SUDDEN_DISAPPEARANCE = auto()
    TERRITORY_DISPLACEMENT = auto()
    SETTLEMENT_APPROACH = auto()
    UNUSUAL_NOCTURNAL_ACTIVITY = auto()

@dataclass
class AnomalyAlert:
    tiger_id: str
    anomaly_type: MovementAnomalyType
    timestamp: datetime
    description: str
    severity: float

class MovementAnomalyDetector:
    """
    Evaluates new sightings against historical KDE home ranges and movement paths.
    Emits anomaly alerts when a tiger deviates beyond normal territory.
    """
    
    def __init__(self):
        self.home_ranges: Dict[str, Dict] = {} # Mock KDE representation
        self.buffer_zones: List[Tuple[float, float, float]] = [] # list of (lat, lon, radius_km)
        
    def add_buffer_zone(self, lat: float, lon: float, radius_km: float):
        """Registers a sensitive buffer zone, e.g., a village."""
        self.buffer_zones.append((lat, lon, radius_km))

    def _haversine_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        R = 6371.0
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def evaluate_sighting(
        self, 
        tiger_id: str, 
        coords: Tuple[float, float], 
        timestamp: datetime,
        historical_sightings: List[Tuple[Tuple[float, float], datetime]]
    ) -> List[AnomalyAlert]:
        """
        Analyzes a new sighting against historical data and emits alerts if necessary.
        """
        alerts = []
        
        # 1. Check Settlement Approach
        for b_lat, b_lon, b_rad in self.buffer_zones:
            dist = self._haversine_distance(coords, (b_lat, b_lon))
            if dist < b_rad:
                alerts.append(
                    AnomalyAlert(
                        tiger_id=tiger_id,
                        anomaly_type=MovementAnomalyType.SETTLEMENT_APPROACH,
                        timestamp=timestamp,
                        description=f"Tiger {tiger_id} approached within {dist:.2f}km of settlement buffer.",
                        severity=0.9
                    )
                )
                
        # 2. Check Territory Displacement / Corridor Deviation
        if historical_sightings:
            # Calculate centroid of history as a very rough mock of a KDE home range
            avg_lat = sum(h[0][0] for h in historical_sightings) / len(historical_sightings)
            avg_lon = sum(h[0][1] for h in historical_sightings) / len(historical_sightings)
            
            dist_from_center = self._haversine_distance(coords, (avg_lat, avg_lon))
            
            if dist_from_center > 15.0: # Arbitrary threshold for territory deviation
                alerts.append(
                    AnomalyAlert(
                        tiger_id=tiger_id,
                        anomaly_type=MovementAnomalyType.TERRITORY_DISPLACEMENT,
                        timestamp=timestamp,
                        description=f"Tiger {tiger_id} is {dist_from_center:.2f}km from historical core territory.",
                        severity=0.7
                    )
                )
                
        # 3. Check Unusual Nocturnal Activity (e.g. active in areas they usually avoid at night)
        # Simplified: Just flag if it's dead of night in a high human footprint area (simulated by buffer proximity)
        hour = timestamp.hour
        if (hour < 4 or hour > 22) and any(
            self._haversine_distance(coords, (b[0], b[1])) < b[2] * 2 for b in self.buffer_zones
        ):
            alerts.append(
                AnomalyAlert(
                    tiger_id=tiger_id,
                    anomaly_type=MovementAnomalyType.UNUSUAL_NOCTURNAL_ACTIVITY,
                    timestamp=timestamp,
                    description=f"Unusual nocturnal approach by {tiger_id} near buffer zones.",
                    severity=0.8
                )
            )

        return alerts

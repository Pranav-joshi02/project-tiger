"""
Predictive module for estimating human-wildlife conflict risks.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from datetime import datetime
import math

class ConflictRiskLevel(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

@dataclass
class ConflictRiskAssessment:
    risk_level: ConflictRiskLevel
    risk_score: float
    affected_villages: List[str]
    buffer_distance_km: float
    warning_polygon: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)

class ConflictRiskPredictor:
    """
    Multi-factor conflict risk engine combining tiger movement trajectories,
    village boundary distance, livestock pasture locations, road crossings,
    and time of day.
    """
    
    def __init__(self):
        self.villages: Dict[str, Tuple[float, float]] = {}
        self.pastures: Dict[str, Tuple[float, float]] = {}
        
    def add_village(self, name: str, coords: Tuple[float, float]):
        self.villages[name] = coords
        
    def add_pasture(self, name: str, coords: Tuple[float, float]):
        self.pastures[name] = coords

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

    def assess_risk(
        self, 
        tiger_trajectory: List[Tuple[float, float]], 
        current_time: datetime
    ) -> ConflictRiskAssessment:
        """
        Computes the conflict risk based on recent movement.
        """
        if not tiger_trajectory:
            return ConflictRiskAssessment(
                risk_level=ConflictRiskLevel.LOW,
                risk_score=0.0,
                affected_villages=[],
                buffer_distance_km=float('inf'),
                warning_polygon={},
                recommendations=["Insufficient trajectory data to assess risk."]
            )
            
        latest_pos = tiger_trajectory[-1]
        
        # Calculate minimum distance to villages and pastures
        min_village_dist = float('inf')
        affected_v = []
        for name, v_coord in self.villages.items():
            dist = self._haversine_distance(latest_pos, v_coord)
            if dist < min_village_dist:
                min_village_dist = dist
            if dist <= 5.0:
                affected_v.append(name)
                
        # Handle case where there are no pastures
        pasture_dists = [self._haversine_distance(latest_pos, p_coord) for p_coord in self.pastures.values()]
        min_pasture_dist = min(pasture_dists) if pasture_dists else float('inf')
        
        # Risk factors
        risk_score = 0.0
        
        # Factor 1: Proximity to villages
        if min_village_dist < 1.0:
            risk_score += 0.5
        elif min_village_dist < 3.0:
            risk_score += 0.3
            
        # Factor 2: Proximity to pastures
        if min_pasture_dist < 2.0:
            risk_score += 0.3
            
        # Factor 3: Time of day (Crepuscular / Nocturnal)
        hour = current_time.hour
        if hour < 6 or hour > 18:
            risk_score += 0.2
            
        # Classify risk level
        risk_score = min(1.0, risk_score)
        
        if risk_score >= 0.8:
            level = ConflictRiskLevel.CRITICAL
        elif risk_score >= 0.5:
            level = ConflictRiskLevel.HIGH
        elif risk_score >= 0.3:
            level = ConflictRiskLevel.MEDIUM
        else:
            level = ConflictRiskLevel.LOW
            
        recs = []
        if level in (ConflictRiskLevel.HIGH, ConflictRiskLevel.CRITICAL):
            recs.append("Dispatch Rapid Response Team to buffer zone.")
            recs.append("Issue SMS alerts to affected village sarpanch.")
            
        polygon = {
            "type": "Polygon",
            "coordinates": [latest_pos] # Mock polygon, would ideally be a projected buffer
        }
            
        return ConflictRiskAssessment(
            risk_level=level,
            risk_score=risk_score,
            affected_villages=affected_v,
            buffer_distance_km=min(min_village_dist, min_pasture_dist),
            warning_polygon=polygon,
            recommendations=recs
        )

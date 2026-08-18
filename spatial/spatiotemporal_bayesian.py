"""
Spatio-temporal Bayesian module for evaluating physical travel plausibility.
"""

from typing import Tuple
from datetime import datetime
import math

class BayesianSpatioTemporalFeasibility:
    """
    Computes P(ID | image, location, time) by checking physical travel plausibility
    between camera stations.
    """
    
    def __init__(self, max_speed_kmh: float = 15.0, terrain_friction: float = 1.2):
        """
        Args:
            max_speed_kmh: Maximum plausible speed for a tiger in km/h.
            terrain_friction: Multiplier for effective distance due to rough terrain.
        """
        self.max_speed_kmh = max_speed_kmh
        self.terrain_friction = terrain_friction

    def _haversine_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Computes haversine distance in km."""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        R = 6371.0
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def compute_feasibility(
        self, 
        last_coord: Tuple[float, float], 
        last_time: datetime, 
        new_coord: Tuple[float, float], 
        new_time: datetime
    ) -> float:
        """
        Outputs transition feasibility score [0, 1].
        Flags impossible teleports (e.g., 20 km in 5 mins).
        """
        if new_time <= last_time:
            # Cannot travel back in time or instantly
            return 0.0
            
        time_diff_hours = (new_time - last_time).total_seconds() / 3600.0
        dist_km = self._haversine_distance(last_coord, new_coord)
        
        # Effective distance considering terrain
        effective_dist_km = dist_km * self.terrain_friction
        
        if effective_dist_km == 0:
            return 1.0 # Same location
            
        required_speed_kmh = effective_dist_km / time_diff_hours
        
        if required_speed_kmh > self.max_speed_kmh:
            # Impossible transition
            return 0.0
            
        # Use an exponential decay function to assign higher feasibility to slower speeds
        # where P = 1.0 at 0 km/h, and drops to ~0.05 at max_speed
        decay_constant = -math.log(0.05) / self.max_speed_kmh
        feasibility = math.exp(-decay_constant * required_speed_kmh)
        
        return max(0.0, min(1.0, feasibility))
        
    def evaluate_identity(
        self,
        vision_confidence: float,
        last_coord: Tuple[float, float],
        last_time: datetime,
        new_coord: Tuple[float, float],
        new_time: datetime
    ) -> float:
        """
        Combines visual re-id confidence with spatio-temporal feasibility.
        Returns the joint posterior probability P(ID | image, location, time).
        """
        feasibility = self.compute_feasibility(last_coord, last_time, new_coord, new_time)
        
        # Simple Bayesian combination assuming independence for demonstration
        # P(ID|image, spatiotemporal) \propto P(image|ID) * P(spatiotemporal|ID)
        # We normalize against an assumed uniform prior.
        joint_prob = vision_confidence * feasibility
        
        return joint_prob

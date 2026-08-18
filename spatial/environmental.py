"""
Environmental context module for augmenting sightings with covariates.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Tuple, Optional
import math

@dataclass
class EnvironmentalCovariates:
    """Dataclass holding environmental covariates for a given spatial point."""
    ndvi: float
    canopy_cover: float
    elevation: float
    slope: float
    dist_to_water_km: float
    dist_to_road_km: float
    prey_density_index: float

class EnvironmentalContextEnricher:
    """
    Augments sighting data with terrain and environmental covariates based on station coordinates.
    Models habitat suitability P(TigerPresence | Environment, Time).
    """
    
    def __init__(self, gis_layers_mock: Optional[Dict] = None):
        """
        Initialize with GIS data layers.
        """
        self.gis_layers = gis_layers_mock or {}

    def fetch_covariates(self, coords: Tuple[float, float], time: datetime) -> EnvironmentalCovariates:
        """
        Fetches environmental covariates for a specific coordinate and time.
        In a real scenario, this would query raster files or a spatial database.
        """
        # Mock logic
        lat, lon = coords
        
        return EnvironmentalCovariates(
            ndvi=0.6 + 0.1 * math.sin(lat),
            canopy_cover=70.0 + 10.0 * math.cos(lon),
            elevation=300.0 + 50.0 * (lat + lon),
            slope=5.0 + 2.0 * abs(math.sin(lat * lon)),
            dist_to_water_km=max(0.1, 5.0 - abs(lat - 21.0)),
            dist_to_road_km=max(0.5, 10.0 - abs(lon - 79.0)),
            prey_density_index=0.8
        )

    def calculate_habitat_suitability(self, covariates: EnvironmentalCovariates) -> float:
        """
        Models habitat suitability P(TigerPresence | Environment).
        Returns a score between [0, 1].
        """
        score = 0.0
        
        # NDVI and Canopy prefer denser forests up to a point
        if covariates.ndvi > 0.4:
            score += 0.2
            
        if covariates.canopy_cover > 50.0:
            score += 0.2
            
        # Water proximity is highly favorable
        if covariates.dist_to_water_km < 2.0:
            score += 0.3
        elif covariates.dist_to_water_km < 5.0:
            score += 0.1
            
        # Avoidance of roads (human disturbance)
        if covariates.dist_to_road_km > 5.0:
            score += 0.15
            
        # High prey density is very favorable
        score += covariates.prey_density_index * 0.15
        
        return min(1.0, max(0.0, score))

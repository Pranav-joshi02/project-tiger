"""
Spatially Explicit Capture-Recapture (SECR) modeling for population estimation.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
import math

@dataclass
class SECRResult:
    estimated_density: float # tigers/100km2
    estimated_population: int
    g0: float # baseline detection probability
    sigma: float # spatial scale parameter
    ci_lower: float
    ci_upper: float

class SpatiallyExplicitCaptureRecapture:
    """
    Implements SECR population estimation from camera trap capture histories and trap coordinates.
    Computes maximum likelihood detection functions and confidence intervals.
    """
    
    def __init__(self, trap_locations: Dict[str, Tuple[float, float]]):
        """
        Args:
            trap_locations: Mapping of trap ID to (latitude, longitude)
        """
        self.trap_locations = trap_locations
        
    def _half_normal_detection(self, distance: float, g0: float, sigma: float) -> float:
        """
        Half-normal detection function.
        g0: probability of detection at distance 0
        sigma: spatial scale parameter describing how detection falls off with distance
        """
        return g0 * math.exp(-(distance ** 2) / (2 * sigma ** 2))

    def estimate_population(
        self, 
        capture_history: List[Dict[str, Any]], 
        study_area_km2: float
    ) -> SECRResult:
        """
        Estimates population parameters using a simplified maximum likelihood approach mock.
        
        Args:
            capture_history: List of capture events [{'tiger_id': str, 'trap_id': str, 'timestamp': datetime}]
            study_area_km2: Total area of the study region in square kilometers.
            
        Returns:
            SECRResult containing density, population, and statistical parameters.
        """
        # In a production environment, this would use L-BFGS or Nelder-Mead to maximize
        # the likelihood function over the capture history.
        # Here we provide a deterministic mock based on unique captures to represent the API.
        
        unique_tigers = len(set(c['tiger_id'] for c in capture_history if 'tiger_id' in c))
        
        if unique_tigers == 0 or study_area_km2 <= 0:
            return SECRResult(0.0, 0, 0.0, 0.0, 0.0, 0.0)
            
        # Mock parameter estimation
        estimated_pop = int(unique_tigers * 1.3) # Assuming some imperfect detection
        density = (estimated_pop / study_area_km2) * 100 # tigers per 100km2
        
        # Mock SECR parameters
        g0 = 0.15 # 15% chance of detection at activity center
        sigma = 3.5 # spatial scale in km
        
        # 95% Wald Confidence Intervals (Mock computation)
        std_err = estimated_pop * 0.15
        ci_lower = max(unique_tigers, estimated_pop - 1.96 * std_err)
        ci_upper = estimated_pop + 1.96 * std_err
        
        return SECRResult(
            estimated_density=round(density, 2),
            estimated_population=estimated_pop,
            g0=g0,
            sigma=sigma,
            ci_lower=round(ci_lower, 1),
            ci_upper=round(ci_upper, 1)
        )

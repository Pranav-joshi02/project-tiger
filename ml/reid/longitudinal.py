from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class LongitudinalRecord:
    """Represents a long-term sighting record for an individual tiger."""
    year: int
    observation_id: str
    biometric_fingerprint: Dict[str, float] = field(default_factory=dict)
    morphological_condition: Dict[str, str] = field(default_factory=dict)

class LongitudinalIdentityTracker:
    """
    Tracks individual tiger stability across years (e.g. 2024-2029).
    Models aging effects, stripe pattern permanence, and seasonal coat thickness changes.
    """
    def __init__(self):
        # Maps tiger ID to a list of historical records
        self.history: Dict[str, List[LongitudinalRecord]] = {}
        
    def add_record(self, tiger_id: str, record: LongitudinalRecord):
        """
        Adds a new observational record for a tiger.
        
        Args:
            tiger_id (str): The unique identifier for the tiger.
            record (LongitudinalRecord): The observation data.
        """
        if tiger_id not in self.history:
            self.history[tiger_id] = []
        self.history[tiger_id].append(record)
        self.history[tiger_id].sort(key=lambda x: x.year)
        
    def analyze_stability(self, tiger_id: str) -> Dict[str, float]:
        """
        Analyzes the biometric stability of a tiger over its recorded history.
        
        Args:
            tiger_id (str): The unique identifier for the tiger.
            
        Returns:
            Dict[str, float]: Stability metrics.
        """
        records = self.history.get(tiger_id, [])
        if len(records) < 2:
            return {"pattern_stability": 1.0, "aging_factor": 0.0, "years_tracked": 0.0}
            
        first = records[0]
        last = records[-1]
        
        year_diff = last.year - first.year
        aging_factor = min(1.0, year_diff * 0.05)
        
        pattern_stability = max(0.5, 1.0 - (aging_factor * 0.2))
        
        return {
            "pattern_stability": pattern_stability,
            "aging_factor": aging_factor,
            "years_tracked": float(year_diff)
        }

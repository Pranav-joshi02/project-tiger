from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

class InjuryType(Enum):
    """Enumeration of potential tiger injuries or physical conditions."""
    EAR_NOTCH = "EAR_NOTCH"
    WOUND_OR_SCAR = "WOUND_OR_SCAR"
    LIMP_GAIT = "LIMP_GAIT"
    BODY_CONDITION_DECLINE = "BODY_CONDITION_DECLINE"
    EYE_INJURY = "EYE_INJURY"

@dataclass
class InjuryDetectionResult:
    """Result of an injury detection scan."""
    injury_detected: bool
    injuries: List[Dict[str, Any]] = field(default_factory=list)
    severity: str = 'LOW' # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    recommendation: str = 'No action required.'

class InjuryAndScarDetector:
    """
    Compares historical reference photos with current sightings to flag physical anomalies,
    scars, missing ear portions, and gait abnormalities.
    """
    def __init__(self, sensitivity: float = 0.5):
        """
        Args:
            sensitivity (float): Detection threshold sensitivity (0.0 to 1.0).
        """
        self.sensitivity = sensitivity
        
    def detect_anomalies(self, current_features: Dict[str, Any], reference_features: Optional[Dict[str, Any]] = None) -> InjuryDetectionResult:
        """
        Scans current physical and behavioral features for signs of injury or decline.
        
        Args:
            current_features (Dict): Features from the current sighting (e.g. gait patterns, localized visual features).
            reference_features (Dict, optional): Historical baseline features.
            
        Returns:
            InjuryDetectionResult: The assessment result.
        """
        injuries = []
        max_severity = 'LOW'
        
        gait_score = current_features.get('gait_irregularity', 0.0)
        if gait_score > (1.0 - self.sensitivity):
            injuries.append({
                "type": InjuryType.LIMP_GAIT.value,
                "confidence": gait_score
            })
            max_severity = 'HIGH' if gait_score > 0.8 else 'MEDIUM'
            
        if reference_features:
            ref_ear = reference_features.get('left_ear_profile', 1.0)
            curr_ear = current_features.get('left_ear_profile', 1.0)
            
            if abs(ref_ear - curr_ear) > 0.3:
                injuries.append({
                    "type": InjuryType.EAR_NOTCH.value,
                    "confidence": 0.9,
                    "location": "left_ear"
                })
                
        is_detected = len(injuries) > 0
        
        recommendation = "No action required."
        if max_severity in ['HIGH', 'CRITICAL']:
            recommendation = "Immediate veterinary review recommended."
        elif max_severity == 'MEDIUM':
            recommendation = "Flag for monitoring in future sightings."
            
        return InjuryDetectionResult(
            injury_detected=is_detected,
            injuries=injuries,
            severity=max_severity,
            recommendation=recommendation
        )

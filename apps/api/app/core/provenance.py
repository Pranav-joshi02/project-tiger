import hashlib
import json
import time
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ModelProvenance:
    model_version: str
    model_hash: str
    backbone: str
    feature_dim: int
    weights_checksum: str
    threshold: float
    preprocessing_version: str
    inference_timestamp: str

class ModelProvenanceTracker:
    """
    Records full provenance metadata for each inference decision and generates verifiable tokens.
    """
    
    def __init__(self, active_model_provenance: ModelProvenance):
        self.current_provenance = active_model_provenance

    def _hash_data(self, data: str) -> str:
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def generate_provenance_token(self, inference_result: Dict[str, Any], image_hash: str) -> str:
        """
        Generates a verifiable provenance token attaching model metadata to inference results.
        """
        provenance_data = {
            "model_version": self.current_provenance.model_version,
            "model_hash": self.current_provenance.model_hash,
            "weights_checksum": self.current_provenance.weights_checksum,
            "threshold": self.current_provenance.threshold,
            "preprocessing_version": self.current_provenance.preprocessing_version,
            "inference_timestamp": str(time.time()),
            "image_hash": image_hash,
            "inference_result_summary": json.dumps(inference_result, sort_keys=True)
        }
        
        token_input = json.dumps(provenance_data, sort_keys=True)
        return self._hash_data(token_input)

    def attach_provenance(self, record: Dict[str, Any], image_hash: str) -> Dict[str, Any]:
        """
        Attaches the current model provenance and a verification token to a record.
        """
        record_with_provenance = record.copy()
        record_with_provenance["provenance"] = {
            "model_version": self.current_provenance.model_version,
            "backbone": self.current_provenance.backbone,
            "feature_dim": self.current_provenance.feature_dim,
            "timestamp": str(time.time()),
        }
        
        token = self.generate_provenance_token(record, image_hash)
        record_with_provenance["provenance_token"] = token
        
        return record_with_provenance

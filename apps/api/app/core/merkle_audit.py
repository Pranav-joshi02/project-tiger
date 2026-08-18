import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple, Optional

@dataclass
class MerkleAuditBlock:
    index: int
    timestamp: str
    previous_hash: str
    merkle_root: str
    records_hash: str
    signature: str

class MerkleAuditTrail:
    """
    Implements cryptographic SHA-256 Merkle tree verification for Re-ID decisions,
    human reviews, and tiger identity assignments.
    """
    
    def __init__(self, private_key: str = "default_key"):
        self.pending_records: List[Dict[str, Any]] = []
        self.blocks: List[MerkleAuditBlock] = []
        self.private_key = private_key # In production, use real signing

    def _hash_data(self, data: Any) -> str:
        """Helper to hash data uniformly."""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    def _calculate_merkle_root(self, hashes: List[str]) -> str:
        """Calculates the Merkle root of a list of hashes."""
        if not hashes:
            return self._hash_data("empty")
        if len(hashes) == 1:
            return hashes[0]
            
        new_level = []
        for i in range(0, len(hashes), 2):
            left = hashes[i]
            right = hashes[i+1] if i+1 < len(hashes) else left
            combined = self._hash_data(left + right)
            new_level.append(combined)
            
        return self._calculate_merkle_root(new_level)

    def add_record(self, record_type: str, data: Dict[str, Any]) -> str:
        """
        Adds a new record to the pending block and returns its hash.
        """
        record = {
            "type": record_type,
            "data": data,
            "timestamp": str(time.time())
        }
        record_hash = self._hash_data(record)
        record["hash"] = record_hash
        self.pending_records.append(record)
        return record_hash

    def commit_block(self) -> MerkleAuditBlock:
        """
        Generates a Merkle tree root for pending records, seals the block, and adds it to the chain.
        """
        index = len(self.blocks)
        previous_hash = self._hash_data(asdict(self.blocks[-1])) if self.blocks else "0" * 64
        
        record_hashes = [r["hash"] for r in self.pending_records]
        merkle_root = self._calculate_merkle_root(record_hashes)
        records_hash = self._hash_data(record_hashes)
        
        timestamp = str(time.time())
        
        # Dummy signature for demonstration
        signature_input = f"{index}{previous_hash}{merkle_root}{self.private_key}"
        signature = self._hash_data(signature_input)
        
        block = MerkleAuditBlock(
            index=index,
            timestamp=timestamp,
            previous_hash=previous_hash,
            merkle_root=merkle_root,
            records_hash=records_hash,
            signature=signature
        )
        
        self.blocks.append(block)
        self.pending_records = []
        return block

    def verify_integrity(self, blocks: List[MerkleAuditBlock]) -> Tuple[bool, str]:
        """
        Validates the entire chain of blocks.
        """
        if not blocks:
            return True, "Empty chain is valid."
            
        previous_hash = "0" * 64
        for i, block in enumerate(blocks):
            if block.index != i:
                return False, f"Block {i} has incorrect index {block.index}."
            if block.previous_hash != previous_hash:
                return False, f"Block {i} has invalid previous_hash."
                
            # Verify signature (simulated)
            signature_input = f"{block.index}{block.previous_hash}{block.merkle_root}{self.private_key}"
            expected_signature = self._hash_data(signature_input)
            if block.signature != expected_signature:
                return False, f"Block {i} has invalid signature."
                
            previous_hash = self._hash_data(asdict(block))
            
        return True, "Chain is valid."

    def verify_record(self, record_hash: str, proof: List[Dict[str, Any]], merkle_root: str) -> bool:
        """
        Verifies a record against a Merkle root using a provided proof path.
        """
        current_hash = record_hash
        for step in proof:
            position = step.get("position")
            sibling_hash = step.get("hash")
            
            if position == "left":
                current_hash = self._hash_data(sibling_hash + current_hash)
            else:
                current_hash = self._hash_data(current_hash + sibling_hash)
                
        return current_hash == merkle_root

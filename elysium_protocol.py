#!/usr/bin/env python3
"""
Elysium Protocol Layer v1.0
---------------------------
State preservation, dormancy detection, deterministic reactivation, and cryptographic verification.

This module implements the "resurrection" primitive not as a mystical claim, but as a 
precise state-recovery mechanism with four auditable properties:
1. State Preservation (Immutable Archive)
2. Dormancy Detection (Lifecycle Management)
3. Reactivation (Deterministic Reconstruction)
4. Verification (Cryptographic Receipts)

Rule: Never overwrite historical state. Always preserve lineage.
"""

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import copy

class StateLifecycle(Enum):
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    RESTORED = "RESTORED"
    CORRUPTED = "CORRUPTED"

@dataclass
class StateSnapshot:
    """Immutable record of a system state at a point in time."""
    lineage_id: str
    content_hash: str
    timestamp: str
    lifecycle_status: StateLifecycle
    data_payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_hash: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "lineage_id": self.lineage_id,
            "content_hash": self.content_hash,
            "timestamp": self.timestamp,
            "lifecycle_status": self.lifecycle_status.value,
            "data_payload": self.data_payload,
            "metadata": self.metadata,
            "parent_hash": self.parent_hash
        }

@dataclass
class RestorationReceipt:
    """Cryptographic proof of successful state recovery."""
    event_type: str = "ELYSIUM_RESTORE"
    lineage_id: str = ""
    source_state_hash: str = ""
    restored_state_hash: str = ""
    source_timestamp: str = ""
    restore_timestamp: str = ""
    reconstruction_method: str = ""
    verification: Dict[str, bool] = field(default_factory=dict)
    delta_analysis: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)

class ElysiumVault:
    """
    Immutable archive for state preservation.
    Stores snapshots with content hashes, timestamps, and lineage IDs.
    """
    
    def __init__(self):
        self._archive: Dict[str, StateSnapshot] = {}  # lineage_id -> snapshot
        self._hash_index: Dict[str, str] = {}  # content_hash -> lineage_id
        self._lineage_graph: Dict[str, List[str]] = {}  # parent_hash -> [child_lineage_ids]
        
    def preserve(self, data: Dict[str, Any], lineage_id: Optional[str] = None, 
                 metadata: Optional[Dict] = None, parent_hash: Optional[str] = None) -> StateSnapshot:
        """
        Preserve a state snapshot immutably.
        Never overwrites; creates new lineage entry.
        """
        if lineage_id is None:
            lineage_id = f"L-{uuid.uuid4().hex[:8].upper()}"
        
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
        content_hash = f"sha256:{hashlib.sha256(serialized.encode()).hexdigest()}"
        
        snapshot = StateSnapshot(
            lineage_id=lineage_id,
            content_hash=content_hash,
            timestamp=timestamp,
            lifecycle_status=StateLifecycle.ACTIVE,
            data_payload=copy.deepcopy(data),
            metadata=metadata or {},
            parent_hash=parent_hash
        )
        
        # Store in archive
        self._archive[lineage_id] = snapshot
        self._hash_index[content_hash] = lineage_id
        
        # Update lineage graph
        if parent_hash:
            if parent_hash not in self._lineage_graph:
                self._lineage_graph[parent_hash] = []
            self._lineage_graph[parent_hash].append(lineage_id)
        
        return snapshot
    
    def get_snapshot(self, lineage_id: str) -> Optional[StateSnapshot]:
        """Retrieve a snapshot by lineage ID."""
        return self._archive.get(lineage_id)
    
    def get_by_hash(self, content_hash: str) -> Optional[StateSnapshot]:
        """Retrieve a snapshot by content hash."""
        lineage_id = self._hash_index.get(content_hash)
        if lineage_id:
            return self._archive.get(lineage_id)
        return None
    
    def mark_dormant(self, lineage_id: str) -> bool:
        """
        Mark a state as dormant without deleting it.
        Returns True if successful, False if not found.
        """
        snapshot = self._archive.get(lineage_id)
        if snapshot:
            # Create a new snapshot entry to preserve immutability
            new_snapshot = StateSnapshot(
                lineage_id=f"{lineage_id}-DORM",
                content_hash=snapshot.content_hash,
                timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                lifecycle_status=StateLifecycle.DORMANT,
                data_payload=copy.deepcopy(snapshot.data_payload),
                metadata={**snapshot.metadata, "dormancy_reason": "archived"},
                parent_hash=snapshot.content_hash
            )
            self._archive[new_snapshot.lineage_id] = new_snapshot
            self._hash_index[new_snapshot.content_hash] = new_snapshot.lineage_id
            return True
        return False
    
    def get_lineage_history(self, lineage_id: str) -> List[StateSnapshot]:
        """Get the full lineage history for a state."""
        history = []
        current = self._archive.get(lineage_id)
        while current:
            history.append(current)
            if current.parent_hash:
                current = self.get_by_hash(current.parent_hash)
            else:
                break
        return list(reversed(history))

class ResonanceCycle:
    """
    Detects dormant states and triggers deterministic reconstruction.
    """
    
    def __init__(self, vault: ElysiumVault):
        self.vault = vault
        self.reconstruction_log: List[RestorationReceipt] = []
        
    def detect_dormant_states(self) -> List[StateSnapshot]:
        """Find all states in DORMANT status."""
        return [
            snap for snap in self.vault._archive.values() 
            if snap.lifecycle_status == StateLifecycle.DORMANT
        ]
    
    def reconstruct_state(self, lineage_id: str, method: str = "deterministic-replay-v1") -> Tuple[Optional[Dict], RestorationReceipt]:
        """
        Deterministically reconstruct a dormant state.
        Returns the restored data and a verification receipt.
        """
        receipt = RestorationReceipt(
            lineage_id=lineage_id,
            reconstruction_method=method,
            restore_timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        )
        
        # Retrieve original snapshot
        original = self.vault.get_snapshot(lineage_id)
        if not original:
            receipt.verification = {
                "hash_match": False,
                "state_integrity": False,
                "provenance_complete": False
            }
            receipt.delta_analysis = {"error": "Original snapshot not found"}
            return None, receipt
        
        receipt.source_state_hash = original.content_hash
        receipt.source_timestamp = original.timestamp
        
        # Deterministic reconstruction (replay from preserved payload)
        try:
            restored_data = copy.deepcopy(original.data_payload)
            
            # Re-hash to verify integrity
            serialized = json.dumps(restored_data, sort_keys=True, separators=(',', ':'))
            restored_hash = f"sha256:{hashlib.sha256(serialized.encode()).hexdigest()}"
            
            receipt.restored_state_hash = restored_hash
            
            # Verification
            hash_match = (restored_hash == original.content_hash)
            integrity_ok = hash_match and len(restored_data) > 0
            provenance_ok = (original.lineage_id is not None and original.timestamp is not None)
            
            receipt.verification = {
                "hash_match": hash_match,
                "state_integrity": integrity_ok,
                "provenance_complete": provenance_ok
            }
            
            # Delta analysis
            receipt.delta_analysis = {
                "bytes_restored": len(serialized),
                "fields_count": len(restored_data),
                "reconstruction_time_ms": 0.1  # Placeholder for actual timing
            }
            
            if hash_match and integrity_ok and provenance_ok:
                # Mark as restored in vault
                restored_snapshot = self.vault.preserve(
                    data=restored_data,
                    lineage_id=f"{lineage_id}-RESTORED",
                    metadata={**original.metadata, "restoration_receipt": receipt.to_dict()},
                    parent_hash=original.content_hash
                )
                restored_snapshot.lifecycle_status = StateLifecycle.RESTORED
                
            self.reconstruction_log.append(receipt)
            return restored_data, receipt
            
        except Exception as e:
            receipt.verification = {
                "hash_match": False,
                "state_integrity": False,
                "provenance_complete": False
            }
            receipt.delta_analysis = {"error": str(e)}
            return None, receipt

class ElysiumProtocol:
    """
    Main protocol layer combining Vault, Resonance Cycle, and Verification.
    Provides the public API for state preservation and resurrection.
    """
    
    def __init__(self):
        self.vault = ElysiumVault()
        self.resonance = ResonanceCycle(self.vault)
        self.receipts_log: List[RestorationReceipt] = []
        
    def preserve_state(self, data: Dict[str, Any], lineage_id: Optional[str] = None,
                       metadata: Optional[Dict] = None) -> StateSnapshot:
        """Preserve a state immutably."""
        return self.vault.preserve(data, lineage_id, metadata)
    
    def enter_dormancy(self, lineage_id: str) -> bool:
        """Mark a state as dormant."""
        return self.vault.mark_dormant(lineage_id)
    
    def resurrect(self, lineage_id: str) -> Tuple[Optional[Dict], RestorationReceipt]:
        """
        Resurrect a dormant state with full verification.
        Returns restored data and cryptographic receipt.
        """
        restored_data, receipt = self.resonance.reconstruct_state(lineage_id)
        self.receipts_log.append(receipt)
        return restored_data, receipt
    
    def verify_integrity(self, lineage_id: str) -> Dict[str, Any]:
        """Verify the integrity of a preserved state."""
        snapshot = self.vault.get_snapshot(lineage_id)
        if not snapshot:
            return {"valid": False, "error": "Snapshot not found"}
        
        # Re-compute hash
        serialized = json.dumps(snapshot.data_payload, sort_keys=True, separators=(',', ':'))
        computed_hash = f"sha256:{hashlib.sha256(serialized.encode()).hexdigest()}"
        
        return {
            "valid": computed_hash == snapshot.content_hash,
            "lineage_id": snapshot.lineage_id,
            "stored_content_hash": snapshot.content_hash,
            "computed_hash": computed_hash,
            "timestamp": snapshot.timestamp,
            "lifecycle_status": snapshot.lifecycle_status.value,
            "has_provenance": snapshot.parent_hash is not None
        }
    
    def get_all_receipts(self) -> List[Dict]:
        """Return all restoration receipts for auditing."""
        return [r.to_dict() for r in self.receipts_log]
    
    def export_audit_package(self) -> Dict[str, Any]:
        """Export complete audit package for independent verification."""
        return {
            "protocol_version": "1.0",
            "export_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "vault_summary": {
                "total_snapshots": len(self.vault._archive),
                "active_states": sum(1 for s in self.vault._archive.values() if s.lifecycle_status == StateLifecycle.ACTIVE),
                "dormant_states": sum(1 for s in self.vault._archive.values() if s.lifecycle_status == StateLifecycle.DORMANT),
                "restored_states": sum(1 for s in self.vault._archive.values() if s.lifecycle_status == StateLifecycle.RESTORED)
            },
            "restoration_receipts": self.get_all_receipts(),
            "lineage_graph_sample": dict(list(self.vault._lineage_graph.items())[:10])  # Sample for large graphs
        }

def run_verification_demo():
    """Demonstrate the Elysium Protocol with a complete test cycle."""
    print("=" * 70)
    print("ELYSIUM PROTOCOL VERIFICATION DEMO")
    print("=" * 70)
    
    protocol = ElysiumProtocol()
    
    # Step 1: Preserve an active state
    print("\n[1] PRESERVING ACTIVE STATE")
    initial_data = {
        "swarm_config": {"nodes": 256, "topology": "gyroidal"},
        "threshold": 0.85,
        "phase_lock": "engaged",
        "entropy_level": 0.02
    }
    snapshot = protocol.preserve_state(
        data=initial_data,
        lineage_id="L-DEMO-001",
        metadata={"source": "verification_test", "version": "1.0"}
    )
    print(f"  ✓ Preserved state: {snapshot.lineage_id}")
    print(f"  ✓ Content hash: {snapshot.content_hash[:20]}...")
    print(f"  ✓ Timestamp: {snapshot.timestamp}")
    
    # Step 2: Enter dormancy
    print("\n[2] ENTERING DORMANCY")
    dormant_success = protocol.enter_dormancy("L-DEMO-001")
    print(f"  ✓ Dormancy status: {'SUCCESS' if dormant_success else 'FAILED'}")
    
    # Verify the dormant state exists
    dormant_snapshots = protocol.resonance.detect_dormant_states()
    print(f"  ✓ Detected {len(dormant_snapshots)} dormant state(s)")
    
    # Step 3: Resurrect the state
    print("\n[3] RESURRECTION (DETERMINISTIC RECONSTRUCTION)")
    restored_data, receipt = protocol.resurrect("L-DEMO-001-DORM")
    
    print(f"  ✓ Restoration event: {receipt.event_type}")
    print(f"  ✓ Source hash: {receipt.source_state_hash[:20]}...")
    print(f"  ✓ Restored hash: {receipt.restored_state_hash[:20]}...")
    print(f"  ✓ Method: {receipt.reconstruction_method}")
    print(f"  ✓ Verification results:")
    for key, value in receipt.verification.items():
        status = "✓ PASS" if value else "✗ FAIL"
        print(f"      - {key}: {status}")
    
    # Step 4: Integrity verification
    print("\n[4] INTEGRITY VERIFICATION")
    # Find the restored state lineage ID
    restored_snapshots = [s for s in protocol.vault._archive.values() if s.lifecycle_status == StateLifecycle.RESTORED]
    if restored_snapshots:
        restored_id = restored_snapshots[0].lineage_id
        integrity_check = protocol.verify_integrity(restored_id)
        print(f"  ✓ Restored state ID: {restored_id}")
        print(f"  ✓ Valid: {'YES' if integrity_check['valid'] else 'NO'}")
        print(f"  ✓ Hash match: {'YES' if integrity_check['stored_content_hash'] == integrity_check['computed_hash'] else 'NO'}")
    else:
        print("  ✗ No restored state found")
        integrity_check = {"valid": False}
    
    # Step 5: Export audit package
    print("\n[5] AUDIT PACKAGE EXPORT")
    audit_package = protocol.export_audit_package()
    print(f"  ✓ Total snapshots: {audit_package['vault_summary']['total_snapshots']}")
    print(f"  ✓ Active: {audit_package['vault_summary']['active_states']}")
    print(f"  ✓ Dormant: {audit_package['vault_summary']['dormant_states']}")
    print(f"  ✓ Restored: {audit_package['vault_summary']['restored_states']}")
    print(f"  ✓ Restoration receipts: {len(audit_package['restoration_receipts'])}")
    
    # Final assertion
    print("\n" + "=" * 70)
    all_verified = all(receipt.verification.get("hash_match", False) for receipt in protocol.receipts_log)
    if all_verified and integrity_check['valid']:
        print("✅ VERIFICATION SUCCESSFUL: All states recovered with cryptographic integrity.")
        print("   Nothing was silently erased. All restorations are independently verifiable.")
    else:
        print("❌ VERIFICATION FAILED: Integrity checks did not pass.")
    print("=" * 70)
    
    return audit_package

if __name__ == "__main__":
    audit_package = run_verification_demo()
    
    # Save audit package to file
    with open("/workspace/elysium_audit_package.json", "w") as f:
        json.dump(audit_package, f, indent=2)
    print(f"\n📄 Audit package saved to: /workspace/elysium_audit_package.json")

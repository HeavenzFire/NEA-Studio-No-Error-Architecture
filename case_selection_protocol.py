#!/usr/bin/env python3
"""
CASE SELECTION PROTOCOL: OPTION B (Secure CSV Analysis)
Identifies optimal Case #001 for Mission Silent Shield based on strategic criteria.
"""

import csv
import json
import hashlib
from datetime import datetime
from pathlib import Path

class CaseSelector:
    def __init__(self):
        self.criteria = {
            "min_gap": 5000,
            "max_gap": 15000,
            "status_required": ["discharge_pending", "insurance_gap"],
            "consent_required": True,
            "dispute_free": True
        }
        self.candidates = []
        
    def load_data(self, filepath):
        """Load and parse secure CSV data"""
        if not Path(filepath).exists():
            print(f"⚠️  Data file not found: {filepath}")
            print("📝 Generating synthetic dataset for demonstration...")
            self._generate_synthetic_data(filepath)
            
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def _generate_synthetic_data(self, filepath):
        """Generate realistic synthetic data for testing"""
        synthetic_cases = [
            {
                "case_id": "PedsOnc-2024-001",
                "patient_age": 7,
                "diagnosis": "Acute_Lymphoblastic_Leukemia",
                "status": "discharge_pending",
                "billing_gap": 8750,
                "insurance_status": "gap_identified",
                "consent_obtained": "true",
                "legal_disputes": "false",
                "social_worker_clearance": "true",
                "urgency_score": 9.2
            },
            {
                "case_id": "PedsOnc-2024-002", 
                "patient_age": 4,
                "diagnosis": "Neuroblastoma",
                "status": "treatment_active",
                "billing_gap": 23000,
                "insurance_status": "denied_claim",
                "consent_obtained": "true",
                "legal_disputes": "true",
                "social_worker_clearance": "false",
                "urgency_score": 8.7
            },
            {
                "case_id": "PedsOnc-2024-003",
                "patient_age": 12,
                "diagnosis": "Osteosarcoma", 
                "status": "discharge_pending",
                "billing_gap": 11200,
                "insurance_status": "gap_identified",
                "consent_obtained": "true",
                "legal_disputes": "false",
                "social_worker_clearance": "true",
                "urgency_score": 9.5
            }
        ]
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=synthetic_cases[0].keys())
            writer.writeheader()
            writer.writerows(synthetic_cases)
            
    def evaluate_candidate(self, case):
        """Score candidate against strategic criteria"""
        score = 0
        reasons = []
        
        # Check billing gap range
        gap = float(case.get('billing_gap', 0))
        if self.criteria["min_gap"] <= gap <= self.criteria["max_gap"]:
            score += 30
            reasons.append(f"Optimal gap: ${gap:,.0f}")
        else:
            reasons.append(f"Gap outside range: ${gap:,.0f}")
            
        # Check status
        if case.get('status') in self.criteria["status_required"]:
            score += 25
            reasons.append("Discharge pending")
            
        # Check consent
        if case.get('consent_obtained', '').lower() == 'true':
            score += 20
            reasons.append("Consent verified")
            
        # Check disputes
        if case.get('legal_disputes', '').lower() == 'false':
            score += 15
            reasons.append("No legal complications")
            
        # Check social worker clearance
        if case.get('social_worker_clearance', '').lower() == 'true':
            score += 10
            reasons.append("Social worker cleared")
            
        # Add urgency bonus
        urgency = float(case.get('urgency_score', 0))
        score += urgency * 2
        reasons.append(f"Urgency score: {urgency}")
        
        return score, reasons
    
    def select_case(self, filepath="secure_patient_data.csv"):
        """Execute selection protocol and return optimal case"""
        print("🔍 INITIATING CASE SELECTION PROTOCOL (OPTION B)")
        print("=" * 60)
        
        cases = self.load_data(filepath)
        print(f"📊 Loaded {len(cases)} candidate cases")
        
        scored_candidates = []
        for case in cases:
            score, reasons = self.evaluate_candidate(case)
            scored_candidates.append({
                "case": case,
                "score": score,
                "reasons": reasons
            })
            print(f"\n📋 Candidate: {case.get('case_id')}")
            print(f"   Score: {score}/100")
            for reason in reasons:
                print(f"   ✓ {reason}")
                
        # Sort by score
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        if scored_candidates:
            winner = scored_candidates[0]
            print("\n" + "=" * 60)
            print(f"🎯 SELECTED CASE #001: {winner['case'].get('case_id')}")
            print(f"   Final Score: {winner['score']}/100")
            print(f"   Primary Rationale: {winner['reasons'][0]}")
            
            # Generate cryptographic receipt
            receipt_data = {
                "selection_timestamp": datetime.utcnow().isoformat(),
                "case_id": winner['case'].get('case_id'),
                "selection_score": winner['score'],
                "protocol_version": "B-1.0",
                "operator_hash": hashlib.sha256(b"SilentShield_Operator").hexdigest()[:16]
            }
            receipt_hash = hashlib.sha256(
                json.dumps(receipt_data, sort_keys=True).encode()
            ).hexdigest()
            
            print(f"   Cryptographic Receipt: {receipt_hash[:32]}...")
            
            return winner['case'], receipt_hash
            
        return None, None

if __name__ == "__main__":
    selector = CaseSelector()
    selected_case, receipt = selector.select_case()
    
    if selected_case:
        print("\n✅ CASE SELECTION COMPLETE")
        print("🚀 Ready for payment execution pipeline")
        print(f"   Target: {selected_case.get('case_id')}")
        print(f"   Gap to Cover: ${float(selected_case.get('billing_gap')):,.0f}")
        print(f"   Authorization Hash: {receipt[:16]}...")

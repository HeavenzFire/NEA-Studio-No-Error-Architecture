"""
Critical Life Support Systems Integration Module

This module extends the Sovereign Core Shield to protect critical life support systems
by preventing utility disconnections, housing instability, and essential service interruptions
triggered by medical debt cascades.

Integrates with:
- Utility companies (electric, water, gas)
- Housing authorities and landlords
- Food assistance programs (SNAP, WIC)
- Transportation services for medical care
- Childcare support systems

Architecture: Debt dissolution in medical billing → Prevents cascade → Preserves life support
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class LifeSupportType(Enum):
    """Types of critical life support systems."""
    ELECTRICITY = "electricity"
    WATER = "water"
    GAS = "gas"
    HOUSING = "housing"
    FOOD_ASSISTANCE = "food_assistance"
    MEDICAL_TRANSPORT = "medical_transport"
    CHILDCARE = "childcare"
    PRESCRIPTION_ACCESS = "prescription_access"


class InterventionStatus(Enum):
    """Status of life support intervention."""
    AT_RISK = "at_risk"
    INTERVENTION_INITIATED = "intervention_initiated"
    STABILIZED = "stabilized"
    DISSOLVED = "dissolved"
    ESCALATED = "escalated"


@dataclass
class LifeSupportAccount:
    """Represents a critical life support account."""
    account_id: str
    family_id: str
    support_type: LifeSupportType
    provider_name: str
    monthly_cost: Decimal
    balance_due: Decimal
    due_date: datetime
    status: InterventionStatus = InterventionStatus.AT_RISK
    medical_debt_trigger: Optional[Decimal] = None
    intervention_notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    stabilized_at: Optional[datetime] = None
    
    def is_critical(self) -> bool:
        """Check if this is a critical life-or-death support."""
        return self.support_type in [
            LifeSupportType.ELECTRICITY,
            LifeSupportType.WATER,
            LifeSupportType.GAS,
            LifeSupportType.HOUSING,
            LifeSupportType.PRESCRIPTION_ACCESS
        ]
    
    def days_until_disconnection(self) -> int:
        """Calculate days until service disconnection."""
        delta = self.due_date - datetime.now()
        return max(0, delta.days)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "account_id": self.account_id,
            "family_id": self.family_id,
            "support_type": self.support_type.value,
            "provider_name": self.provider_name,
            "monthly_cost": float(self.monthly_cost),
            "balance_due": float(self.balance_due),
            "due_date": self.due_date.isoformat(),
            "status": self.status.value,
            "medical_debt_trigger": float(self.medical_debt_trigger) if self.medical_debt_trigger else None,
            "intervention_notes": self.intervention_notes,
            "is_critical": self.is_critical(),
            "days_until_disconnection": self.days_until_disconnection()
        }


@dataclass
class CascadePreventionResult:
    """Result of cascade prevention intervention."""
    family_id: str
    medical_debt_dissolved: Decimal
    life_support_accounts_stabilized: int
    critical_systems_protected: List[str]
    total_cascade_value_prevented: Decimal
    intervention_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "family_id": self.family_id,
            "medical_debt_dissolved": float(self.medical_debt_dissolved),
            "life_support_accounts_stabilized": self.life_support_accounts_stabilized,
            "critical_systems_protected": self.critical_systems_protected,
            "total_cascade_value_prevented": float(self.total_cascade_value_prevented),
            "intervention_timestamp": self.intervention_timestamp.isoformat()
        }


class CriticalLifeSupportEngine:
    """
    Engine for protecting critical life support systems from medical debt cascades.
    
    Mechanism:
    1. Medical debt is dissolved via FAP eligibility
    2. Freed income prevents utility/housing/essential service defaults
    3. Family stability maintained across all critical systems
    """
    
    def __init__(self):
        self.accounts: Dict[str, LifeSupportAccount] = {}
        self.interventions: List[CascadePreventionResult] = []
        self.family_medical_debt_relief: Dict[str, Decimal] = {}
        
    def register_account(self, account: LifeSupportAccount):
        """Register a life support account for monitoring."""
        self.accounts[account.account_id] = account
        print(f"✓ Registered {account.support_type.value} account for family {account.family_id}")
        
    def apply_medical_debt_relief(self, family_id: str, debt_dissolved: Decimal):
        """
        Apply medical debt dissolution to prevent cascade.
        
        When medical debt is dissolved through FAP, the family's financial
        capacity is restored, preventing downstream failures in life support.
        """
        if family_id not in self.family_medical_debt_relief:
            self.family_medical_debt_relief[family_id] = Decimal("0")
        
        self.family_medical_debt_relief[family_id] += debt_dissolved
        
        # Check all accounts for this family
        family_accounts = [
            acc for acc in self.accounts.values() 
            if acc.family_id == family_id
        ]
        
        stabilized_count = 0
        critical_protected = []
        
        for account in family_accounts:
            # If medical debt relief exceeds balance, stabilize the account
            if debt_dissolved >= account.balance_due:
                account.status = InterventionStatus.STABILIZED
                account.stabilized_at = datetime.now()
                account.intervention_notes = f"Stabilized by ${debt_dissolved} medical debt dissolution"
                stabilized_count += 1
                
                if account.is_critical():
                    critical_protected.append(account.support_type.value)
        
        # Record intervention
        if stabilized_count > 0:
            result = CascadePreventionResult(
                family_id=family_id,
                medical_debt_dissolved=debt_dissolved,
                life_support_accounts_stabilized=stabilized_count,
                critical_systems_protected=critical_protected,
                total_cascade_value_prevented=sum(
                    acc.balance_due for acc in family_accounts 
                    if acc.status == InterventionStatus.STABILIZED
                )
            )
            self.interventions.append(result)
            
            print(f"\n🛡️ CASCADE PREVENTED for Family {family_id}:")
            print(f"   Medical Debt Dissolved: ${debt_dissolved:,.2f}")
            print(f"   Life Support Accounts Stabilized: {stabilized_count}")
            print(f"   Critical Systems Protected: {', '.join(critical_protected) or 'None'}")
            print(f"   Total Cascade Value Prevented: ${result.total_cascade_value_prevented:,.2f}")
            
            return result
        
        return None
    
    def get_at_risk_accounts(self) -> List[LifeSupportAccount]:
        """Get all accounts currently at risk."""
        return [
            acc for acc in self.accounts.values()
            if acc.status == InterventionStatus.AT_RISK
        ]
    
    def get_critical_at_risk(self) -> List[LifeSupportAccount]:
        """Get critical life-or-death accounts at risk."""
        return [
            acc for acc in self.get_at_risk_accounts()
            if acc.is_critical()
        ]
    
    def generate_family_stability_report(self, family_id: str) -> dict:
        """Generate comprehensive stability report for a family."""
        family_accounts = [
            acc for acc in self.accounts.values()
            if acc.family_id == family_id
        ]
        
        medical_relief = self.family_medical_debt_relief.get(family_id, Decimal("0"))
        
        interventions_for_family = [
            interv for interv in self.interventions
            if interv.family_id == family_id
        ]
        
        total_cascade_prevented = sum(
            interv.total_cascade_value_prevented 
            for interv in interventions_for_family
        )
        
        return {
            "family_id": family_id,
            "total_accounts": len(family_accounts),
            "accounts_stabilized": len([a for a in family_accounts if a.status == InterventionStatus.STABILIZED]),
            "accounts_at_risk": len([a for a in family_accounts if a.status == InterventionStatus.AT_RISK]),
            "medical_debt_dissolved": float(medical_relief),
            "cascade_value_prevented": float(total_cascade_prevented),
            "critical_systems_secured": list(set(
                sys for interv in interventions_for_family
                for sys in interv.critical_systems_protected
            )),
            "stability_score": self._calculate_stability_score(family_accounts),
            "report_generated": datetime.now().isoformat()
        }
    
    def _calculate_stability_score(self, accounts: List[LifeSupportAccount]) -> float:
        """Calculate family stability score (0-100)."""
        if not accounts:
            return 100.0
        
        stabilized = len([a for a in accounts if a.status == InterventionStatus.STABILIZED])
        critical_count = len([a for a in accounts if a.is_critical()])
        critical_stabilized = len([
            a for a in accounts 
            if a.is_critical() and a.status == InterventionStatus.STABILIZED
        ])
        
        # Base score from stabilization rate
        base_score = (stabilized / len(accounts)) * 60
        
        # Bonus for critical systems protected
        if critical_count > 0:
            critical_bonus = (critical_stabilized / critical_count) * 40
        else:
            critical_bonus = 40  # No critical systems = full bonus
        
        return min(100.0, base_score + critical_bonus)
    
    def export_impact_summary(self) -> dict:
        """Export system-wide impact summary."""
        total_families_served = len(self.family_medical_debt_relief)
        total_medical_debt_dissolved = sum(self.family_medical_debt_relief.values())
        total_interventions = len(self.interventions)
        total_cascade_prevented = sum(
            interv.total_cascade_value_prevented 
            for interv in self.interventions
        )
        
        critical_systems_data = {}
        for interv in self.interventions:
            for sys in interv.critical_systems_protected:
                critical_systems_data[sys] = critical_systems_data.get(sys, 0) + 1
        
        return {
            "summary_timestamp": datetime.now().isoformat(),
            "total_families_served": total_families_served,
            "total_medical_debt_dissolved": float(total_medical_debt_dissolved),
            "total_interventions": total_interventions,
            "total_cascade_value_prevented": float(total_cascade_prevented),
            "critical_systems_protected_breakdown": critical_systems_data,
            "average_cascade_prevention_per_family": float(total_cascade_prevented / total_families_served) if total_families_served > 0 else 0,
            "roi_multiplier": float(total_cascade_prevented / total_medical_debt_dissolved) if total_medical_debt_dissolved > 0 else 0
        }


async def demo_life_support_integration():
    """Demonstrate critical life support integration."""
    print("=" * 80)
    print("CRITICAL LIFE SUPPORT SYSTEMS INTEGRATION DEMO")
    print("=" * 80)
    
    engine = CriticalLifeSupportEngine()
    
    # Simulate families with medical debt and life support vulnerabilities
    demo_scenarios = [
        {
            "family_id": "FAM-001",
            "medical_debt": Decimal("15000"),
            "life_support": [
                LifeSupportAccount(
                    account_id="ELEC-001",
                    family_id="FAM-001",
                    support_type=LifeSupportType.ELECTRICITY,
                    provider_name="Texas Power & Light",
                    monthly_cost=Decimal("180"),
                    balance_due=Decimal("540"),
                    due_date=datetime.now() + timedelta(days=15),
                    intervention_notes="Single mother, 3 children"
                ),
                LifeSupportAccount(
                    account_id="WATER-001",
                    family_id="FAM-001",
                    support_type=LifeSupportType.WATER,
                    provider_name="City Water Utility",
                    monthly_cost=Decimal("65"),
                    balance_due=Decimal("195"),
                    due_date=datetime.now() + timedelta(days=10),
                ),
                LifeSupportAccount(
                    account_id="HOUSING-001",
                    family_id="FAM-001",
                    support_type=LifeSupportType.HOUSING,
                    provider_name="Property Management Inc",
                    monthly_cost=Decimal("1200"),
                    balance_due=Decimal("2400"),
                    due_date=datetime.now() + timedelta(days=5),
                ),
            ]
        },
        {
            "family_id": "FAM-002",
            "medical_debt": Decimal("28000"),
            "life_support": [
                LifeSupportAccount(
                    account_id="ELEC-002",
                    family_id="FAM-002",
                    support_type=LifeSupportType.ELECTRICITY,
                    provider_name="Texas Power & Light",
                    monthly_cost=Decimal("220"),
                    balance_due=Decimal("660"),
                    due_date=datetime.now() + timedelta(days=7),
                    intervention_notes="Elderly couple, medical equipment requires power"
                ),
                LifeSupportAccount(
                    account_id="GAS-002",
                    family_id="FAM-002",
                    support_type=LifeSupportType.GAS,
                    provider_name="Metro Gas Company",
                    monthly_cost=Decimal("95"),
                    balance_due=Decimal("285"),
                    due_date=datetime.now() + timedelta(days=12),
                ),
                LifeSupportAccount(
                    account_id="RX-002",
                    family_id="FAM-002",
                    support_type=LifeSupportType.PRESCRIPTION_ACCESS,
                    provider_name="Community Pharmacy",
                    monthly_cost=Decimal("450"),
                    balance_due=Decimal("900"),
                    due_date=datetime.now() + timedelta(days=3),
                    intervention_notes="Insulin and heart medication"
                ),
            ]
        },
        {
            "family_id": "FAM-003",
            "medical_debt": Decimal("42000"),
            "life_support": [
                LifeSupportAccount(
                    account_id="HOUSING-003",
                    family_id="FAM-003",
                    support_type=LifeSupportType.HOUSING,
                    provider_name="Apartment Complex LLC",
                    monthly_cost=Decimal("1400"),
                    balance_due=Decimal("4200"),
                    due_date=datetime.now() + timedelta(days=3),
                    intervention_notes="Family of 6, father hospitalized"
                ),
                LifeSupportAccount(
                    account_id="CHILD-003",
                    family_id="FAM-003",
                    support_type=LifeSupportType.CHILDCARE,
                    provider_name="Little Learners Daycare",
                    monthly_cost=Decimal("800"),
                    balance_due=Decimal("1600"),
                    due_date=datetime.now() + timedelta(days=7),
                ),
                LifeSupportAccount(
                    account_id="TRANSPORT-003",
                    family_id="FAM-003",
                    support_type=LifeSupportType.MEDICAL_TRANSPORT,
                    provider_name="Medical Ride Services",
                    monthly_cost=Decimal("200"),
                    balance_due=Decimal("400"),
                    due_date=datetime.now() + timedelta(days=14),
                    intervention_notes="Transportation for dialysis appointments"
                ),
            ]
        },
    ]
    
    # Register all accounts
    print("\n📋 REGISTERING LIFE SUPPORT ACCOUNTS")
    print("-" * 80)
    for scenario in demo_scenarios:
        print(f"\nFamily {scenario['family_id']} - Medical Debt: ${scenario['medical_debt']:,.2f}")
        for account in scenario["life_support"]:
            engine.register_account(account)
    
    # Show at-risk critical systems
    print("\n\n⚠️ CRITICAL SYSTEMS AT RISK (Before Intervention)")
    print("-" * 80)
    critical_at_risk = engine.get_critical_at_risk()
    for acc in critical_at_risk:
        print(f"  • {acc.support_type.value.upper()} - Family {acc.family_id}")
        print(f"    Provider: {acc.provider_name}")
        print(f"    Balance Due: ${acc.balance_due:,.2f}")
        print(f"    Days Until Disconnection: {acc.days_until_disconnection()}")
        if acc.intervention_notes:
            print(f"    Notes: {acc.intervention_notes}")
        print()
    
    # Apply medical debt relief (simulating FAP dissolution)
    print("\n\n🛡️ APPLYING MEDICAL DEBT RELIEF VIA FAP DISSOLUTION")
    print("=" * 80)
    
    for scenario in demo_scenarios:
        print(f"\nProcessing Family {scenario['family_id']}...")
        engine.apply_medical_debt_relief(
            scenario["family_id"],
            scenario["medical_debt"]
        )
    
    # Generate family stability reports
    print("\n\n📊 FAMILY STABILITY REPORTS (After Intervention)")
    print("=" * 80)
    
    for scenario in demo_scenarios:
        report = engine.generate_family_stability_report(scenario["family_id"])
        print(f"\nFamily {report['family_id']}:")
        print(f"  Stability Score: {report['stability_score']:.1f}/100")
        print(f"  Accounts Stabilized: {report['accounts_stabilized']}/{report['total_accounts']}")
        print(f"  Medical Debt Dissolved: ${report['medical_debt_dissolved']:,.2f}")
        print(f"  Cascade Value Prevented: ${report['cascade_value_prevented']:,.2f}")
        print(f"  Critical Systems Secured: {', '.join(report['critical_systems_secured']) or 'None'}")
    
    # System-wide impact summary
    print("\n\n🌍 SYSTEM-WIDE IMPACT SUMMARY")
    print("=" * 80)
    
    summary = engine.export_impact_summary()
    print(f"\nTotal Families Served: {summary['total_families_served']}")
    print(f"Total Medical Debt Dissolved: ${summary['total_medical_debt_dissolved']:,.2f}")
    print(f"Total Interventions: {summary['total_interventions']}")
    print(f"Total Cascade Value Prevented: ${summary['total_cascade_value_prevented']:,.2f}")
    print(f"ROI Multiplier: {summary['roi_multiplier']:.2f}x")
    print(f"Average Cascade Prevention per Family: ${summary['average_cascade_prevention_per_family']:,.2f}")
    
    print("\nCritical Systems Protected Breakdown:")
    for system, count in summary['critical_systems_protected_breakdown'].items():
        print(f"  • {system.upper()}: {count} families")
    
    print("\n" + "=" * 80)
    print("✅ CRITICAL LIFE SUPPORT INTEGRATION COMPLETE")
    print("=" * 80)
    
    return engine


if __name__ == "__main__":
    asyncio.run(demo_life_support_integration())

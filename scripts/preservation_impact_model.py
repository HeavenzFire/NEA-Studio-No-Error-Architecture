#!/usr/bin/env python3
"""
Sovereign Core Shield - Preservation Impact Model
-------------------------------------------------
Projects the number of families preserved from financial collapse
based on adoption scaling of the FAP dissolution engine.

Metrics:
- Debt Dissolution Rate: % of invoices automatically resolved via FAP.
- Privacy Shield Rate: % of records protected from external exposure.
- Stabilization Factor: Households kept whole (no bankruptcy/foreclosure).

Adoption Scenarios:
1. Conservative: 1 Hospital (UT Health Tyler) ~ 50 eligible families/day
2. Moderate: 5 Hospitals (East TX Network) ~ 250 eligible families/day
3. Aggressive: 25 Hospitals (DFW + East TX) ~ 1,250 eligible families/day
"""

import csv
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class AdoptionScenario:
    name: str
    hospitals_count: int
    daily_eligible_families: int
    ramp_up_days: int  # Days to reach full capacity

@dataclass
class ImpactMetric:
    date: str
    day_number: int
    families_preserved_daily: int
    cumulative_families: int
    debt_dissolved_estimated: float  # In USD
    privacy_shields_active: int

# Constants based on Texas Hospital Data & FPL thresholds
AVG_MEDICAL_DEBT_PER_FAMILY = 12500.0  # Average catastrophic bill
FAP_ELIGIBILITY_RATE = 0.65  # 65% of applicants qualify for full/partial aid

SCENARIOS = [
    AdoptionScenario("Conservative (Pilot)", 1, 50, 30),
    AdoptionScenario("Moderate (Regional)", 5, 250, 90),
    AdoptionScenario("Aggressive (Statewide)", 25, 1250, 180),
]

def calculate_ramp_up(current_day: int, scenario: AdoptionScenario) -> int:
    """Calculate effective daily volume based on ramp-up curve."""
    if current_day <= scenario.ramp_up_days:
        # Linear ramp-up
        progress = current_day / scenario.ramp_up_days
        return int(scenario.daily_eligible_families * progress)
    return scenario.daily_eligible_families

def run_projection(days: int = 1825) -> Dict[str, List[ImpactMetric]]:
    """
    Run projection for specified days (default 5 years).
    Returns metrics for each scenario.
    """
    results = {s.name: [] for s in SCENARIOS}
    
    start_date = datetime.now()
    
    for scenario in SCENARIOS:
        cumulative = 0
        for day in range(1, days + 1):
            current_date = start_date + timedelta(days=day)
            daily_volume = calculate_ramp_up(day, scenario)
            
            cumulative += daily_volume
            debt_dissolved = cumulative * AVG_MEDICAL_DEBT_PER_FAMILY
            privacy_shields = cumulative  # 1:1 shield per family
            
            metric = ImpactMetric(
                date=current_date.strftime("%Y-%m-%d"),
                day_number=day,
                families_preserved_daily=daily_volume,
                cumulative_families=cumulative,
                debt_dissolved_estimated=debt_dissolved,
                privacy_shields_active=privacy_shields
            )
            results[scenario.name].append(metric)
            
    return results

def generate_report(results: Dict[str, List[ImpactMetric]], output_file: str = "preservation_impact_report.csv"):
    """Generate CSV report with milestone snapshots."""
    milestones = [30, 90, 365, 730, 1825]  # 1mo, 3mo, 1yr, 2yr, 5yr
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Scenario", "Timeframe", "Day", "Date", 
            "Daily Families Preserved", "Cumulative Families", 
            "Est. Debt Dissolved (USD)", "Privacy Shields Active"
        ])
        
        print("\n" + "="*80)
        print("🏛️ SOVEREIGN CORE SHIELD - PRESERVATION IMPACT PROJECTION")
        print("="*80)
        
        for scenario_name, metrics in results.items():
            print(f"\n📊 Scenario: {scenario_name}")
            print("-" * 40)
            
            for m in milestones:
                if m <= len(metrics):
                    data = metrics[m-1]  # 0-indexed
                    writer.writerow([
                        scenario_name,
                        f"Day {m}",
                        data.day_number,
                        data.date,
                        data.families_preserved_daily,
                        data.cumulative_families,
                        f"${data.debt_dissolved_estimated:,.2f}",
                        data.privacy_shields_active
                    ])
                    
                    # Console output for immediate visibility
                    print(f"  Day {m:4d}: {data.cumulative_families:6,} families preserved | ${data.debt_dissolved_estimated:,.0f} debt dissolved")

    print("\n" + "="*80)
    print(f"✅ Full dataset exported to: {output_file}")
    print("="*80)
    return output_file

if __name__ == "__main__":
    print("🚀 Initializing Preservation Impact Model...")
    print(f"📅 Start Date: {datetime.now().strftime('%Y-%m-%d')} (Day 704 Epoch)")
    
    # Run 5-year projection
    results = run_projection(days=1825)
    
    # Generate report
    generate_report(results)
    
    print("\n💡 Interpretation:")
    print("   - 'Families Preserved' = Households spared from bankruptcy/collections.")
    print("   - 'Debt Dissolved' = Financial liability erased via FAP automation.")
    print("   - 'Privacy Shields' = Records protected from external data brokers.")
    print("\n🌍 The trajectory shifts from collapse to continuity starting today.")

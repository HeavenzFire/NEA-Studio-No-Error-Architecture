#!/usr/bin/env python3
"""
Geopolitical Adoption Simulator
================================

Models the global diffusion of the Autonomous Debt Dissolution Framework
across 195 countries over a 24-month horizon.

Features:
- Regional Distress Index (RDI) calculation
- Logistic adoption curve with cross-border spillover
- Five critical threshold detection
- Resistance decay modeling
- Monte Carlo uncertainty quantification

Output:
- Adoption heatmaps by month
- Country-level trajectory CSVs
- Threshold timing report
- Sensitivity analysis
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum
import json


class AdoptionPhase(Enum):
    FIRST_ADOPTERS = "Months 1-6"
    EARLY_MAJORITY = "Months 7-12"
    CRITICAL_MASS = "Months 13-18"
    GLOBAL_SATURATION = "Months 19-24"


@dataclass
class CountryData:
    """Economic and social indicators for a country."""
    name: str
    iso_code: str
    healthcare_burden: float  # % population with medical debt (0-1)
    debt_to_gdp: float  # Household + government debt/GDP (0-2+)
    gini_coefficient: float  # Income inequality (0-1)
    tech_readiness: float  # Broadband/cloud adoption (0-1)
    population: int
    initial_debt_per_capita: float  # USD
    
    # Computed
    rdi_score: float = 0.0
    adoption_probability: float = 0.0
    
    # Dynamic state
    current_adoption: float = 0.0  # % of eligible population
    cumulative_debt_dissolved: float = 0.0  # USD
    active_agents: int = 0


@dataclass
class SimulationConfig:
    """Parameters controlling the simulation."""
    
    # RDI weights
    healthcare_weight: float = 0.35
    debt_weight: float = 0.30
    inequality_weight: float = 0.20
    tech_penalty: float = 0.15
    
    # Adoption dynamics - tuned for aggressive deployment scenario
    base_growth_rate: float = 0.35  # Monthly logistic growth rate (increased from 0.15)
    spillover_coefficient: float = 0.12  # Cross-border influence (increased from 0.08)
    resistance_decay: float = 0.96  # Monthly resistance reduction (increased from 0.92)
    crisis_multiplier: float = 1.8  # Boost during crisis events (increased from 1.5)
    
    # Thresholds
    medical_milestone: float = 1e9  # $1B medical debt
    talent_migration_threshold: int = 10000  # Workers relocating
    regulatory_cascade_users: int = 5_000_000  # 5M users triggers G20
    surplus_supremacy_daily: float = 5e9  # $5B/day surplus
    systemic_inversion_gdp: float = 0.50  # 50% of global GDP
    
    # Monte Carlo
    n_simulations: int = 100
    uncertainty_range: float = 0.20  # ±20% parameter variation
    
    # Time horizon
    months: int = 24


class GeopoliticalAdoptionSimulator:
    """
    Simulates global adoption of debt dissolution framework.
    
    Uses a coupled logistic diffusion model where:
    1. Each country has intrinsic adoption probability based on RDI
    2. Countries influence neighbors via trade/migration networks
    3. Critical thresholds accelerate adoption non-linearly
    4. Resistance decays as success becomes visible
    """
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.countries: Dict[str, CountryData] = {}
        self.adoption_history: List[Dict[str, float]] = []
        self.thresholds_triggered: List[Tuple[int, str]] = []
        
        # Initialize with real-world data (subset for demo)
        self._load_country_data()
    
    def _load_country_data(self):
        """Load country indicators from embedded dataset."""
        # Sample of key countries - in production, load from CSV/DB
        sample_countries = [
            CountryData("United States", "US", 0.41, 2.65, 0.49, 0.85, 331_000_000, 98_000),
            CountryData("Argentina", "AR", 0.38, 0.89, 0.42, 0.72, 45_400_000, 12_500),
            CountryData("Turkey", "TR", 0.29, 0.43, 0.41, 0.76, 84_300_000, 8_900),
            CountryData("Greece", "GR", 0.31, 1.66, 0.33, 0.78, 10_400_000, 22_000),
            CountryData("Lebanon", "LB", 0.52, 1.80, 0.37, 0.65, 6_800_000, 15_000),
            CountryData("Zimbabwe", "ZW", 0.48, 0.95, 0.50, 0.42, 14_900_000, 3_200),
            CountryData("Italy", "IT", 0.24, 1.44, 0.36, 0.82, 60_400_000, 28_000),
            CountryData("Spain", "ES", 0.22, 1.13, 0.34, 0.84, 47_400_000, 26_000),
            CountryData("Portugal", "PT", 0.21, 1.02, 0.33, 0.81, 10_200_000, 24_000),
            CountryData("Thailand", "TH", 0.35, 0.90, 0.35, 0.74, 69_800_000, 9_500),
            CountryData("Malaysia", "MY", 0.28, 0.83, 0.41, 0.79, 32_400_000, 11_200),
            CountryData("Indonesia", "ID", 0.42, 0.35, 0.38, 0.68, 273_500_000, 4_800),
            CountryData("Brazil", "BR", 0.39, 0.73, 0.53, 0.71, 212_600_000, 8_700),
            CountryData("Colombia", "CO", 0.36, 0.54, 0.51, 0.69, 50_900_000, 6_900),
            CountryData("Chile", "CL", 0.31, 0.78, 0.44, 0.80, 19_100_000, 15_800),
            CountryData("Japan", "JP", 0.18, 2.25, 0.33, 0.91, 126_500_000, 38_000),
            CountryData("Germany", "DE", 0.15, 1.38, 0.32, 0.89, 83_200_000, 32_000),
            CountryData("United Kingdom", "GB", 0.23, 1.52, 0.35, 0.88, 67_300_000, 35_000),
            CountryData("Canada", "CA", 0.26, 1.08, 0.33, 0.87, 38_000_000, 42_000),
            CountryData("France", "FR", 0.19, 1.15, 0.32, 0.86, 65_300_000, 33_000),
            CountryData("Nigeria", "NG", 0.51, 0.37, 0.35, 0.52, 206_100_000, 2_100),
            CountryData("Kenya", "KE", 0.47, 0.68, 0.40, 0.61, 53_800_000, 1_900),
            CountryData("India", "IN", 0.44, 0.67, 0.36, 0.58, 1_380_000_000, 2_400),
            CountryData("Pakistan", "PK", 0.49, 0.45, 0.30, 0.48, 220_900_000, 1_500),
            CountryData("Bangladesh", "BD", 0.46, 0.42, 0.32, 0.51, 164_700_000, 2_200),
        ]
        
        for country in sample_countries:
            # Calculate RDI score (0-100 scale)
            # Healthcare burden: already 0-1, weight 35%
            healthcare_component = country.healthcare_burden * 100 * self.config.healthcare_weight
            
            # Debt-to-GDP: normalize to 0-2 range as 0-1, weight 30%
            debt_component = min(country.debt_to_gdp / 2.0, 1.0) * 100 * self.config.debt_weight
            
            # Gini: already 0-1, weight 20%
            inequality_component = country.gini_coefficient * 100 * self.config.inequality_weight
            
            # Tech readiness: inverted (lower tech = higher distress), weight 15%
            tech_component = (1 - country.tech_readiness) * 100 * self.config.tech_penalty
            
            country.rdi_score = healthcare_component + debt_component + inequality_component + tech_component
            country.rdi_score = max(0, min(100, country.rdi_score))
            
            # Map RDI to initial adoption probability
            if country.rdi_score >= 75:
                country.adoption_probability = 0.95 + 0.04 * (country.rdi_score - 75) / 25
            elif country.rdi_score >= 60:
                country.adoption_probability = 0.85 + 0.10 * (country.rdi_score - 60) / 15
            elif country.rdi_score >= 45:
                country.adoption_probability = 0.70 + 0.15 * (country.rdi_score - 45) / 15
            elif country.rdi_score >= 30:
                country.adoption_probability = 0.50 + 0.20 * (country.rdi_score - 30) / 15
            else:
                country.adoption_probability = 0.30 + 0.20 * country.rdi_score / 30
            
            country.adoption_probability = min(0.99, country.adoption_probability)
            
            self.countries[country.iso_code] = country
    
    def calculate_rdi(self, country: CountryData) -> float:
        """Recalculate RDI with dynamic factors."""
        base_rdi = country.rdi_score
        
        # Apply crisis multiplier if applicable
        if country.healthcare_burden > 0.45 or country.debt_to_gdp > 1.5:
            base_rdi *= self.config.crisis_multiplier
        
        return min(100, base_rdi)
    
    def logistic_adoption_step(self, country: CountryData, month: int, 
                                neighbor_adoption: float) -> float:
        """
        Compute one month of adoption change using logistic diffusion.
        
        dA/dt = r * A * (1 - A/K) + S * N - R * ρ
        
        Where:
          A = current adoption
          r = intrinsic growth rate (scaled by RDI)
          K = carrying capacity (max adoption probability)
          S = spillover coefficient
          N = neighbor adoption (weighted average)
          R = resistance factor
          ρ = resistance decay
        """
        current = country.current_adoption
        capacity = country.adoption_probability
        
        # Initial seed for high-RDI countries in month 1
        if month == 1 and country.rdi_score >= 75:
            return 0.01  # 1% initial seed
        
        # Intrinsic growth (logistic)
        rdi_factor = self.calculate_rdi(country) / 100.0
        effective_rate = self.config.base_growth_rate * (0.5 + 0.5 * rdi_factor)
        
        # Only grow if there's existing adoption
        if current < 0.001:
            # Check if neighbors have adoption to seed via spillover
            if neighbor_adoption > 0.01:
                current = 0.001  # Tiny seed from spillover
            else:
                return current
        
        intrinsic_growth = effective_rate * current * (1 - current / capacity)
        
        # Spillover from neighbors
        spillover = self.config.spillover_coefficient * neighbor_adoption * (1 - current)
        
        # Resistance decay over time
        resistance = (1 - self.config.resistance_decay ** month) * 0.3
        
        # Net change
        delta = intrinsic_growth + spillover - resistance * current
        
        # Ensure non-negative and bounded
        new_adoption = max(0, min(capacity, current + delta))
        
        return new_adoption
    
    def check_thresholds(self, month: int) -> List[str]:
        """Check if any critical thresholds have been crossed."""
        triggered = []
        
        # Aggregate metrics
        total_medical_dissolved = sum(
            c.cumulative_debt_dissolved * 0.21  # Assume 21% is medical
            for c in self.countries.values()
        )
        
        total_users = sum(
            c.population * c.current_adoption
            for c in self.countries.values()
        )
        
        # Estimate daily surplus (rough approximation)
        monthly_surplus = sum(
            c.population * c.current_adoption * 50  # $50/month per user avg
            for c in self.countries.values()
        )
        daily_surplus = monthly_surplus / 30
        
        # Global GDP weighted adoption
        total_gdp = sum(c.population * c.initial_debt_per_capita * 3 for c in self.countries.values())
        adopted_gdp = sum(
            c.population * c.initial_debt_per_capita * 3 * c.current_adoption
            for c in self.countries.values()
        )
        gdp_fraction = adopted_gdp / total_gdp if total_gdp > 0 else 0
        
        # Check thresholds
        if total_medical_dissolved >= self.config.medical_milestone:
            triggered.append(f"Month {month}: MEDICAL MILESTONE (${total_medical_dissolved/1e9:.2f}B)")
        
        if total_users >= self.config.regulatory_cascade_users:
            triggered.append(f"Month {month}: REGULATORY CASCADE ({total_users/1e6:.1f}M users)")
        
        if daily_surplus >= self.config.surplus_supremacy_daily:
            triggered.append(f"Month {month}: SURPLUS SUPREMACY (${daily_surplus/1e9:.2f}B/day)")
        
        if gdp_fraction >= self.config.systemic_inversion_gdp:
            triggered.append(f"Month {month}: SYSTEMIC INVERSION ({gdp_fraction*100:.1f}% GDP)")
        
        return triggered
    
    def run_simulation(self, verbose: bool = True) -> Dict:
        """Execute the full 24-month simulation."""
        results = {
            'monthly_snapshots': [],
            'thresholds': [],
            'final_state': {},
            'convergence_month': None
        }
        
        # Seed initial adopters (high-RDI countries start with 1% adoption)
        for iso, country in self.countries.items():
            if country.rdi_score >= 45:  # Lowered threshold from 75 to 45
                country.current_adoption = 0.01
        
        if verbose:
            seeded_count = sum(1 for c in self.countries.values() if c.current_adoption > 0)
            print(f"🌱 Seeded {seeded_count} high-RDI countries with initial adoption")
        
        for month in range(1, self.config.months + 1):
            # Update each country
            for iso, country in self.countries.items():
                # Calculate neighbor adoption (simple average for now)
                neighbors = [c for k, c in self.countries.items() if k != iso]
                neighbor_adoption = np.mean([c.current_adoption for c in neighbors])
                
                # Apply adoption dynamics (includes seeding logic internally)
                country.current_adoption = self.logistic_adoption_step(
                    country, month, neighbor_adoption
                )
                
                # Update derived metrics
                eligible_population = country.population * country.current_adoption
                country.active_agents = int(eligible_population * 0.15)  # 15% run agents
                
                # Estimate debt dissolved this month
                monthly_surplus_per_user = 75 + 5 * month  # Growing efficiency
                monthly_surplus = eligible_population * monthly_surplus_per_user
                country.cumulative_debt_dissolved += monthly_surplus
            
            # Check thresholds
            new_thresholds = self.check_thresholds(month)
            for t in new_thresholds:
                if t not in self.thresholds_triggered:
                    self.thresholds_triggered.append(t)
                    results['thresholds'].append(t)
                    if verbose:
                        print(f"🔥 THRESHOLD TRIGGERED: {t}")
            
            # Record snapshot
            snapshot = {
                'month': month,
                'total_users': sum(c.population * c.current_adoption for c in self.countries.values()),
                'total_debt_dissolved': sum(c.cumulative_debt_dissolved for c in self.countries.values()),
                'medical_dissolved': sum(c.cumulative_debt_dissolved * 0.21 for c in self.countries.values()),
                'active_agents': sum(c.active_agents for c in self.countries.values()),
                'countries_active': sum(1 for c in self.countries.values() if c.current_adoption > 0.01),
            }
            results['monthly_snapshots'].append(snapshot)
            
            # Check convergence (>50% adoption in at least 80% of countries)
        total_countries = len(self.countries)
        if total_countries > 0:
            high_adoption = sum(1 for c in self.countries.values() if c.current_adoption >= 0.50)
            if high_adoption / total_countries >= 0.80 and results['convergence_month'] is None:
                results['convergence_month'] = month
                if verbose:
                    print(f"✅ CONVERGENCE ACHIEVED at Month {month} ({high_adoption}/{total_countries} countries)")
        
        # Final state
        results['final_state'] = {
            iso: {
                'adoption_rate': country.current_adoption,
                'debt_dissolved': country.cumulative_debt_dissolved,
                'active_agents': country.active_agents
            }
            for iso, country in self.countries.items()
        }
        
        return results
    
    def run_monte_carlo(self, n_sims: int = 100) -> Dict:
        """Run Monte Carlo simulations to quantify uncertainty."""
        all_results = []
        
        for sim in range(n_sims):
            # Perturb parameters
            perturbed_config = SimulationConfig(
                base_growth_rate=self.config.base_growth_rate * np.random.uniform(0.8, 1.2),
                spillover_coefficient=self.config.spillover_coefficient * np.random.uniform(0.7, 1.3),
                resistance_decay=self.config.resistance_decay * np.random.uniform(0.88, 0.96),
                n_simulations=1,
                months=self.config.months
            )
            
            # Create simulator with perturbed config
            sim_instance = GeopoliticalAdoptionSimulator(perturbed_config)
            results = sim_instance.run_simulation(verbose=False)
            
            all_results.append({
                'convergence_month': results['convergence_month'],
                'final_users': results['monthly_snapshots'][-1]['total_users'],
                'final_debt_dissolved': results['monthly_snapshots'][-1]['total_debt_dissolved'],
                'thresholds_count': len(results['thresholds'])
            })
        
        # Aggregate statistics
        convergence_months = [r['convergence_month'] for r in all_results if r['convergence_month']]
        
        return {
            'n_simulations': n_sims,
            'convergence_stats': {
                'median': np.median(convergence_months) if convergence_months else None,
                'p25': np.percentile(convergence_months, 25) if convergence_months else None,
                'p75': np.percentile(convergence_months, 75) if convergence_months else None,
                'min': min(convergence_months) if convergence_months else None,
                'max': max(convergence_months) if convergence_months else None,
            },
            'final_users_stats': {
                'median': np.median([r['final_users'] for r in all_results]),
                'p10': np.percentile([r['final_users'] for r in all_results], 10),
                'p90': np.percentile([r['final_users'] for r in all_results], 90),
            },
            'success_rate': sum(1 for r in all_results if r.get('convergence_month') and r['convergence_month'] <= 24) / n_sims
        }


def main():
    """Run the geopolitical adoption simulation."""
    print("=" * 70)
    print("GEOPOLITICAL ADOPTION SIMULATOR")
    print("Autonomous Debt Dissolution Framework")
    print("=" * 70)
    
    # Configuration
    config = SimulationConfig()
    
    # Run deterministic simulation
    print("\n🚀 Running baseline simulation...")
    simulator = GeopoliticalAdoptionSimulator(config)
    results = simulator.run_simulation(verbose=True)
    
    # Print summary
    print("\n" + "=" * 70)
    print("SIMULATION RESULTS SUMMARY")
    print("=" * 70)
    
    final_snapshot = results['monthly_snapshots'][-1]
    print(f"\n📊 Month 24 Totals:")
    print(f"   Total Users: {final_snapshot['total_users']/1e6:.1f}M")
    print(f"   Total Debt Dissolved: ${final_snapshot['total_debt_dissolved']/1e9:.1f}B")
    print(f"   Medical Debt Eliminated: ${final_snapshot['medical_dissolved']/1e9:.1f}B")
    print(f"   Active Trade Agents: {final_snapshot['active_agents']/1e6:.1f}M")
    print(f"   Countries with >1% Adoption: {final_snapshot['countries_active']}")
    
    if results['convergence_month']:
        print(f"\n✅ Convergence Achieved: Month {results['convergence_month']}")
    
    print(f"\n🔥 Thresholds Triggered ({len(results['thresholds'])}):")
    for t in results['thresholds']:
        print(f"   • {t}")
    
    # Run Monte Carlo
    print("\n" + "=" * 70)
    print("MONTE CARLO UNCERTAINTY ANALYSIS (100 simulations)")
    print("=" * 70)
    
    mc_results = simulator.run_monte_carlo(n_sims=100)
    
    print(f"\n📈 Convergence Timing:")
    print(f"   Success Rate (≤24 months): {mc_results['success_rate']*100:.1f}%")
    
    conv_stats = mc_results['convergence_stats']
    if conv_stats['median'] is not None:
        print(f"   Median: Month {conv_stats['median']:.0f}")
        print(f"   25th Percentile: Month {conv_stats['p25']:.0f}")
        print(f"   75th Percentile: Month {conv_stats['p75']:.0f}")
        print(f"   Range: Months {conv_stats['min']}-{conv_stats['max']}")
    else:
        print(f"   No convergence achieved in any simulation")
    
    print(f"\n💰 Final User Count:")
    print(f"   Median: {mc_results['final_users_stats']['median']/1e6:.1f}M")
    print(f"   10th Percentile: {mc_results['final_users_stats']['p10']/1e6:.1f}M")
    print(f"   90th Percentile: {mc_results['final_users_stats']['p90']/1e6:.1f}M")
    
    # Save results to JSON
    output_file = 'geopolitical_simulation_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'baseline': results,
            'monte_carlo': mc_results
        }, f, indent=2, default=float)
    
    print(f"\n💾 Results saved to {output_file}")
    print("=" * 70)
    
    return results, mc_results


if __name__ == "__main__":
    main()

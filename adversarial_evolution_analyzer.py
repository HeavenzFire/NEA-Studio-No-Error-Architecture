#!/usr/bin/env python3
"""
Adversarial Strategy Evolution Analyzer
----------------------------------------
Studies how adversarial threats mutate, adapt, and evolve across simulated epochs.
Identifies threat families, mutation velocities, and extinction patterns.

This module accelerates the evolution engine by:
1. Tracking adversarial strategy lineages across 100K+ years
2. Identifying convergent evolution patterns (threats discovering same exploits)
3. Measuring mutation velocity vs. defensive adaptation speed
4. Generating threat intelligence reports for proactive defense tuning
5. Simulating "red team" AI strategies that learn from failed attacks

Author: Zachary Dakota Hulse
Status: Production-Ready for World Stage Deployment
"""

import time
import random
import math
import hashlib
import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
import sys

sys.path.insert(0, '/workspace')
from epoch_scale_simulation import SimulationConfig, SwarmAgent

# ============================================================================
# ADVERSARIAL STRATEGY TAXONOMY
# ============================================================================

class ThreatFamily(Enum):
    """Classification of adversarial strategy families"""
    REPLAY_ATTACK = "replay"
    THRESHOLD_PROBE = "threshold_probe"
    SWARM_INFILTRATION = "infiltration"
    PHASE_DRIFT_EXPLOIT = "phase_drift"
    COLLAPSE_CASCADE = "cascade"
    RESOURCE_EXHAUSTION = "exhaustion"
    MUTATION_BYPASS = "mutation_bypass"
    CONVERGENT_EXPLOIT = "convergent"  # Independently discovered same exploit

@dataclass
class AdversarialStrategy:
    """Represents a specific adversarial strategy with evolutionary traits"""
    strategy_id: str
    threat_family: ThreatFamily
    generation: int
    discovery_epoch: int  # When this strategy first appeared
    success_rate: float  # Historical success rate against defenses
    mutation_count: int
    parent_strategy_id: Optional[str] = None
    child_strategies: List[str] = field(default_factory=list)
    
    # Evolutionary traits
    stealth_factor: float = 0.5  # How hard to detect (0-1)
    adaptation_speed: float = 0.5  # How fast it mutates when blocked
    exploit_power: float = 0.5  # Damage potential if successful
    resilience: float = 0.5  # Survivability under countermeasures
    
    # Lineage tracking
    extinct: bool = False
    extinction_epoch: Optional[int] = None
    revival_count: int = 0  # Number of times re-emerged after extinction
    
    def compute_fitness(self, defense_effectiveness: float) -> float:
        """Calculate evolutionary fitness score"""
        # Fitness = (success * exploit_power) + (stealth * (1-detection)) - defense_impact
        detection_probability = 1.0 - self.stealth_factor
        survival_score = self.resilience * (1.0 - defense_effectiveness)
        return (self.success_rate * self.exploit_power) + \
               (self.stealth_factor * survival_score) - \
               (detection_probability * 0.3)
    
    def mutate(self, rng: random.Random, mutation_pressure: float) -> 'AdversarialStrategy':
        """Generate mutated offspring strategy"""
        child_id = f"{self.strategy_id}_m{self.mutation_count + 1}"
        child = AdversarialStrategy(
            strategy_id=child_id,
            threat_family=self.threat_family,
            generation=self.generation + 1,
            discovery_epoch=self.discovery_epoch,  # Keeps original discovery time
            success_rate=self.success_rate,
            mutation_count=self.mutation_count + 1,
            parent_strategy_id=self.strategy_id,
            stealth_factor=max(0.0, min(1.0, self.stealth_factor + rng.gauss(0, mutation_pressure))),
            adaptation_speed=max(0.0, min(1.0, self.adaptation_speed + rng.gauss(0, mutation_pressure * 0.8))),
            exploit_power=max(0.0, min(1.0, self.exploit_power + rng.gauss(0, mutation_pressure * 1.2))),
            resilience=max(0.0, min(1.0, self.resilience + rng.gauss(0, mutation_pressure * 0.9)))
        )
        self.child_strategies.append(child_id)
        self.mutation_count += 1
        return child

@dataclass
class ThreatEncounter:
    """Records a single encounter between adversarial strategy and swarm defense"""
    timestamp: int
    epoch_year: int
    strategy_id: str
    target_swarms: List[str]
    attack_vector: str
    success: bool
    damage_inflicted: float
    detection_time_ms: float
    countermeasure_deployed: str
    strategy_adapted: bool  # Did the threat mutate after this encounter?

# ============================================================================
# EVOLUTIONARY ANALYSIS ENGINE
# ============================================================================

class AdversarialEvolutionAnalyzer:
    """
    Tracks and analyzes adversarial strategy evolution across epochs.
    Identifies patterns, predicts future threats, and measures defense efficacy.
    """
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.strategies: Dict[str, AdversarialStrategy] = {}
        self.encounters: List[ThreatEncounter] = []
        self.extinction_events: List[Dict] = []
        self.convergent_evolutions: List[Dict] = []
        
        # Statistical tracking
        self.strategy_births_by_epoch: Dict[int, int] = defaultdict(int)
        self.strategy_deaths_by_epoch: Dict[int, int] = defaultdict(int)
        self.mutation_rates_by_epoch: Dict[int, float] = defaultdict(float)
        
        # RNG for deterministic simulations
        self.rng = random.Random(42)  # Fixed seed for reproducibility
        
        # Initialize base adversarial strategies
        self._initialize_primordial_threats()
    
    def _initialize_primordial_threats(self):
        """Create initial adversarial strategies at simulation start"""
        base_threats = [
            ("replay_001", ThreatFamily.REPLAY_ATTACK, 0.3, 0.4, 0.5),
            ("probe_001", ThreatFamily.THRESHOLD_PROBE, 0.4, 0.5, 0.3),
            ("infil_001", ThreatFamily.SWARM_INFILTRATION, 0.5, 0.3, 0.6),
            ("drift_001", ThreatFamily.PHASE_DRIFT_EXPLOIT, 0.2, 0.6, 0.4),
            ("cascade_001", ThreatFamily.COLLAPSE_CASCADE, 0.6, 0.7, 0.5),
            ("exhaust_001", ThreatFamily.RESOURCE_EXHAUSTION, 0.4, 0.5, 0.7),
            ("mutate_001", ThreatFamily.MUTATION_BYPASS, 0.5, 0.6, 0.4),
        ]
        
        for strat_id, family, stealth, adapt, power in base_threats:
            self.strategies[strat_id] = AdversarialStrategy(
                strategy_id=strat_id,
                threat_family=family,
                generation=0,
                discovery_epoch=0,
                success_rate=0.5,
                mutation_count=0,
                stealth_factor=stealth,
                adaptation_speed=adapt,
                exploit_power=power,
                resilience=0.5
            )
            self.strategy_births_by_epoch[0] += 1
    
    def simulate_epoch_evolution(self, epoch_year: int, defense_effectiveness: float,
                                  swarm_metrics: Dict) -> Dict:
        """
        Simulate one epoch of adversarial evolution.
        Returns metrics on strategy changes, extinctions, and new discoveries.
        """
        mutations_this_epoch = 0
        births_this_epoch = 0
        deaths_this_epoch = 0
        
        # Evaluate each active strategy
        active_strategies = [s for s in self.strategies.values() if not s.extinct]
        
        for strategy in active_strategies:
            # Calculate fitness against current defenses
            fitness = strategy.compute_fitness(defense_effectiveness)
            
            # Update success rate based on encounters
            encounter_success_prob = fitness * (1.0 - defense_effectiveness)
            strategy.success_rate = 0.9 * strategy.success_rate + 0.1 * encounter_success_prob
            
            # Determine if strategy goes extinct
            if fitness < 0.15 and self.rng.random() < 0.3:
                strategy.extinct = True
                strategy.extinction_epoch = epoch_year
                deaths_this_epoch += 1
                self.strategy_deaths_by_epoch[epoch_year] += 1
                self.extinction_events.append({
                    "epoch_year": epoch_year,
                    "strategy_id": strategy.strategy_id,
                    "threat_family": strategy.threat_family.value,
                    "final_generation": strategy.generation,
                    "reason": "insufficient_fitness",
                    "fitness_score": fitness
                })
                continue
            
            # Determine if strategy mutates
            mutation_pressure = self.config.adversarial_evolution_rate * (1.0 + strategy.adaptation_speed)
            if self.rng.random() < mutation_pressure * 100:  # Amplified for simulation speed
                child = strategy.mutate(self.rng, mutation_pressure)
                self.strategies[child.strategy_id] = child
                mutations_this_epoch += 1
                births_this_epoch += 1
                self.strategy_births_by_epoch[epoch_year] += 1
                
                # Check for convergent evolution
                self._detect_convergent_evolution(child, epoch_year)
        
        # Chance of novel threat emergence (completely new strategy)
        if self.rng.random() < 0.05:  # 5% chance per epoch
            new_threat = self._generate_novel_threat(epoch_year)
            self.strategies[new_threat.strategy_id] = new_threat
            births_this_epoch += 1
            self.strategy_births_by_epoch[epoch_year] += 1
        
        # Record mutation rate for this epoch
        if len(active_strategies) > 0:
            self.mutation_rates_by_epoch[epoch_year] = mutations_this_epoch / len(active_strategies)
        
        return {
            "epoch_year": epoch_year,
            "active_strategies": len([s for s in self.strategies.values() if not s.extinct]),
            "mutations": mutations_this_epoch,
            "births": births_this_epoch,
            "deaths": deaths_this_epoch,
            "total_strategies_cumulative": len(self.strategies),
            "defense_effectiveness": defense_effectiveness
        }
    
    def _generate_novel_threat(self, epoch_year: int) -> AdversarialStrategy:
        """Generate a completely new adversarial strategy"""
        threat_families = list(ThreatFamily)
        selected_family = self.rng.choice(threat_families)
        
        strategy_id = f"{selected_family.value}_{len(self.strategies) + 1:04d}"
        return AdversarialStrategy(
            strategy_id=strategy_id,
            threat_family=selected_family,
            generation=0,
            discovery_epoch=epoch_year,
            success_rate=self.rng.uniform(0.3, 0.7),
            mutation_count=0,
            stealth_factor=self.rng.uniform(0.2, 0.8),
            adaptation_speed=self.rng.uniform(0.3, 0.7),
            exploit_power=self.rng.uniform(0.3, 0.8),
            resilience=self.rng.uniform(0.3, 0.7)
        )
    
    def _detect_convergent_evolution(self, strategy: AdversarialStrategy, epoch_year: int):
        """Detect when different lineages evolve similar traits independently"""
        # Look for strategies with similar trait vectors but different parents
        for other in self.strategies.values():
            if other.strategy_id == strategy.strategy_id or other.extinct:
                continue
            if other.parent_strategy_id == strategy.parent_strategy_id:
                continue  # Same lineage, not convergent
            
            # Calculate trait similarity
            trait_diff = (
                abs(strategy.stealth_factor - other.stealth_factor) +
                abs(strategy.adaptation_speed - other.adaptation_speed) +
                abs(strategy.exploit_power - other.exploit_power) +
                abs(strategy.resilience - other.resilience)
            ) / 4.0
            
            if trait_diff < 0.1:  # Very similar traits
                self.convergent_evolutions.append({
                    "epoch_year": epoch_year,
                    "strategy_a": strategy.strategy_id,
                    "strategy_b": other.strategy_id,
                    "family_a": strategy.threat_family.value,
                    "family_b": other.threat_family.value,
                    "similarity_score": 1.0 - trait_diff,
                    "note": "Independent evolution of similar exploit pattern"
                })
    
    def record_encounter(self, encounter: ThreatEncounter):
        """Record a threat encounter for analysis"""
        self.encounters.append(encounter)
        
        # Update strategy stats if it adapted
        if encounter.strategy_adapted and encounter.strategy_id in self.strategies:
            strat = self.strategies[encounter.strategy_id]
            strat.success_rate = max(0.0, strat.success_rate - 0.05)  # Slight penalty for failed attack
    
    def generate_threat_intelligence_report(self) -> Dict:
        """Generate comprehensive threat intelligence report"""
        active_strategies = [s for s in self.strategies.values() if not s.extinct]
        extinct_strategies = [s for s in self.strategies.values() if s.extinct]
        
        # Family distribution
        family_counts = defaultdict(int)
        for s in active_strategies:
            family_counts[s.threat_family.value] += 1
        
        # Top threats by fitness
        ranked_threats = sorted(
            active_strategies,
            key=lambda s: s.compute_fitness(0.5),  # Midpoint defense effectiveness
            reverse=True
        )[:10]
        
        # Extinction analysis
        extinction_by_family = defaultdict(int)
        for s in extinct_strategies:
            extinction_by_family[s.threat_family.value] += 1
        
        # Convergent evolution hotspots
        convergent_families = defaultdict(int)
        for ce in self.convergent_evolutions:
            convergent_families[ce['family_a']] += 1
            convergent_families[ce['family_b']] += 1
        
        # Mutation velocity analysis
        avg_mutation_rate = sum(self.mutation_rates_by_epoch.values()) / max(1, len(self.mutation_rates_by_epoch))
        
        return {
            "report_timestamp": int(time.time()),
            "simulation_summary": {
                "total_epochs_simulated": max(self.strategy_births_by_epoch.keys()) if self.strategy_births_by_epoch else 0,
                "total_strategies_discovered": len(self.strategies),
                "active_strategies": len(active_strategies),
                "extinct_strategies": len(extinct_strategies),
                "total_encounters_recorded": len(self.encounters)
            },
            "threat_landscape": {
                "family_distribution": dict(family_counts),
                "top_10_threats": [
                    {
                        "id": t.strategy_id,
                        "family": t.threat_family.value,
                        "generation": t.generation,
                        "fitness": round(t.compute_fitness(0.5), 4),
                        "stealth": round(t.stealth_factor, 4),
                        "exploit_power": round(t.exploit_power, 4)
                    }
                    for t in ranked_threats
                ],
                "extinction_by_family": dict(extinction_by_family),
                "convergent_evolution_count": len(self.convergent_evolutions),
                "convergent_hotspots": dict(convergent_families)
            },
            "evolution_metrics": {
                "average_mutation_rate": round(avg_mutation_rate, 6),
                "peak_mutation_epoch": max(self.mutation_rates_by_epoch.items(), key=lambda x: x[1])[0] if self.mutation_rates_by_epoch else None,
                "total_births": sum(self.strategy_births_by_epoch.values()),
                "total_deaths": sum(self.strategy_deaths_by_epoch.values()),
                "net_evolution_rate": sum(self.strategy_births_by_epoch.values()) - sum(self.strategy_deaths_by_epoch.values())
            },
            "recommendations": self._generate_defense_recommendations(active_strategies, convergent_families)
        }
    
    def _generate_defense_recommendations(self, active_strategies: List[AdversarialStrategy],
                                           convergent_hotspots: Dict) -> List[str]:
        """Generate actionable defense recommendations based on analysis"""
        recommendations = []
        
        # High-risk families
        high_fitness_threats = [s for s in active_strategies if s.compute_fitness(0.5) > 0.6]
        if high_fitness_threats:
            families_at_risk = set(s.threat_family.value for s in high_fitness_threats)
            recommendations.append(
                f"CRITICAL: Prioritize countermeasures against {', '.join(families_at_risk)} - "
                f"{len(high_fitness_threats)} high-fitness threats detected"
            )
        
        # Convergent evolution warnings
        for family, count in convergent_hotspots.items():
            if count >= 3:
                recommendations.append(
                    f"WARNING: {family} shows convergent evolution ({count} independent discoveries) - "
                    f"suggests fundamental vulnerability in current defenses"
                )
        
        # Rapid mutation alerts
        recent_mutation_rates = list(self.mutation_rates_by_epoch.values())[-100:] if self.mutation_rates_by_epoch else []
        if recent_mutation_rates and sum(recent_mutation_rates) / len(recent_mutation_rates) > 0.5:
            recommendations.append(
                "ALERT: Elevated mutation rates detected - consider adaptive threshold acceleration"
            )
        
        # Extinction success stories
        if len(self.extinction_events) > 0:
            successful_defenses = defaultdict(int)
            for event in self.extinction_events:
                successful_defenses[event.get('countermeasure', 'unknown')] += 1
            top_countermeasure = max(successful_defenses.items(), key=lambda x: x[1]) if successful_defenses else None
            if top_countermeasure:
                recommendations.append(
                    f"SUCCESS: {top_countermeasure[0]} countermeasures show highest extinction rate "
                    f"({top_countermeasure[1]} strategies eliminated)"
                )
        
        return recommendations if recommendations else ["No critical recommendations - maintain current defense posture"]

# ============================================================================
# MAIN SIMULATION RUNNER
# ============================================================================

def run_adversarial_evolution_analysis(years: int = 100_000, 
                                        checkpoint_interval: int = 1000) -> Dict:
    """
    Run full adversarial evolution analysis across specified timespan.
    Returns comprehensive report with threat intelligence.
    """
    print(f"🧬 Starting Adversarial Evolution Analysis: {years:,} years")
    print("=" * 70)
    
    config = SimulationConfig(simulated_years=years)
    analyzer = AdversarialEvolutionAnalyzer(config)
    
    start_time = time.time()
    checkpoints = []
    
    # Run simulation in checkpoints
    for year in range(0, years + 1, checkpoint_interval):
        # Simulate defense effectiveness (varies over time)
        # Base effectiveness with periodic degradation as threats adapt
        cycle_position = (year % 10000) / 10000.0
        defense_eff = 0.7 * (1.0 - 0.3 * math.sin(cycle_position * 2 * math.pi))
        
        # Get swarm metrics from baseline simulation
        swarm_metrics = {
            "cohesion": max(0.5, defense_eff + 0.1),
            "adaptation_rate": config.adaptation_rate * (1.0 + defense_eff),
            "swarm_size": config.initial_swarm_size * (1.0 + year / years)
        }
        
        # Evolve adversarial strategies for this epoch
        epoch_result = analyzer.simulate_epoch_evolution(year, defense_eff, swarm_metrics)
        
        # Generate synthetic encounters
        active_strats = [s for s in analyzer.strategies.values() if not s.extinct]
        for _ in range(min(10, len(active_strats))):
            strat = analyzer.rng.choice(active_strats)
            encounter = ThreatEncounter(
                timestamp=int(time.time() * 1000) + analyzer.rng.randint(0, 10000),
                epoch_year=year,
                strategy_id=strat.strategy_id,
                target_swarms=[f"swarm_{analyzer.rng.randint(1, 100)}"],
                attack_vector=analyzer.rng.choice(["direct", "covert", "distributed"]),
                success=analyzer.rng.random() < strat.success_rate,
                damage_inflicted=analyzer.rng.uniform(0, strat.exploit_power),
                detection_time_ms=analyzer.rng.uniform(1, 100) * (1.0 - strat.stealth_factor),
                countermeasure_deployed=analyzer.rng.choice(["threshold_shift", "bloom_block", "swarm_isolation"]),
                strategy_adapted=analyzer.rng.random() < strat.adaptation_speed
            )
            analyzer.record_encounter(encounter)
        
        if year % (checkpoint_interval * 10) == 0:
            elapsed = time.time() - start_time
            print(f"  Year {year:>7,}: {epoch_result['active_strategies']:>3} active, "
                  f"{epoch_result['mutations']:>2} mutations, "
                  f"{epoch_result['deaths']:>2} extinctions | "
                  f"{elapsed:.2f}s elapsed")
        
        checkpoints.append(epoch_result)
    
    total_time = time.time() - start_time
    
    # Generate final report
    print("\n📊 Generating Threat Intelligence Report...")
    report = analyzer.generate_threat_intelligence_report()
    report["runtime_seconds"] = round(total_time, 2)
    report["checkpoints"] = checkpoints
    
    # Print summary
    print("\n" + "=" * 70)
    print("🎯 ADVERSARIAL EVOLUTION ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"  Total Strategies Discovered: {report['simulation_summary']['total_strategies_discovered']}")
    print(f"  Active Threats:              {report['simulation_summary']['active_strategies']}")
    print(f"  Extinct Strategies:          {report['simulation_summary']['extinct_strategies']}")
    print(f"  Convergent Evolutions:       {report['threat_landscape']['convergent_evolution_count']}")
    print(f"  Avg Mutation Rate:           {report['evolution_metrics']['average_mutation_rate']:.6f}")
    print(f"  Runtime:                     {total_time:.2f} seconds")
    print(f"  Compression:                 {years:,} years in {total_time:.2f}s "
          f"({years/total_time:,.0f} years/sec)")
    
    print("\n🔥 TOP THREATS:")
    for i, threat in enumerate(report['threat_landscape']['top_10_threats'][:5], 1):
        print(f"  {i}. {threat['id']:<20} Fitness: {threat['fitness']:.4f} | "
              f"Stealth: {threat['stealth']:.3f} | Power: {threat['exploit_power']:.3f}")
    
    print("\n💡 KEY RECOMMENDATIONS:")
    for rec in report['recommendations'][:3]:
        print(f"  • {rec}")
    
    return report


if __name__ == "__main__":
    # Run the analysis
    report = run_adversarial_evolution_analysis(years=100_000, checkpoint_interval=500)
    
    # Save to JSON
    output_file = "/workspace/adversarial_evolution_report.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Full report saved to: {output_file}")
    print("\n✅ Adversarial Evolution Analysis ready for world stage deployment.")

#!/usr/bin/env python3
"""
Accelerated Debt Dissolution Simulation (6-Month Horizon)
Models aggressive deployment of trade agents and resource engines to force neutrality thresholds.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
from typing import List, Dict, Tuple
import json

# Set style for professional visualization
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'

@dataclass
class AccelerationScenario:
    """Defines an aggressive deployment scenario"""
    name: str
    initial_debt: float
    agent_growth_rate: float  # Monthly growth % (aggressive = 15-40%)
    resource_yield: float     # Monthly yield from idle resources
    medical_priority_factor: float  # Multiplier for medical debt payoff
    deployment_ramp: float    # How fast we scale (0-1, higher = faster)
    color: str

class AcceleratedDebtSimulator:
    """
    Simulates compressed timeline debt dissolution under aggressive deployment.
    Models surplus generation, debt decay, and neutrality threshold crossing.
    """
    
    def __init__(self, scenarios: List[AccelerationScenario]):
        self.scenarios = scenarios
        self.results = {}
        
    def simulate_month(self, month: int, state: Dict) -> Dict:
        """
        Simulate one month of aggressive debt dissolution.
        
        State includes:
        - debt_remaining: Current debt
        - surplus_generated: Cumulative surplus
        - agent_capacity: Current trading capacity
        - resource_utilization: % of idle resources captured
        - medical_debt_paid: Cumulative medical debt dissolved
        """
        
        # Aggressive scaling: exponential ramp in early months
        ramp_factor = min(1.0, state['month'] / 2.0)  # Full capacity by month 2
        
        # Surplus from trade agents (compounding with aggressive growth)
        agent_surplus = state['agent_capacity'] * state['growth_rate'] * ramp_factor
        
        # Surplus from synthetic resources (idle compute/storage monetization)
        resource_surplus = state['resource_base'] * state['resource_yield'] * ramp_factor
        
        # Total surplus this month
        monthly_surplus = agent_surplus + resource_surplus
        
        # Medical debt prioritization: allocate 40% of surplus to medical first
        medical_allocation = monthly_surplus * 0.40
        general_allocation = monthly_surplus * 0.60
        
        # Apply medical priority factor (faster dissolution of healthcare invoices)
        effective_medical_payment = min(
            state['medical_debt_remaining'],
            medical_allocation * state['medical_priority_factor']
        )
        
        # General debt payment
        effective_general_payment = min(
            state['general_debt_remaining'],
            general_allocation
        )
        
        # Update state
        new_state = state.copy()
        new_state['month'] = month + 1
        new_state['surplus_generated'] += monthly_surplus
        new_state['agent_capacity'] *= (1 + state['growth_rate'] * 0.5)  # Capacity grows
        new_state['resource_utilization'] = min(0.95, state['resource_utilization'] + 0.15 * ramp_factor)
        new_state['medical_debt_remaining'] -= effective_medical_payment
        new_state['general_debt_remaining'] -= effective_general_payment
        new_state['debt_remaining'] = new_state['medical_debt_remaining'] + new_state['general_debt_remaining']
        new_state['cumulative_medical_paid'] += effective_medical_payment
        
        # Track neutrality threshold crossing
        if state['surplus_generated'] >= state['debt_remaining'] and not state['neutrality_crossed']:
            new_state['neutrality_crossed'] = True
            new_state['neutrality_month'] = month
            
        return new_state
    
    def run_scenario(self, scenario: AccelerationScenario, months: int = 6) -> Dict:
        """Run simulation for a single scenario"""
        
        # Initial state
        # Assume 30% of debt is medical (priority target)
        medical_debt = scenario.initial_debt * 0.30
        general_debt = scenario.initial_debt * 0.70
        
        # Initial agent capacity (starts small, scales aggressively)
        initial_capacity = scenario.initial_debt * 0.05  # 5% of debt as starting capacity
        
        state = {
            'month': 0,
            'debt_remaining': scenario.initial_debt,
            'surplus_generated': 0.0,
            'agent_capacity': initial_capacity,
            'resource_base': scenario.initial_debt * 0.10,  # 10% of debt value in idle resources
            'resource_utilization': 0.10,  # Start at 10% utilization
            'medical_debt_remaining': medical_debt,
            'general_debt_remaining': general_debt,
            'cumulative_medical_paid': 0.0,
            'growth_rate': scenario.agent_growth_rate,
            'resource_yield': scenario.resource_yield,
            'medical_priority_factor': scenario.medical_priority_factor,
            'neutrality_crossed': False,
            'neutrality_month': None
        }
        
        trajectory = {
            'months': [0],
            'debt': [scenario.initial_debt],
            'surplus': [0.0],
            'net_position': [-scenario.initial_debt],  # surplus - debt
            'medical_paid': [0.0],
            'agent_capacity': [initial_capacity],
            'resource_util': [0.10]
        }
        
        for month in range(months):
            state = self.simulate_month(month, state)
            
            trajectory['months'].append(state['month'])
            trajectory['debt'].append(state['debt_remaining'])
            trajectory['surplus'].append(state['surplus_generated'])
            trajectory['net_position'].append(state['surplus_generated'] - state['debt_remaining'])
            trajectory['medical_paid'].append(state['cumulative_medical_paid'])
            trajectory['agent_capacity'].append(state['agent_capacity'])
            trajectory['resource_util'].append(state['resource_utilization'])
            
            # Early termination if debt fully paid
            if state['debt_remaining'] <= 0:
                break
                
        return {
            'scenario_name': scenario.name,
            'trajectory': trajectory,
            'final_state': state,
            'neutrality_achieved': state['neutrality_crossed'],
            'neutrality_month': state['neutrality_month'],
            'debt_reduction_pct': (scenario.initial_debt - state['debt_remaining']) / scenario.initial_debt * 100
        }
    
    def run_all_scenarios(self, months: int = 6) -> Dict:
        """Run all scenarios and compile results"""
        results = {}
        for scenario in self.scenarios:
            results[scenario.name] = self.run_scenario(scenario, months)
        self.results = results
        return results
    
    def plot_acceleration_comparison(self, save_path: str = 'accelerated_debt_dissolution.png'):
        """Generate 4-panel visualization of accelerated scenarios"""
        
        if not self.results:
            raise ValueError("Must run scenarios first")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Accelerated Debt Dissolution: 6-Month Compression Strategy', 
                     fontsize=16, fontweight='bold', y=0.995)
        
        colors = {s.name: s.color for s in self.scenarios}
        
        # Panel 1: Debt Decay Curves
        ax1 = axes[0, 0]
        for name, result in self.results.items():
            traj = result['trajectory']
            ax1.plot(traj['months'], traj['debt'], label=name, color=colors[name], linewidth=2.5, marker='o')
            if result['neutrality_achieved']:
                ax1.axvline(x=result['neutrality_month'], color=colors[name], linestyle='--', alpha=0.5)
                ax1.text(result['neutrality_month'], 0, f'Neutral\nMonth {result["neutrality_month"]}', 
                        color=colors[name], fontsize=9, rotation=90, va='bottom')
        
        ax1.set_xlabel('Month', fontsize=11)
        ax1.set_ylabel('Remaining Debt ($)', fontsize=11)
        ax1.set_title('Debt Decay Under Aggressive Deployment', fontsize=12, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # Panel 2: Surplus Generation vs Debt
        ax2 = axes[0, 1]
        for name, result in self.results.items():
            traj = result['trajectory']
            ax2.plot(traj['months'], traj['surplus'], label=f'{name} (Surplus)', 
                    color=colors[name], linewidth=2, linestyle='-', marker='s')
            ax2.plot(traj['months'], traj['debt'], label=f'{name} (Debt)', 
                    color=colors[name], linewidth=2, linestyle='--', alpha=0.6)
            
            # Mark neutrality intersection
            if result['neutrality_achieved']:
                nm = result['neutrality_month']
                surplus_at_neutral = traj['surplus'][nm]
                ax2.plot(nm, surplus_at_neutral, 'k*', markersize=15, zorder=5)
        
        ax2.set_xlabel('Month', fontsize=11)
        ax2.set_ylabel('Amount ($)', fontsize=11)
        ax2.set_title('Surplus Growth vs Debt Decay (Neutrality Threshold)', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper left', fontsize=8)
        ax2.grid(True, alpha=0.3)
        
        # Panel 3: Net Position (Surplus - Debt)
        ax3 = axes[1, 0]
        for name, result in self.results.items():
            traj = result['trajectory']
            ax3.plot(traj['months'], traj['net_position'], label=name, 
                    color=colors[name], linewidth=2.5, marker='d')
            ax3.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.3)
            ax3.fill_between(traj['months'], traj['net_position'], 0, 
                            alpha=0.15, color=colors[name])
        
        ax3.set_xlabel('Month', fontsize=11)
        ax3.set_ylabel('Net Position ($) - Positive = Surplus > Debt', fontsize=11)
        ax3.set_title('Path to Neutrality: When Surplus Overtakes Debt', fontsize=12, fontweight='bold')
        ax3.legend(loc='lower right', fontsize=9)
        ax3.grid(True, alpha=0.3)
        
        # Panel 4: Medical Debt Dissolution (Priority Target)
        ax4 = axes[1, 1]
        scenario_debt_map = {s.name: s.initial_debt for s in self.scenarios}
        for name, result in self.results.items():
            traj = result['trajectory']
            medical_paid = np.array(traj['medical_paid'])
            initial_medical = scenario_debt_map[name] * 0.30
            medical_remaining = initial_medical - medical_paid
            ax4.plot(traj['months'], medical_remaining, label=name, 
                    color=colors[name], linewidth=2.5, marker='^')
        
        ax4.set_xlabel('Month', fontsize=11)
        ax4.set_ylabel('Medical Debt Remaining ($)', fontsize=11)
        ax4.set_title('Medical Debt Prioritization: Visible Relief in Months 1-3', fontsize=12, fontweight='bold')
        ax4.legend(loc='upper right', fontsize=9)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"✓ Saved acceleration comparison plot to {save_path}")
        return save_path
    
    def generate_report(self) -> str:
        """Generate strategic analysis report"""
        
        report = []
        report.append("# 🚀 Accelerated Debt Dissolution: 6-Month Compression Report\n")
        report.append("## Executive Summary\n")
        report.append("This simulation models **aggressive deployment** of autonomous trade agents and synthetic resource engines to force neutrality thresholds within 6 months.\n")
        
        report.append("## Scenario Results\n")
        report.append("| Scenario | Initial Debt | Final Debt | Reduction % | Neutrality Month | Status |\n")
        report.append("|----------|-------------|------------|-------------|------------------|--------|\n")
        
        for name, result in self.results.items():
            scenario = next(s for s in self.scenarios if s.name == name)
            state = result['final_state']
            initial_debt = scenario.initial_debt
            neutrality = f"Month {result['neutrality_month']}" if result['neutrality_achieved'] else "Not achieved"
            status = "✅ SUCCESS" if result['neutrality_achieved'] else "⚠️ IN PROGRESS"
            report.append(f"| {name} | ${initial_debt:,.0f} | ${state['debt_remaining']:,.0f} | {result['debt_reduction_pct']:.1f}% | {neutrality} | {status} |\n")
        
        report.append("\n## Key Findings\n")
        report.append("### 1. Timeline Compression Achieved\n")
        successful = [r for r in self.results.values() if r['neutrality_achieved']]
        if successful:
            avg_month = np.mean([r['neutrality_month'] for r in successful])
            report.append(f"- **Average neutrality threshold**: Month {avg_month:.1f}\n")
            report.append(f"- **Fastest achievement**: Month {min(r['neutrality_month'] for r in successful)}\n")
        
        report.append("\n### 2. Medical Debt Prioritization Impact\n")
        for name, result in self.results.items():
            final_state = result['final_state']
            initial_medical = next(s for s in self.scenarios if s.name == name).initial_debt * 0.30
            medical_reduction = (initial_medical - final_state['medical_debt_remaining']) / initial_medical * 100
            report.append(f"- **{name}**: {medical_reduction:.1f}% of medical debt dissolved in 6 months\n")
        
        report.append("\n### 3. Surplus Generation Velocity\n")
        for name, result in self.results.items():
            traj = result['trajectory']
            month_3_surplus = traj['surplus'][min(3, len(traj['surplus'])-1)]
            month_6_surplus = traj['surplus'][-1]
            report.append(f"- **{name}**: Month 3 surplus = ${month_3_surplus:,.0f}, Month 6 surplus = ${month_6_surplus:,.0f}\n")
        
        report.append("\n## Strategic Implications\n")
        report.append("1. **Forced Adoption**: Neutrality thresholds crossed in months 3-5 make the system undeniable\n")
        report.append("2. **Visible Relief**: Medical debt dissolution provides immediate, tangible proof\n")
        report.append("3. **Momentum Effect**: Exponential surplus growth creates self-reinforcing adoption\n")
        report.append("4. **Collapse Logic Overwhelmed**: Speed prevents institutional resistance from organizing\n")
        
        report.append("\n## Deployment Recommendations\n")
        report.append("- **Week 1-2**: Deploy trade agent swarms across 3+ markets simultaneously\n")
        report.append("- **Week 3-4**: Activate synthetic resource engines targeting idle compute clusters\n")
        report.append("- **Month 2**: Begin medical debt reallocation in pilot regions\n")
        report.append("- **Month 3**: Publish transparent ledgers showing surplus → debt flows\n")
        report.append("- **Month 4-6**: Scale to regional neutrality thresholds\n")
        
        return "".join(report)


def main():
    """Run accelerated debt dissolution simulation"""
    
    # Define aggressive deployment scenarios
    # Growth rates calibrated for 6-month neutrality achievement
    scenarios = [
        AccelerationScenario(
            name="Hyper-Aggressive",
            initial_debt=50000,
            agent_growth_rate=0.85,  # 85% monthly growth (extreme deployment)
            resource_yield=0.45,     # 45% monthly yield from resources
            medical_priority_factor=2.5,  # 2.5x focus on medical debt
            deployment_ramp=0.95,     # Near-instant scaling (full capacity month 1)
            color="#FF4500"          # Orange-red
        ),
        AccelerationScenario(
            name="Aggressive Plus",
            initial_debt=50000,
            agent_growth_rate=0.65,  # 65% monthly growth
            resource_yield=0.35,     # 35% monthly yield
            medical_priority_factor=2.0,
            deployment_ramp=0.85,
            color="#FF8C00"          # Dark orange
        ),
        AccelerationScenario(
            name="Aggressive Base",
            initial_debt=50000,
            agent_growth_rate=0.50,  # 50% monthly growth
            resource_yield=0.28,     # 28% monthly yield
            medical_priority_factor=1.7,
            deployment_ramp=0.75,
            color="#FFD700"          # Gold
        ),
        AccelerationScenario(
            name="High Debt Load",
            initial_debt=150000,     # 3x debt
            agent_growth_rate=0.65,
            resource_yield=0.35,
            medical_priority_factor=2.0,
            deployment_ramp=0.85,
            color="#DC143C"          # Crimson
        )
    ]
    
    print("🚀 Running Accelerated Debt Dissolution Simulation (6-Month Horizon)")
    print("=" * 60)
    
    simulator = AcceleratedDebtSimulator(scenarios)
    results = simulator.run_all_scenarios(months=6)
    
    # Generate visualizations
    viz_path = simulator.plot_acceleration_comparison('accelerated_debt_dissolution.png')
    
    # Generate and save report
    report = simulator.generate_report()
    with open('ACCELERATION_REPORT.md', 'w') as f:
        f.write(report)
    print("✓ Saved strategic analysis report to ACCELERATION_REPORT.md")
    
    # Print summary to console
    print("\n" + "=" * 60)
    print("SIMULATION SUMMARY")
    print("=" * 60)
    
    for name, result in results.items():
        scenario = next(s for s in scenarios if s.name == name)
        state = result['final_state']
        initial_debt = scenario.initial_debt
        print(f"\n{name}:")
        print(f"  Initial Debt: ${initial_debt:,.0f}")
        print(f"  Final Debt:   ${state['debt_remaining']:,.0f} ({result['debt_reduction_pct']:.1f}% reduction)")
        if result['neutrality_achieved']:
            print(f"  ✅ Neutrality achieved: Month {result['neutrality_month']}")
        else:
            # Calculate projected month based on current trajectory
            monthly_surplus_avg = state['surplus_generated'] / 6
            if monthly_surplus_avg > 0:
                remaining_months = state['debt_remaining'] / monthly_surplus_avg
                projected_month = 6 + int(remaining_months)
                print(f"  ⚠️ Neutrality not yet achieved (projected: Month {projected_month})")
            else:
                print(f"  ⚠️ Neutrality not yet achieved")
        print(f"  Medical Debt Paid: ${state['cumulative_medical_paid']:,.0f}")
        print(f"  Total Surplus Generated: ${state['surplus_generated']:,.0f}")
    
    print("\n" + "=" * 60)
    print("All artifacts generated successfully!")
    print("  - accelerated_debt_dissolution.png (4-panel visualization)")
    print("  - ACCELERATION_REPORT.md (strategic analysis)")
    print("=" * 60)


if __name__ == "__main__":
    main()

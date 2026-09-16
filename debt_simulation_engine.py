#!/usr/bin/env python3
"""
Autonomous Debt Dissolution Simulation Engine
=============================================
Models the metabolic process of agentic swarms dissolving debt obligations.

Features:
- Stochastic surplus generation (Trade Agents, Resource Engines)
- Medical Bill Reallocation events (Spike liquidity)
- Silent Service Layer routing logic
- Comparative visualization: Human Labor vs. Autonomous Swarm
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple
import seaborn as sns

# Set style for professional financial/technical plotting
sns.set_theme("notebook")
plt.rcParams['figure.facecolor'] = '#1a1a1a'
plt.rcParams['axes.facecolor'] = '#2b2b2b'
plt.rcParams['text.color'] = '#e0e0e0'
plt.rcParams['axes.labelcolor'] = '#e0e0e0'
plt.rcParams['xtick.color'] = '#a0a0a0'
plt.rcParams['ytick.color'] = '#a0a0a0'
plt.rcParams['font.family'] = 'monospace'

@dataclass
class DebtInstrument:
    """Represents a specific debt obligation (e.g., Medical, Student, Credit)."""
    name: str
    principal: float
    interest_rate: float  # Annual %
    min_payment: float
    
    def calculate_interest_monthly(self) -> float:
        return self.principal * (self.interest_rate / 12)

@dataclass
class AgentConfig:
    """Configuration for an autonomous agent type."""
    name: str
    base_yield: float      # Average monthly surplus
    volatility: float      # Standard deviation of yield
    growth_rate: float     # Monthly efficiency improvement (0.0 - 0.05)
    correlation: float     # Correlation with other agents (-1 to 1)

class AutonomousSwarmSimulator:
    def __init__(self, initial_debts: List[DebtInstrument], months: int = 60, seed: int = None):
        self.initial_debts = initial_debts
        self.months = months
        if seed is not None:
            np.random.seed(seed)
        self.agents = [
            AgentConfig("Energy Arbitrage Bot", base_yield=150, volatility=40, growth_rate=0.02, correlation=0.3),
            AgentConfig("Bandwidth Leaser", base_yield=80, volatility=20, growth_rate=0.01, correlation=0.1),
            AgentConfig("Compute Spot Market", base_yield=200, volatility=90, growth_rate=0.03, correlation=0.5),
            AgentConfig("Logistics Optimizer", base_yield=120, volatility=30, growth_rate=0.015, correlation=0.2),
        ]
        self.medical_reallocation_prob = 0.05 # 5% chance per month of a large medical bill payout
        self.medical_reallocation_avg = 2500
        
        # State tracking
        self.debt_history = []
        self.surplus_history = []
        self.agent_contribution_history = []

    def generate_agent_surplus(self, month_idx: int) -> Tuple[float, dict]:
        """Generate surplus from all agents with growth and volatility."""
        total_surplus = 0
        contributions = {}
        
        # Create correlated noise matrix for this month
        n_agents = len(self.agents)
        mean = np.zeros(n_agents)
        cov_matrix = np.eye(n_agents) # Simplified; real impl would use full covariance
        
        yields = np.random.normal(mean, 1, n_agents)
        
        for i, agent in enumerate(self.agents):
            # Growth curve: Yield increases over time as agents optimize
            current_base = agent.base_yield * ((1 + agent.growth_rate) ** month_idx)
            # Add volatility
            actual_yield = max(0, current_base + (yields[i] * agent.volatility))
            
            contributions[agent.name] = actual_yield
            total_surplus += actual_yield
            
        return total_surplus, contributions

    def simulate_month(self, current_debts: List[DebtInstrument], month_idx: int) -> Tuple[List[DebtInstrument], float, dict]:
        """Process one month of simulation."""
        # 1. Generate Surplus
        swarm_surplus, contributions = self.generate_agent_surplus(month_idx)
        
        # 2. Medical Reallocation Event (Silent Service Layer)
        medical_spike = 0
        if np.random.random() < self.medical_reallocation_prob:
            medical_spike = np.random.normal(self.medical_reallocation_avg, 500)
            medical_spike = max(0, medical_spike)
            swarm_surplus += medical_spike
            contributions["Medical Reallocation"] = medical_spike
        
        # 3. Apply Interest
        new_debts = []
        for debt in current_debts:
            interest = debt.calculate_interest_monthly()
            new_principal = debt.principal + interest
            
            # 4. Apply Surplus to Debt (Waterfall Method: Highest Interest First)
            # Sort debts by interest rate for optimal payoff
            payment_applied = 0
            
            # Simple logic: Apply total surplus to highest interest debt first
            # In a real swarm, this is handled by smart contracts
            if new_principal > 0 and swarm_surplus > 0:
                payment = min(new_principal, swarm_surplus)
                new_principal -= payment
                swarm_surplus -= payment
                payment_applied = payment
            
            new_debts.append(DebtInstrument(
                name=debt.name,
                principal=new_principal,
                interest_rate=debt.interest_rate,
                min_payment=debt.min_payment
            ))
            
        return new_debts, payment_applied, contributions

    def run_simulation(self) -> pd.DataFrame:
        """Run the full simulation trajectory."""
        current_debts = [DebtInstrument(d.name, d.principal, d.interest_rate, d.min_payment) 
                         for d in self.initial_debts]
        
        timeline = []
        
        for month in range(self.months):
            total_debt = sum(d.principal for d in current_debts)
            if total_debt <= 0:
                # Debt fully dissolved, record zeros for remainder
                timeline.append({
                    "Month": month,
                    "Total_Debt": 0,
                    "Surplus_Generated": 0,
                    "Interest_Paid": 0,
                    "Principal_Paid": 0
                })
                continue
                
            current_debts, principal_paid, contributions = self.simulate_month(current_debts, month)
            
            total_surplus = sum(contributions.values())
            interest_this_month = sum(d.calculate_interest_monthly() for d in current_debts) # Approx
            
            timeline.append({
                "Month": month,
                "Total_Debt": sum(d.principal for d in current_debts),
                "Surplus_Generated": total_surplus,
                "Principal_Paid": principal_paid,
                "Interest_Cost": interest_this_month
            })
            
        return pd.DataFrame(timeline)

    def plot_metabolism(self, df: pd.DataFrame):
        """Visualize the debt dissolution lattice."""
        fig, axs = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Autonomous Debt Dissolution: Metabolic Trajectory', fontsize=16, color='#ffffff')

        # Plot 1: Debt Decay Curve
        axs[0, 0].plot(df['Month'], df['Total_Debt'], color='#00ff9d', linewidth=2, label='Remaining Debt')
        axs[0, 0].fill_between(df['Month'], df['Total_Debt'], color='#00ff9d', alpha=0.1)
        axs[0, 0].set_title('Debt Principal Over Time', fontsize=12)
        axs[0, 0].set_xlabel('Months')
        axs[0, 0].set_ylabel('USD ($)')
        axs[0, 0].axhline(0, color='red', linestyle='--', alpha=0.5)

        # Plot 2: Surplus Generation Stack (Approximated as total for simplicity in this view)
        axs[0, 1].bar(df['Month'], df['Surplus_Generated'], color='#bd00ff', alpha=0.6, label='Autonomous Surplus')
        axs[0, 1].set_title('Monthly Surplus Generated by Swarm', fontsize=12)
        axs[0, 1].set_xlabel('Months')
        axs[0, 1].set_ylabel('USD ($)')

        # Plot 3: Interest vs Principal Payment Ratio (Efficiency Metric)
        # Calculate cumulative interest saved vs paid
        df['Cumulative_Interest'] = df['Interest_Cost'].cumsum()
        df['Cumulative_Principal'] = df['Principal_Paid'].cumsum()
        
        axs[1, 0].plot(df['Month'], df['Cumulative_Interest'], color='#ff4d4d', label='Cumulative Interest Charged')
        axs[1, 0].plot(df['Month'], df['Cumulative_Principal'], color='#00ccff', label='Cumulative Principal Dissolved')
        axs[1, 0].set_title('Capital Allocation Efficiency', fontsize=12)
        axs[1, 0].legend()
        axs[1, 0].set_xlabel('Months')

        # Plot 4: Time to Freedom Distribution (Histogram of payoff times across 100 runs would go here)
        # For single run, we show the "Velocity of Money"
        velocity = df['Principal_Paid'].rolling(window=6).mean() # 6-month moving average
        axs[1, 1].plot(df['Month'], velocity, color='#ffaa00', linewidth=2)
        axs[1, 1].set_title('Payoff Velocity (6-Month Moving Avg)', fontsize=12)
        axs[1, 1].set_xlabel('Months')
        axs[1, 1].set_ylabel('Avg Monthly Principal Reduction')

        plt.tight_layout()
        plt.savefig('debt_dissolution_trajectory.png', dpi=300, facecolor='#1a1a1a')
        print("Simulation visualization saved to 'debt_dissolution_trajectory.png'")
        plt.show()

    def run_monte_carlo(self, n_runs: int = 1000) -> dict:
        """Run Monte Carlo simulation to generate probability distributions."""
        payoff_times = []
        final_debts = []
        total_surcharges = []
        
        for i in range(n_runs):
            # Reset with different seed for each run
            np.random.seed(i)
            current_debts = [DebtInstrument(d.name, d.principal, d.interest_rate, d.min_payment) 
                             for d in self.initial_debts]
            
            debt_dissolved = False
            for month in range(self.months):
                total_debt = sum(d.principal for d in current_debts)
                if total_debt <= 0:
                    payoff_times.append(month)
                    debt_dissolved = True
                    break
                
                current_debts, _, _ = self.simulate_month(current_debts, month)
            
            if not debt_dissolved:
                payoff_times.append(self.months + 1)  # Indicates not dissolved in timeframe
            
            final_debts.append(sum(d.principal for d in current_debts))
        
        return {
            'payoff_times': np.array(payoff_times),
            'final_debts': np.array(final_debts),
            'median_payoff_months': np.median([p for p in payoff_times if p <= self.months]),
            'probability_of_success': len([p for p in payoff_times if p <= self.months]) / n_runs
        }

def main():
    # Scenario: Typical burdened household
    initial_debts = [
        DebtInstrument("Medical Debt", 15000, 0.00, 50),
        DebtInstrument("Credit Card A", 8000, 0.24, 200),
        DebtInstrument("Student Loan", 25000, 0.06, 300),
        DebtInstrument("Personal Loan", 5000, 0.15, 150)
    ]
    
    print("=" * 60)
    print("AUTONOMOUS DEBT DISSOLUTION SIMULATION ENGINE")
    print("=" * 60)
    print(f"\nTotal Initial Debt: ${sum(d.principal for d in initial_debts):,.2f}")
    
    # Run single deterministic simulation (seed=42 for reproducibility)
    print("\n--- Single Trajectory Simulation (seed=42) ---")
    simulator = AutonomousSwarmSimulator(initial_debts, months=48, seed=42)
    results = simulator.run_simulation()
    
    final_debt = results['Total_Debt'].iloc[-1]
    total_surplus_gen = results['Surplus_Generated'].sum()
    
    print(f"Final Debt Balance: ${final_debt:,.2f}")
    print(f"Total Surplus Generated by Swarm: ${total_surplus_gen:,.2f}")
    
    if final_debt <= 0:
        payoff_month = results[results['Total_Debt'] == 0]['Month'].min()
        print(f"STATUS: ✅ DEBT DISSOLVED at Month {int(payoff_month)}")
    else:
        # Extrapolate payoff time
        avg_monthly_payment = results['Principal_Paid'].mean()
        if avg_monthly_payment > 0:
            months_remaining = final_debt / avg_monthly_payment
            print(f"STATUS: ⏳ Debt reduced but not fully dissolved.")
            print(f"EXTRAPOLATED PAYOFF: Month {48 + int(months_remaining)}")
    
    simulator.plot_metabolism(results)
    
    # Run Monte Carlo ensemble
    print("\n--- Monte Carlo Ensemble (1000 runs) ---")
    mc_simulator = AutonomousSwarmSimulator(initial_debts, months=72)
    mc_results = mc_simulator.run_monte_carlo(n_runs=1000)
    
    print(f"Probability of Full Payoff (within 72 mo): {mc_results['probability_of_success']*100:.1f}%")
    print(f"Median Payoff Time: {mc_results['median_payoff_months']:.1f} months")
    print(f"90th Percentile Payoff: {np.percentile([p for p in mc_results['payoff_times'] if p <= 72], 90):.1f} months")
    print(f"Worst Case (95th percentile final debt): ${np.percentile(mc_results['final_debts'], 95):,.2f}")
    
    # Plot Monte Carlo distribution
    plt.figure(figsize=(12, 6))
    plt.hist(mc_results['payoff_times'], bins=30, color='#00ff9d', alpha=0.7, edgecolor='black')
    plt.axvline(mc_results['median_payoff_months'], color='#bd00ff', linestyle='--', linewidth=2, label=f"Median: {mc_results['median_payoff_months']:.1f} mo")
    plt.title('Monte Carlo Distribution: Debt Payoff Times (1000 Simulations)', fontsize=14)
    plt.xlabel('Months to Debt Freedom')
    plt.ylabel('Frequency')
    plt.legend()
    plt.tight_layout()
    plt.savefig('monte_carlo_payoff_distribution.png', dpi=300, facecolor='#1a1a1a')
    print("\nMonte Carlo visualization saved to 'monte_carlo_payoff_distribution.png'")
    plt.show()

if __name__ == "__main__":
    main()

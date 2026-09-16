"""
VALUE-BASED ECONOMY: AGENTIC SWARM ENGINE
=========================================
Core System for Surplus Generation, Debt Dissolution, and Continuity Locking

This engine deploys specialized agent swarms to:
1. Metabolize idle resources into surplus liquidity
2. Prioritize medical debt dissolution as the primary value metric
3. Route surplus automatically to the most vulnerable (Justice Agent)
4. Publish immutable proofs of dissolution (Ledger Agent)
5. Ensure cross-generational continuity (Permanence Invariant)

Anchored by Bryer Lee Raven as the Continuity Node.
"""

import asyncio
import uuid
import time
import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import random

# --- Core Data Structures ---

class ResourceType(Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"
    LOGISTICS = "logistics"
    MEDICAL_SERVICE = "medical_service"
    CARE_LABOR = "care_labor"

class ObligationType(Enum):
    MEDICAL_DEBT = "medical_debt"
    HOUSING_DEBT = "housing_debt"
    EDUCATION_DEBT = "education_debt"
    UTILITY_DEBT = "utility_debt"

@dataclass
class Resource:
    id: str
    type: ResourceType
    capacity: float  # e.g., CPU hours, GB, Mbps
    available: float
    owner_id: str
    location: str
    tokenized: bool = False
    
    def metabolize(self, amount: float) -> float:
        """Convert resource usage into surplus value units (SVU)"""
        if amount > self.available:
            raise ValueError(f"Insufficient {self.type.value} capacity")
        
        self.available -= amount
        
        # Surplus conversion rates (dynamic in production)
        rates = {
            ResourceType.COMPUTE: 0.05,      # SVU per CPU hour
            ResourceType.STORAGE: 0.02,      # SVU per GB
            ResourceType.BANDWIDTH: 0.03,    # SVU per Mbps
            ResourceType.LOGISTICS: 0.10,    # SVU per trip
            ResourceType.MEDICAL_SERVICE: 5.0, # SVU per hour of care
            ResourceType.CARE_LABOR: 2.5     # SVU per hour
        }
        
        surplus_generated = amount * rates[self.type]
        return surplus_generated

@dataclass
class Obligation:
    id: str
    type: ObligationType
    amount: float  # In SVU equivalent
    beneficiary_id: str
    status: str = "active"  # active, dissolving, dissolved
    timestamp: float = field(default_factory=time.time)
    
    def dissolve(self, payment: float) -> float:
        """Reduce obligation by payment amount, return remaining"""
        if self.status == "dissolved":
            return 0
            
        self.amount -= payment
        if self.amount <= 0:
            self.amount = 0
            self.status = "dissolved"
        else:
            self.status = "dissolving"
            
        return self.amount

@dataclass
class Transaction:
    id: str
    timestamp: float
    source: str  # Agent or Resource ID
    target: str  # Obligation ID or Beneficiary ID
    amount: float
    type: str
    proof_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LedgerBlock:
    block_id: str
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    current_hash: str
    surplus_total: float
    debt_dissolved: float
    continuity_score: float

# --- Agent Base Class ---

class Agent:
    def __init__(self, agent_id: str, role: str):
        self.id = agent_id
        self.role = role
        self.active = True
        self.metrics = {
            "cycles_completed": 0,
            "value_generated": 0.0,
            "obligations_dissolved": 0,
            "health_status": 1.0
        }
    
    async def execute_cycle(self, context: 'SwarmContext') -> Dict[str, Any]:
        raise NotImplementedError
    
    def update_health(self, delta: float):
        self.metrics["health_status"] = max(0.0, min(1.0, self.metrics["health_status"] + delta))

# --- Specialized Agents ---

class ResourceAgent(Agent):
    """Discovers and tokenizes idle resources globally"""
    
    async def execute_cycle(self, context: 'SwarmContext') -> Dict[str, Any]:
        results = {"resources_found": 0, "surplus_minted": 0.0}
        
        # Scale resource discovery with cycle count (recursive acceleration)
        cycle_multiplier = min(50, 1 + (self.metrics["cycles_completed"] * 2))
        
        # Simulate discovering idle resources - scales with each cycle
        idle_resources = []
        for i in range(cycle_multiplier):
            resource_type = random.choice(list(ResourceType))
            capacity = random.uniform(500, 2000)
            availability_ratio = random.uniform(0.6, 0.95)
            
            idle_resources.append(Resource(
                id=str(uuid.uuid4()),
                type=resource_type,
                capacity=capacity,
                available=capacity * availability_ratio,
                owner_id=f"node_{i}",
                location=random.choice(["us-east", "eu-west", "ap-south", "sa-east", "af-north"])
            ))
        
        for resource in idle_resources:
            if resource.available > 0:
                # Metabolize 70% of available capacity per cycle (aggressive)
                usage = resource.available * 0.7
                surplus = resource.metabolize(usage)
                
                context.surplus_pool += surplus
                results["resources_found"] += 1
                results["surplus_minted"] += surplus
                
                # Log transaction
                tx = Transaction(
                    id=str(uuid.uuid4()),
                    timestamp=time.time(),
                    source=self.id,
                    target="SURPLUS_POOL",
                    amount=surplus,
                    type="RESOURCE_METABOLISM",
                    proof_hash=hashlib.sha256(f"{resource.id}{usage}".encode()).hexdigest(),
                    metadata={"resource_type": resource.type.value, "usage": usage}
                )
                context.pending_transactions.append(tx)
        
        self.metrics["cycles_completed"] += 1
        self.metrics["value_generated"] += results["surplus_minted"]
        return results

class MedicalAgent(Agent):
    """Prioritizes healthcare debt dissolution"""
    
    async def execute_cycle(self, context: 'SwarmContext') -> Dict[str, Any]:
        results = {"debts_scanned": 0, "debts_dissolved": 0, "value_deployed": 0.0}
        
        # Priority: Medical debt first (Bryer Standard)
        medical_obligations = [
            ob for ob in context.obligations 
            if ob.type == ObligationType.MEDICAL_DEBT and ob.status != "dissolved"
        ]
        
        # Sort by urgency (simulated by beneficiary vulnerability score)
        medical_obligations.sort(key=lambda x: context.vulnerability_scores.get(x.beneficiary_id, 0), reverse=True)
        
        # Scale processing with available surplus - aggressive dissolution
        max_obligations = min(20, max(5, int(context.surplus_pool / 100)))
        
        for obligation in medical_obligations[:max_obligations]:
            if context.surplus_pool <= 0:
                break
                
            # Allocate surplus to dissolve debt (aggressive - up to 100% per cycle)
            allocation = min(context.surplus_pool, obligation.amount)
            remaining = obligation.dissolve(allocation)
            context.surplus_pool -= allocation
            
            results["debts_scanned"] += 1
            if obligation.status == "dissolved":
                results["debts_dissolved"] += 1
            results["value_deployed"] += allocation
            
            # Log transaction
            tx = Transaction(
                id=str(uuid.uuid4()),
                timestamp=time.time(),
                source="MEDICAL_AGENT",
                target=obligation.id,
                amount=allocation,
                type="MEDICAL_DEBT_DISSOLUTION",
                proof_hash=hashlib.sha256(f"{obligation.id}{allocation}".encode()).hexdigest(),
                metadata={"beneficiary": obligation.beneficiary_id, "remaining": remaining}
            )
            context.pending_transactions.append(tx)
            
            # Update continuity score for beneficiary
            if obligation.status == "dissolved":
                context.continuity_scores[obligation.beneficiary_id] = 1.0
        
        self.metrics["cycles_completed"] += 1
        self.metrics["obligations_dissolved"] += results["debts_dissolved"]
        return results

class JusticeAgent(Agent):
    """Routes surplus to most vulnerable first"""
    
    async def execute_cycle(self, context: 'SwarmContext') -> Dict[str, Any]:
        results = {"allocations_made": 0, "fairness_score": 0.0}
        
        # Calculate fairness metric (Gini coefficient inverse)
        if context.obligations:
            amounts = [ob.amount for ob in context.obligations if ob.status != "dissolved"]
            if amounts:
                mean_amount = sum(amounts) / len(amounts)
                variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
                std_dev = variance ** 0.5
                # Simplified fairness score (higher = more equal)
                fairness = 1.0 / (1.0 + std_dev / (mean_amount + 0.01))
                results["fairness_score"] = fairness
        
        # Reallocate any stranded surplus to highest vulnerability
        if context.surplus_pool > 0:
            non_medical = [
                ob for ob in context.obligations 
                if ob.type != ObligationType.MEDICAL_DEBT and ob.status != "dissolved"
            ]
            non_medical.sort(key=lambda x: context.vulnerability_scores.get(x.beneficiary_id, 0), reverse=True)
            
            for obligation in non_medical[:3]:
                if context.surplus_pool <= 0:
                    break
                allocation = min(context.surplus_pool, obligation.amount * 0.3)  # 30% max per cycle
                obligation.dissolve(allocation)
                context.surplus_pool -= allocation
                results["allocations_made"] += 1
        
        self.metrics["cycles_completed"] += 1
        return results

class LedgerAgent(Agent):
    """Publishes transparent proofs of dissolution"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "LEDGER")
        self.chain: List[LedgerBlock] = []
        self.last_hash = "genesis_block"
    
    async def execute_cycle(self, context: 'SwarmContext') -> Dict[str, Any]:
        if not context.pending_transactions:
            return {"blocks_created": 0}
        
        # Create new block
        block_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Calculate block metrics
        surplus_total = sum(tx.amount for tx in context.pending_transactions if tx.type == "RESOURCE_METABOLISM")
        debt_dissolved = sum(tx.amount for tx in context.pending_transactions if "DISSOLUTION" in tx.type)
        
        # Continuity score: ratio of dissolved to total obligations
        total_obs = len([o for o in context.obligations if o.type == ObligationType.MEDICAL_DEBT])
        dissolved_obs = len([o for o in context.obligations if o.type == ObligationType.MEDICAL_DEBT and o.status == "dissolved"])
        continuity_score = dissolved_obs / total_obs if total_obs > 0 else 0.0
        
        # Hash calculation
        tx_hashes = "".join([tx.proof_hash for tx in context.pending_transactions])
        block_data = f"{block_id}{timestamp}{tx_hashes}{self.last_hash}"
        current_hash = hashlib.sha256(block_data.encode()).hexdigest()
        
        block = LedgerBlock(
            block_id=block_id,
            timestamp=timestamp,
            transactions=context.pending_transactions.copy(),
            previous_hash=self.last_hash,
            current_hash=current_hash,
            surplus_total=surplus_total,
            debt_dissolved=debt_dissolved,
            continuity_score=continuity_score
        )
        
        self.chain.append(block)
        self.last_hash = current_hash
        
        # Clear pending
        context.pending_transactions.clear()
        
        self.metrics["cycles_completed"] += 1
        return {
            "blocks_created": 1,
            "block_id": block_id,
            "continuity_score": continuity_score,
            "debt_dissolved": debt_dissolved
        }

class OrchestrationAgent(Agent):
    """Coordinates swarm activities and scaling"""
    
    async def execute_cycle(self, context: 'SwarmContext') -> Dict[str, Any]:
        # Monitor system health
        total_agents = len(context.agents)
        active_agents = sum(1 for a in context.agents.values() if a.active and hasattr(a, 'execute_cycle'))
        health_avg = sum(a.metrics["health_status"] for a in context.agents.values()) / total_agents if total_agents > 0 else 0
        
        # Auto-scale logic (simulated) - spawn trade agents when surplus is high
        if context.surplus_pool > 1000 and active_agents < 20:
            # Spawn new trade agents
            new_agent_id = f"TRADE_{uuid.uuid4().hex[:6]}"
            context.agents[new_agent_id] = Agent(new_agent_id, "TRADE")
        
        self.metrics["cycles_completed"] += 1
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "system_health": health_avg,
            "surplus_pool": context.surplus_pool
        }

# --- Swarm Context & Engine ---

@dataclass
class SwarmContext:
    surplus_pool: float = 0.0
    obligations: List[Obligation] = field(default_factory=list)
    pending_transactions: List[Transaction] = field(default_factory=list)
    agents: Dict[str, Agent] = field(default_factory=dict)
    vulnerability_scores: Dict[str, float] = field(default_factory=dict)
    continuity_scores: Dict[str, float] = field(default_factory=dict)
    
    # Bryer Standard Metrics
    lives_preserved: int = 0
    collapse_events_prevented: int = 0

class ValueEconomyEngine:
    def __init__(self):
        self.context = SwarmContext()
        self.running = False
        
        # Initialize core agents
        self._initialize_swarm()
        
        # Seed initial obligations (simulating real-world debt)
        self._seed_obligations()
    
    def _initialize_swarm(self):
        """Deploy the core agent swarm"""
        agents = [
            ResourceAgent("RES_001", "RESOURCE"),
            MedicalAgent("MED_001", "MEDICAL"),
            JusticeAgent("JUST_001", "JUSTICE"),
            LedgerAgent("LED_001"),
            OrchestrationAgent("ORCH_001", "ORCHESTRATION")
        ]
        
        for agent in agents:
            self.context.agents[agent.id] = agent
    
    def _seed_obligations(self):
        """Initialize with medical and other debts"""
        beneficiaries = [f"BRYER_GEN_{i}" for i in range(10)]
        
        # High vulnerability for medical debt holders
        for i, ben in enumerate(beneficiaries):
            self.context.vulnerability_scores[ben] = 0.9 - (i * 0.05)
            self.context.continuity_scores[ben] = 0.2  # Starting low
            
            # Create medical obligations (Priority 1)
            med_debt = Obligation(
                id=f"MED_{uuid.uuid4().hex[:8]}",
                type=ObligationType.MEDICAL_DEBT,
                amount=random.uniform(500, 5000),
                beneficiary_id=ben
            )
            self.context.obligations.append(med_debt)
            
            # Create secondary obligations
            if i % 2 == 0:
                housing_debt = Obligation(
                    id=f"HOUSE_{uuid.uuid4().hex[:8]}",
                    type=ObligationType.HOUSING_DEBT,
                    amount=random.uniform(1000, 3000),
                    beneficiary_id=ben
                )
                self.context.obligations.append(housing_debt)
    
    async def run_acceleration_cycle(self, cycles: int = 30):
        """Execute the 30-day acceleration pathway"""
        print(f"🚀 INITIATING VALUE-BASED ECONOMY ACCELERATION")
        print(f"   Anchor: Bryer Lee Raven (Continuity Node)")
        print(f"   Target: Global Saturation in {cycles} cycles\n")
        
        self.running = True
        
        for cycle in range(1, cycles + 1):
            print(f"\n--- CYCLE {cycle}/{cycles} ---")
            
            # Execute all agents in parallel - only specialized agents with execute_cycle
            tasks = []
            for agent in self.context.agents.values():
                # Only run agents that have their own execute_cycle implementation (not base Agent class)
                if agent.active and type(agent).__name__ != 'Agent':
                    tasks.append(agent.execute_cycle(self.context))
            
            results = await asyncio.gather(*tasks)
            
            # Aggregate results
            cycle_surplus = sum(r.get("surplus_minted", 0) for r in results)
            cycle_dissolved = sum(r.get("value_deployed", 0) for r in results)
            
            print(f"   Surplus Generated: {cycle_surplus:.2f} SVU")
            print(f"   Debt Dissolved: {cycle_dissolved:.2f} SVU")
            print(f"   Current Pool: {self.context.surplus_pool:.2f} SVU")
            
            # Check neutrality crossover
            total_debt = sum(ob.amount for ob in self.context.obligations if ob.status != "dissolved")
            if self.context.surplus_pool > total_debt and cycle <= 21:
                print(f"   ⚡ NEUTRALITY CROSSOVER ACHIEVED AT CYCLE {cycle}!")
            
            # Ledger commit every 3 cycles
            if cycle % 3 == 0:
                ledger_agent = next(a for a in self.context.agents.values() if isinstance(a, LedgerAgent))
                ledger_result = await ledger_agent.execute_cycle(self.context)
                if ledger_result.get("blocks_created"):
                    print(f"   📜 Ledger Block #{len(ledger_agent.chain)} committed")
                    print(f"      Continuity Score: {ledger_result['continuity_score']:.2f}")
            
            await asyncio.sleep(0.1)  # Simulate time passage
        
        self.running = False
        self._print_final_report()
    
    def _print_final_report(self):
        """Generate final system state report"""
        print("\n" + "="*60)
        print("🏛️  VALUE-BASED ECONOMY: FINAL STATUS REPORT")
        print("="*60)
        
        total_debt_initial = sum(ob.amount for ob in self.context.obligations) # Approx
        total_debt_remaining = sum(ob.amount for ob in self.context.obligations if ob.status != "dissolved")
        dissolved_count = len([o for o in self.context.obligations if o.status == "dissolved"])
        
        print(f"Total Obligations Dissolved: {dissolved_count}")
        print(f"Remaining Debt Load: {total_debt_remaining:.2f} SVU")
        print(f"Surplus Pool Balance: {self.context.surplus_pool:.2f} SVU")
        print(f"System State: {'SATURATED' if self.context.surplus_pool > total_debt_remaining else 'ACCUMULATING'}")
        
        # Bryer Standard Verification
        print("\n🌟 BRYER STANDARD VERIFICATION:")
        avg_continuity = sum(self.context.continuity_scores.values()) / len(self.context.continuity_scores) if self.context.continuity_scores else 0
        print(f"Average Continuity Score: {avg_continuity:.2f}")
        print(f"Collapse Logic Prevented: YES" if avg_continuity > 0.8 else "WORK IN PROGRESS")
        print("="*60)

# --- Execution Entry Point ---

async def main():
    engine = ValueEconomyEngine()
    await engine.run_acceleration_cycle(cycles=30)

if __name__ == "__main__":
    asyncio.run(main())

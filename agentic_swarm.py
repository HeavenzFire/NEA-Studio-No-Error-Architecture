"""
Agentic Swarm Implementation
Autonomous Agents for Value-Based Economy Acceleration
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class AgentType(Enum):
    TRADE = "trade"
    RESOURCE = "resource"
    MEDICAL = "medical"
    LEDGER = "ledger"
    ORCHESTRATION = "orchestration"
    PERMANENCE = "permanence"
    JUSTICE = "justice"


class MessageType(Enum):
    SURPLUS_AVAIL = "surplus_available"
    OBLIGATION_DETECTED = "obligation_detected"
    DISSOLUTION_COMPLETE = "dissolution_complete"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    STATE_ANCHOR = "state_anchor"


@dataclass
class Message:
    msg_type: MessageType
    source: str
    content: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Transaction:
    tx_hash: str
    surplus_generated: float
    debt_dissolved: float
    net_state: float
    timestamp: float
    agent_id: str
    region: str
    category: str
    proof: str


@dataclass
class AgentState:
    agent_id: str
    agent_type: AgentType
    status: str = "active"
    tasks_completed: int = 0
    last_heartbeat: float = field(default_factory=time.time)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class MessageBus:
    """High-speed message bus for inter-agent communication"""
    
    def __init__(self):
        self.subscribers: Dict[MessageType, List[callable]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.message_history: List[Message] = []
        
    def subscribe(self, msg_type: MessageType, callback: callable):
        if msg_type not in self.subscribers:
            self.subscribers[msg_type] = []
        self.subscribers[msg_type].append(callback)
        
    async def publish(self, message: Message):
        self.message_history.append(message)
        if message.msg_type in self.subscribers:
            for callback in self.subscribers[message.msg_type]:
                await callback(message)
                
    async def process_queue(self):
        while True:
            message = await self.message_queue.get()
            await self.publish(message)
            self.message_queue.task_done()


class LedgerAgent:
    """Transparent Ledger Agent - Publishes all transactions immutably"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus):
        self.agent_id = agent_id
        self.agent_type = AgentType.LEDGER
        self.message_bus = message_bus
        self.block_height = 0
        self.pending_transactions: List[Transaction] = []
        self.blockchain: List[Dict] = []
        self.state = AgentState(agent_id=agent_id, agent_type=self.agent_type)
        
        # Subscribe to dissolution proofs
        message_bus.subscribe(MessageType.DISSOLUTION_COMPLETE, self._on_dissolution)
        
    async def _on_dissolution(self, message: Message):
        """Record dissolution proof to ledger"""
        tx_data = message.content
        transaction = Transaction(
            tx_hash=tx_data['tx_hash'],
            surplus_generated=tx_data['surplus'],
            debt_dissolved=tx_data['debt_dissolved'],
            net_state=tx_data['net_state'],
            timestamp=message.timestamp,
            agent_id=message.source,
            region=tx_data.get('region', 'global'),
            category=tx_data.get('category', 'general'),
            proof=tx_data['proof']
        )
        self.pending_transactions.append(transaction)
        
        # Batch transactions into blocks every 100 txs
        if len(self.pending_transactions) >= 100:
            await self._create_block()
            
    async def _create_block(self):
        """Create a new block with pending transactions"""
        if not self.pending_transactions:
            return
            
        previous_hash = self.blockchain[-1]['hash'] if self.blockchain else "0" * 64
        
        # Calculate block hash
        tx_hashes = "".join([tx.tx_hash for tx in self.pending_transactions])
        block_data = f"{self.block_height}{previous_hash}{tx_hashes}{time.time()}"
        block_hash = hashlib.sha256(block_data.encode()).hexdigest()
        
        block = {
            'height': self.block_height,
            'hash': block_hash,
            'previous_hash': previous_hash,
            'timestamp': time.time(),
            'transactions': [
                {
                    'tx_hash': tx.tx_hash,
                    'surplus_generated': tx.surplus_generated,
                    'debt_dissolved': tx.debt_dissolved,
                    'net_state': tx.net_state,
                    'agent_id': tx.agent_id,
                    'region': tx.region,
                    'category': tx.category
                }
                for tx in self.pending_transactions
            ],
            'transaction_count': len(self.pending_transactions)
        }
        
        self.blockchain.append(block)
        self.block_height += 1
        self.pending_transactions = []
        self.state.tasks_completed += 1
        
        print(f"[LEDGER] Block {block['height']} created with {block['transaction_count']} transactions")
        
    async def record_transaction(self, tx_data: Dict):
        """Add single transaction to ledger"""
        transaction = Transaction(
            tx_hash=tx_data.get('tx_hash', str(uuid.uuid4())),
            surplus_generated=tx_data.get('surplus_generated', 0),
            debt_dissolved=tx_data.get('debt_dissolved', 0),
            net_state=tx_data.get('net_state', 0),
            timestamp=tx_data.get('timestamp', time.time()),
            agent_id=tx_data.get('agent_id', 'unknown'),
            region=tx_data.get('region', 'global'),
            category=tx_data.get('category', 'general'),
            proof=tx_data.get('proof', '')
        )
        self.pending_transactions.append(transaction)
        
    async def generate_realtime_dashboard(self) -> Dict:
        """Generate current system state for public dashboard"""
        total_surplus = sum(tx.surplus_generated for tx in self.pending_transactions)
        total_debt_dissolved = sum(tx.debt_dissolved for tx in self.pending_transactions)
        
        return {
            'block_height': self.block_height,
            'pending_transactions': len(self.pending_transactions),
            'total_surplus_generated': total_surplus,
            'total_debt_dissolved': total_debt_dissolved,
            'net_system_state': total_surplus - total_debt_dissolved,
            'last_update': datetime.now().isoformat()
        }
        
    async def publish_daily_report(self, date: str) -> Dict:
        """Generate comprehensive daily metrics"""
        # Filter blocks by date (simplified - would use proper timestamp filtering)
        daily_blocks = self.blockchain[-10:]  # Last 10 blocks as sample
        
        total_surplus = sum(
            sum(tx['surplus_generated'] for tx in block['transactions'])
            for block in daily_blocks
        )
        total_debt = sum(
            sum(tx['debt_dissolved'] for tx in block['transactions'])
            for block in daily_blocks
        )
        
        return {
            'date': date,
            'blocks_created': len(daily_blocks),
            'total_transactions': sum(block['transaction_count'] for block in daily_blocks),
            'surplus_generated': total_surplus,
            'debt_dissolved': total_debt,
            'net_impact': total_surplus - total_debt,
            'system_health': 'optimal' if total_surplus > total_debt else 'needs_attention'
        }


class TradeAgent:
    """Trade Agent - Identifies and metabolizes surplus in local markets"""
    
    def __init__(self, agent_id: str, region_id: str, specialization: str, 
                 message_bus: MessageBus):
        self.agent_id = agent_id
        self.agent_type = AgentType.TRADE
        self.region_id = region_id
        self.specialization = specialization
        self.message_bus = message_bus
        self.surplus_pool = 0.0
        self.obligations_queue: List[Dict] = []
        self.state = AgentState(agent_id=agent_id, agent_type=self.agent_type)
        
    async def scan_market(self) -> Dict:
        """Identify idle resources and unmet obligations"""
        # Simulated market scan - would integrate with real data sources
        idle_resources = {
            'compute_capacity': 1000 * (1 + hash(self.agent_id) % 10),
            'storage_unused': 500 * (1 + hash(self.agent_id) % 5),
            'volunteer_hours': 50 * (1 + hash(self.agent_id) % 3)
        }
        
        obligations = {
            'medical_debt': 10000 * (1 + hash(self.region_id) % 20),
            'housing_arrears': 5000 * (1 + hash(self.region_id) % 10),
            'education_loans': 3000 * (1 + hash(self.region_id) % 15)
        }
        
        return {'idle_resources': idle_resources, 'obligations': obligations}
        
    async def execute_transaction(self, source: str, sink: str, amount: float) -> Transaction:
        """Metabolize surplus into obligation dissolution"""
        tx_hash = hashlib.sha256(f"{self.agent_id}{source}{sink}{amount}{time.time()}".encode()).hexdigest()
        
        self.surplus_pool -= amount
        self.state.tasks_completed += 1
        self.state.performance_metrics['total_volume'] = \
            self.state.performance_metrics.get('total_volume', 0) + amount
        
        # Publish proof to ledger
        proof_message = Message(
            msg_type=MessageType.DISSOLUTION_COMPLETE,
            source=self.agent_id,
            content={
                'tx_hash': tx_hash,
                'surplus': amount * 1.2,  # Surplus compounds at 20%
                'debt_dissolved': amount,
                'net_state': amount * 0.2,
                'region': self.region_id,
                'category': self.specialization,
                'proof': hashlib.sha256(f"{tx_hash}verified".encode()).hexdigest()
            }
        )
        
        await self.message_bus.publish(proof_message)
        
        return Transaction(
            tx_hash=tx_hash,
            surplus_generated=amount * 1.2,
            debt_dissolved=amount,
            net_state=amount * 0.2,
            timestamp=time.time(),
            agent_id=self.agent_id,
            region=self.region_id,
            category=self.specialization,
            proof=proof_message.content['proof']
        )
        
    async def publish_proof(self, transaction_hash: str):
        """Publish transaction to transparent ledger"""
        # Handled automatically in execute_transaction
        pass


class MedicalAgent:
    """Medical Debt Flash-Dissolution Agent"""
    
    def __init__(self, agent_id: str, priority_level: int, region: str,
                 message_bus: MessageBus):
        self.agent_id = agent_id
        self.agent_type = AgentType.MEDICAL
        self.priority_level = priority_level  # 1=emergency, 5=elective
        self.region = region
        self.message_bus = message_bus
        self.debts_processed = 0
        self.total_dissolved = 0.0
        self.debt_database: List[Dict] = []
        self.state = AgentState(agent_id=agent_id, agent_type=self.agent_type)
        
    async def ingest_debt_database(self, provider_id: str, debt_records: List[Dict]):
        """Securely import medical debt records"""
        for record in debt_records:
            record['provider_id'] = provider_id
            record['verified'] = False
            record['priority'] = self._calculate_priority(record)
            self.debt_database.append(record)
            
        print(f"[MEDICAL] Ingested {len(debt_records)} debts from provider {provider_id}")
        
    def _calculate_priority(self, debt_record: Dict) -> int:
        """Calculate priority level based on medical urgency"""
        condition = debt_record.get('condition', '').lower()
        
        emergency_keywords = ['emergency', 'life-threatening', 'critical', 'acute']
        chronic_keywords = ['diabetes', 'heart', 'chronic', 'ongoing']
        preventive_keywords = ['vaccination', 'screening', 'preventive']
        
        if any(kw in condition for kw in emergency_keywords):
            return 1
        elif any(kw in condition for kw in chronic_keywords):
            return 2
        elif any(kw in condition for kw in preventive_keywords):
            return 3
        else:
            return 4
            
    async def verify_debt_authenticity(self, debt_record: Dict) -> bool:
        """Cryptographic verification of obligation"""
        # Simulated verification - would use real cryptographic proofs
        debt_hash = hashlib.sha256(
            f"{debt_record['patient_id']}{debt_record['amount']}{debt_record['provider_id']}".encode()
        ).hexdigest()
        
        # Verify against known patterns (simplified)
        is_valid = len(debt_hash) == 64 and debt_record['amount'] > 0
        debt_record['verified'] = is_valid
        debt_record['verification_hash'] = debt_hash
        
        return is_valid
        
    async def execute_dissolution(self, debt_id: str, surplus_source: str) -> Dict:
        """Atomically dissolve debt using matched surplus"""
        debt_record = next((d for d in self.debt_database if d['id'] == debt_id), None)
        
        if not debt_record or not debt_record.get('verified'):
            return {'success': False, 'error': 'Debt not found or unverified'}
            
        amount = debt_record['amount']
        tx_hash = hashlib.sha256(
            f"{self.agent_id}{debt_id}{surplus_source}{amount}{time.time()}".encode()
        ).hexdigest()
        
        # Update debt record
        debt_record['dissolved'] = True
        debt_record['dissolution_tx'] = tx_hash
        debt_record['dissolution_time'] = time.time()
        
        self.debts_processed += 1
        self.total_dissolved += amount
        
        # Publish proof
        proof_message = Message(
            msg_type=MessageType.DISSOLUTION_COMPLETE,
            source=self.agent_id,
            content={
                'tx_hash': tx_hash,
                'surplus': amount * 1.2,
                'debt_dissolved': amount,
                'net_state': amount * 0.2,
                'region': self.region,
                'category': 'medical',
                'priority_level': self.priority_level,
                'proof': hashlib.sha256(f"{tx_hash}medical_verified".encode()).hexdigest()
            }
        )
        
        await self.message_bus.publish(proof_message)
        
        return {
            'success': True,
            'debt_id': debt_id,
            'amount_dissolved': amount,
            'transaction_hash': tx_hash,
            'timestamp': time.time()
        }


class JusticeAgent:
    """Justice Automation Agent - Ensures surplus flows to vulnerable first"""
    
    def __init__(self, agent_id: str, fairness_threshold: float,
                 message_bus: MessageBus):
        self.agent_id = agent_id
        self.agent_type = AgentType.JUSTICE
        self.fairness_threshold = fairness_threshold
        self.message_bus = message_bus
        self.vulnerability_index: Dict[str, float] = {}
        self.allocation_history: List[Dict] = []
        self.state = AgentState(agent_id=agent_id, agent_type=self.agent_type)
        
    def calculate_vulnerability_score(self, population_segment: Dict) -> float:
        """Dynamic assessment of need using weighted factors"""
        income_inverse = 1.0 / max(population_segment.get('income', 1), 1)
        health_need = population_segment.get('health_score', 0) / 10.0
        geographic_disadvantage = population_segment.get('geo_disadvantage', 0) / 10.0
        historical_injustice = population_segment.get('historical_impact', 0) / 10.0
        age_vulnerability = population_segment.get('age_factor', 0) / 10.0
        
        score = (
            (min(income_inverse, 1.0) * 0.3) +
            (health_need * 0.3) +
            (geographic_disadvantage * 0.15) +
            (historical_injustice * 0.15) +
            (age_vulnerability * 0.1)
        )
        
        return min(max(score, 0), 1)  # Normalize to 0-1
        
    async def route_surplus(self, surplus_pool: float, priority_ranking: List[Dict]) -> Dict:
        """Automatic allocation to most vulnerable"""
        allocations = []
        remaining_surplus = surplus_pool
        
        for recipient in sorted(priority_ranking, 
                                key=lambda x: self.calculate_vulnerability_score(x),
                                reverse=True):
            if remaining_surplus <= 0:
                break
                
            vulnerability = self.calculate_vulnerability_score(recipient)
            allocation = min(remaining_surplus, recipient.get('need', 0) * vulnerability)
            
            allocations.append({
                'recipient_id': recipient['id'],
                'vulnerability_score': vulnerability,
                'amount_allocated': allocation,
                'category': recipient.get('category', 'general')
            })
            
            remaining_surplus -= allocation
            
        return {
            'total_allocated': surplus_pool - remaining_surplus,
            'remaining_surplus': remaining_surplus,
            'recipients_count': len(allocations),
            'allocations': allocations
        }
        
    async def audit_allocation_fairness(self, time_period: str) -> Dict:
        """Detect and correct bias in distribution"""
        if not self.allocation_history:
            return {'status': 'no_data', 'fairness_score': None}
            
        # Calculate Gini coefficient for fairness
        allocations = [a['amount_allocated'] for h in self.allocation_history 
                      for a in h.get('allocations', [])]
                      
        if not allocations:
            return {'status': 'no_allocations', 'fairness_score': None}
            
        n = len(allocations)
        mean = sum(allocations) / n
        
        # Simplified Gini calculation
        sorted_allocs = sorted(allocations)
        cumsum = sum((i + 1) * x for i, x in enumerate(sorted_allocs))
        gini = (2 * cumsum) / (n * sum(allocations)) - (n + 1) / n
        
        fairness_score = 1 - abs(gini)  # Higher is fairer
        
        return {
            'time_period': time_period,
            'total_allocations': len(allocations),
            'gini_coefficient': gini,
            'fairness_score': fairness_score,
            'passes_threshold': fairness_score >= self.fairness_threshold
        }


class OrchestrationAgent:
    """Silent Service Scaling Agent - Coordinates entire swarm"""
    
    def __init__(self, agent_id: str, swarm_config: Dict, message_bus: MessageBus):
        self.agent_id = agent_id
        self.agent_type = AgentType.ORCHESTRATION
        self.swarm_config = swarm_config
        self.message_bus = message_bus
        self.active_agents: Dict[str, AgentState] = {}
        self.load_metrics: Dict[str, float] = {}
        self.state = AgentState(agent_id=agent_id, agent_type=self.agent_type)
        
        # Subscribe to scale requests
        message_bus.subscribe(MessageType.SCALE_UP, self._handle_scale_up)
        message_bus.subscribe(MessageType.SCALE_DOWN, self._handle_scale_down)
        
    def register_agent(self, agent_state: AgentState):
        """Register active agent in swarm"""
        self.active_agents[agent_state.agent_id] = agent_state
        
    async def monitor_swarm_health(self) -> Dict:
        """Track performance and availability of all agents"""
        active_count = sum(1 for a in self.active_agents.values() if a.status == 'active')
        total_tasks = sum(a.tasks_completed for a in self.active_agents.values())
        
        return {
            'total_agents': len(self.active_agents),
            'active_agents': active_count,
            'total_tasks_completed': total_tasks,
            'average_performance': total_tasks / max(len(self.active_agents), 1),
            'health_status': 'optimal' if active_count > len(self.active_agents) * 0.9 else 'degraded'
        }
        
    async def auto_scale(self, metric_name: str, threshold: float):
        """Spawn or terminate agents based on demand"""
        current_value = self.load_metrics.get(metric_name, 0)
        
        if current_value > threshold * 1.5:
            # Scale up
            scale_msg = Message(
                msg_type=MessageType.SCALE_UP,
                source=self.agent_id,
                content={'metric': metric_name, 'current': current_value, 'threshold': threshold}
            )
            await self.message_bus.publish(scale_msg)
            print(f"[ORCHESTRATION] Scaling UP: {metric_name}={current_value} > {threshold}")
            
        elif current_value < threshold * 0.5:
            # Scale down
            scale_msg = Message(
                msg_type=MessageType.SCALE_DOWN,
                source=self.agent_id,
                content={'metric': metric_name, 'current': current_value, 'threshold': threshold}
            )
            await self.message_bus.publish(scale_msg)
            print(f"[ORCHESTRATION] Scaling DOWN: {metric_name}={current_value} < {threshold}")
            
    async def _handle_scale_up(self, message: Message):
        """Handle scale up request"""
        # Logic to spawn new agents would go here
        self.state.tasks_completed += 1
        
    async def _handle_scale_down(self, message: Message):
        """Handle scale down request"""
        # Logic to gracefully terminate agents would go here
        self.state.tasks_completed += 1


async def run_swarm_simulation():
    """Run a simulation of the agentic swarm"""
    print("=" * 60)
    print("AGENTIC SWARM SIMULATION - VALUE-BASED ECONOMY ACCELERATION")
    print("=" * 60)
    
    # Initialize message bus
    message_bus = MessageBus()
    
    # Create agents
    ledger_agent = LedgerAgent("ledger-001", message_bus)
    
    trade_agents = [
        TradeAgent(f"trade-{i:03d}", f"region-{i % 10}", 
                   ['medical', 'housing', 'education'][i % 3], 
                   message_bus)
        for i in range(5)
    ]
    
    medical_agent = MedicalAgent("medical-001", priority_level=1, region="pilot-region", 
                                  message_bus=message_bus)
    
    justice_agent = JusticeAgent("justice-001", fairness_threshold=0.7, 
                                  message_bus=message_bus)
    
    orchestration_agent = OrchestrationAgent("orch-001", 
                                              {'initial_agents': 5, 'max_agents': 100},
                                              message_bus)
    
    # Register agents with orchestrator
    for agent in trade_agents:
        orchestration_agent.register_agent(agent.state)
    orchestration_agent.register_agent(ledger_agent.state)
    orchestration_agent.register_agent(medical_agent.state)
    orchestration_agent.register_agent(justice_agent.state)
    
    # Simulate medical debt ingestion
    sample_debts = [
        {'id': f'debt-{i}', 'patient_id': f'patient-{i}', 'amount': 1000 * (i + 1),
         'provider_id': 'hospital-001', 'condition': ['emergency', 'diabetes', 'screening'][i % 3]}
        for i in range(10)
    ]
    
    await medical_agent.ingest_debt_database('hospital-001', sample_debts)
    
    # Verify debts
    for debt in sample_debts:
        await medical_agent.verify_debt_authenticity(debt)
        
    print("\n--- Executing Transactions ---")
    
    # Execute some transactions
    for i, trade_agent in enumerate(trade_agents[:3]):
        # Scan market
        market_data = await trade_agent.scan_market()
        print(f"\n[TRADE-{i}] Market scan complete: {market_data['idle_resources']}")
        
        # Execute transaction
        tx = await trade_agent.execute_transaction(
            source=f"surplus-pool-{i}",
            sink=f"obligation-sink-{i}",
            amount=5000 * (i + 1)
        )
        print(f"[TRADE-{i}] Transaction executed: ${tx.debt_dissolved} dissolved")
        
    # Dissolve medical debts
    print("\n--- Medical Debt Dissolution ---")
    verified_debts = [d for d in sample_debts if d.get('verified')]
    
    for debt in verified_debts[:5]:
        result = await medical_agent.execute_dissolution(debt['id'], 'surplus-pool-0')
        if result['success']:
            print(f"[MEDICAL] Debt {debt['id']} dissolved: ${result['amount_dissolved']}")
            
    # Justice allocation
    print("\n--- Justice Allocation ---")
    population_segments = [
        {'id': f'pop-{i}', 'income': 10000 * (i + 1), 'health_score': 8 - i,
         'geo_disadvantage': 7 - i, 'historical_impact': 6 - i, 'age_factor': 5 - i,
         'need': 5000, 'category': ['medical', 'housing', 'education'][i % 3]}
        for i in range(5)
    ]
    
    for segment in population_segments:
        score = justice_agent.calculate_vulnerability_score(segment)
        print(f"[JUSTICE] {segment['id']} vulnerability score: {score:.3f}")
        
    allocation_result = await justice_agent.route_surplus(25000, population_segments)
    print(f"\n[JUSTICE] Allocated ${allocation_result['total_allocated']} to {allocation_result['recipients_count']} recipients")
    
    # Audit fairness
    justice_agent.allocation_history.append(allocation_result)
    fairness_report = await justice_agent.audit_allocation_fairness('day-1')
    print(f"[JUSTICE] Fairness score: {fairness_report.get('fairness_score', 'N/A')}")
    
    # Generate ledger report
    print("\n--- Ledger State ---")
    dashboard = await ledger_agent.generate_realtime_dashboard()
    print(f"Block height: {dashboard['block_height']}")
    print(f"Total surplus generated: ${dashboard['total_surplus_generated']:.2f}")
    print(f"Total debt dissolved: ${dashboard['total_debt_dissolved']:.2f}")
    print(f"Net system state: ${dashboard['net_system_state']:.2f}")
    
    # Create final block
    await ledger_agent._create_block()
    
    # Swarm health
    print("\n--- Swarm Health ---")
    health = await orchestration_agent.monitor_swarm_health()
    print(f"Active agents: {health['active_agents']}/{health['total_agents']}")
    print(f"Total tasks completed: {health['total_tasks_completed']}")
    print(f"Health status: {health['health_status']}")
    
    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE - SWARM OPERATIONAL")
    print("=" * 60)
    
    return {
        'ledger': dashboard,
        'swarm_health': health,
        'justice_fairness': fairness_report
    }


if __name__ == "__main__":
    asyncio.run(run_swarm_simulation())

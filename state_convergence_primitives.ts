/**
 * Phase 1 Implementation: State Convergence Primitives
 * 
 * Bridges Gap #1 from GAP_ANALYSIS_REMEDIATION.md
 * Implements three-layer state model:
 * - Control Plane: Raft consensus for critical decisions
 * - Data Plane: CRDTs for eventual consistency
 * - Intent Plane: Policy engine for routing
 */

import * as Automerge from '@automerge/automerge';
import type { Doc } from '@automerge/automerge';

// ============================================================================
// Type Definitions
// ============================================================================

type NodeId = string;
type FacetId = string;
type VectorKey = 'ODIN' | 'THOR' | 'LOKI' | 'FREYA' | 'FRIGG' | 'FREYR';

interface Position {
  x: number;
  y: number;
  z: number;
}

interface LatticeNodeCRDT {
  id: NodeId;
  position: Position;
  vector: VectorKey | null;
  facetId: FacetId | null;
  health: number; // 0.0 to 1.0
  lastHeartbeat: number;
  metadata: Record<string, any>;
}

interface LatticeFacetCRDT {
  id: FacetId;
  type: string;
  vertexIds: NodeId[];
  centroid: Position;
  serviceUrl?: string;
  health: number;
  activeStreams: string[];
}

interface ControlDecision {
  id: string;
  timestamp: number;
  proposer: NodeId;
  action: 'REBALANCE' | 'FAILOVER' | 'SCALE' | 'HEAL';
  targetId: NodeId | FacetId;
  rationale: string;
  signatures: string[]; // Ed25519 signatures
  executed: boolean;
}

// ============================================================================
// Layer 1: CRDT Data Plane
// ============================================================================

interface LatticeState {
  nodes: Record<NodeId, LatticeNodeCRDT>;
  facets: Record<FacetId, LatticeFacetCRDT>;
  vectors: Record<VectorKey, NodeId>;
  version: number;
  [key: string]: any; // Index signature for Automerge compatibility
}

class LatticeCRDT {
  private doc: Doc<LatticeState>;
  
  constructor(initialState?: LatticeState) {
    this.doc = Automerge.from<LatticeState>(initialState || {
      nodes: {},
      facets: {},
      vectors: {} as Record<VectorKey, NodeId>,
      version: 0
    });
  }

  /**
   * Merge remote state (idempotent, commutative, associative)
   */
  merge(remoteDoc: Doc<LatticeState>): void {
    this.doc = Automerge.merge(this.doc, remoteDoc);
  }

  /**
   * Update node health (concurrent-safe)
   */
  updateNodeHealth(nodeId: NodeId, health: number): void {
    this.doc = Automerge.change(this.doc, `Update ${nodeId} health`, (state) => {
      if (state.nodes[nodeId]) {
        state.nodes[nodeId].health = Math.max(0, Math.min(1, health));
        state.nodes[nodeId].lastHeartbeat = Date.now();
        state.version++;
      }
    });
  }

  /**
   * Add or update node (idempotent)
   */
  upsertNode(node: LatticeNodeCRDT): void {
    this.doc = Automerge.change(this.doc, `Upsert node ${node.id}`, (state) => {
      state.nodes[node.id] = {
        ...node,
        lastHeartbeat: Date.now()
      };
      state.version++;
    });
  }

  /**
   * Remove node (tombstone handled by Automerge)
   */
  removeNode(nodeId: NodeId): void {
    this.doc = Automerge.change(this.doc, `Remove node ${nodeId}`, (state) => {
      delete state.nodes[nodeId];
      state.version++;
    });
  }

  /**
   * Update facet health
   */
  updateFacetHealth(facetId: FacetId, health: number): void {
    this.doc = Automerge.change(this.doc, `Update ${facetId} health`, (state) => {
      if (state.facets[facetId]) {
        state.facets[facetId].health = Math.max(0, Math.min(1, health));
        state.version++;
      }
    });
  }

  /**
   * Get current state snapshot
   */
  getSnapshot(): LatticeState {
    return { ...this.doc };
  }

  /**
   * Serialize for transmission
   */
  serialize(): Uint8Array {
    return Automerge.save(this.doc);
  }

  /**
   * Deserialize from binary
   */
  static deserialize(data: Uint8Array): LatticeCRDT {
    const doc = Automerge.load<LatticeState>(data);
    const crdt = new LatticeCRDT();
    crdt.doc = doc;
    return crdt;
  }

  /**
   * Compute entropy metric (Gap #3 preparation)
   */
  computeEntropy(): number {
    const nodes = Object.values(this.doc.nodes);
    if (nodes.length === 0) return 0;

    const healthyNodes = nodes.filter(n => n.health > 0.8).length;
    const avgHealth = nodes.reduce((sum, n) => sum + n.health, 0) / nodes.length;
    
    // Entropy = 1 - (healthy_ratio * avg_health)
    // Lower is better (more ordered)
    return 1 - ((healthyNodes / nodes.length) * avgHealth);
  }

  /**
   * Compute syntropy (Φ) - inverse of entropy
   */
  computeSyntropy(): number {
    return 1 - this.computeEntropy();
  }
}

// ============================================================================
// Layer 2: Control Plane Interface (Raft Placeholder)
// ============================================================================

interface RaftConfig {
  nodeId: NodeId;
  peerNodes: NodeId[];
  electionTimeout?: number;
  heartbeatInterval?: number;
}

class ControlPlane {
  private config: RaftConfig;
  private pendingDecisions: Map<string, ControlDecision> = new Map();
  private decisionLog: ControlDecision[] = [];
  
  constructor(config: RaftConfig) {
    this.config = config;
  }

  /**
   * Propose a control decision (requires consensus)
   */
  async propose(decision: Omit<ControlDecision, 'id' | 'signatures' | 'executed'>): Promise<ControlDecision> {
    const fullDecision: ControlDecision = {
      ...decision,
      id: `decision-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      signatures: [],
      executed: false
    };

    // In production: Send to Raft consensus
    // For now: Simulate with local signing
    console.log(`[ControlPlane] Proposing: ${decision.action} on ${decision.targetId}`);
    
    // Simulate consensus delay
    await new Promise(resolve => setTimeout(resolve, 10));
    
    // Self-sign (in production: collect threshold signatures)
    const signature = await this.signDecision(fullDecision);
    fullDecision.signatures.push(signature);
    
    this.pendingDecisions.set(fullDecision.id, fullDecision);
    this.decisionLog.push(fullDecision);
    
    return fullDecision;
  }

  /**
   * Execute a decided action
   */
  async execute(decisionId: string, crdt: LatticeCRDT): Promise<boolean> {
    const decision = this.pendingDecisions.get(decisionId);
    if (!decision) {
      throw new Error(`Decision ${decisionId} not found`);
    }

    if (decision.signatures.length < 1) { // Threshold in production
      throw new Error('Insufficient signatures for execution');
    }

    console.log(`[ControlPlane] Executing: ${decision.action}`);
    
    // Apply state changes based on action type
    switch (decision.action) {
      case 'REBALANCE':
        // Trigger rebalancing logic
        break;
      case 'FAILOVER':
        // Mark node as failed, trigger failover
        crdt.updateNodeHealth(decision.targetId as NodeId, 0);
        break;
      case 'SCALE':
        // Add new nodes
        break;
      case 'HEAL':
        // Attempt recovery
        crdt.updateNodeHealth(decision.targetId as NodeId, 0.9);
        break;
    }

    decision.executed = true;
    return true;
  }

  /**
   * Sign a decision (Ed25519 in production)
   */
  private async signDecision(decision: ControlDecision): Promise<string> {
    const payload = JSON.stringify({
      id: decision.id,
      action: decision.action,
      targetId: decision.targetId,
      timestamp: decision.timestamp
    });
    
    // Placeholder: Base64 encode (use Ed25519 in production)
    return Buffer.from(payload).toString('base64');
  }

  /**
   * Verify decision signatures
   */
  async verifySignatures(decision: ControlDecision): Promise<boolean> {
    // In production: Verify Ed25519 signatures against known public keys
    return decision.signatures.length >= 1;
  }

  getDecisionLog(): ControlDecision[] {
    return [...this.decisionLog];
  }
}

// ============================================================================
// Layer 3: Intent Plane (Policy Engine)
// ============================================================================

type PolicyAction = 'ROUTE' | 'BLOCK' | 'THROTTLE' | 'AUDIT';

interface PolicyRule {
  id: string;
  name: string;
  condition: (intent: IntentVector, state: LatticeState) => boolean;
  action: PolicyAction;
  priority: number;
  metadata?: Record<string, any>;
}

interface IntentVector {
  semanticEmbedding: number[];
  sourceId: NodeId;
  targetType?: string;
  urgency: number; // 0.0 to 1.0
  metadata?: Record<string, any>;
}

class IntentPolicyEngine {
  private rules: PolicyRule[] = [];

  /**
   * Register a policy rule
   */
  registerRule(rule: PolicyRule): void {
    this.rules.push(rule);
    this.rules.sort((a, b) => b.priority - a.priority);
  }

  /**
   * Evaluate intent against policies
   */
  evaluate(intent: IntentVector, state: LatticeState): PolicyAction {
    for (const rule of this.rules) {
      if (rule.condition(intent, state)) {
        console.log(`[PolicyEngine] Rule "${rule.name}" matched: ${rule.action}`);
        return rule.action;
      }
    }
    return 'ROUTE'; // Default action
  }

  /**
   * Built-in safety policies
   */
  loadDefaultPolicies(): void {
    // Policy 1: Block requests to unhealthy facets
    this.registerRule({
      id: 'safety-1',
      name: 'Block Unhealthy Facets',
      condition: (intent, state) => {
        if (!intent.targetType) return false;
        const facet = Object.values(state.facets).find(f => f.type === intent.targetType);
        return !!facet && facet.health < 0.5;
      },
      action: 'BLOCK',
      priority: 100
    });

    // Policy 2: Audit high-urgency requests
    this.registerRule({
      id: 'audit-1',
      name: 'Audit High Urgency',
      condition: (intent, state) => intent.urgency > 0.9,
      action: 'AUDIT',
      priority: 90
    });

    // Policy 3: Throttle during high entropy
    this.registerRule({
      id: 'throttle-1',
      name: 'Throttle During Chaos',
      condition: (intent, state) => {
        const crdt = new LatticeCRDT(state);
        return crdt.computeEntropy() > 0.3;
      },
      action: 'THROTTLE',
      priority: 80
    });
  }
}

// ============================================================================
// Integration: Three-Layer Orchestrator
// ============================================================================

interface ThreeLayerConfig {
  nodeId: NodeId;
  peers: NodeId[];
}

class ThreeLayerOrchestrator {
  private dataPlane: LatticeCRDT;
  private controlPlane: ControlPlane;
  private intentPlane: IntentPolicyEngine;

  constructor(config: ThreeLayerConfig) {
    this.dataPlane = new LatticeCRDT();
    this.controlPlane = new ControlPlane({
      nodeId: config.nodeId,
      peerNodes: config.peers
    });
    this.intentPlane = new IntentPolicyEngine();
    this.intentPlane.loadDefaultPolicies();
  }

  /**
   * Process an incoming intent
   */
  async processIntent(intent: IntentVector): Promise<PolicyAction> {
    const state = this.dataPlane.getSnapshot();
    const action = this.intentPlane.evaluate(intent, state);
    
    console.log(`[Orchestrator] Intent processed: ${action}`);
    return action;
  }

  /**
   * Propose a control action
   */
  async proposeControlAction(
    action: 'REBALANCE' | 'FAILOVER' | 'SCALE' | 'HEAL',
    targetId: NodeId | FacetId,
    rationale: string
  ): Promise<ControlDecision> {
    return this.controlPlane.propose({
      timestamp: Date.now(),
      proposer: this.controlPlane['config'].nodeId,
      action,
      targetId,
      rationale
    });
  }

  /**
   * Sync with remote state
   */
  syncRemoteState(remoteData: Uint8Array): void {
    const remoteCRDT = LatticeCRDT.deserialize(remoteData);
    this.dataPlane.merge(remoteCRDT['doc']);
  }

  /**
   * Export state for transmission
   */
  exportState(): Uint8Array {
    return this.dataPlane.serialize();
  }

  /**
   * Get system metrics
   */
  getMetrics() {
    const state = this.dataPlane.getSnapshot();
    return {
      syntropy: this.dataPlane.computeSyntropy(),
      entropy: this.dataPlane.computeEntropy(),
      nodeCount: Object.keys(state.nodes).length,
      facetCount: Object.keys(state.facets).length,
      pendingDecisions: this.controlPlane.getDecisionLog().filter(d => !d.executed).length
    };
  }
}

// ============================================================================
// Exports
// ============================================================================

export {
  LatticeCRDT,
  ControlPlane,
  IntentPolicyEngine,
  ThreeLayerOrchestrator,
  LatticeState,
  LatticeNodeCRDT,
  LatticeFacetCRDT,
  ControlDecision,
  IntentVector,
  PolicyRule,
  PolicyAction
};

// ============================================================================
// Usage Example
// ============================================================================

/*
// Initialize orchestrator
const orchestrator = new ThreeLayerOrchestrator({
  nodeId: 'node-1',
  peers: ['node-2', 'node-3']
});

// Add some nodes
orchestrator['dataPlane'].upsertNode({
  id: 'node-1',
  position: { x: 0, y: 5, z: 0 },
  vector: 'ODIN',
  facetId: 'facet-LANGUAGE',
  health: 1.0,
  lastHeartbeat: Date.now(),
  metadata: { type: 'DIVINE_ANCHOR' }
});

// Process an intent
const intent: IntentVector = {
  semanticEmbedding: [0.1, 0.9, 0.2],
  sourceId: 'node-1',
  targetType: 'LANGUAGE',
  urgency: 0.7
};

await orchestrator.processIntent(intent);

// Propose a control action
const decision = await orchestrator.proposeControlAction(
  'HEAL',
  'node-1',
  'Proactive health restoration'
);

await orchestrator['controlPlane'].execute(decision.id, orchestrator['dataPlane']);

// Get metrics
console.log('System Metrics:', orchestrator.getMetrics());

// Serialize for sync
const stateBytes = orchestrator.exportState();
// Send to peers...
*/

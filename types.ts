
export enum ControlMode {
  REACTIVE = 'REACTIVE',
  BOUNDED = 'BOUNDED'
}

export type DomainContext = 'GENERAL' | 'MEDICAL_ROBOTICS' | 'AEROSPACE' | 'FINTECH';

export interface Invariant {
  id: string;
  name: string;
  expression: string; // Formal logic representation
  limit: number;
  current: number;
  unit: string;
  status: 'STABLE' | 'WARNING' | 'VIOLATED';
  safetyCritical: boolean;
}

export interface WorkUnit {
  id: string;
  payload: number;
  timestamp: number;
  status: 'PENDING' | 'ADMITTED' | 'PREEMPTED' | 'FAILED' | 'COMPLETED';
  failureRisk?: number;
  architecture: ControlMode;
  reason?: string;
  latencyManifold?: number; // Simulated dependency depth overhead
}

export interface ControlMetrics {
  syntropy: number; // Φ: Index of internal order vs entropy
  operationalMultiplier: number; // Efficiency gain vs reactive systems
  stateCoverage: number; // % of possible state space mapped and bounded
  containmentProof: number; // % of potential failures successfully preempted
  mtbf: number; // Mean Time Between Failures (ms)
  atomicSuccessRatio: number; // % of operations that completed without state drift
  throughput: number;
  totalStates: number;
}

export interface KpiMetrics {
  admissionRate: number;
  failureRate: number;
  totalRequests: number;
  syntropy: number;
  opMultiplier: number;
}

export interface SystemState {
  metrics: ControlMetrics;
  invariants: Invariant[];
  activeWork: WorkUnit[];
  history: WorkUnit[];
  domain: DomainContext;
}

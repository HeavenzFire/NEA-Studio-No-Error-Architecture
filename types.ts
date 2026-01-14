
export enum ArchitectureMode {
  TRADITIONAL = 'TRADITIONAL',
  NO_ERROR = 'NO_ERROR'
}

export interface SystemConstraint {
  id: string;
  name: string;
  threshold: number;
  currentValue: number;
  unit: string;
}

export interface WorkUnit {
  id: string;
  payload: number;
  timestamp: number;
  status: 'PENDING' | 'ADMITTED' | 'REFUSED' | 'FAILED' | 'COMPLETED';
  reason?: string;
}

export interface KpiMetrics {
  admissionRate: number;
  failureRate: number;
  totalRequests: number;
  avgPayload: number;
}

export interface SystemState {
  throughput: number;
  coherence: number;
  entropy: number;
  activeWork: WorkUnit[];
  history: WorkUnit[];
  kpis: KpiMetrics;
}

export interface RefusalResult {
  admitted: boolean;
  reason?: string;
}

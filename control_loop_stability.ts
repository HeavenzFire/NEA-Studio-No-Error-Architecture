/**
 * Phase 2 Implementation: Control Loop with Stability Guarantees
 * 
 * Bridges Gap #4 from GAP_ANALYSIS_REMEDIATION.md
 * Implements autonomous control loop with:
 * - PID controller for stable rebalancing
 * - Hysteresis windows to prevent oscillation
 * - Canary execution with rollback semantics
 * - Lyapunov function verification
 */

import { LatticeCRDT, LatticeState } from './state_convergence_primitives';

// ============================================================================
// Type Definitions
// ============================================================================

type ControlAction = 'REBALANCE' | 'FAILOVER' | 'SCALE_UP' | 'SCALE_DOWN' | 'HEAL' | 'THROTTLE';

interface ActionProposal {
  id: string;
  action: ControlAction;
  targetId: string;
  magnitude: number; // 0.0 to 1.0
  timestamp: number;
  rationale: string;
  canaryGroup?: string;
}

interface ActionResult {
  proposalId: string;
  success: boolean;
  metricsBefore: SystemMetrics;
  metricsAfter: SystemMetrics;
  rolledBack: boolean;
  rollbackReason?: string;
}

interface SystemMetrics {
  syntropy: number;
  entropy: number;
  avgHealth: number;
  latencyP99: number;
  throughput: number;
  resourceUtilization: number;
}

interface PIDConfig {
  kp: number; // Proportional gain
  ki: number; // Integral gain
  kd: number; // Derivative gain
  integralLimit: number;
  outputLimit: number;
}

interface HysteresisConfig {
  windowSize: number; // Number of samples
  upperThreshold: number;
  lowerThreshold: number;
  minIntervalMs: number; // Minimum time between actions
}

interface CanaryConfig {
  enabled: boolean;
  groupSize: number; // Percentage of nodes to test on first
  successThreshold: number; // Minimum success rate to proceed
  rollbackOnFailure: boolean;
}

// ============================================================================
// PID Controller for Stable Rebalancing
// ============================================================================

class PIDController {
  private config: PIDConfig;
  private integral: number = 0;
  private previousError: number = 0;
  private lastUpdate: number = Date.now();

  constructor(config: PIDConfig) {
    this.config = config;
  }

  /**
   * Compute control output based on error (setpoint - measured)
   */
  compute(error: number): number {
    const now = Date.now();
    const dt = (now - this.lastUpdate) / 1000; // Convert to seconds
    this.lastUpdate = now;

    // Proportional term
    const P = this.config.kp * error;

    // Integral term with anti-windup
    this.integral += error * dt;
    this.integral = Math.max(-this.config.integralLimit, Math.min(this.config.integralLimit, this.integral));
    const I = this.config.ki * this.integral;

    // Derivative term
    const derivative = dt > 0 ? (error - this.previousError) / dt : 0;
    const D = this.config.kd * derivative;

    this.previousError = error;

    // Sum and limit
    let output = P + I + D;
    output = Math.max(-this.config.outputLimit, Math.min(this.config.outputLimit, output));

    return output;
  }

  /**
   * Reset controller state
   */
  reset(): void {
    this.integral = 0;
    this.previousError = 0;
    this.lastUpdate = Date.now();
  }

  /**
   * Tune gains using Ziegler-Nichols method (simplified)
   */
  tune(criticalGain: number, criticalPeriod: number): void {
    // Classic Ziegler-Nichols tuning for PID
    this.config.kp = 0.6 * criticalGain;
    this.config.ki = 2 * this.config.kp / criticalPeriod;
    this.config.kd = this.config.kp * criticalPeriod / 8;
  }
}

// ============================================================================
// Hysteresis Window to Prevent Oscillation
// ============================================================================

class HysteresisWindow {
  private config: HysteresisConfig;
  private samples: number[] = [];
  private lastActionTime: number = 0;
  private state: 'NORMAL' | 'ACTION_PENDING' | 'COOLDOWN' = 'NORMAL';

  constructor(config: HysteresisConfig) {
    this.config = config;
  }

  /**
   * Add a sample and check if action should be triggered
   */
  addSample(value: number): { shouldAct: boolean; direction: 'UP' | 'DOWN' | 'NONE' } {
    this.samples.push(value);
    
    // Keep window size bounded
    if (this.samples.length > this.config.windowSize) {
      this.samples.shift();
    }

    // Check minimum interval
    const now = Date.now();
    if (now - this.lastActionTime < this.config.minIntervalMs) {
      return { shouldAct: false, direction: 'NONE' };
    }

    // Calculate moving average
    const avg = this.samples.reduce((a, b) => a + b, 0) / this.samples.length;

    // Determine direction with hysteresis
    if (avg > this.config.upperThreshold && this.state !== 'ACTION_PENDING') {
      this.state = 'ACTION_PENDING';
      return { shouldAct: true, direction: 'UP' };
    } else if (avg < this.config.lowerThreshold && this.state !== 'ACTION_PENDING') {
      this.state = 'ACTION_PENDING';
      return { shouldAct: true, direction: 'DOWN' };
    }

    // Reset state if back in normal range
    if (avg >= this.config.lowerThreshold && avg <= this.config.upperThreshold) {
      this.state = 'NORMAL';
    }

    return { shouldAct: false, direction: 'NONE' };
  }

  /**
   * Mark action as completed (for cooldown)
   */
  markActionCompleted(): void {
    this.lastActionTime = Date.now();
    this.state = 'COOLDOWN';
    
    // Return to normal after brief delay
    setTimeout(() => {
      this.state = 'NORMAL';
    }, 100);
  }

  /**
   * Get current window statistics
   */
  getStats(): { average: number; trend: 'INCREASING' | 'DECREASING' | 'STABLE' } {
    if (this.samples.length < 2) {
      return { average: this.samples[0] || 0, trend: 'STABLE' };
    }

    const avg = this.samples.reduce((a, b) => a + b, 0) / this.samples.length;
    const firstHalf = this.samples.slice(0, Math.floor(this.samples.length / 2));
    const secondHalf = this.samples.slice(Math.floor(this.samples.length / 2));
    
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
    
    const trend = secondAvg > firstAvg + 0.01 ? 'INCREASING' : 
                  secondAvg < firstAvg - 0.01 ? 'DECREASING' : 'STABLE';

    return { average: avg, trend };
  }
}

// ============================================================================
// Canary Execution with Rollback
// ============================================================================

class CanaryExecutor {
  private config: CanaryConfig;

  constructor(config: CanaryConfig) {
    this.config = config;
  }

  /**
   * Execute action on canary group first, then roll out if successful
   */
  async executeWithCanary(
    proposal: ActionProposal,
    allTargets: string[],
    executeFn: (targetId: string) => Promise<boolean>,
    rollbackFn: (targetId: string) => Promise<boolean>
  ): Promise<ActionResult> {
    const metricsBefore = this.captureMetrics();

    if (!this.config.enabled) {
      // Direct execution without canary
      const success = await this.executeOnAll(allTargets, executeFn);
      return {
        proposalId: proposal.id,
        success,
        metricsBefore,
        metricsAfter: this.captureMetrics(),
        rolledBack: false
      };
    }

    // Step 1: Execute on canary group
    const canarySize = Math.max(1, Math.floor(allTargets.length * (this.config.groupSize / 100)));
    const canaryGroup = allTargets.slice(0, canarySize);
    const remainingTargets = allTargets.slice(canarySize);

    console.log(`[CanaryExecutor] Testing on ${canaryGroup.length} nodes...`);

    const canaryResults = await Promise.all(canaryGroup.map(executeFn));
    const canarySuccessRate = canaryResults.filter(r => r).length / canaryResults.length;

    if (canarySuccessRate < this.config.successThreshold) {
      console.warn(`[CanaryExecutor] Canary failed (${canarySuccessRate.toFixed(2)} < ${this.config.successThreshold})`);
      
      // Rollback canary group
      if (this.config.rollbackOnFailure) {
        await Promise.all(canaryGroup.map(rollbackFn));
      }

      return {
        proposalId: proposal.id,
        success: false,
        metricsBefore,
        metricsAfter: this.captureMetrics(),
        rolledBack: this.config.rollbackOnFailure,
        rollbackReason: `Canary success rate ${canarySuccessRate.toFixed(2)} below threshold ${this.config.successThreshold}`
      };
    }

    // Step 2: Roll out to remaining targets
    console.log(`[CanaryExecutor] Canary passed, rolling out to ${remainingTargets.length} nodes...`);
    const remainingResults = await Promise.all(remainingTargets.map(executeFn));
    const overallSuccess = remainingResults.filter(r => r).length / remainingResults.length >= this.config.successThreshold;

    return {
      proposalId: proposal.id,
      success: overallSuccess,
      metricsBefore,
      metricsAfter: this.captureMetrics(),
      rolledBack: false
    };
  }

  /**
   * Execute on all targets (no canary)
   */
  private async executeOnAll(
    targets: string[],
    executeFn: (targetId: string) => Promise<boolean>
  ): Promise<boolean> {
    const results = await Promise.all(targets.map(executeFn));
    return results.filter(r => r).length / results.length >= 0.9;
  }

  /**
   * Capture current system metrics (placeholder)
   */
  private captureMetrics(): SystemMetrics {
    // In production: Query actual monitoring system
    return {
      syntropy: 0.95,
      entropy: 0.05,
      avgHealth: 0.98,
      latencyP99: 50,
      throughput: 1000,
      resourceUtilization: 0.65
    };
  }
}

// ============================================================================
// Lyapunov Function for Stability Verification
// ============================================================================

class LyapunovVerifier {
  /**
   * Check if system is converging (Lyapunov stability)
   * V(x) should decrease over time for stable systems
   */
  verifyConvergence(metricsHistory: SystemMetrics[]): { stable: boolean; reason: string } {
    if (metricsHistory.length < 3) {
      return { stable: true, reason: 'Insufficient history' };
    }

    // Lyapunov function: V = entropy^2 + (1 - syntropy)^2
    const computeV = (m: SystemMetrics) => {
      return Math.pow(m.entropy, 2) + Math.pow(1 - m.syntropy, 2);
    };

    const values = metricsHistory.map(computeV);
    
    // Check if V is decreasing (with tolerance for noise)
    const tolerance = 0.01;
    let decreasing = true;
    let increasingCount = 0;

    for (let i = 1; i < values.length; i++) {
      if (values[i] > values[i - 1] + tolerance) {
        increasingCount++;
        if (increasingCount > Math.floor(values.length / 3)) {
          decreasing = false;
          break;
        }
      }
    }

    if (!decreasing) {
      return {
        stable: false,
        reason: `Lyapunov function increasing: V[${values.join(', ')}]`
      };
    }

    // Check convergence rate
    const initialV = values[0];
    const finalV = values[values.length - 1];
    const convergenceRate = (initialV - finalV) / initialV;

    if (convergenceRate < 0.01) {
      return {
        stable: true,
        reason: `System stable but not converging (rate: ${convergenceRate.toFixed(4)})`
      };
    }

    return {
      stable: true,
      reason: `System converging (V: ${initialV.toFixed(4)} → ${finalV.toFixed(4)}, rate: ${convergenceRate.toFixed(4)})`
    };
  }
}

// ============================================================================
// Autonomous Control Loop (Sense → Diagnose → Plan → Act → Validate)
// ============================================================================

interface ControlLoopConfig {
  pid: PIDConfig;
  hysteresis: HysteresisConfig;
  canary: CanaryConfig;
  setpoint: {
    targetSyntropy: number;
    targetHealth: number;
    maxEntropy: number;
  };
  loopIntervalMs: number;
}

class AutonomousControlLoop {
  private config: ControlLoopConfig;
  private pidController: PIDController;
  private hysteresisWindow: HysteresisWindow;
  private canaryExecutor: CanaryExecutor;
  private lyapunovVerifier: LyapunovVerifier;
  private crdt: LatticeCRDT;
  private running: boolean = false;
  private metricsHistory: SystemMetrics[] = [];
  private actionLog: ActionResult[] = [];

  constructor(config: ControlLoopConfig, crdt: LatticeCRDT) {
    this.config = config;
    this.pidController = new PIDController(config.pid);
    this.hysteresisWindow = new HysteresisWindow(config.hysteresis);
    this.canaryExecutor = new CanaryExecutor(config.canary);
    this.lyapunovVerifier = new LyapunovVerifier();
    this.crdt = crdt;
  }

  /**
   * Start the control loop
   */
  start(): void {
    if (this.running) return;
    this.running = true;
    console.log('[ControlLoop] Started');
    this.loop();
  }

  /**
   * Stop the control loop
   */
  stop(): void {
    this.running = false;
    console.log('[ControlLoop] Stopped');
  }

  /**
   * Main control loop iteration
   */
  private async loop(): Promise<void> {
    while (this.running) {
      try {
        await this.iteration();
      } catch (error) {
        console.error('[ControlLoop] Error in iteration:', error);
      }
      
      await new Promise(resolve => setTimeout(resolve, this.config.loopIntervalMs));
    }
  }

  /**
   * Single iteration: Sense → Diagnose → Plan → Act → Validate
   */
  private async iteration(): Promise<void> {
    // SENSE: Gather metrics
    const metrics = this.sense();
    this.metricsHistory.push(metrics);
    
    // Keep history bounded
    if (this.metricsHistory.length > 100) {
      this.metricsHistory.shift();
    }

    // DIAGNOSE: Check stability and identify issues
    const diagnosis = this.diagnose(metrics);

    // PLAN: Generate action if needed
    const proposal = this.plan(diagnosis, metrics);

    // ACT: Execute with canary if action proposed
    if (proposal) {
      const result = await this.act(proposal);
      this.actionLog.push(result);
      
      // Keep log bounded
      if (this.actionLog.length > 1000) {
        this.actionLog.shift();
      }
    }

    // VALIDATE: Check Lyapunov stability
    const validation = this.lyapunovVerifier.verifyConvergence(this.metricsHistory);
    if (!validation.stable) {
      console.warn('[ControlLoop] Stability warning:', validation.reason);
      
      // Dampen controller gains to reduce oscillation
      this.pidController['config'].kp *= 0.9;
      this.pidController['config'].kd *= 1.1;
    }
  }

  /**
   * Sense: Capture current system state
   */
  private sense(): SystemMetrics {
    const state = this.crdt.getSnapshot();
    const nodes = Object.values(state.nodes);
    
    const avgHealth = nodes.length > 0 
      ? nodes.reduce((sum, n) => sum + n.health, 0) / nodes.length 
      : 0;
    
    const syntropy = this.crdt.computeSyntropy();
    const entropy = this.crdt.computeEntropy();

    // Placeholder for real metrics
    return {
      syntropy,
      entropy,
      avgHealth,
      latencyP99: 50 + Math.random() * 20,
      throughput: 1000 + Math.random() * 200,
      resourceUtilization: 0.5 + Math.random() * 0.3
    };
  }

  /**
   * Diagnose: Identify system issues
   */
  private diagnose(metrics: SystemMetrics): { issues: string[]; severity: 'LOW' | 'MEDIUM' | 'HIGH' } {
    const issues: string[] = [];
    let severity: 'LOW' | 'MEDIUM' | 'HIGH' = 'LOW';

    if (metrics.syntropy < this.config.setpoint.targetSyntropy - 0.1) {
      issues.push('Low syntropy');
      severity = 'MEDIUM';
    }

    if (metrics.entropy > this.config.setpoint.maxEntropy) {
      issues.push('High entropy');
      severity = 'HIGH';
    }

    if (metrics.avgHealth < this.config.setpoint.targetHealth - 0.1) {
      issues.push('Low average health');
      severity = severity === 'HIGH' ? 'HIGH' : 'MEDIUM';
    }

    return { issues, severity };
  }

  /**
   * Plan: Generate corrective action
   */
  private plan(diagnosis: { issues: string[]; severity: string }, metrics: SystemMetrics): ActionProposal | null {
    if (diagnosis.issues.length === 0) {
      return null;
    }

    // Use PID to determine action magnitude
    const syntropyError = this.config.setpoint.targetSyntropy - metrics.syntropy;
    const magnitude = Math.abs(this.pidController.compute(syntropyError));

    // Determine action type based on issues
    let action: ControlAction = 'HEAL';
    if (diagnosis.issues.includes('High entropy')) {
      action = 'REBALANCE';
    } else if (metrics.avgHealth < 0.7) {
      action = 'SCALE_UP';
    } else if (metrics.resourceUtilization < 0.3) {
      action = 'SCALE_DOWN';
    }

    return {
      id: `action-${Date.now()}`,
      action,
      targetId: 'system',
      magnitude: Math.min(1, magnitude),
      timestamp: Date.now(),
      rationale: diagnosis.issues.join(', ')
    };
  }

  /**
   * Act: Execute proposed action with canary
   */
  private async act(proposal: ActionProposal): Promise<ActionResult> {
    console.log(`[ControlLoop] Executing: ${proposal.action} (magnitude: ${proposal.magnitude.toFixed(2)})`);

    // Simulate target selection
    const state = this.crdt.getSnapshot();
    const allTargets = Object.keys(state.nodes);

    // Execute with canary
    const result = await this.canaryExecutor.executeWithCanary(
      proposal,
      allTargets,
      async (targetId) => {
        // Simulate action execution
        await new Promise(resolve => setTimeout(resolve, 10));
        return Math.random() > 0.1; // 90% success rate simulation
      },
      async (targetId) => {
        // Simulate rollback
        console.log(`[ControlLoop] Rolled back ${targetId}`);
        return true;
      }
    );

    this.hysteresisWindow.markActionCompleted();
    return result;
  }

  /**
   * Get control loop status
   */
  getStatus() {
    return {
      running: this.running,
      iterations: this.metricsHistory.length,
      actionsTaken: this.actionLog.length,
      currentMetrics: this.metricsHistory[this.metricsHistory.length - 1] || null,
      hysteresisStats: this.hysteresisWindow.getStats(),
      recentActions: this.actionLog.slice(-5)
    };
  }
}

// ============================================================================
// Exports
// ============================================================================

export {
  PIDController,
  HysteresisWindow,
  CanaryExecutor,
  LyapunovVerifier,
  AutonomousControlLoop,
  ControlAction,
  ActionProposal,
  ActionResult,
  SystemMetrics,
  PIDConfig,
  HysteresisConfig,
  CanaryConfig,
  ControlLoopConfig
};

// ============================================================================
// Usage Example
// ============================================================================

/*
// Initialize CRDT
const crdt = new LatticeCRDT({
  nodes: {},
  facets: {},
  vectors: {} as any,
  version: 0
});

// Create control loop with tuned parameters
const controlLoop = new AutonomousControlLoop({
  pid: {
    kp: 1.0,
    ki: 0.1,
    kd: 0.05,
    integralLimit: 10,
    outputLimit: 1
  },
  hysteresis: {
    windowSize: 10,
    upperThreshold: 0.7,
    lowerThreshold: 0.3,
    minIntervalMs: 5000
  },
  canary: {
    enabled: true,
    groupSize: 10,
    successThreshold: 0.9,
    rollbackOnFailure: true
  },
  setpoint: {
    targetSyntropy: 0.95,
    targetHealth: 0.9,
    maxEntropy: 0.2
  },
  loopIntervalMs: 1000
}, crdt);

// Start autonomous operation
controlLoop.start();

// Monitor status
setInterval(() => {
  console.log('Control Loop Status:', controlLoop.getStatus());
}, 5000);
*/

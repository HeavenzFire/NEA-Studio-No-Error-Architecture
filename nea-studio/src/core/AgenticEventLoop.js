/**
 * NEA-Studio: Agentic Event Loop
 * Tier 1: Core State & Logic Engine (Syntropic Foundations)
 * 
 * Autonomous workflow monitor that triggers automated self-correction
 * when the system falls out of alignment.
 */

import { TernaryState, TernaryStateManager } from './TernaryStateManager.js';

class AgenticEventLoop {
  constructor(options = {}) {
    this.stateManager = new TernaryStateManager();
    this.isRunning = false;
    this.intervalId = null;
    this.checkInterval = options.checkInterval || 100; // ms
    this.correctionThreshold = options.correctionThreshold || -1;
    this.maxCorrectionAttempts = options.maxCorrectionAttempts || 3;
    this.correctionAttempts = new Map();
    this.agents = [];
    this.metrics = {
      cycles: 0,
      corrections: 0,
      lastCorrectionTime: null,
      startTime: null
    };
  }

  /**
   * Register an agent with monitoring and correction capabilities
   */
  registerAgent(agentConfig) {
    const agent = {
      id: agentConfig.id,
      name: agentConfig.name,
      monitor: agentConfig.monitor,      // Function to check health
      correct: agentConfig.correct,      // Function to self-correct
      priority: agentConfig.priority || 1,
      enabled: true
    };
    
    this.agents.push(agent);
    this.stateManager.register(`agent_${agent.id}`, 0);
    this.correctionAttempts.set(agent.id, 0);
    
    console.log(`[NEA] Agent registered: ${agent.name} (${agent.id})`);
    return agent;
  }

  /**
   * Start the autonomous event loop
   */
  start() {
    if (this.isRunning) {
      console.warn('[NEA] Event loop already running');
      return;
    }

    this.isRunning = true;
    this.metrics.startTime = Date.now();
    console.log('[NEA] Agentic Event Loop started');

    this.intervalId = setInterval(() => {
      this._tick();
    }, this.checkInterval);
  }

  /**
   * Stop the event loop
   */
  stop() {
    this.isRunning = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    console.log('[NEA] Agentic Event Loop stopped');
  }

  /**
   * Main loop tick - monitors all agents and triggers corrections
   */
  _tick() {
    this.metrics.cycles++;

    // Monitor each agent
    for (const agent of this.agents) {
      if (!agent.enabled) continue;

      this._monitorAgent(agent);
    }

    // Update global system state
    const globalState = this.stateManager.getGlobalState();
    
    if (globalState.isNegative()) {
      console.warn(`[NEA] System in negative state at cycle ${this.metrics.cycles}`);
    }
  }

  /**
   * Monitor a single agent's health
   */
  _monitorAgent(agent) {
    const result = this.stateManager.handleOperation(() => {
      return agent.monitor();
    }, false);

    const stateKey = `agent_${agent.id}`;
    
    if (result.success && result.value === true) {
      // Agent healthy - positive state
      this.stateManager.update(stateKey, 1);
      this.correctionAttempts.set(agent.id, 0); // Reset attempts
    } else {
      // Agent unhealthy - shift to neutral or negative
      const attempts = this.correctionAttempts.get(agent.id);
      
      if (attempts >= this.maxCorrectionAttempts) {
        // Max attempts reached - negative state
        this.stateManager.update(stateKey, -1);
        console.error(`[NEA] Agent ${agent.name} exceeded correction attempts`);
      } else {
        // Try to correct - neutral state during recovery
        this.stateManager.update(stateKey, 0);
        this._triggerCorrection(agent);
      }
    }
  }

  /**
   * Trigger self-correction for an agent
   */
  _triggerCorrection(agent) {
    const attempts = this.correctionAttempts.get(agent.id);
    this.correctionAttempts.set(agent.id, attempts + 1);
    this.metrics.corrections++;
    this.metrics.lastCorrectionTime = Date.now();

    console.log(`[NEA] Triggering correction for ${agent.name} (attempt ${attempts + 1})`);

    const correctionResult = this.stateManager.handleOperation(() => {
      return agent.correct(attempts);
    }, false);

    if (correctionResult.success && correctionResult.value === true) {
      console.log(`[NEA] Correction successful for ${agent.name}`);
      this.correctionAttempts.set(agent.id, 0);
    } else {
      console.warn(`[NEA] Correction failed for ${agent.name}: ${correctionResult.error || 'Unknown error'}`);
    }
  }

  /**
   * Get current system metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      uptime: this.metrics.startTime ? Date.now() - this.metrics.startTime : 0,
      agentsCount: this.agents.length,
      activeAgents: this.agents.filter(a => a.enabled).length,
      globalState: this.stateManager.getGlobalState().toJSON(),
      allStates: this.stateManager.getAllStates()
    };
  }

  /**
   * Enable/disable specific agent
   */
  setAgentEnabled(agentId, enabled) {
    const agent = this.agents.find(a => a.id === agentId);
    if (agent) {
      agent.enabled = enabled;
      console.log(`[NEA] Agent ${agent.name} ${enabled ? 'enabled' : 'disabled'}`);
    }
  }

  /**
   * Subscribe to system state changes
   */
  onStateChange(callback) {
    return this.stateManager.subscribe(callback);
  }
}

// Example usage and testing
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

if (process.argv[1] === __filename) {
  console.log('=== NEA-Studio Agentic Event Loop Test ===\n');

  const loop = new AgenticEventLoop({ checkInterval: 500 });

  // Register test agents
  loop.registerAgent({
    id: 'memory',
    name: 'Memory Monitor',
    priority: 3,
    monitor: () => {
      // Simulate memory check (90% healthy)
      return Math.random() > 0.1;
    },
    correct: (attempt) => {
      console.log(`  → Correcting memory... attempt ${attempt + 1}`);
      return Math.random() > 0.3; // 70% success rate
    }
  });

  loop.registerAgent({
    id: 'compute',
    name: 'Compute Validator',
    priority: 2,
    monitor: () => {
      // Simulate compute check (95% healthy)
      return Math.random() > 0.05;
    },
    correct: (attempt) => {
      console.log(`  → Correcting compute... attempt ${attempt + 1}`);
      return true; // Always succeeds
    }
  });

  // Subscribe to state changes
  loop.onStateChange((payload) => {
    console.log(`[STATE] ${payload.name}: ${payload.state.state} | Global: ${payload.globalState.state}`);
  });

  // Start the loop
  loop.start();

  // Run for 5 seconds then show metrics
  setTimeout(() => {
    console.log('\n=== Metrics After 5 Seconds ===');
    console.log(JSON.stringify(loop.getMetrics(), null, 2));
    loop.stop();
    console.log('\nTest complete!');
    process.exit(0);
  }, 5000);
}

export { AgenticEventLoop };

/**
 * NEA-Studio: Balanced Ternary State Manager
 * Tier 1: Core State & Logic Engine (Syntropic Foundations)
 * 
 * Implements balanced ternary logic (+1/0/-1) for continuous state flow
 * where exceptions shift the system into neutral/regenerative states
 * rather than breaking execution.
 */

class TernaryState {
  constructor(value = 0) {
    this.setValue(value);
  }

  /**
   * Set ternary value ensuring only -1, 0, or +1
   */
  setValue(value) {
    if (value > 0) this.value = 1;      // Positive
    else if (value < 0) this.value = -1; // Negative  
    else this.value = 0;                 // Neutral
    return this;
  }

  /**
   * Get human-readable state name
   */
  getStateName() {
    const states = {
      '1': 'Positive',
      '0': 'Neutral', 
      '-1': 'Negative'
    };
    return states[this.value] || 'Unknown';
  }

  /**
   * Combine two ternary states using balanced ternary arithmetic
   */
  combine(other) {
    const otherVal = other instanceof TernaryState ? other.value : other;
    let result = this.value + otherVal;
    
    // Balanced ternary carry logic
    if (result > 1) result -= 3;
    if (result < -1) result += 3;
    
    return new TernaryState(result);
  }

  /**
   * Negate the current state
   */
  negate() {
    return new TernaryState(-this.value);
  }

  /**
   * Check if state is neutral (regenerative)
   */
  isNeutral() {
    return this.value === 0;
  }

  /**
   * Check if state is positive (flowing)
   */
  isPositive() {
    return this.value === 1;
  }

  /**
   * Check if state is negative (requires correction)
   */
  isNegative() {
    return this.value === -1;
  }

  toJSON() {
    return {
      value: this.value,
      state: this.getStateName(),
      timestamp: Date.now()
    };
  }
}

class TernaryStateManager {
  constructor() {
    this.states = new Map();
    this.globalState = new TernaryState(0);
    this.listeners = [];
  }

  /**
   * Register a named state
   */
  register(name, initialValue = 0) {
    const state = new TernaryState(initialValue);
    this.states.set(name, state);
    this._notifyChange(name, state);
    return state;
  }

  /**
   * Update a specific state
   */
  update(name, value) {
    if (!this.states.has(name)) {
      throw new Error(`State '${name}' not registered`);
    }
    
    const state = this.states.get(name);
    const oldValue = state.value;
    state.setValue(value);
    
    // Recalculate global state
    this._recalculateGlobalState();
    this._notifyChange(name, state);
    
    return state;
  }

  /**
   * Handle errors by shifting to neutral instead of throwing
   */
  handleOperation(operation, fallbackValue = 0) {
    try {
      const result = operation();
      return { success: true, value: result, state: new TernaryState(1) };
    } catch (error) {
      // Shift to neutral regenerative state instead of failing
      console.warn(`[NEA] Operation shifted to neutral state: ${error.message}`);
      return { 
        success: false, 
        value: fallbackValue, 
        state: new TernaryState(0),
        error: error.message 
      };
    }
  }

  /**
   * Subscribe to state changes
   */
  subscribe(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(l => l !== callback);
    };
  }

  /**
   * Get current global system state
   */
  getGlobalState() {
    return this.globalState;
  }

  /**
   * Get all registered states
   */
  getAllStates() {
    const result = {};
    this.states.forEach((state, name) => {
      result[name] = state.toJSON();
    });
    return result;
  }

  _recalculateGlobalState() {
    let sum = 0;
    this.states.forEach(state => {
      sum += state.value;
    });
    
    // Normalize to ternary range
    if (sum > 0) this.globalState.setValue(1);
    else if (sum < 0) this.globalState.setValue(-1);
    else this.globalState.setValue(0);
  }

  _notifyChange(name, state) {
    const payload = {
      name,
      state: state.toJSON(),
      globalState: this.globalState.toJSON()
    };
    
    this.listeners.forEach(callback => {
      try {
        callback(payload);
      } catch (e) {
        console.error('[NEA] Listener error handled gracefully:', e.message);
      }
    });
  }
}

// Export for both Node.js and browser environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { TernaryState, TernaryStateManager };
} else if (typeof window !== 'undefined') {
  window.TernaryState = TernaryState;
  window.TernaryStateManager = TernaryStateManager;
}

export { TernaryState, TernaryStateManager };

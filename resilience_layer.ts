/**
 * Ride-Along Resilience Layer
 * 
 * Production-grade fault tolerance patterns for the Lattice Orchestrator.
 * Ensures nothing is left unaccounted for during neural mesh operations.
 */

// ============================================================================
// 1. WebSocket Auto-Reconnection & Heartbeat (Keep-Alive)
// ============================================================================

interface ResilientWebSocketOptions {
  reconnectDelay?: number;
  heartbeatInterval?: number;
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
}

class ResilientWebSocket {
  private url: string;
  private ws: WebSocket | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private reconnectDelay: number;
  private heartbeatInterval: number;
  private messageHandlers: Set<(data: any) => void> = new Set();
  private stateHandlers: Set<(state: 'connecting' | 'open' | 'closed' | 'error') => void> = new Set();
  
  constructor(url: string, options: ResilientWebSocketOptions = {}) {
    this.url = url;
    this.reconnectDelay = options.reconnectDelay || 3000;
    this.heartbeatInterval = options.heartbeatInterval || 30000;
    
    if (options.onMessage) {
      this.messageHandlers.add(options.onMessage);
    }
    
    this.connect();
  }

  private connect(): void {
    this.notifyState('connecting');
    console.log(`[ResilientWS] Connecting to ${this.url}...`);
    
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('[ResilientWS] Connection established');
        this.notifyState('open');
        
        // Start heartbeat
        this.pingInterval = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'PING', timestamp: Date.now() }));
          }
        }, this.heartbeatInterval);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle pong responses
          if (data.type === 'PONG') {
            console.log('[ResilientWS] Heartbeat acknowledged');
            return;
          }
          
          this.messageHandlers.forEach(handler => handler(data));
        } catch (e) {
          console.warn('[ResilientWS] Non-JSON message:', event.data);
          this.messageHandlers.forEach(handler => handler(event.data));
        }
      };

      this.ws.onclose = () => {
        console.warn(`[ResilientWS] Connection closed. Reconnecting in ${this.reconnectDelay}ms...`);
        this.notifyState('closed');
        
        if (this.pingInterval) {
          clearInterval(this.pingInterval);
          this.pingInterval = null;
        }
        
        this.ws = null;
        setTimeout(() => this.connect(), this.reconnectDelay);
      };

      this.ws.onerror = (error) => {
        console.error('[ResilientWS] Socket error:', error);
        this.notifyState('error');
      };
      
    } catch (error) {
      console.error('[ResilientWS] Failed to create socket:', error);
      setTimeout(() => this.connect(), this.reconnectDelay);
    }
  }

  public send(data: any): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(typeof data === 'string' ? data : JSON.stringify(data));
      return true;
    }
    console.warn('[ResilientWS] Cannot send - socket not open');
    return false;
  }

  public onMessage(handler: (data: any) => void): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  public onStateChange(handler: (state: 'connecting' | 'open' | 'closed' | 'error') => void): () => void {
    this.stateHandlers.add(handler);
    return () => this.stateHandlers.delete(handler);
  }

  private notifyState(state: 'connecting' | 'open' | 'closed' | 'error'): void {
    this.stateHandlers.forEach(handler => handler(state));
  }

  public close(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  public getState(): 'connecting' | 'open' | 'closed' | 'error' {
    if (!this.ws) return 'closed';
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'open';
      case WebSocket.CLOSING: return 'closed';
      case WebSocket.CLOSED: return 'closed';
      default: return 'error';
    }
  }
}

// ============================================================================
// 2. Circuit Breaker Pattern
// ============================================================================

type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

interface CircuitBreakerOptions {
  threshold?: number;
  timeout?: number;
  halfOpenRequests?: number;
  onStateChange?: (state: CircuitState, failures: number) => void;
}

class CircuitBreaker<T extends (...args: any[]) => Promise<any>> {
  private fn: T;
  private failures: number = 0;
  private successes: number = 0;
  private threshold: number;
  private timeout: number;
  private state: CircuitState = 'CLOSED';
  private nextTry: number = 0;
  private halfOpenMax: number;
  private halfOpenRequests: number = 0;
  private onStateChange?: (state: CircuitState, failures: number) => void;

  constructor(fn: T, options: CircuitBreakerOptions = {}) {
    this.fn = fn;
    this.threshold = options.threshold || 3;
    this.timeout = options.timeout || 10000;
    this.halfOpenMax = options.halfOpenRequests || 1;
    this.onStateChange = options.onStateChange;
  }

  async call(...args: Parameters<T>): Promise<ReturnType<T>> {
    if (this.state === 'OPEN') {
      if (Date.now() >= this.nextTry) {
        this.state = 'HALF_OPEN';
        this.halfOpenRequests = 0;
        console.log('[CircuitBreaker] Entering HALF_OPEN state');
        this.onStateChange?.('HALF_OPEN', this.failures);
      } else {
        const waitTime = Math.ceil((this.nextTry - Date.now()) / 1000);
        throw new Error(`[CircuitBreaker] OPEN - Fast-failing. Retry in ${waitTime}s`);
      }
    }

    if (this.state === 'HALF_OPEN' && this.halfOpenRequests >= this.halfOpenMax) {
      throw new Error('[CircuitBreaker] HALF_OPEN - Max concurrent test requests reached');
    }

    this.halfOpenRequests++;

    try {
      const result = await this.fn(...args);
      this.recordSuccess();
      return result;
    } catch (error) {
      this.recordFailure();
      throw error;
    }
  }

  private recordSuccess(): void {
    this.failures = 0;
    this.successes++;
    
    if (this.state === 'HALF_OPEN') {
      this.state = 'CLOSED';
      console.log('[CircuitBreaker] Circuit CLOSED after successful test');
      this.onStateChange?.('CLOSED', this.failures);
    }
  }

  private recordFailure(): void {
    this.failures++;
    
    if (this.state === 'HALF_OPEN') {
      this.state = 'OPEN';
      this.nextTry = Date.now() + this.timeout;
      console.log('[CircuitBreaker] Circuit re-opened from HALF_OPEN');
      this.onStateChange?.('OPEN', this.failures);
    } else if (this.failures >= this.threshold) {
      this.state = 'OPEN';
      this.nextTry = Date.now() + this.timeout;
      console.log(`[CircuitBreaker] Circuit OPEN after ${this.failures} failures`);
      this.onStateChange?.('OPEN', this.failures);
    }
  }

  getState(): CircuitState {
    if (this.state === 'OPEN' && Date.now() >= this.nextTry) {
      return 'HALF_OPEN';
    }
    return this.state;
  }

  getStats(): { failures: number; successes: number; state: CircuitState } {
    return {
      failures: this.failures,
      successes: this.successes,
      state: this.getState()
    };
  }

  reset(): void {
    this.failures = 0;
    this.successes = 0;
    this.state = 'CLOSED';
    this.nextTry = 0;
    console.log('[CircuitBreaker] Manually reset');
    this.onStateChange?.('CLOSED', 0);
  }
}

// ============================================================================
// 3. Exponential Backoff Retry Engine
// ============================================================================

interface RetryOptions {
  retries?: number;
  baseDelay?: number;
  maxDelay?: number;
  jitter?: boolean;
  shouldRetry?: (error: Error, attempt: number) => boolean;
}

async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const {
    retries = 3,
    baseDelay = 1000,
    maxDelay = 30000,
    jitter = true,
    shouldRetry
  } = options;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      // Check if we should retry
      if (shouldRetry && !shouldRetry(lastError, attempt)) {
        console.log(`[RetryEngine] Not retrying: ${lastError.message}`);
        throw lastError;
      }

      if (attempt === retries) {
        console.log(`[RetryEngine] Max retries (${retries}) exhausted`);
        throw lastError;
      }

      // Calculate delay with exponential backoff
      const exponentialDelay = baseDelay * Math.pow(2, attempt);
      const delay = Math.min(exponentialDelay, maxDelay);
      
      // Add jitter to prevent thundering herd
      const finalDelay = jitter 
        ? delay * (0.5 + Math.random() * 0.5) 
        : delay;

      console.warn(
        `[RetryEngine] Attempt ${attempt + 1}/${retries + 1} failed. ` +
        `Retrying in ${Math.round(finalDelay)}ms. Error: ${lastError.message}`
      );

      await new Promise(resolve => setTimeout(resolve, finalDelay));
    }
  }

  throw lastError;
}

// Convenience wrapper for fetch
async function fetchWithRetry(
  url: string,
  options: RequestInit & RetryOptions = {},
  retryOptions?: RetryOptions
): Promise<Response> {
  const { retries, baseDelay, maxDelay, jitter, shouldRetry, ...fetchOptions } = options;

  return retryWithBackoff(async () => {
    const response = await fetch(url, fetchOptions);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response;
  }, { retries, baseDelay, maxDelay, jitter, shouldRetry });
}

// ============================================================================
// 4. Sandbox Exception Boundary
// ============================================================================

interface SandboxMetrics {
  unhandledRejections: number;
  uncaughtErrors: number;
  lastError?: {
    type: 'rejection' | 'error';
    message: string;
    timestamp: number;
    stack?: string;
  };
}

class SandboxBoundary {
  private metrics: SandboxMetrics = {
    unhandledRejections: 0,
    uncaughtErrors: 0
  };
  
  private errorLog: Array<{
    type: 'rejection' | 'error';
    message: string;
    timestamp: number;
    stack?: string;
    context?: any;
  }> = [];

  private maxLogSize: number = 100;
  private onCriticalError?: (error: any, type: 'rejection' | 'error') => void;

  constructor(options?: { 
    maxLogSize?: number;
    onCriticalError?: (error: any, type: 'rejection' | 'error') => void;
  }) {
    if (options) {
      this.maxLogSize = options.maxLogSize || 100;
      this.onCriticalError = options.onCriticalError;
    }
    
    this.install();
  }

  private install(): void {
    // Intercept unhandled promise rejections
    window.addEventListener('unhandledrejection', event => {
      this.metrics.unhandledRejections++;
      
      const errorInfo = {
        type: 'rejection' as const,
        message: event.reason?.message || String(event.reason),
        timestamp: Date.now(),
        stack: event.reason?.stack,
        context: { reason: event.reason }
      };

      this.logError(errorInfo);
      
      // Prevent default browser error propagation
      event.preventDefault();
      
      console.warn('[SandboxBoundary] Intercepted unhandled rejection:', event.reason);
      
      if (this.onCriticalError) {
        this.onCriticalError(event.reason, 'rejection');
      }
    });

    // Intercept uncaught errors
    window.addEventListener('error', event => {
      this.metrics.uncaughtErrors++;
      
      const errorInfo = {
        type: 'error' as const,
        message: event.message,
        timestamp: Date.now(),
        stack: event.error?.stack,
        context: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno
        }
      };

      this.logError(errorInfo);
      
      console.warn('[SandboxBoundary] Intercepted uncaught error:', event.message);
      
      if (this.onCriticalError) {
        this.onCriticalError(event.error || event.message, 'error');
      }
    });

    console.log('[SandboxBoundary] Exception boundary installed');
  }

  private logError(errorInfo: {
    type: 'rejection' | 'error';
    message: string;
    timestamp: number;
    stack?: string;
    context?: any;
  }): void {
    this.metrics.lastError = {
      type: errorInfo.type,
      message: errorInfo.message,
      timestamp: errorInfo.timestamp,
      stack: errorInfo.stack
    };

    this.errorLog.push(errorInfo);
    
    // Trim log if exceeds max size
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(-this.maxLogSize);
    }
  }

  getMetrics(): SandboxMetrics {
    return { ...this.metrics };
  }

  getErrorLog(): typeof this.errorLog {
    return [...this.errorLog];
  }

  clearLog(): void {
    this.errorLog = [];
    console.log('[SandboxBoundary] Error log cleared');
  }

  wrap<T extends (...args: any[]) => any>(
    fn: T,
    fallback?: () => ReturnType<T>
  ): (...args: Parameters<T>) => ReturnType<T> | undefined {
    return (...args: Parameters<T>): ReturnType<T> | undefined => {
      try {
        return fn(...args);
      } catch (error) {
        console.error('[SandboxBoundary] Caught error in wrapped function:', error);
        
        this.logError({
          type: 'error',
          message: error instanceof Error ? error.message : String(error),
          timestamp: Date.now(),
          stack: error instanceof Error ? error.stack : undefined
        });

        if (fallback) {
          return fallback();
        }
        
        return undefined;
      }
    };
  }

  async wrapAsync<T extends (...args: any[]) => Promise<any>>(
    fn: T,
    fallback?: () => Promise<ReturnType<T>>
  ): Promise<ReturnType<T> | undefined> {
    try {
      return await fn();
    } catch (error) {
      console.error('[SandboxBoundary] Caught error in wrapped async function:', error);
      
      this.logError({
        type: 'rejection',
        message: error instanceof Error ? error.message : String(error),
        timestamp: Date.now(),
        stack: error instanceof Error ? error.stack : undefined
      });

      if (fallback) {
        return fallback();
      }
      
      return undefined;
    }
  }
}

// ============================================================================
// Export All Resilience Patterns
// ============================================================================

export {
  ResilientWebSocket,
  CircuitBreaker,
  retryWithBackoff,
  fetchWithRetry,
  SandboxBoundary
};

export type {
  ResilientWebSocketOptions,
  CircuitBreakerOptions,
  RetryOptions,
  CircuitState,
  SandboxMetrics
};

// ============================================================================
// Quick Usage Example
// ============================================================================

/*
// 1. Resilient WebSocket
const ws = new ResilientWebSocket('wss://lattice.example.com/socket', {
  onMessage: (data) => console.log('Received:', data),
  heartbeatInterval: 30000
});

ws.onStateChange((state) => {
  console.log('WebSocket state:', state);
});

ws.send({ type: 'SUBSCRIBE', channel: 'lattice-updates' });


// 2. Circuit Breaker for AI Facet Calls
const visionService = new CircuitBreaker(
  async (image: Uint8Array) => {
    const response = await fetch('/api/vision/analyze', {
      method: 'POST',
      body: image
    });
    return response.json();
  },
  { threshold: 3, timeout: 15000 }
);

try {
  const result = await visionService.call(imageData);
  console.log('Vision analysis:', result);
} catch (error) {
  console.error('Vision service unavailable:', error);
}


// 3. Retry with Exponential Backoff
const config = await retryWithBackoff(
  async () => {
    const response = await fetch('/api/config');
    if (!response.ok) throw new Error('Config fetch failed');
    return response.json();
  },
  { retries: 5, baseDelay: 1000, jitter: true }
);


// 4. Sandbox Boundary
const sandbox = new SandboxBoundary({
  onCriticalError: (error, type) => {
    console.error(`Critical ${type}:`, error);
    // Send to monitoring service
  }
});

// Wrap risky operations
const safeOperation = sandbox.wrap(
  () => riskyFunction(),
  () => defaultValue
);

const safeAsyncOperation = sandbox.wrapAsync(
  () => riskyAsyncFunction(),
  () => Promise.resolve(defaultValue)
);
*/

// ============================================================================
// 5. Child-First Life-First Protocol (Pediatric Oncology Priority)
// ============================================================================

/**
 * Invoice interface for medical billing simulation
 */
interface MedicalInvoice {
  invoice_id: string;
  patient_age: number;
  diagnosis: string;
  category: 'pediatric_oncology' | 'general_care' | 'elder_care' | 'trauma' | string;
  amount_usd: number;
  status: 'outstanding' | 'paid' | 'processing';
  priority_flag: 'LIFE_FIRST' | 'HIGH' | 'STANDARD';
}

/**
 * Surplus flow allocation result
 */
interface AllocationResult {
  invoice_id: string;
  amount_allocated: number;
  remaining_balance: number;
  status: 'paid' | 'partial' | 'pending';
  priority_level: 'LIFE_FIRST' | 'HIGH' | 'STANDARD';
  timestamp: number;
}

/**
 * Life-First Surplus Allocator
 * 
 * Implements child-first activation logic: pediatric oncology bills
 * are always prioritized before any other surplus distribution.
 * 
 * Priority Order:
 * 1. LIFE_FIRST (pediatric oncology) - MUST be cleared first
 * 2. HIGH (trauma, emergency) - Cleared after children stabilized
 * 3. STANDARD (general care, elder care) - Cleared last
 */
class LifeFirstAllocator {
  private invoices: MedicalInvoice[] = [];
  private allocationLog: AllocationResult[] = [];
  private totalSurplusAvailable: number = 0;
  private cascadeMode: 'children_only' | 'all_patients_us' | 'global' = 'children_only';

  /**
   * Load invoices from dataset (synthetic or real API integration)
   */
  loadInvoices(invoices: MedicalInvoice[]): void {
    this.invoices = [...invoices];
    console.log(`[LifeFirst] Loaded ${invoices.length} invoices into detection layer`);
  }

  /**
   * Add surplus funds to the pool for distribution
   */
  addSurplus(amount: number): void {
    this.totalSurplusAvailable += amount;
    console.log(`[LifeFirst] Surplus pool updated: $${this.totalSurplusAvailable.toLocaleString()}`);
    // Auto-trigger neutralization when surplus is added
    this.neutralizeOutstandingBills();
  }

  /**
   * Priority sorting: LIFE_FIRST > HIGH > STANDARD
   * Within same priority: lower patient age first (children prioritized)
   */
  private sortByPriority(invoices: MedicalInvoice[]): MedicalInvoice[] {
    const priorityOrder: Record<string, number> = {
      'LIFE_FIRST': 0,
      'HIGH': 1,
      'STANDARD': 2
    };

    return invoices.sort((a, b) => {
      // First sort by priority flag
      const priorityDiff = priorityOrder[a.priority_flag] - priorityOrder[b.priority_flag];
      if (priorityDiff !== 0) return priorityDiff;
      
      // Within same priority, sort by age (younger first)
      return a.patient_age - b.patient_age;
    });
  }

  /**
   * Silent Redistribution: Automatically detect and dissolve bills
   * No bureaucracy, no application needed - invisible absorption
   */
  neutralizeOutstandingBills(): AllocationResult[] {
    const outstanding = this.invoices.filter(inv => inv.status === 'outstanding');
    
    if (outstanding.length === 0) {
      console.log('[LifeFirst] No outstanding bills to neutralize');
      return [];
    }

    // Sort by child-first priority
    const sorted = this.sortByPriority(outstanding);
    const results: AllocationResult[] = [];
    let remainingSurplus = this.totalSurplusAvailable;

    console.log(`[LifeFirst] Processing ${sorted.length} outstanding bills with $${remainingSurplus.toLocaleString()} surplus`);

    for (const invoice of sorted) {
      // Cascade expansion check: skip non-children if in children_only mode and children still have bills
      if (this.cascadeMode === 'children_only' && invoice.category !== 'pediatric_oncology') {
        const childrenStillHaveBills = sorted.some(
          inv => inv.category === 'pediatric_oncology' && inv.status === 'outstanding'
        );
        if (childrenStillHaveBills) {
          console.log(`[LifeFirst] Deferring ${invoice.invoice_id} (${invoice.category}) - children's bills pending`);
          continue;
        }
      }

      if (remainingSurplus <= 0) break;

      const allocation = Math.min(invoice.amount_usd, remainingSurplus);
      const newStatus: 'paid' | 'processing' = allocation >= invoice.amount_usd ? 'paid' : 'processing';
      
      // Update invoice status
      invoice.status = newStatus;
      invoice.amount_usd -= allocation;
      remainingSurplus -= allocation;

      const result: AllocationResult = {
        invoice_id: invoice.invoice_id,
        amount_allocated: allocation,
        remaining_balance: invoice.amount_usd,
        status: newStatus === 'paid' ? 'paid' : 'partial',
        priority_level: invoice.priority_flag,
        timestamp: Date.now()
      };

      this.allocationLog.push(result);
      results.push(result);

      console.log(`[LifeFirst] Neutralized ${invoice.invoice_id}: $${allocation.toLocaleString()} allocated to ${invoice.diagnosis} (Age ${invoice.patient_age})`);
    }

    this.totalSurplusAvailable = remainingSurplus;
    
    if (results.length > 0) {
      console.log(`[LifeFirst] Batch complete: ${results.length} bills processed, $${(this.getTotalAllocated(results)).toLocaleString()} distributed`);
    }

    return results;
  }

  private getTotalAllocated(results: AllocationResult[]): number {
    return results.reduce((sum, r) => sum + r.amount_allocated, 0);
  }

  /**
   * Get audit trail of all allocations (traceable and reproducible)
   */
  getAuditTrail(): AllocationResult[] {
    return [...this.allocationLog];
  }

  /**
   * Get current status of all invoices
   */
  getInvoiceStatus(): MedicalInvoice[] {
    return [...this.invoices];
  }

  /**
   * Expand cascade: move from children_only to broader pools
   */
  expandCascade(mode: 'children_only' | 'all_patients_us' | 'global'): void {
    const previousMode = this.cascadeMode;
    this.cascadeMode = mode;
    console.log(`[LifeFirst] Cascade expanded: ${previousMode} → ${mode}`);
    
    // Re-trigger neutralization with new scope
    if (this.totalSurplusAvailable > 0) {
      this.neutralizeOutstandingBills();
    }
  }

  /**
   * Check if all LIFE_FIRST (pediatric oncology) bills are cleared
   */
  areChildrenStabilized(): boolean {
    const lifeFirstOutstanding = this.invoices.some(
      inv => inv.priority_flag === 'LIFE_FIRST' && inv.status === 'outstanding'
    );
    return !lifeFirstOutstanding;
  }

  /**
   * Export allocation report for compliance auditing
   */
  exportReport(): {
    summary: {
      total_invoices: number;
      paid_count: number;
      outstanding_count: number;
      total_distributed: number;
      children_stabilized: boolean;
      cascade_mode: string;
    };
    allocations: AllocationResult[];
    timestamp: string;
  } {
    const paid = this.invoices.filter(inv => inv.status === 'paid').length;
    const outstanding = this.invoices.filter(inv => inv.status === 'outstanding').length;
    
    return {
      summary: {
        total_invoices: this.invoices.length,
        paid_count: paid,
        outstanding_count: outstanding,
        total_distributed: this.getTotalAllocated(this.allocationLog),
        children_stabilized: this.areChildrenStabilized(),
        cascade_mode: this.cascadeMode
      },
      allocations: this.getAuditTrail(),
      timestamp: new Date().toISOString()
    };
  }
}

// ============================================================================
// Example Usage & Simulation
// ============================================================================

/**
 * Simulate child-first activation with synthetic billing data
 * 
 * This demonstrates the architecture can prioritize children with cancer
 * without needing unauthorized access to hospital systems.
 */
/*
async function runChildFirstSimulation() {
  // Load synthetic bills (in production, this would come from hospital API integration)
  const syntheticBills: MedicalInvoice[] = await loadSyntheticBills('synthetic_bills.json');
  
  // Initialize allocator with child-first hardcoded priority
  const allocator = new LifeFirstAllocator();
  allocator.loadInvoices(syntheticBills);
  
  // Simulate surplus flows from synthetic throughput (9M+ events/sec validated)
  const simulatedSurplus = 600000; // $600K surplus available
  
  console.log('\\n[LifeFirst] === CHILD-FIRST ACTIVATION SIMULATION ===');
  console.log(`[LifeFirst] Initial surplus: $${simulatedSurplus.toLocaleString()}\\n`);
  
  // Trigger silent redistribution
  allocator.addSurplus(simulatedSurplus);
  
  // Verify children stabilized first
  const childrenStabilized = allocator.areChildrenStabilized();
  console.log(`\\n[LifeFirst] Children stabilized: ${childrenStabilized}`);
  
  // Export audit trail for compliance
  const report = allocator.exportReport();
  console.log('[LifeFirst] Audit report generated:', JSON.stringify(report.summary, null, 2));
  
  // If children are stabilized, expand cascade
  if (childrenStabilized) {
    console.log('\\n[LifeFirst] Expanding cascade to all patients...');
    allocator.expandCascade('all_patients_us');
  }
  
  return report;
}

// Run simulation
runChildFirstSimulation().catch(console.error);
*/

export { LifeFirstAllocator, MedicalInvoice, AllocationResult };

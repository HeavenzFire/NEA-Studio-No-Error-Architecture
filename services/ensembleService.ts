
import { formalizeSpec as geminiFormalize } from './geminiService';
import { formalizeSpec as qwenFormalize } from './qwenService';

export interface SpecResult {
  moduleName: string;
  formalLogic: string;
  invariants: Array<{
    property: string;
    definition: string;
    safetyCritical: boolean;
  }>;
  preemptionStrategy: string;
  summary: string;
  source: 'gemini' | 'qwen' | 'ensemble';
  confidence?: number;
}

export interface EnsembleResult {
  consensus: SpecResult;
  geminiResult: SpecResult;
  qwenResult: SpecResult;
  votingDetails: {
    agreements: string[];
    disagreements: string[];
    resolution: string;
  };
}

/**
 * Run both LLMs in parallel and return individual results
 */
export const runParallelInference = async (description: string): Promise<{ gemini: SpecResult; qwen: SpecResult }> => {
  const [geminiResult, qwenResult] = await Promise.allSettled([
    geminiFormalize(description).then(r => ({ ...r, source: 'gemini' as const })),
    qwenFormalize(description).then(r => ({ ...r, source: 'qwen' as const }))
  ]);

  if (geminiResult.status === 'rejected' && qwenResult.status === 'rejected') {
    throw new Error('Both LLM endpoints failed');
  }

  return {
    gemini: geminiResult.status === 'fulfilled' ? geminiResult.value : null as any,
    qwen: qwenResult.status === 'fulfilled' ? qwenResult.value : null as any
  };
};

/**
 * Compare two spec results and identify agreements/disagreements
 */
const compareSpecs = (a: SpecResult, b: SpecResult) => {
  const agreements: string[] = [];
  const disagreements: string[] = [];

  // Compare module names
  if (a.moduleName === b.moduleName) {
    agreements.push(`moduleName: ${a.moduleName}`);
  } else {
    disagreements.push(`moduleName: "${a.moduleName}" vs "${b.moduleName}"`);
  }

  // Compare preemption strategies
  if (a.preemptionStrategy === b.preemptionStrategy) {
    agreements.push(`preemptionStrategy: ${a.preemptionStrategy}`);
  } else {
    disagreements.push(`preemptionStrategy divergence detected`);
  }

  // Compare invariant count and safety-critical flags
  const aSafetyCount = a.invariants.filter(i => i.safetyCritical).length;
  const bSafetyCount = b.invariants.filter(i => i.safetyCritical).length;
  
  if (aSafetyCount === bSafetyCount) {
    agreements.push(`safetyCritical invariants count: ${aSafetyCount}`);
  } else {
    disagreements.push(`safetyCritical count: ${aSafetyCount} vs ${bSafetyCount}`);
  }

  // Compare formal logic similarity (simple length-based heuristic)
  const logicLenDiff = Math.abs(a.formalLogic.length - b.formalLogic.length);
  if (logicLenDiff < 50) {
    agreements.push('formalLogic structure similar');
  } else {
    disagreements.push('formalLogic structure divergent');
  }

  return { agreements, disagreements };
};

/**
 * Ensemble voting: Run both models and produce consensus spec
 */
export const runEnsembleFormalization = async (description: string): Promise<EnsembleResult> => {
  const parallel = await runParallelInference(description);
  
  const { gemini, qwen } = parallel;
  const comparison = compareSpecs(gemini, qwen);

  // Consensus building: prefer Gemini for formal logic, Qwen for invariants if more comprehensive
  const consensusInvariants = qwen.invariants.length > gemini.invariants.length 
    ? qwen.invariants 
    : gemini.invariants;

  const consensus: SpecResult = {
    moduleName: gemini.moduleName, // Default to Gemini
    formalLogic: gemini.formalLogic, // Prefer Gemini's formal logic
    invariants: consensusInvariants,
    preemptionStrategy: comparison.agreements.length > comparison.disagreements.length
      ? gemini.preemptionStrategy // Use common strategy if agreed
      : `${gemini.preemptionStrategy}; ${qwen.preemptionStrategy}`, // Combine if divergent
    summary: `${gemini.summary} [Ensemble: Gemini+Qwen consensus]`,
    source: 'ensemble',
    confidence: comparison.agreements.length / (comparison.agreements.length + comparison.disagreements.length || 1)
  };

  return {
    consensus,
    geminiResult: gemini,
    qwenResult: qwen,
    votingDetails: {
      agreements: comparison.agreements,
      disagreements: comparison.disagreements,
      resolution: comparison.disagreements.length === 0 
        ? 'Full consensus achieved' 
        : `Resolved ${comparison.disagreements.length} divergence(s) via ensemble policy`
    }
  };
};

/**
 * Get best result from either model based on invariant coverage
 */
export const getBestSingleResult = async (description: string): Promise<SpecResult> => {
  const parallel = await runParallelInference(description);
  
  return parallel.qwen.invariants.length > parallel.gemini.invariants.length
    ? parallel.qwen
    : parallel.gemini;
};

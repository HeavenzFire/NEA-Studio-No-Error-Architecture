#!/usr/bin/env node

/**
 * Mesh Review Pipeline - Ensemble Spec Runner
 * Executes dual-LLM formalization and outputs consensus results
 */

import { runEnsembleFormalization } from '../services/ensembleService.js';
import { writeFileSync } from 'fs';

const TEST_DESCRIPTION = `
A distributed work admission system that uses bounded control theory 
to refuse incoming requests when internal state invariants approach violation thresholds.
The system must maintain syntropy above 0.7 and never admit work that would cause 
state drift beyond the operational manifold.
`;

async function runReview() {
  console.log('🔷 Mesh Review Pipeline - Starting Ensemble Formalization\n');
  console.log(`Input: ${TEST_DESCRIPTION.trim()}\n`);

  try {
    const result = await runEnsembleFormalization(TEST_DESCRIPTION);

    // Output to GitHub Actions summary
    console.log('## 🧠 Dual-LLM Ensemble Results\n');
    
    console.log('### Gemini Result');
    console.log(`- **Module**: ${result.geminiResult.moduleName}`);
    console.log(`- **Invariants**: ${result.geminiResult.invariants.length} (${result.geminiResult.invariants.filter(i => i.safetyCritical).length} safety-critical)`);
    console.log(`- **Summary**: ${result.geminiResult.summary}\n`);

    console.log('### Qwen Result');
    console.log(`- **Module**: ${result.qwenResult.moduleName}`);
    console.log(`- **Invariants**: ${result.qwenResult.invariants.length} (${result.qwenResult.invariants.filter(i => i.safetyCritical).length} safety-critical)`);
    console.log(`- **Summary**: ${result.qwenResult.summary}\n`);

    console.log('### 🎯 Consensus Spec');
    console.log(`- **Module**: ${result.consensus.moduleName}`);
    console.log(`- **Confidence**: ${(result.consensus.confidence * 100).toFixed(1)}%`);
    console.log(`- **Resolution**: ${result.votingDetails.resolution}\n`);

    console.log('### Voting Details');
    console.log('**Agreements**:');
    result.votingDetails.agreements.forEach(a => console.log(`- ✅ ${a}`));
    console.log('\n**Disagreements**:');
    result.votingDetails.disagreements.forEach(d => console.log(`- ⚠️ ${d}`));

    console.log('\n### Formal Logic (Consensus)');
    console.log('```tla');
    console.log(result.consensus.formalLogic);
    console.log('```\n');

    // Write artifacts for upload
    writeFileSync('review-output.json', JSON.stringify(result, null, 2));
    writeFileSync('consensus-spec.json', JSON.stringify(result.consensus, null, 2));

    console.log('\n✅ Artifacts written: review-output.json, consensus-spec.json');
    console.log('📡 Cortex Signal Bus: Telemetry active');

  } catch (error) {
    console.error('❌ Ensemble formalization failed:', error.message);
    console.error('\n⚠️ Ensure GEMINI_API_KEY and QWEN_API_KEY are set in environment/secrets');
    process.exit(1);
  }
}

runReview();

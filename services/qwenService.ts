
import { chat } from "dashscope";

export const formalizeSpec = async (description: string) => {
  const response = await chat({
    messages: [
      {
        role: "system",
        content: `You are a Formal Methods Engineer. Convert the following system description into a Formal Invariance Specification.
    
    Use TLA+ style logic for the 'formalLogic' field.
    Focus on:
    1. Type Invariants (Variables and their domains).
    2. Safety Properties (What must never happen).
    3. Transition Relations (Atomic state changes).
    
    Respond with valid JSON matching this schema:
    {
      "moduleName": string,
      "formalLogic": string,
      "invariants": [{"property": string, "definition": string, "safetyCritical": boolean}],
      "preemptionStrategy": string,
      "summary": string
    }`
      },
      {
        role: "user",
        content: description
      }
    ]
  });

  const result = JSON.parse(response.output?.text || "{}");
  
  // Ensure schema compatibility with Gemini output
  return {
    moduleName: result.moduleName || "QwenDerivedModule",
    formalLogic: result.formalLogic || "",
    invariants: result.invariants || [],
    preemptionStrategy: result.preemptionStrategy || "",
    summary: result.summary || ""
  };
};

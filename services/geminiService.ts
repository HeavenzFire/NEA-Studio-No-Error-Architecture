
import { GoogleGenAI, Type } from "@google/genai";

const getAI = () => new GoogleGenAI({ apiKey: process.env.API_KEY });

export const formalizeSpec = async (description: string) => {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: "gemini-3-pro-preview",
    contents: `You are a Formal Methods Engineer. Convert the following system description into a Formal Invariance Specification.
    
    Use TLA+ style logic for the 'formalLogic' field.
    Focus on:
    1. Type Invariants (Variables and their domains).
    2. Safety Properties (What must never happen).
    3. Transition Relations (Atomic state changes).
    
    Description: ${description}`,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          moduleName: { type: Type.STRING },
          formalLogic: { type: Type.STRING, description: "TLA+ or formal logic block." },
          invariants: { type: Type.ARRAY, items: { 
            type: Type.OBJECT,
            properties: {
              property: { type: Type.STRING },
              definition: { type: Type.STRING },
              safetyCritical: { type: Type.BOOLEAN }
            }
          }},
          preemptionStrategy: { type: Type.STRING, description: "How to refuse work to maintain invariants." },
          summary: { type: Type.STRING }
        },
        required: ["moduleName", "formalLogic", "invariants", "preemptionStrategy", "summary"]
      }
    }
  });

  return JSON.parse(response.text);
};

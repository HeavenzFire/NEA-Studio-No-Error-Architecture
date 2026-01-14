
import { GoogleGenAI, Type } from "@google/genai";

const getAI = () => new GoogleGenAI({ apiKey: process.env.API_KEY });

export const formalizeSpec = async (description: string) => {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: "gemini-3-pro-preview",
    contents: `You are a Senior Systems Architect specializing in No-Error Architecture (NEA). 
    Your goal is to convert an informal system description into a formal NEA Specification.
    
    NEA principles:
    1. Replace Exceptions with Refusals (Pre-admission validation).
    2. Total State Transitions (Atomic/Complete).
    3. Constraints as First-Class Logic.
    4. Collapse Observation and Control.
    
    Description: ${description}`,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          systemName: { type: Type.STRING },
          refusalLogic: { type: Type.STRING, description: "Detailed admission control rules." },
          atomicTransitions: { type: Type.ARRAY, items: { type: Type.STRING }, description: "List of valid total transitions." },
          constraints: { type: Type.ARRAY, items: { 
            type: Type.OBJECT,
            properties: {
              metric: { type: Type.STRING },
              boundary: { type: Type.STRING },
              controlMechanism: { type: Type.STRING }
            }
          }},
          summary: { type: Type.STRING }
        },
        required: ["systemName", "refusalLogic", "atomicTransitions", "constraints", "summary"]
      },
      thinkingConfig: { thinkingBudget: 1000 }
    }
  });

  return JSON.parse(response.text);
};

export const analyzeLineByLine = async (code: string) => {
  const ai = getAI();
  const response = await ai.models.generateContent({
    model: "gemini-3-pro-preview",
    contents: `Analyze this code and suggest how to remove exception handling and replace it with NEA Refusals and Deterministic paths.
    
    Code:
    ${code}`,
    config: {
      systemInstruction: "Identify 'try-catch' blocks and 'if (error)' checks. Suggest atomic transition alternatives."
    }
  });
  
  return response.text;
};

/**
 * useDebate Hook
 * Manages the AI debate pipeline execution and progress tracking.
 */

import { useState, useCallback } from "react";
import api from "../lib/api";

export interface DebateResult {
  market_id: string;
  predikt: number;
  confidence: number;
  validators: {
    model: string;
    prediction: number;
    score: number;
    challenged: boolean;
    reasoning_preview: string;
  }[];
  debate_rounds: number;
  total_challenges: number;
  status: string;
}

const DEBATE_STEPS = [
  "Initializing AI validators...",
  "Generating independent predictions...",
  "Running debate round 1...",
  "Cross-examining reasoning...",
  "Running debate round 2...",
  "Scoring reasoning quality...",
  "Computing intelligence-weighted predikt...",
  "Building reasoning tree...",
  "Finalizing on-chain...",
];

export function useDebate() {
  const [isDebating, setIsDebating] = useState(false);
  const [currentStep, setCurrentStep] = useState("");
  const [stepIndex, setStepIndex] = useState(0);
  const [result, setResult] = useState<DebateResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runDebate = useCallback(
    async (
      marketId: string,
      context?: string,
      onProgress?: (step: string, index: number) => void
    ) => {
      setIsDebating(true);
      setError(null);
      setResult(null);

      try {
        // Animate through steps while API call runs
        const stepPromise = (async () => {
          for (let i = 0; i < DEBATE_STEPS.length; i++) {
            setCurrentStep(DEBATE_STEPS[i]);
            setStepIndex(i);
            onProgress?.(DEBATE_STEPS[i], i);
            await new Promise((r) =>
              setTimeout(r, 600 + Math.random() * 800)
            );
          }
        })();

        // Actual API call
        const apiPromise = api.runDebate(marketId, context);

        // Wait for both
        const [, debateResult] = await Promise.all([stepPromise, apiPromise]);

        setResult(debateResult);
        return debateResult;
      } catch (err: any) {
        setError(err.message);
        return null;
      } finally {
        setIsDebating(false);
        setCurrentStep("");
        setStepIndex(0);
      }
    },
    []
  );

  return {
    isDebating,
    currentStep,
    stepIndex,
    totalSteps: DEBATE_STEPS.length,
    result,
    error,
    runDebate,
  };
}

export default useDebate;

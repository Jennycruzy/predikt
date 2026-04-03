/**
 * useMarkets Hook
 * Manages market state, creation, and listing.
 * In production, syncs with on-chain state via wagmi.
 * For demo, manages local + API state.
 */

import { useState, useCallback } from "react";
import api from "../lib/api";

export interface MarketData {
  id: string;
  question: string;
  category: string;
  status: string;
  predikt: number | null;
  confidence: number | null;
  created_at: string;
  deadline: string;
  validators: any[];
  debate_rounds: any[];
  totalYes?: number;
  totalNo?: number;
  onChainAddress?: string;
}

export function useMarkets(initialMarkets: MarketData[] = []) {
  const [markets, setMarkets] = useState<MarketData[]>(initialMarkets);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createMarket = useCallback(
    async (params: {
      question: string;
      category: string;
      deadline_hours?: number;
    }) => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.createMarket({
          question: params.question,
          category: params.category,
          deadline_hours: params.deadline_hours || 168,
        });

        const newMarket: MarketData = {
          id: result.market_id,
          question: params.question,
          category: params.category,
          status: "open",
          predikt: null,
          confidence: null,
          created_at: new Date().toISOString(),
          deadline: result.deadline,
          validators: [],
          debate_rounds: [],
          totalYes: 0,
          totalNo: 0,
        };

        setMarkets((prev) => [newMarket, ...prev]);
        return newMarket;
      } catch (err: any) {
        setError(err.message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const refreshMarkets = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.listMarkets();
      setMarkets(result.markets);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateMarket = useCallback((id: string, updates: Partial<MarketData>) => {
    setMarkets((prev) =>
      prev.map((m) => (m.id === id ? { ...m, ...updates } : m))
    );
  }, []);

  return {
    markets,
    setMarkets,
    loading,
    error,
    createMarket,
    refreshMarkets,
    updateMarket,
  };
}

export default useMarkets;

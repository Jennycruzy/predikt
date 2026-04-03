"use client";

import { useState, useCallback, useEffect } from "react";
import PrediktGauge from "../components/PrediktGauge";
import ReasoningTree from "../components/ReasoningTree";
import DebateTimeline from "../components/DebateTimeline";
import PredictionDistribution from "../components/PredictionDistribution";
import ReputationChart, { REPUTATION_HISTORY } from "../components/ReputationChart";
import MarketCard from "../components/MarketCard";
import ValidatorCard from "../components/ValidatorCard";
import CreateMarketModal from "../components/CreateMarketModal";
import FaucetModal from "../components/FaucetModal";
import WalletConnect from "../components/WalletConnect";
import { useAccount } from "wagmi";
import useContract from "../hooks/useContract";
import { VALIDATORS, STATUS_COLORS, STAKING_CONFIG, TOKEN_CONFIG, CATEGORIES } from "../lib/constants";

// Sample data removed for real-world integration

// ═══════════════════════════════════════════════════════
// Main Page Component
// ═══════════════════════════════════════════════════════

export default function DashboardPage() {
  const [markets, setMarkets] = useState<any[]>([]);
  const [selectedMarket, setSelectedMarket] = useState<any>(null);
  const [activeTab, setActiveTab] = useState("predikt");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showFaucetModal, setShowFaucetModal] = useState(false);
  const [isDebating, setIsDebating] = useState(false);
  const [debateStep, setDebateStep] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [stakePosition, setStakePosition] = useState<"YES" | "NO">("YES");
  const [stakeAmount, setStakeAmount] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [marketStatusFilter, setMarketStatusFilter] = useState<"active" | "resolved" | "all">("active");

  const { isConnected: walletConnected, address: walletAddress } = useAccount();
  const { wallet, userPosition, txPending, claimFaucet, placeBet, createMarket, claimWinnings, refreshData } = useContract();
  const balance = wallet.balance;

  const fetchMarkets = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await fetch(`/api/markets`);
      const data = await res.json();
      setMarkets(data.markets || []);
      if (data.markets?.length > 0 && !selectedMarket) {
        setSelectedMarket(data.markets[0]);
      }
    } catch (err) {
      console.error("Failed to fetch markets:", err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedMarket]);

  useEffect(() => {
    fetchMarkets();
  }, [fetchMarkets]);

  // Sync user position when market changes
  useEffect(() => {
    if (selectedMarket) {
      refreshData(selectedMarket.id);
    }
  }, [selectedMarket, refreshData]);

  const runDebate = useCallback(async (market: any) => {
    setIsDebating(true);
    setDebateStep("Starting debate...");

    try {
      // Step 1: kick off the background job (returns instantly)
      const startRes = await fetch(`/api/run-debate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ market_id: market.id, num_rounds: 2 }),
      });
      if (!startRes.ok) {
        const e = await startRes.json().catch(() => ({}));
        throw new Error(e.detail || "Failed to start debate");
      }
      const { job_id } = await startRes.json();

      // Step 2: poll /debate-job/:id until done
      let data: any = null;
      while (true) {
        await new Promise(r => setTimeout(r, 3000));
        const pollRes = await fetch(`/api/debate-job/${job_id}`);
        const job = await pollRes.json();

        if (job.step) setDebateStep(job.step);

        if (job.status === "completed") {
          data = job.result;
          break;
        } else if (job.status === "failed") {
          throw new Error(job.error || "Debate failed");
        }
        // still "pending" → keep polling
      }

      // Step 3: update debate results in UI, then re-fetch actual on-chain status
      setSelectedMarket((prev: any) => ({
        ...prev,
        predikt: data.predikt,
        confidence: data.confidence,
        // Don't override status here — fetchMarkets() will read the real on-chain value
        validators: data.validators.map((v: any) => ({
          ...v,
          reasoning: v.reasoning || v.reasoning_preview,
        })),
        debate_rounds: data.rounds_data || [],
        validator_count: data.validators.length,
      }));
      setActiveTab("debate");
    } catch (err: any) {
      console.error("Debate failed:", err);
      alert(`Debate failed: ${err.message}`);
    } finally {
      setIsDebating(false);
      setDebateStep("");
    }
  }, [fetchMarkets]);

  const tabs = [
    { id: "predikt", label: "Predikt" },
    { id: "staking", label: "Stake" },
    { id: "debate", label: "Live Debate" },
    { id: "tree", label: "Reasoning Tree" },
    { id: "reputation", label: "Reputation" },
  ];

  const totalPool = selectedMarket ? (selectedMarket.total_yes || 0) + (selectedMarket.total_no || 0) : 0;
  const yesOdds = (selectedMarket && totalPool > 0) ? ((selectedMarket.total_yes || 0) / totalPool * 100).toFixed(0) : "50";
  const noOdds = (selectedMarket && totalPool > 0) ? ((selectedMarket.total_no || 0) / totalPool * 100).toFixed(0) : "50";

  // A market whose deadline has passed is expired regardless of what status the backend holds
  const marketIsExpired = selectedMarket?.deadline ? new Date(selectedMarket.deadline) <= new Date() : false;
  const isTrulySettled = selectedMarket ? ["resolved", "finalized", "cancelled"].includes(selectedMarket.status) : false;
  const showAsExpired = marketIsExpired && !isTrulySettled;

  // Resolved outcome — true = YES won, false = NO won, null = still open
  const isFinalized = selectedMarket?.status === "finalized";
  const resolvedYes: boolean | null = isFinalized && selectedMarket?.resolved_yes != null
    ? selectedMarket.resolved_yes
    : null;
  const winnerLabel = resolvedYes === true ? "YES" : resolvedYes === false ? "NO" : null;
  const winnerColor = resolvedYes === true ? "#00D4AA" : resolvedYes === false ? "#FF3366" : "#A855F7";

  // When finalized, override odds bar to show 100% for winning side
  const displayYesOdds = resolvedYes === true ? "100" : resolvedYes === false ? "0" : yesOdds;
  const displayNoOdds  = resolvedYes === false ? "100" : resolvedYes === true ? "0" : noOdds;

  return (
    <div style={{ background: "#0E0D0A", color: "#F0ECE2", minHeight: "100vh", fontFamily: "'DM Sans', sans-serif", position: "relative", overflow: "hidden" }}>
      <div className="grain-overlay" />
      <div style={{ position: "fixed", top: -200, right: -200, width: 600, height: 600, borderRadius: "50%", background: "radial-gradient(circle, rgba(168,85,247,0.04) 0%, transparent 70%)", pointerEvents: "none" }} />

      <div style={{ position: "relative", zIndex: 2, maxWidth: 1400, margin: "0 auto", padding: "20px 24px" }}>
        {/* ═══ HEADER ═══ */}
        <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 32, paddingBottom: 16, borderBottom: "1px solid rgba(240,236,226,0.06)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg, #00D4AA 0%, #A855F7 100%)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>◎</div>
            <div>
              <h1 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: "-0.02em", fontFamily: "'DM Mono', monospace" }}>PREDIKT<span style={{ color: "#00D4AA" }}>.</span>ai</h1>
              <p style={{ margin: 0, fontSize: 10, color: "rgba(240,236,226,0.35)", letterSpacing: "0.12em", textTransform: "uppercase", fontFamily: "'DM Mono', monospace" }}>GenLayer Studionet · Reasoning-Driven Prediction</p>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, background: "rgba(0,212,170,0.08)", borderRadius: 20, padding: "5px 14px" }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#00D4AA", animation: "pulse 2s infinite" }} />
              <span style={{ fontSize: 11, color: "#00D4AA", fontFamily: "'DM Mono', monospace" }}>Studionet</span>
            </div>

            {/* Wallet */}
            {walletConnected ? (
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ background: "rgba(255,255,255,0.04)", borderRadius: 10, padding: "6px 14px", display: "flex", alignItems: "center", gap: 8, border: "1px solid rgba(255,255,255,0.06)" }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: "#00D4AA", fontFamily: "'DM Mono', monospace" }}>{balance.toLocaleString()} mUSDL</span>
                  <span style={{ fontSize: 10, color: "rgba(240,236,226,0.3)" }}>|</span>
                  <span style={{ fontSize: 10, color: "rgba(240,236,226,0.5)", fontFamily: "'DM Mono', monospace" }}>{walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}</span>
                </div>
                <button onClick={() => setShowFaucetModal(true)} disabled={txPending}
                  style={{ background: "rgba(168,85,247,0.12)", border: "1px solid rgba(168,85,247,0.3)", borderRadius: 10, padding: "6px 14px", color: "#A855F7", fontSize: 11, cursor: txPending ? "default" : "pointer", fontFamily: "'DM Mono', monospace", fontWeight: 600 }}>
                  💰 Claim
                </button>
              </div>
            ) : (
              <WalletConnect />
            )}

            <div style={{ background: "rgba(0,212,170,0.06)", border: "1px solid rgba(0,212,170,0.15)", borderRadius: 10, padding: "6px 14px", display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#00D4AA", animation: "pulse 2s infinite" }} />
              <span style={{ fontSize: 11, color: "rgba(0,212,170,0.7)", fontFamily: "'DM Mono', monospace" }}>AI generates markets</span>
            </div>
          </div>
        </header>

        {/* ═══ MAIN GRID ═══ */}
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 24, minHeight: "calc(100vh - 120px)" }}>
          {/* Sidebar */}
          <aside style={{ display: "flex", flexDirection: "column", gap: 0 }}>
            {/* Category filter pills */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 10 }}>
              {[{ id: "all", label: "All", icon: "◈" }, ...CATEGORIES.filter(c => markets.some(m => m.category === c.id))].map(cat => (
                <button key={cat.id} onClick={() => setSelectedCategory(cat.id)}
                  style={{
                    background: selectedCategory === cat.id ? "rgba(0,212,170,0.12)" : "rgba(255,255,255,0.03)",
                    border: selectedCategory === cat.id ? "1px solid rgba(0,212,170,0.3)" : "1px solid rgba(255,255,255,0.06)",
                    borderRadius: 8, padding: "4px 10px", color: selectedCategory === cat.id ? "#00D4AA" : "rgba(240,236,226,0.45)",
                    fontSize: 10, cursor: "pointer", fontFamily: "'DM Mono', monospace", fontWeight: 600,
                    transition: "all 0.15s",
                  }}>
                  {cat.icon} {cat.label}
                </button>
              ))}
            </div>

            {/* Status sub-tabs */}
            <div style={{ display: "flex", gap: 2, marginBottom: 12, background: "rgba(255,255,255,0.03)", borderRadius: 8, padding: 3 }}>
              {(["active", "resolved", "all"] as const).map(s => (
                <button key={s} onClick={() => setMarketStatusFilter(s)}
                  style={{
                    flex: 1, background: marketStatusFilter === s ? "rgba(240,236,226,0.07)" : "transparent",
                    border: "none", borderRadius: 6, padding: "5px 0",
                    color: marketStatusFilter === s ? "#F0ECE2" : "rgba(240,236,226,0.35)",
                    fontSize: 10, cursor: "pointer", fontFamily: "'DM Mono', monospace",
                    fontWeight: marketStatusFilter === s ? 700 : 500, textTransform: "uppercase", letterSpacing: "0.06em",
                    transition: "all 0.15s",
                  }}>
                  {s}
                </button>
              ))}
            </div>

            {/* Market list */}
            {(() => {
              const ACTIVE_STATUSES = ["active", "open", "debating", "resolving"];
              const RESOLVED_STATUSES = ["resolved", "finalized", "undetermined", "cancelled"];

              const byCategory = selectedCategory === "all"
                ? markets
                : markets.filter(m => m.category === selectedCategory);

              const now = new Date();
              const activeList   = byCategory.filter(m => ACTIVE_STATUSES.includes(m.status) && !(m.deadline && new Date(m.deadline) <= now));
              const resolvedList = byCategory.filter(m => RESOLVED_STATUSES.includes(m.status) || (ACTIVE_STATUSES.includes(m.status) && m.deadline && new Date(m.deadline) <= now));

              const visibleActive   = marketStatusFilter === "resolved" ? [] : activeList;
              const visibleResolved = marketStatusFilter === "active"   ? [] : resolvedList;

              if (byCategory.length === 0) {
                return (
                  <p style={{ fontSize: 11, color: "rgba(240,236,226,0.25)", fontFamily: "'DM Mono', monospace", textAlign: "center", marginTop: 32 }}>
                    No markets in this category
                  </p>
                );
              }

              return (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {/* Active section */}
                  {visibleActive.length > 0 && (
                    <>
                      <div style={{ display: "flex", alignItems: "center", gap: 6, margin: "4px 0 4px" }}>
                        <span style={{ fontSize: 9, textTransform: "uppercase", letterSpacing: "0.12em", color: "#00D4AA", fontFamily: "'DM Mono', monospace", fontWeight: 700 }}>Active</span>
                        <span style={{ fontSize: 9, color: "rgba(0,212,170,0.4)", fontFamily: "'DM Mono', monospace" }}>{visibleActive.length}</span>
                        <div style={{ flex: 1, height: 1, background: "rgba(0,212,170,0.12)" }} />
                      </div>
                      {visibleActive.map(m => (
                        <MarketCard key={m.id} market={m} selected={selectedMarket?.id === m.id}
                          onClick={() => { setSelectedMarket(m); setActiveTab("predikt"); }} />
                      ))}
                    </>
                  )}

                  {/* Resolved section */}
                  {visibleResolved.length > 0 && (
                    <>
                      <div style={{ display: "flex", alignItems: "center", gap: 6, margin: "8px 0 4px" }}>
                        <span style={{ fontSize: 9, textTransform: "uppercase", letterSpacing: "0.12em", color: "#A855F7", fontFamily: "'DM Mono', monospace", fontWeight: 700 }}>Resolved</span>
                        <span style={{ fontSize: 9, color: "rgba(168,85,247,0.4)", fontFamily: "'DM Mono', monospace" }}>{visibleResolved.length}</span>
                        <div style={{ flex: 1, height: 1, background: "rgba(168,85,247,0.12)" }} />
                      </div>
                      {visibleResolved.map(m => (
                        <MarketCard key={m.id} market={m} selected={selectedMarket?.id === m.id}
                          onClick={() => { setSelectedMarket(m); setActiveTab("predikt"); }} />
                      ))}
                    </>
                  )}

                  {/* Empty state for the current filter */}
                  {visibleActive.length === 0 && visibleResolved.length === 0 && (
                    <p style={{ fontSize: 11, color: "rgba(240,236,226,0.25)", fontFamily: "'DM Mono', monospace", textAlign: "center", marginTop: 32 }}>
                      No {marketStatusFilter === "all" ? "" : marketStatusFilter} markets here
                    </p>
                  )}
                </div>
              );
            })()}
          </aside>

          {/* Main Content */}
          <main>
            {isLoading ? (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "rgba(240,236,226,0.3)" }}>
                <span style={{ fontSize: 13, fontFamily: "'DM Mono', monospace" }}>Syncing with GenLayer Studionet...</span>
              </div>
            ) : markets.length === 0 ? (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "rgba(240,236,226,0.3)" }}>
                <span style={{ fontSize: 13, fontFamily: "'DM Mono', monospace" }}>No active markets found. Create one to begin.</span>
              </div>
            ) : selectedMarket && (
              <>
                {/* Market Header */}
                <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: "24px 28px", marginBottom: 20, border: "1px solid rgba(255,255,255,0.04)" }}>
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                        {(() => {
                          const badgeColor = showAsExpired ? "#FF6B35" : (STATUS_COLORS[selectedMarket.status as keyof typeof STATUS_COLORS] || "#666");
                          return (
                            <span style={{ fontSize: 11, padding: "3px 10px", borderRadius: 10, background: `${badgeColor}15`, color: badgeColor, fontFamily: "'DM Mono', monospace", fontWeight: 600 }}>
                              {showAsExpired ? "EXPIRED" : selectedMarket.status.toUpperCase()}
                            </span>
                          );
                        })()}
                        <span style={{ fontSize: 11, color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>{selectedMarket.id}</span>
                        {totalPool > 0 && (
                          <span style={{ fontSize: 11, color: "rgba(240,236,226,0.4)", fontFamily: "'DM Mono', monospace", background: "rgba(255,255,255,0.04)", borderRadius: 8, padding: "2px 8px" }}>
                            Pool: {totalPool.toLocaleString()} mUSDL
                          </span>
                        )}
                      </div>
                      <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, lineHeight: 1.3, letterSpacing: "-0.02em", maxWidth: 700 }}>{selectedMarket.question}</h2>
                    </div>
                    {!showAsExpired && !["finalized", "resolved", "cancelled"].includes(selectedMarket.status) && (
                      <button onClick={() => runDebate(selectedMarket)} disabled={isDebating}
                        style={{ background: isDebating ? "rgba(255,255,255,0.06)" : "linear-gradient(135deg, #FF6B35, #FF3366)", border: "none", borderRadius: 12, padding: "12px 24px", color: isDebating ? "rgba(240,236,226,0.5)" : "#fff", fontWeight: 700, fontSize: 14, cursor: isDebating ? "default" : "pointer", whiteSpace: "nowrap", fontFamily: "'DM Sans', sans-serif" }}>
                        {isDebating ? debateStep : "⚡ Launch Debate"}
                      </button>
                    )}
                  </div>

                  {/* Resolution outcome banner */}
                  {winnerLabel && (
                    <div style={{ marginTop: 16, background: `${winnerColor}10`, border: `1px solid ${winnerColor}30`, borderRadius: 10, padding: "10px 16px", display: "flex", alignItems: "center", gap: 12 }}>
                      <span style={{ fontSize: 20 }}>{winnerLabel === "YES" ? "✅" : "❌"}</span>
                      <div>
                        <p style={{ margin: 0, fontWeight: 800, fontSize: 14, color: winnerColor, fontFamily: "'DM Mono', monospace" }}>{winnerLabel} WON</p>
                        <p style={{ margin: 0, fontSize: 11, color: "rgba(240,236,226,0.4)" }}>Market resolved · Winning stakers can claim payouts below</p>
                      </div>
                    </div>
                  )}

                  {/* Odds bar — shows 100/0 when resolved */}
                  {totalPool > 0 && (
                    <div style={{ marginTop: 12 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <span style={{ fontSize: 11, color: resolvedYes === false ? "rgba(0,212,170,0.3)" : "#00D4AA", fontFamily: "'DM Mono', monospace", fontWeight: resolvedYes === true ? 800 : 600 }}>YES {displayYesOdds}%{resolvedYes === true ? " ✓" : ""}</span>
                        <span style={{ fontSize: 11, color: resolvedYes === true ? "rgba(255,51,102,0.3)" : "#FF3366", fontFamily: "'DM Mono', monospace", fontWeight: resolvedYes === false ? 800 : 600 }}>NO {displayNoOdds}%{resolvedYes === false ? " ✓" : ""}</span>
                      </div>
                      <div style={{ display: "flex", height: 6, borderRadius: 3, overflow: "hidden", background: "rgba(255,255,255,0.06)" }}>
                        <div style={{ width: `${displayYesOdds}%`, background: resolvedYes === false ? "rgba(0,212,170,0.2)" : "#00D4AA", borderRadius: "3px 0 0 3px", transition: "width 0.8s" }} />
                        <div style={{ width: `${displayNoOdds}%`, background: resolvedYes === true ? "rgba(255,51,102,0.2)" : "#FF3366", borderRadius: "0 3px 3px 0", transition: "width 0.8s" }} />
                      </div>
                    </div>
                  )}
                </div>

                {/* Tabs */}
                <div style={{ display: "flex", gap: 4, marginBottom: 20, background: "rgba(255,255,255,0.02)", borderRadius: 12, padding: 4, width: "fit-content" }}>
                  {tabs.map((t) => (
                    <button key={t.id} onClick={() => setActiveTab(t.id)}
                      style={{ background: activeTab === t.id ? "rgba(240,236,226,0.08)" : "transparent", border: "none", borderRadius: 8, padding: "8px 18px", color: activeTab === t.id ? "#F0ECE2" : "rgba(240,236,226,0.4)", fontWeight: activeTab === t.id ? 700 : 500, fontSize: 13, cursor: "pointer", fontFamily: "'DM Sans', sans-serif", transition: "all 0.2s" }}>
                      {t.label}
                    </button>
                  ))}
                </div>

                {/* ═══ TAB: Predikt ═══ */}
                {activeTab === "predikt" && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                    <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: 24, border: "1px solid rgba(255,255,255,0.04)", display: "flex", flexDirection: "column", alignItems: "center" }}>
                      <h3 style={{ margin: "0 0 8px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace", alignSelf: "flex-start" }}>Final Predikt</h3>
                      {showAsExpired && selectedMarket.predikt == null ? (
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flex: 1, gap: 10, padding: "24px 0" }}>
                          <span style={{ fontSize: 36 }}>⏰</span>
                          <p style={{ margin: 0, fontWeight: 700, color: "#FF6B35", fontFamily: "'DM Mono', monospace", fontSize: 13 }}>Market Expired</p>
                          <p style={{ margin: 0, fontSize: 11, color: "rgba(240,236,226,0.35)", textAlign: "center", lineHeight: 1.5 }}>AI validators are resolving this market.<br />Results will appear here shortly.</p>
                        </div>
                      ) : (
                        <>
                          <PrediktGauge value={selectedMarket.predikt} confidence={selectedMarket.confidence} size={220} />
                          {selectedMarket.predikt != null && (
                            <div style={{ display: "flex", gap: 20, marginTop: 12 }}>
                              {[{ label: "validators", val: selectedMarket.validator_count || 0 }, { label: "rounds", val: selectedMarket.debate_rounds?.length || 0 }, { label: "challenges", val: selectedMarket.debate_rounds?.reduce((a: number, r: any) => a + (r.critiques?.length || 0), 0) || 0 }].map((s) => (
                                <div key={s.label} style={{ textAlign: "center" }}>
                                  <div style={{ fontSize: 10, color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>{s.label}</div>
                                  <div style={{ fontSize: 18, fontWeight: 800, fontFamily: "'DM Mono', monospace" }}>{s.val}</div>
                                </div>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: 24, border: "1px solid rgba(255,255,255,0.04)" }}>
                      <h3 style={{ margin: "0 0 16px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>Prediction Spread</h3>
                      {selectedMarket.validators?.length ? <PredictionDistribution validators={selectedMarket.validators} /> : <p style={{ color: "rgba(240,236,226,0.3)", fontStyle: "italic", fontSize: 13 }}>{showAsExpired ? "Resolution in progress…" : "Launch debate to see predictions"}</p>}
                    </div>
                    <div style={{ gridColumn: "1 / -1", background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: 24, border: "1px solid rgba(255,255,255,0.04)" }}>
                      <h3 style={{ margin: "0 0 16px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>Validator Leaderboard</h3>
                      {selectedMarket.validators?.length ? (
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12 }}>
                          {[...selectedMarket.validators].sort((a, b) => b.score - a.score).map((v, i) => (
                            <ValidatorCard key={v.model} validator={v} rank={i} />
                          ))}
                        </div>
                      ) : <p style={{ color: "rgba(240,236,226,0.3)", fontStyle: "italic", fontSize: 13 }}>No validators yet</p>}
                    </div>
                  </div>
                )}

                {/* ═══ TAB: Staking ═══ */}
                {activeTab === "staking" && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                    {/* Staking Panel */}
                    <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: 24, border: "1px solid rgba(255,255,255,0.04)" }}>
                      <h3 style={{ margin: "0 0 16px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>Place Your Stake</h3>

                      {!walletConnected ? (
                        <div style={{ textAlign: "center", padding: 40 }}>
                          <p style={{ color: "rgba(240,236,226,0.4)", marginBottom: 16 }}>Connect wallet to stake mUSDL</p>
                          <WalletConnect />
                        </div>
                      ) : (showAsExpired || !["open", "active"].includes(selectedMarket.status)) ? (
                        <div style={{ textAlign: "center", padding: 40 }}>
                          {showAsExpired ? (
                            <>
                              <div style={{ fontSize: 36, marginBottom: 12 }}>⏰</div>
                              <p style={{ color: "#FF6B35", fontWeight: 700, marginBottom: 8, fontFamily: "'DM Mono', monospace", fontSize: 13 }}>Market Expired</p>
                              <p style={{ fontSize: 12, color: "rgba(240,236,226,0.4)", marginBottom: 20, lineHeight: 1.5 }}>Staking is closed. If you backed the winning outcome, claim your winnings below.</p>
                              <button
                                onClick={() => claimWinnings(selectedMarket.id)}
                                disabled={txPending}
                                style={{ background: txPending ? "rgba(255,255,255,0.06)" : "linear-gradient(135deg, #00D4AA, #A855F7)", border: "none", borderRadius: 12, padding: "14px 32px", color: txPending ? "rgba(240,236,226,0.4)" : "#fff", fontWeight: 800, fontSize: 16, cursor: txPending ? "default" : "pointer", fontFamily: "'DM Sans', sans-serif" }}>
                                {txPending ? "Claiming..." : "💰 Cashout Winnings"}
                              </button>
                            </>
                          ) : (
                            <>
                              {winnerLabel ? (
                                <>
                                  <div style={{ fontSize: 32, marginBottom: 8 }}>{winnerLabel === "YES" ? "✅" : "❌"}</div>
                                  <p style={{ color: winnerColor, fontWeight: 800, marginBottom: 6, fontFamily: "'DM Mono', monospace", fontSize: 16 }}>{winnerLabel} WON</p>
                                  {totalPool > 0 && (
                                    <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 10, padding: "10px 16px", marginBottom: 16, textAlign: "left" }}>
                                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                                        <span style={{ fontSize: 11, color: "rgba(240,236,226,0.4)" }}>Winning pool</span>
                                        <span style={{ fontSize: 12, fontWeight: 700, fontFamily: "'DM Mono', monospace", color: winnerColor }}>
                                          {(winnerLabel === "YES" ? selectedMarket.total_yes : selectedMarket.total_no || 0).toLocaleString()} mUSDL staked
                                        </span>
                                      </div>
                                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                                        <span style={{ fontSize: 11, color: "rgba(240,236,226,0.4)" }}>Total payout pool</span>
                                        <span style={{ fontSize: 12, fontWeight: 700, fontFamily: "'DM Mono', monospace" }}>
                                          {(totalPool * 0.98).toFixed(0)} mUSDL (after 2% fee)
                                        </span>
                                      </div>
                                    </div>
                                  )}
                                  <p style={{ fontSize: 12, color: "rgba(240,236,226,0.4)", marginBottom: 16 }}>If you staked on {winnerLabel}, claim your proportional share of the pool now.</p>
                                  <button onClick={() => claimWinnings(selectedMarket.id)} disabled={txPending}
                                    style={{ background: txPending ? "rgba(255,255,255,0.06)" : `linear-gradient(135deg, ${winnerColor}, #A855F7)`, border: "none", borderRadius: 12, padding: "14px 32px", color: txPending ? "rgba(240,236,226,0.4)" : "#fff", fontWeight: 800, fontSize: 16, cursor: txPending ? "default" : "pointer", fontFamily: "'DM Sans', sans-serif" }}>
                                    {txPending ? "Claiming..." : "💰 Cashout Winnings"}
                                  </button>
                                </>
                              ) : (
                                <>
                                  <p style={{ color: "rgba(240,236,226,0.4)", marginBottom: 16 }}>This market is <strong style={{ color: "#FFB347" }}>{selectedMarket.status}</strong>. Staking is closed.</p>
                                  <p style={{ fontSize: 12, color: "rgba(240,236,226,0.4)" }}>Outcome is being determined by AI validators.</p>
                                </>
                              )}
                            </>
                          )}
                        </div>
                      ) : (
                        <>
                          {/* Position selector */}
                          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
                            {(["YES", "NO"] as const).map((pos) => (
                              <button key={pos} onClick={() => setStakePosition(pos)}
                                style={{ flex: 1, padding: "12px 0", borderRadius: 10, border: stakePosition === pos ? `2px solid ${pos === "YES" ? "#00D4AA" : "#FF3366"}` : "2px solid rgba(255,255,255,0.06)", background: stakePosition === pos ? (pos === "YES" ? "rgba(0,212,170,0.1)" : "rgba(255,51,102,0.1)") : "rgba(255,255,255,0.02)", color: stakePosition === pos ? (pos === "YES" ? "#00D4AA" : "#FF3366") : "rgba(240,236,226,0.5)", fontWeight: 800, fontSize: 16, cursor: "pointer", fontFamily: "'DM Mono', monospace" }}>
                                {pos}
                              </button>
                            ))}
                          </div>

                          {/* Amount input */}
                          <div style={{ marginBottom: 16 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                              <label style={{ fontSize: 11, color: "rgba(240,236,226,0.4)", fontFamily: "'DM Mono', monospace" }}>Amount (mUSDL)</label>
                              <span style={{ fontSize: 11, color: "rgba(240,236,226,0.4)", fontFamily: "'DM Mono', monospace" }}>Balance: {balance.toLocaleString()}</span>
                            </div>
                            <div style={{ display: "flex", gap: 8 }}>
                              <input type="number" value={stakeAmount} onChange={(e) => setStakeAmount(e.target.value)} placeholder={`Min ${STAKING_CONFIG.minStake}`}
                                style={{ flex: 1, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10, padding: "10px 14px", color: "#F0ECE2", fontSize: 16, fontFamily: "'DM Mono', monospace", outline: "none" }} />
                              <button onClick={() => setStakeAmount(String(Math.min(balance, STAKING_CONFIG.maxStake)))}
                                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10, padding: "10px 14px", color: "rgba(240,236,226,0.5)", fontSize: 11, cursor: "pointer", fontFamily: "'DM Mono', monospace" }}>MAX</button>
                            </div>
                          </div>

                          {/* Quick amounts */}
                          <div style={{ display: "flex", gap: 6, marginBottom: 20 }}>
                            {[50, 100, 250, 500, 1000].map((a) => (
                              <button key={a} onClick={() => setStakeAmount(String(Math.min(a, balance)))}
                                style={{ flex: 1, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 8, padding: "6px 0", color: "rgba(240,236,226,0.5)", fontSize: 11, cursor: "pointer", fontFamily: "'DM Mono', monospace" }}>{a}</button>
                            ))}
                          </div>

                          {/* Potential payout */}
                          {stakeAmount && parseFloat(stakeAmount) > 0 && (
                            <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 10, padding: "10px 14px", marginBottom: 16 }}>
                              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                                <span style={{ fontSize: 11, color: "rgba(240,236,226,0.4)" }}>Potential payout</span>
                                <span style={{ fontSize: 13, fontWeight: 800, color: "#00D4AA", fontFamily: "'DM Mono', monospace" }}>
                                  {(() => {
                                    const amt = parseFloat(stakeAmount);
                                    const pool = totalPool + amt;
                                    const winPool = (stakePosition === "YES" ? (selectedMarket.total_yes || 0) : (selectedMarket.total_no || 0)) + amt;
                                    const fee = pool * STAKING_CONFIG.platformFee / 100;
                                    return ((pool - fee) * amt / winPool).toFixed(0);
                                  })()} mUSDL
                                </span>
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={{ fontSize: 10, color: "rgba(240,236,226,0.3)" }}>Platform fee</span>
                                <span style={{ fontSize: 10, color: "rgba(240,236,226,0.3)", fontFamily: "'DM Mono', monospace" }}>{STAKING_CONFIG.platformFee}%</span>
                              </div>
                            </div>
                          )}

                          <button onClick={() => placeBet(selectedMarket.id, stakePosition, parseFloat(stakeAmount))} disabled={txPending || !stakeAmount || parseFloat(stakeAmount) < STAKING_CONFIG.minStake || parseFloat(stakeAmount) > balance}
                            style={{ width: "100%", background: stakeAmount && parseFloat(stakeAmount) >= STAKING_CONFIG.minStake ? (stakePosition === "YES" ? "linear-gradient(135deg, #00D4AA, #00B894)" : "linear-gradient(135deg, #FF3366, #FF1744)") : "rgba(255,255,255,0.06)", border: "none", borderRadius: 12, padding: "14px", color: stakeAmount && parseFloat(stakeAmount) >= STAKING_CONFIG.minStake ? "#fff" : "rgba(240,236,226,0.3)", fontWeight: 800, fontSize: 16, cursor: stakeAmount && parseFloat(stakeAmount) >= STAKING_CONFIG.minStake ? "pointer" : "default", fontFamily: "'DM Sans', sans-serif" }}>
                            {txPending ? "Confirming..." : `Stake ${stakePosition}`}
                          </button>
                        </>
                      )}
                    </div>

                    {/* Market Pool Info */}
                    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                      <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: 24, border: "1px solid rgba(255,255,255,0.04)" }}>
                        <h3 style={{ margin: "0 0 16px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>Market Pool</h3>
                        <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
                          <div style={{ flex: 1, background: "rgba(0,212,170,0.06)", borderRadius: 12, padding: 16, textAlign: "center" }}>
                            <div style={{ fontSize: 10, color: "rgba(0,212,170,0.7)", fontFamily: "'DM Mono', monospace", marginBottom: 4 }}>YES Pool</div>
                            <div style={{ fontSize: 22, fontWeight: 800, color: "#00D4AA", fontFamily: "'DM Mono', monospace" }}>{(selectedMarket.total_yes || 0).toLocaleString()}</div>
                            <div style={{ fontSize: 10, color: "rgba(240,236,226,0.3)" }}>mUSDL</div>
                          </div>
                          <div style={{ flex: 1, background: "rgba(255,51,102,0.06)", borderRadius: 12, padding: 16, textAlign: "center" }}>
                            <div style={{ fontSize: 10, color: "rgba(255,51,102,0.7)", fontFamily: "'DM Mono', monospace", marginBottom: 4 }}>NO Pool</div>
                            <div style={{ fontSize: 22, fontWeight: 800, color: "#FF3366", fontFamily: "'DM Mono', monospace" }}>{(selectedMarket.total_no || 0).toLocaleString()}</div>
                            <div style={{ fontSize: 10, color: "rgba(240,236,226,0.3)" }}>mUSDL</div>
                          </div>
                        </div>
                        <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 10, padding: "10px 14px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                            <span style={{ fontSize: 11, color: "rgba(240,236,226,0.4)" }}>Total pool</span>
                            <span style={{ fontSize: 13, fontWeight: 800, fontFamily: "'DM Mono', monospace" }}>{totalPool.toLocaleString()} mUSDL</span>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <span style={{ fontSize: 11, color: "rgba(240,236,226,0.4)" }}>Resolution</span>
                            <span style={{ fontSize: 11, color: "rgba(240,236,226,0.5)", fontFamily: "'DM Mono', monospace" }}>AI Debate Predikt</span>
                          </div>
                        </div>
                      </div>

                      <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: 24, border: "1px solid rgba(255,255,255,0.04)" }}>
                        <h3 style={{ margin: "0 0 12px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>How It Works</h3>
                        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                          {[
                            { num: "1", text: "Stake mUSDL on YES or NO" },
                            { num: "2", text: "AI validators debate & generate predikt" },
                            { num: "3", text: "Market resolves based on reasoning quality" },
                            { num: "4", text: "Winners claim proportional payouts" },
                          ].map((s) => (
                            <div key={s.num} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                              <div style={{ width: 24, height: 24, borderRadius: "50%", background: "rgba(0,212,170,0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, color: "#00D4AA", fontWeight: 700, fontFamily: "'DM Mono', monospace", flexShrink: 0 }}>{s.num}</div>
                              <span style={{ fontSize: 12, color: "rgba(240,236,226,0.6)" }}>{s.text}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Cashout / Your Position */}
                      <div style={{ background: "rgba(168,85,247,0.06)", borderRadius: 16, padding: 24, border: "1px solid rgba(168,85,247,0.15)" }}>
                        <h3 style={{ margin: "0 0 12px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(168,85,247,0.7)", fontFamily: "'DM Mono', monospace" }}>Your Position</h3>
                        {!walletConnected ? (
                          <p style={{ fontSize: 12, color: "rgba(240,236,226,0.35)" }}>Connect wallet to view your stakes</p>
                        ) : (
                          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <span style={{ fontSize: 12, color: "rgba(240,236,226,0.5)" }}>YES staked</span>
                              <span style={{ fontFamily: "'DM Mono', monospace", color: "#00D4AA", fontSize: 13 }}>{userPosition?.yesStake || 0} mUSDL</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <span style={{ fontSize: 12, color: "rgba(240,236,226,0.5)" }}>NO staked</span>
                              <span style={{ fontFamily: "'DM Mono', monospace", color: "#FF3366", fontSize: 13 }}>{userPosition?.noStake || 0} mUSDL</span>
                            </div>
                            {selectedMarket.status === "finalized" && (
                              <button
                                onClick={() => claimWinnings(selectedMarket.id)}
                                disabled={txPending}
                                style={{ marginTop: 8, width: "100%", background: txPending ? "rgba(255,255,255,0.06)" : "linear-gradient(135deg, #A855F7, #7C3AED)", border: "none", borderRadius: 10, padding: "12px", color: "#fff", fontWeight: 700, fontSize: 14, cursor: txPending ? "default" : "pointer", fontFamily: "'DM Sans', sans-serif" }}>
                                {txPending ? "Claiming..." : "💰 Cashout Winnings"}
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* ═══ TAB: Debate ═══ */}
                {activeTab === "debate" && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                    <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: 24, border: "1px solid rgba(255,255,255,0.04)" }}>
                      <h3 style={{ margin: "0 0 16px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>Validator Reasoning</h3>
                      <div style={{ display: "flex", flexDirection: "column", gap: 12, maxHeight: 500, overflowY: "auto" }}>
                        {selectedMarket.validators?.length ? selectedMarket.validators.map((v: any) => {
                          const info = VALIDATORS.find((x) => x.model === v.model);
                          return (
                            <div key={v.model} style={{ background: "rgba(255,255,255,0.02)", borderRadius: 10, padding: 14, borderLeft: `3px solid ${info?.color}` }}>
                              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                                <span style={{ color: info?.color, fontSize: 14 }}>{info?.icon}</span>
                                <span style={{ fontWeight: 700, fontSize: 13, color: info?.color }}>{v.model}</span>
                                <span style={{ marginLeft: "auto", fontFamily: "'DM Mono', monospace", fontSize: 14, fontWeight: 800 }}>{(v.prediction * 100).toFixed(0)}%</span>
                              </div>
                              <pre style={{ margin: 0, fontSize: 11, color: "rgba(240,236,226,0.65)", lineHeight: 1.6, whiteSpace: "pre-wrap", fontFamily: "'DM Sans', sans-serif" }}>{v.reasoning}</pre>
                            </div>
                          );
                        }) : <p style={{ color: "rgba(240,236,226,0.3)", fontStyle: "italic" }}>Launch debate to see reasoning</p>}
                      </div>
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: 24, border: "1px solid rgba(255,255,255,0.04)" }}>
                      <h3 style={{ margin: "0 0 16px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>Challenge Timeline</h3>
                      <DebateTimeline rounds={selectedMarket.debate_rounds} />
                    </div>
                  </div>
                )}

                {/* ═══ TAB: Reasoning Tree ═══ */}
                {activeTab === "tree" && (
                  <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: 24, border: "1px solid rgba(255,255,255,0.04)" }}>
                    <h3 style={{ margin: "0 0 16px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>Reasoning Tree</h3>
                    {selectedMarket.validators?.length ? (
                      <>
                        <div style={{ display: "flex", gap: 16, marginBottom: 16, flexWrap: "wrap" }}>
                          {VALIDATORS.map((v) => (
                            <div key={v.model} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                              <div style={{ width: 10, height: 10, borderRadius: "50%", background: v.color }} />
                              <span style={{ fontSize: 11, color: "rgba(240,236,226,0.5)" }}>{v.model}</span>
                            </div>
                          ))}
                          <div style={{ display: "flex", alignItems: "center", gap: 6, marginLeft: 16 }}>
                            <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#FF3366" }} />
                            <span style={{ fontSize: 11, color: "rgba(240,236,226,0.5)" }}>Valid challenge</span>
                          </div>
                        </div>
                        <ReasoningTree market={selectedMarket} />
                      </>
                    ) : <p style={{ color: "rgba(240,236,226,0.3)", fontStyle: "italic" }}>Launch debate to generate reasoning tree</p>}
                  </div>
                )}

                {/* ═══ TAB: Reputation ═══ */}
                {activeTab === "reputation" && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                    <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: 24, border: "1px solid rgba(255,255,255,0.04)" }}>
                      <h3 style={{ margin: "0 0 16px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>Reputation Over Time</h3>
                      <ReputationChart />
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 16, padding: 24, border: "1px solid rgba(255,255,255,0.04)" }}>
                      <h3 style={{ margin: "0 0 16px", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.35)", fontFamily: "'DM Mono', monospace" }}>Validator Stats</h3>
                      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                        {VALIDATORS.map((v) => {
                          const rep = REPUTATION_HISTORY[v.model];
                          const current = rep[rep.length - 1];
                          const trend = current - rep[rep.length - 2];
                          return (
                            <div key={v.model} style={{ display: "flex", alignItems: "center", gap: 12, background: "rgba(255,255,255,0.03)", borderRadius: 10, padding: "10px 14px" }}>
                              <span style={{ color: v.color, fontSize: 18, width: 24 }}>{v.icon}</span>
                              <div style={{ flex: 1 }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                                  <span style={{ fontWeight: 700, fontSize: 13 }}>{v.model}</span>
                                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                    <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 16, fontWeight: 800, color: v.color }}>{current.toFixed(1)}</span>
                                    <span style={{ fontSize: 10, color: trend >= 0 ? "#00D4AA" : "#FF3366", fontFamily: "'DM Mono', monospace" }}>{trend >= 0 ? "▲" : "▼"}{Math.abs(trend).toFixed(1)}</span>
                                  </div>
                                </div>
                                <div style={{ height: 4, borderRadius: 2, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
                                  <div style={{ height: "100%", width: `${current * 10}%`, background: v.color, borderRadius: 2 }} />
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </main>
        </div>
      </div>

      <FaucetModal isOpen={showFaucetModal} onClose={() => setShowFaucetModal(false)} />
    </div>
  );
}

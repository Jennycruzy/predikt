"use client";
import { useState } from "react";
import { CATEGORIES } from "../lib/constants";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (params: { question: string; category: string; deadline_hours: number }) => void;
  walletBalance?: number;
}

const DEADLINE_OPTIONS = [
  { label: "1 hour", value: 1 },
  { label: "6 hours", value: 6 },
  { label: "12 hours", value: 12 },
  { label: "24 hours", value: 24 },
  { label: "48 hours", value: 48 },
];

export default function CreateMarketModal({ isOpen, onClose, onCreate, walletBalance }: Props) {
  const [question, setQuestion] = useState("");
  const [category, setCategory] = useState("crypto");
  const [deadlineHours, setDeadlineHours] = useState(24);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleCreate = async () => {
    if (!question.trim() || question.length < 10) return;
    setIsSubmitting(true);
    try {
      await onCreate({ question, category, deadline_hours: deadlineHours });
      setQuestion("");
      onClose();
    } catch (err) {
      console.error("Market creation failed:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputStyle = {
    width: "100%", background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10,
    padding: "10px 14px", color: "#F0ECE2", fontSize: 14,
    fontFamily: "'DM Sans', sans-serif", resize: "none" as const,
    outline: "none", boxSizing: "border-box" as const,
  };

  const chipStyle = (active: boolean) => ({
    background: active ? "rgba(0,212,170,0.15)" : "rgba(255,255,255,0.04)",
    border: active ? "1px solid rgba(0,212,170,0.3)" : "1px solid rgba(255,255,255,0.06)",
    borderRadius: 8, padding: "6px 14px",
    color: active ? "#00D4AA" : "rgba(240,236,226,0.5)",
    fontSize: 12, cursor: "pointer", fontFamily: "'DM Mono', monospace",
  });

  return (
    <div
      style={{
        position: "fixed", inset: 0, zIndex: 100,
        display: "flex", alignItems: "center", justifyContent: "center",
        background: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)",
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#1A1814", borderRadius: 20, padding: 32,
          width: 540, maxWidth: "90vw",
          border: "1px solid rgba(240,236,226,0.1)",
          boxShadow: "0 40px 100px rgba(0,0,0,0.5)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ margin: "0 0 4px", fontSize: 20, fontWeight: 800, letterSpacing: "-0.02em" }}>
          Create Prediction Market
        </h2>
        <p style={{ margin: "0 0 24px", fontSize: 13, color: "rgba(240,236,226,0.45)" }}>
          Ask a YES/NO question. Other users stake mUSDL and GenLayer AI validators resolve it.
        </p>

        {/* ── TIP ── */}
        <div style={{ background: "rgba(0,212,170,0.06)", border: "1px solid rgba(0,212,170,0.15)", borderRadius: 10, padding: "10px 14px", marginBottom: 20 }}>
          <p style={{ margin: 0, fontSize: 12, color: "rgba(0,212,170,0.8)" }}>
            💡 <strong>Tip:</strong> Write questions that resolve within 24 hours. e.g. "Will Bitcoin close above $84,000 today?"
          </p>
        </div>

        {/* Question */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.4)", marginBottom: 6, fontFamily: "'DM Mono', monospace" }}>
            Your Question
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Will BTC close above $84,000 by end of day today?"
            rows={3}
            style={inputStyle}
          />
          <div style={{ fontSize: 10, color: "rgba(240,236,226,0.3)", marginTop: 4, fontFamily: "'DM Mono', monospace" }}>
            {question.length}/500 · Must be a YES/NO question
          </div>
        </div>

        {/* Category */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.4)", marginBottom: 6, fontFamily: "'DM Mono', monospace" }}>
            Category
          </label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {CATEGORIES.map((cat) => (
              <button key={cat.id} onClick={() => setCategory(cat.id)} style={chipStyle(category === cat.id)}>
                {cat.icon} {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Deadline */}
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(240,236,226,0.4)", marginBottom: 6, fontFamily: "'DM Mono', monospace" }}>
            Resolves In
          </label>
          <div style={{ display: "flex", gap: 8 }}>
            {DEADLINE_OPTIONS.map(({ label, value }) => (
              <button key={value} onClick={() => setDeadlineHours(value)} style={chipStyle(deadlineHours === value)}>
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Balance */}
        {walletBalance != null && (
          <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 10, padding: "10px 14px", marginBottom: 20, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "rgba(240,236,226,0.5)" }}>Your Balance</span>
            <span style={{ fontSize: 14, fontWeight: 800, color: "#00D4AA", fontFamily: "'DM Mono', monospace" }}>{walletBalance.toLocaleString()} mUSDL</span>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button onClick={onClose} style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10, padding: "10px 20px", color: "rgba(240,236,226,0.6)", fontWeight: 600, fontSize: 13, cursor: "pointer", fontFamily: "'DM Sans', sans-serif" }}>
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={!question.trim() || question.length < 10 || isSubmitting}
            style={{
              background: question.trim() && question.length >= 10 && !isSubmitting ? "linear-gradient(135deg, #00D4AA, #00B894)" : "rgba(255,255,255,0.06)",
              border: "none", borderRadius: 10, padding: "10px 24px",
              color: question.trim() && question.length >= 10 && !isSubmitting ? "#0E0D0A" : "rgba(240,236,226,0.3)",
              fontWeight: 700, fontSize: 13,
              cursor: question.trim() && question.length >= 10 && !isSubmitting ? "pointer" : "default",
              fontFamily: "'DM Sans', sans-serif",
            }}
          >
            {isSubmitting ? "Creating..." : "⚡ Create Market"}
          </button>
        </div>
      </div>
    </div>
  );
}

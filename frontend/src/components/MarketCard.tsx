"use client";
import { CATEGORIES, STATUS_COLORS } from "../lib/constants";

interface Props {
  market: any;
  selected: boolean;
  onClick: () => void;
}

export default function MarketCard({ market, selected, onClick }: Props) {
  const categoryIcon = CATEGORIES.find((c) => c.id === market.category)?.icon || "○";
  const statusColor = STATUS_COLORS[market.status as keyof typeof STATUS_COLORS] || "#666";

  return (
    <button
      onClick={onClick}
      style={{
        background: selected ? "rgba(240,236,226,0.06)" : "rgba(255,255,255,0.02)",
        border: selected
          ? "1px solid rgba(240,236,226,0.12)"
          : "1px solid rgba(255,255,255,0.04)",
        borderRadius: 12,
        padding: "14px 16px",
        textAlign: "left",
        cursor: "pointer",
        color: "#F0ECE2",
        transition: "all 0.2s",
        width: "100%",
      }}
    >
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        marginBottom: 6,
      }}>
        <span style={{ fontSize: 14 }}>{categoryIcon}</span>
        <span style={{
          fontSize: 10, padding: "2px 8px", borderRadius: 10,
          background: `${statusColor}15`, color: statusColor,
          fontFamily: "'DM Mono', monospace",
        }}>
          {market.status}
        </span>
      </div>

      <p style={{
        margin: 0, fontSize: 13, fontWeight: 600, lineHeight: 1.4, marginBottom: 8,
      }}>
        {market.question.length > 60 ? market.question.slice(0, 60) + "…" : market.question}
      </p>

      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <span style={{
          fontSize: 10, color: "rgba(240,236,226,0.35)",
          fontFamily: "'DM Mono', monospace",
        }}>
          {market.validator_count || 0} validators
          {market.total_yes != null && market.total_no != null
            ? ` · ${((market.total_yes || 0) + (market.total_no || 0)).toLocaleString()} mUSDL`
            : ""}
        </span>
        {market.predikt != null && (
          <span style={{
            fontSize: 13, fontWeight: 800, color: "#00D4AA",
            fontFamily: "'DM Mono', monospace",
          }}>
            {(market.predikt * 100).toFixed(0)}%
          </span>
        )}
      </div>
    </button>
  );
}

"use client";
import { VALIDATORS } from "../lib/constants";

interface Props {
  validator: any;
  rank: number;
}

export default function ValidatorCard({ validator, rank }: Props) {
  const info = VALIDATORS.find((x) => x.model === validator.model);

  return (
    <div style={{
      background: "rgba(255,255,255,0.03)", borderRadius: 12,
      padding: 16, borderTop: `3px solid ${info?.color}`,
    }}>
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        marginBottom: 10,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: info?.color, fontSize: 16 }}>{info?.icon}</span>
          <span style={{ fontWeight: 700, fontSize: 13 }}>{validator.model}</span>
        </div>
        {rank === 0 && (
          <span style={{
            fontSize: 10, background: "rgba(0,212,170,0.15)",
            color: "#00D4AA", padding: "2px 8px", borderRadius: 8,
            fontFamily: "'DM Mono', monospace",
          }}>
            TOP
          </span>
        )}
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 11, color: "rgba(240,236,226,0.5)" }}>Prediction</span>
        <span style={{
          fontSize: 13, fontWeight: 800,
          fontFamily: "'DM Mono', monospace", color: info?.color,
        }}>
          {(validator.prediction * 100).toFixed(1)}%
        </span>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <span style={{ fontSize: 11, color: "rgba(240,236,226,0.5)" }}>Score</span>
        <span style={{
          fontSize: 13, fontWeight: 800, fontFamily: "'DM Mono', monospace",
        }}>
          {(validator.score * 100).toFixed(0)}
        </span>
      </div>

      <div style={{
        marginTop: 8, height: 4, borderRadius: 2,
        background: "rgba(255,255,255,0.06)", overflow: "hidden",
      }}>
        <div style={{
          height: "100%", width: `${validator.score * 100}%`,
          background: info?.color, borderRadius: 2, transition: "width 0.5s ease",
        }} />
      </div>
    </div>
  );
}

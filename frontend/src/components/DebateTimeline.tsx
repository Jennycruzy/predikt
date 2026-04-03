"use client";
import { VALIDATORS } from "../lib/constants";

interface Props {
  rounds: any[];
}

export default function DebateTimeline({ rounds }: Props) {
  if (!rounds?.length) {
    return (
      <p style={{ color: "rgba(240,236,226,0.3)", fontStyle: "italic" }}>
        No debate rounds yet
      </p>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {rounds.map((round, ri) => (
        <div key={ri}>
          <div style={{
            display: "flex", alignItems: "center", gap: 8, marginBottom: 10,
          }}>
            <span style={{
              background: "rgba(255,255,255,0.06)", borderRadius: 20,
              padding: "3px 12px", fontSize: 11,
              fontFamily: "'DM Mono', monospace", color: "rgba(240,236,226,0.5)",
            }}>
              Round {round.round}
            </span>
            <div style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.06)" }} />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {round.critiques?.map((c: any, ci: number) => {
              const challengerInfo = VALIDATORS.find((v) => v.model === c.challenger);
              const targetInfo = VALIDATORS.find((v) => v.model === c.target);
              return (
                <div key={ci} style={{
                  background: "rgba(255,255,255,0.03)", borderRadius: 10,
                  padding: "10px 14px",
                  borderLeft: `3px solid ${c.valid ? "#FF3366" : "#FFB800"}`,
                }}>
                  <div style={{
                    display: "flex", alignItems: "center", gap: 6, marginBottom: 4,
                  }}>
                    <span style={{
                      color: challengerInfo?.color, fontWeight: 700, fontSize: 12,
                    }}>
                      {c.challenger}
                    </span>
                    <span style={{ color: "rgba(240,236,226,0.3)", fontSize: 11 }}>→</span>
                    <span style={{
                      color: targetInfo?.color, fontWeight: 700, fontSize: 12,
                    }}>
                      {c.target}
                    </span>
                    <span style={{
                      marginLeft: "auto",
                      background: c.valid
                        ? "rgba(255,51,102,0.15)"
                        : "rgba(255,184,0,0.15)",
                      color: c.valid ? "#FF3366" : "#FFB800",
                      borderRadius: 12, padding: "2px 8px", fontSize: 10,
                      fontFamily: "'DM Mono', monospace",
                    }}>
                      {(c.type || "challenge").replace("_", " ")}
                    </span>
                  </div>
                  <p style={{
                    color: "rgba(240,236,226,0.7)", fontSize: 12,
                    margin: 0, lineHeight: 1.5,
                  }}>
                    {c.critique}
                  </p>
                  <div style={{ marginTop: 6, display: "flex", gap: 12 }}>
                    <span style={{
                      fontSize: 10, color: "rgba(240,236,226,0.4)",
                      fontFamily: "'DM Mono', monospace",
                    }}>
                      severity: {c.severity}
                    </span>
                    <span style={{
                      fontSize: 10,
                      color: c.valid ? "#00D4AA" : "#FF3366",
                      fontFamily: "'DM Mono', monospace",
                    }}>
                      {c.valid ? "upheld" : "dismissed"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

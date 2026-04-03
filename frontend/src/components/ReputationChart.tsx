"use client";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import { VALIDATORS } from "../lib/constants";

const REPUTATION_HISTORY: Record<string, number[]> = {
  "gpt-4o": [6.5, 6.8, 7.0, 6.9, 7.1, 7.3, 7.2, 7.4, 7.2, 7.5, 7.3, 7.2],
  "claude-sonnet": [7.0, 7.2, 7.1, 7.4, 7.6, 7.5, 7.8, 7.7, 7.9, 7.8, 8.0, 7.8],
  "gemini-pro": [6.0, 6.3, 6.5, 6.4, 6.7, 6.8, 6.6, 7.0, 6.9, 7.1, 6.8, 6.9],
  "llama-3": [5.5, 5.8, 6.0, 6.2, 6.1, 6.3, 6.5, 6.4, 6.6, 6.5, 6.7, 6.5],
  "mistral-large": [6.2, 6.4, 6.6, 6.5, 6.8, 7.0, 6.9, 7.1, 7.0, 7.2, 7.1, 7.0],
};

export { REPUTATION_HISTORY };

export default function ReputationChart() {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const data = months.map((m, i) => {
    const point: any = { month: m };
    Object.entries(REPUTATION_HISTORY).forEach(([model, scores]) => {
      point[model] = scores[i];
    });
    return point;
  });

  return (
    <div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ left: 0, right: 10, top: 10, bottom: 5 }}>
          <XAxis
            dataKey="month"
            tick={{ fill: "rgba(240,236,226,0.4)", fontSize: 10, fontFamily: "'DM Mono', monospace" }}
            axisLine={false} tickLine={false}
          />
          <YAxis
            domain={[4, 9]}
            tick={{ fill: "rgba(240,236,226,0.4)", fontSize: 10, fontFamily: "'DM Mono', monospace" }}
            axisLine={false} tickLine={false}
          />
          <Tooltip contentStyle={{
            background: "#1A1814",
            border: "1px solid rgba(240,236,226,0.1)",
            borderRadius: 8,
            fontFamily: "'DM Sans', sans-serif",
            color: "#F0ECE2",
          }} />
          {VALIDATORS.map((v) => (
            <Line
              key={v.model} type="monotone" dataKey={v.model}
              stroke={v.color} strokeWidth={2} dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 12 }}>
        {VALIDATORS.map((v) => (
          <div key={v.model} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 10, height: 3, borderRadius: 2, background: v.color }} />
            <span style={{
              fontSize: 10, color: "rgba(240,236,226,0.5)",
              fontFamily: "'DM Mono', monospace",
            }}>
              {v.model}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

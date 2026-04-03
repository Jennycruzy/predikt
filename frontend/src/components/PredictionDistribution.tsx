"use client";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { VALIDATORS } from "../lib/constants";

interface Props {
  validators: any[];
}

export default function PredictionDistribution({ validators }: Props) {
  if (!validators?.length) return null;

  const data = validators
    .map((v: any) => {
      const info = VALIDATORS.find((x) => x.model === v.model);
      return {
        name: v.model.split("-").pop(),
        prediction: +(v.prediction * 100).toFixed(1),
        score: +(v.score * 100).toFixed(0),
        fill: info?.color || "#888",
      };
    })
    .sort((a, b) => a.prediction - b.prediction);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20, top: 5, bottom: 5 }}>
        <XAxis
          type="number" domain={[0, 100]}
          tick={{ fill: "rgba(240,236,226,0.4)", fontSize: 10, fontFamily: "'DM Mono', monospace" }}
          axisLine={false} tickLine={false}
        />
        <YAxis
          type="category" dataKey="name"
          tick={{ fill: "#F0ECE2", fontSize: 11, fontFamily: "'DM Sans', sans-serif" }}
          axisLine={false} tickLine={false} width={70}
        />
        <Tooltip contentStyle={{
          background: "#1A1814",
          border: "1px solid rgba(240,236,226,0.1)",
          borderRadius: 8,
          fontFamily: "'DM Sans', sans-serif",
          color: "#F0ECE2",
        }} />
        <Bar dataKey="prediction" radius={[0, 6, 6, 0]} barSize={18}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.fill} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

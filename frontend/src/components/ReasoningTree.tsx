"use client";
import { useRef, useEffect } from "react";
import * as d3 from "d3";
import { VALIDATORS } from "../lib/constants";

interface Props {
  market: any;
}

export default function ReasoningTree({ market }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !market?.validators?.length) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const w = 900, h = 600;
    svg.attr("viewBox", `0 0 ${w} ${h}`);

    const treeData = {
      name: market.question.length > 50
        ? market.question.slice(0, 50) + "…"
        : market.question,
      children: market.validators.map((v: any) => {
        const vInfo = VALIDATORS.find((x) => x.model === v.model);
        const critiques: any[] = [];
        market.debate_rounds?.forEach((r: any) => {
          r.critiques?.forEach((c: any) => {
            if (c.target === v.model) critiques.push(c);
          });
        });
        return {
          name: v.model,
          color: vInfo?.color || "#888",
          prediction: v.prediction,
          score: v.score,
          children: critiques.map((c: any) => ({
            name: `${c.challenger}: ${c.type.replace("_", " ")}`,
            color: c.valid ? "#FF3366" : "#FFB800",
            severity: c.severity,
          })),
        };
      }),
    };

    const root = d3.hierarchy(treeData);
    const treeLayout = d3.tree().size([h - 80, w - 300]);
    treeLayout(root as any);

    // Links
    svg.selectAll(".link")
      .data(root.links())
      .enter().append("path")
      .attr("d", d3.linkHorizontal()
        .x((d: any) => d.y + 120)
        .y((d: any) => d.x + 40) as any)
      .attr("fill", "none")
      .attr("stroke", (d: any) => d.target.data.color || "rgba(255,255,255,0.1)")
      .attr("stroke-width", (d: any) => d.target.depth === 1 ? 2.5 : 1.5)
      .attr("stroke-opacity", 0.5);

    // Nodes
    const nodes = svg.selectAll(".node")
      .data(root.descendants())
      .enter().append("g")
      .attr("transform", (d: any) => `translate(${d.y + 120},${d.x + 40})`);

    nodes.append("circle")
      .attr("r", (d: any) => d.depth === 0 ? 10 : d.depth === 1 ? 8 : 5)
      .attr("fill", (d: any) => d.data.color || "#F0ECE2")
      .attr("stroke", (d: any) => d.depth === 0 ? "#F0ECE2" : "none")
      .attr("stroke-width", 2);

    nodes.append("text")
      .attr("x", (d: any) => d.depth === 0 ? -15 : d.children ? -14 : 12)
      .attr("y", (d: any) => d.depth === 0 ? -18 : 4)
      .attr("text-anchor", (d: any) =>
        d.depth === 0 ? "end" : d.children ? "end" : "start")
      .attr("fill", "#F0ECE2")
      .attr("font-size", (d: any) => d.depth === 0 ? 12 : d.depth === 1 ? 11 : 9)
      .attr("font-family", "'DM Sans', sans-serif")
      .attr("opacity", (d: any) => d.depth === 2 ? 0.6 : 0.9)
      .text((d: any) => {
        const n = d.data.name;
        if (d.depth === 1) return `${n} (${(d.data.prediction * 100).toFixed(0)}%)`;
        return n.length > 45 ? n.slice(0, 45) + "…" : n;
      });

    // Score badges
    nodes.filter((d: any) => d.depth === 1)
      .append("text")
      .attr("x", -14).attr("y", 18)
      .attr("text-anchor", "end")
      .attr("fill", (d: any) => d.data.color)
      .attr("font-size", 9)
      .attr("font-family", "'DM Mono', monospace")
      .text((d: any) => `score: ${d.data.score?.toFixed(2)}`);
  }, [market]);

  if (!market?.validators?.length) {
    return (
      <p style={{ color: "rgba(240,236,226,0.3)", fontStyle: "italic" }}>
        Launch debate to generate reasoning tree
      </p>
    );
  }

  return (
    <div style={{
      background: "rgba(0,0,0,0.3)", borderRadius: 12, padding: 16, overflow: "auto",
    }}>
      <svg ref={svgRef} style={{ width: "100%", height: 400 }} />
    </div>
  );
}

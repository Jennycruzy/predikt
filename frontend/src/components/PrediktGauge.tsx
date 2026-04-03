"use client";
import { useRef, useEffect } from "react";
import * as d3 from "d3";

interface Props {
  value: number | null;   // 0-1 probability
  confidence: number | null;
  size?: number;
}

export default function PrediktGauge({ value, confidence, size = 220 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || value == null) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const w = size, h = size;
    const r = w * 0.38;
    const cx = w / 2, cy = h / 2 + 10;
    const startAngle = -Math.PI * 0.75;
    const endAngle = Math.PI * 0.75;
    const totalAngle = endAngle - startAngle;

    const arc = d3.arc()
      .innerRadius(r - 14)
      .outerRadius(r)
      .startAngle(startAngle)
      .cornerRadius(7);

    // Background track
    svg.append("path")
      .attr("d", arc({ endAngle } as any))
      .attr("transform", `translate(${cx},${cy})`)
      .attr("fill", "rgba(255,255,255,0.06)");

    // Gradient
    const gradient = svg.append("defs")
      .append("linearGradient")
      .attr("id", "gaugeGrad")
      .attr("x1", "0%").attr("y1", "0%")
      .attr("x2", "100%").attr("y2", "0%");
    gradient.append("stop").attr("offset", "0%").attr("stop-color", "#FF3366");
    gradient.append("stop").attr("offset", "50%").attr("stop-color", "#FFB800");
    gradient.append("stop").attr("offset", "100%").attr("stop-color", "#00D4AA");

    // Value arc
    const valAngle = startAngle + totalAngle * value;
    svg.append("path")
      .attr("d", arc({ endAngle: valAngle } as any))
      .attr("transform", `translate(${cx},${cy})`)
      .attr("fill", "url(#gaugeGrad)");

    // Center text
    svg.append("text")
      .attr("x", cx).attr("y", cy - 8)
      .attr("text-anchor", "middle")
      .attr("fill", "#F0ECE2")
      .attr("font-size", size * 0.2)
      .attr("font-weight", "800")
      .attr("font-family", "'DM Mono', monospace")
      .text(`${(value * 100).toFixed(0)}%`);

    svg.append("text")
      .attr("x", cx).attr("y", cy + 18)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(240,236,226,0.5)")
      .attr("font-size", 11)
      .attr("font-family", "'DM Sans', sans-serif")
      .text(confidence != null ? `${(confidence * 100).toFixed(0)}% confidence` : "");
  }, [value, confidence, size]);

  if (value == null) {
    return (
      <div style={{
        width: size, height: size,
        display: "flex", alignItems: "center", justifyContent: "center",
        color: "rgba(240,236,226,0.3)", fontFamily: "'DM Sans',sans-serif", fontSize: 14,
      }}>
        Awaiting debate...
      </div>
    );
  }

  return <svg ref={svgRef} width={size} height={size} />;
}

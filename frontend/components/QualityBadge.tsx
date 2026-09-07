"use client";

import React from "react";
import { ImageQuality } from "../lib/api";

interface QualityBadgeProps {
  quality: ImageQuality;
}

export function QualityBadge({ quality }: QualityBadgeProps) {
  const isGradable = quality.status === "gradable";

  return (
    <div style={{
      display: "inline-flex",
      alignItems: "center",
      gap: "0.75rem",
      padding: "0.6rem 1.25rem",
      borderRadius: "12px",
      background: isGradable ? "rgba(16, 185, 129, 0.12)" : "rgba(239, 68, 68, 0.12)",
      border: `1px solid ${isGradable ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
      color: isGradable ? "#10b981" : "#ef4444",
      fontWeight: "700",
      fontSize: "0.95rem"
    }}>
      <div style={{
        width: "10px",
        height: "10px",
        borderRadius: "50%",
        backgroundColor: isGradable ? "#10b981" : "#ef4444",
        boxShadow: `0 0 10px ${isGradable ? "#10b981" : "#ef4444"}`
      }} />
      <span>Quality Status: {isGradable ? "GRADABLE" : "UNGRADABLE"}</span>
      <span style={{
        marginLeft: "0.5rem",
        paddingLeft: "0.75rem",
        borderLeft: `1px solid ${isGradable ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
        color: "var(--text-main)",
        fontSize: "0.85rem",
        fontWeight: "600"
      }}>
        Score: {(quality.score * 100).toFixed(1)}%
      </span>
    </div>
  );
}

"use client";

import React from "react";
import { ImageQuality } from "../lib/api";

interface QualityBadgeProps {
  quality: ImageQuality;
}

export function QualityBadge({ quality }: QualityBadgeProps) {
  const statusUpper = (quality.status || "").toUpperCase();
  const isBorderline = statusUpper === "BORDERLINE";
  const isUngradable = statusUpper === "UNGRADABLE";
  const isGradable = !isUngradable && !isBorderline;

  const color = isBorderline ? "#d97706" : isGradable ? "#10b981" : "#ef4444";
  const bg = isBorderline
    ? "rgba(217, 119, 6, 0.12)"
    : isGradable
    ? "rgba(16, 185, 129, 0.12)"
    : "rgba(239, 68, 68, 0.12)";
  const border = isBorderline
    ? "rgba(217, 119, 6, 0.3)"
    : isGradable
    ? "rgba(16, 185, 129, 0.3)"
    : "rgba(239, 68, 68, 0.3)";

  const label = isBorderline
    ? "BORDERLINE (ENHANCED)"
    : isGradable
    ? "GRADABLE"
    : "UNGRADABLE";

  return (
    <div style={{
      display: "inline-flex",
      alignItems: "center",
      gap: "0.75rem",
      padding: "0.6rem 1.25rem",
      borderRadius: "12px",
      background: bg,
      border: `1px solid ${border}`,
      color: color,
      fontWeight: "700",
      fontSize: "0.95rem"
    }}>
      <div style={{
        width: "10px",
        height: "10px",
        borderRadius: "50%",
        backgroundColor: color,
        boxShadow: `0 0 10px ${color}`
      }} />
      <span>Quality Status: {label}</span>
      <span style={{
        marginLeft: "0.5rem",
        paddingLeft: "0.75rem",
        borderLeft: `1px solid ${border}`,
        color: "var(--text-main)",
        fontSize: "0.85rem",
        fontWeight: "600"
      }}>
        Score: {(quality.score * 100).toFixed(1)}%
      </span>
    </div>
  );
}


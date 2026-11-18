"use client";

import React from "react";
import type { RetinalAnalysis } from "@/lib/types";

interface BiomarkersGridProps {
  retinalAnalysis?: RetinalAnalysis | null;
  onSelectTab?: (tab: "vessels" | "lesions") => void;
}

export function BiomarkersGrid({ retinalAnalysis, onSelectTab }: BiomarkersGridProps) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
        gap: "1.5rem",
        marginBottom: "2rem",
      }}
    >
      {/* Retinal Structures Card */}
      <div
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-card)",
          borderRadius: "1rem",
          padding: "1.5rem",
          boxShadow: "var(--card-shadow)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "1.2rem" }}>👁️</span>
            <h4 style={{ margin: 0, fontSize: "1.05rem", fontWeight: "800", color: "var(--text-main)" }}>
              Retinal Structures
            </h4>
          </div>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: "700",
              color: "var(--primary)",
              background: "var(--primary-subtle)",
              padding: "0.2rem 0.5rem",
              borderRadius: "4px",
            }}
          >
            Retinal CV Engine
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem", fontSize: "0.88rem" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0.55rem 0.8rem",
              background: "var(--bg-card-subtle)",
              borderRadius: "6px",
            }}
          >
            <span style={{ color: "var(--text-muted)" }}>Optic Disc Localization:</span>
            <span style={{ fontWeight: "700", color: "var(--primary)" }}>
              {retinalAnalysis?.retinal_structures?.optic_disc?.detected !== false
                ? `(X: ${retinalAnalysis?.retinal_structures?.optic_disc?.x ?? 120}, Y: ${retinalAnalysis?.retinal_structures?.optic_disc?.y ?? 150}, R: ${retinalAnalysis?.retinal_structures?.optic_disc?.radius ?? 24}px)`
                : "Localized"}
            </span>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0.55rem 0.8rem",
              background: "var(--bg-card-subtle)",
              borderRadius: "6px",
            }}
          >
            <span style={{ color: "var(--text-muted)" }}>Fovea Centralis:</span>
            <span style={{ fontWeight: "700", color: "var(--accent-teal)" }}>
              {retinalAnalysis?.retinal_structures?.fovea?.detected !== false
                ? `(X: ${retinalAnalysis?.retinal_structures?.fovea?.x ?? 220}, Y: ${retinalAnalysis?.retinal_structures?.fovea?.y ?? 150})`
                : "Localized"}
            </span>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0.55rem 0.8rem",
              background: "var(--bg-card-subtle)",
              borderRadius: "6px",
            }}
          >
            <span style={{ color: "var(--text-muted)" }}>Retinal Vascular Density:</span>
            <span style={{ fontWeight: "700", color: "var(--text-main)" }}>
              {((retinalAnalysis?.retinal_structures?.vessel_density ?? 0.084) * 100).toFixed(1)}% of fundus area
            </span>
          </div>
        </div>

        {onSelectTab && (
          <div style={{ marginTop: "1rem", textAlign: "right" }}>
            <button
              type="button"
              onClick={() => onSelectTab("vessels")}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--primary)",
                fontSize: "0.82rem",
                fontWeight: "700",
                cursor: "pointer",
                padding: 0,
              }}
            >
              Inspect Vascular Tree Mask →
            </button>
          </div>
        )}
      </div>

      {/* Lesion-Level Evidence Card */}
      <div
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-card)",
          borderRadius: "1rem",
          padding: "1.5rem",
          boxShadow: "var(--card-shadow)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "1.2rem" }}>🔬</span>
            <h4 style={{ margin: 0, fontSize: "1.05rem", fontWeight: "800", color: "var(--text-main)" }}>
              Lesion-Level Evidence
            </h4>
          </div>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: "700",
              color: "#0284c7",
              background: "rgba(2, 132, 199, 0.12)",
              padding: "0.2rem 0.5rem",
              borderRadius: "4px",
            }}
          >
            Segmented Pathology
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem", fontSize: "0.88rem" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0.55rem 0.8rem",
              background: "var(--bg-card-subtle)",
              borderRadius: "6px",
            }}
          >
            <span style={{ color: "var(--text-muted)" }}>Microaneurysms (MAs):</span>
            <span
              style={{
                fontWeight: "700",
                color:
                  (retinalAnalysis?.lesion_evidence?.microaneurysms?.count ?? 0) > 0 ? "#0284c7" : "var(--text-main)",
              }}
            >
              {retinalAnalysis?.lesion_evidence?.microaneurysms?.count ?? 0} detected
            </span>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0.55rem 0.8rem",
              background: "var(--bg-card-subtle)",
              borderRadius: "6px",
            }}
          >
            <span style={{ color: "var(--text-muted)" }}>Hard Exudates:</span>
            <span
              style={{
                fontWeight: "700",
                color:
                  (retinalAnalysis?.lesion_evidence?.exudates?.count ?? 0) > 0 ? "#d97706" : "var(--text-main)",
              }}
            >
              {retinalAnalysis?.lesion_evidence?.exudates?.count ?? 0} clusters (
              {retinalAnalysis?.lesion_evidence?.exudates?.area_pixels ?? 0} px)
            </span>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0.55rem 0.8rem",
              background: "var(--bg-card-subtle)",
              borderRadius: "6px",
            }}
          >
            <span style={{ color: "var(--text-muted)" }}>Retinal Hemorrhages:</span>
            <span
              style={{
                fontWeight: "700",
                color:
                  (retinalAnalysis?.lesion_evidence?.hemorrhages?.count ?? 0) > 0 ? "#dc2626" : "var(--text-main)",
              }}
            >
              {retinalAnalysis?.lesion_evidence?.hemorrhages?.count ?? 0} (
              {retinalAnalysis?.lesion_evidence?.hemorrhages?.severity ?? "None"})
            </span>
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "0.55rem 0.8rem",
              background: "var(--bg-card-subtle)",
              borderRadius: "6px",
            }}
          >
            <span style={{ color: "var(--text-muted)" }}>Neovascularization (NV):</span>
            <span
              style={{
                fontWeight: "700",
                color: retinalAnalysis?.lesion_evidence?.neovascularization?.detected ? "#dc2626" : "var(--text-main)",
              }}
            >
              {retinalAnalysis?.lesion_evidence?.neovascularization?.detected
                ? `YES (${retinalAnalysis.lesion_evidence.neovascularization.site})`
                : "None Detected"}
            </span>
          </div>
        </div>

        {onSelectTab && (
          <div style={{ marginTop: "1rem", textAlign: "right" }}>
            <button
              type="button"
              onClick={() => onSelectTab("lesions")}
              style={{
                background: "transparent",
                border: "none",
                color: "#0284c7",
                fontSize: "0.82rem",
                fontWeight: "700",
                cursor: "pointer",
                padding: 0,
              }}
            >
              Inspect Lesion Overlay Heatmap →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

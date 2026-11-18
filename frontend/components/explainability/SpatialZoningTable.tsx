"use client";

import React from "react";
import type { SpatialAnalysis } from "@/lib/types";

interface SpatialZoningTableProps {
  spatialAnalysis?: SpatialAnalysis | null;
  onSelectSpatialTab?: () => void;
}

export function SpatialZoningTable({ spatialAnalysis, onSelectSpatialTab }: SpatialZoningTableProps) {
  if (!spatialAnalysis) return null;

  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border-card)",
        borderRadius: "1rem",
        padding: "1.5rem",
        marginBottom: "2rem",
        boxShadow: "var(--card-shadow)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
        <div>
          <h4 style={{ margin: 0, fontSize: "1.05rem", fontWeight: "800", color: "var(--text-main)" }}>
            6-Sector Retinal Zoning & Anatomical Analysis
          </h4>
          <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.82rem", color: "var(--text-muted)" }}>
            ETDRS-aligned sector partition mapping pathology to retinal anatomical coordinates
          </p>
        </div>
        {onSelectSpatialTab && (
          <button
            type="button"
            onClick={onSelectSpatialTab}
            style={{
              padding: "0.4rem 0.8rem",
              background: "var(--primary-subtle)",
              color: "var(--primary)",
              border: "1px solid rgba(13, 148, 136, 0.2)",
              borderRadius: "6px",
              fontSize: "0.78rem",
              fontWeight: "700",
              cursor: "pointer",
            }}
          >
            View Spatial Map →
          </button>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.25rem" }}>
        <div style={{ padding: "0.75rem", background: "var(--bg-card-subtle)", borderRadius: "8px" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Macular Threat Level</div>
          <div
            style={{
              fontSize: "0.95rem",
              fontWeight: "800",
              color:
                spatialAnalysis.macula_threat_level === "HIGH_THREAT"
                  ? "#dc2626"
                  : spatialAnalysis.macula_threat_level === "BORDERLINE"
                  ? "#d97706"
                  : "#16a34a",
            }}
          >
            {spatialAnalysis.macula_threat_level.replace("_", " ")}
          </div>
        </div>
        <div style={{ padding: "0.75rem", background: "var(--bg-card-subtle)", borderRadius: "8px" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Affected Quadrants</div>
          <div style={{ fontSize: "0.95rem", fontWeight: "800", color: "var(--text-main)" }}>
            {spatialAnalysis.quadrants_affected_count} of 4 ({spatialAnalysis.affected_quadrants.join(", ") || "None"})
          </div>
        </div>
        <div style={{ padding: "0.75rem", background: "var(--bg-card-subtle)", borderRadius: "8px" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Primary Attention Hotspot</div>
          <div style={{ fontSize: "0.95rem", fontWeight: "800", color: "var(--primary)" }}>
            {spatialAnalysis.primary_attention_hotspot || "None"}
          </div>
        </div>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
          <thead>
            <tr style={{ background: "var(--bg-card-subtle)", textAlign: "left" }}>
              <th style={{ padding: "0.6rem 0.75rem", borderBottom: "2px solid var(--border-card)" }}>Sector</th>
              <th style={{ padding: "0.6rem 0.75rem", borderBottom: "2px solid var(--border-card)" }}>Status</th>
              <th style={{ padding: "0.6rem 0.75rem", borderBottom: "2px solid var(--border-card)" }}>MAs</th>
              <th style={{ padding: "0.6rem 0.75rem", borderBottom: "2px solid var(--border-card)" }}>Exudates</th>
              <th style={{ padding: "0.6rem 0.75rem", borderBottom: "2px solid var(--border-card)" }}>Hems</th>
              <th style={{ padding: "0.6rem 0.75rem", borderBottom: "2px solid var(--border-card)" }}>Mean Attn</th>
              <th style={{ padding: "0.6rem 0.75rem", borderBottom: "2px solid var(--border-card)" }}>Clinical Summary</th>
            </tr>
          </thead>
          <tbody>
            {spatialAnalysis.zones.map((zone) => (
              <tr key={zone.zone_id} style={{ borderBottom: "1px solid var(--border-card)" }}>
                <td style={{ padding: "0.6rem 0.75rem", fontWeight: "700" }}>{zone.zone_name}</td>
                <td style={{ padding: "0.6rem 0.75rem" }}>
                  <span
                    style={{
                      padding: "0.15rem 0.45rem",
                      borderRadius: "4px",
                      fontSize: "0.72rem",
                      fontWeight: "700",
                      background:
                        zone.status === "MACULAR_THREAT" || zone.status === "CRITICAL_NEOVASCULARIZATION"
                          ? "rgba(220, 38, 38, 0.12)"
                          : zone.status === "ACTIVE_LESIONS"
                          ? "rgba(217, 119, 6, 0.12)"
                          : "rgba(22, 163, 74, 0.12)",
                      color:
                        zone.status === "MACULAR_THREAT" || zone.status === "CRITICAL_NEOVASCULARIZATION"
                          ? "#dc2626"
                          : zone.status === "ACTIVE_LESIONS"
                          ? "#d97706"
                          : "#16a34a",
                    }}
                  >
                    {zone.status_label}
                  </span>
                </td>
                <td style={{ padding: "0.6rem 0.75rem" }}>{zone.microaneurysms_count}</td>
                <td style={{ padding: "0.6rem 0.75rem" }}>
                  {zone.exudates_count > 0 ? `${zone.exudates_count} (${zone.exudates_area_px}px)` : "0"}
                </td>
                <td style={{ padding: "0.6rem 0.75rem" }}>{zone.hemorrhages_count}</td>
                <td style={{ padding: "0.6rem 0.75rem" }}>{(zone.attention_mean * 100).toFixed(1)}%</td>
                <td style={{ padding: "0.6rem 0.75rem", color: "var(--text-muted)" }}>
                  {zone.clinical_explanation || zone.lesion_summary}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

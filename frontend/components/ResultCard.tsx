"use client";

import Link from "next/link";
import React from "react";
import { getStaticImageUrl, ScreeningReport } from "../lib/api";
import { QualityBadge } from "./QualityBadge";

interface ResultCardProps {
  report: ScreeningReport;
  originalFile: File | null;
}

const GRADE_COLORS: Record<number, string> = {
  0: "#10b981", // No DR (Green)
  1: "#0284c7", // Mild DR (Blue)
  2: "#d97706", // Moderate DR (Amber)
  3: "#ea580c", // Severe DR (Orange)
  4: "#dc2626", // Proliferative DR (Red)
};

export function ResultCard({ report, originalFile }: ResultCardProps) {
  const { image_quality, dr_prediction, explanation, recommendation, disclaimer } = report;
  const isGradable = image_quality.status === "gradable";
  const caseId = report.case_id || `case_${report.sample_id}`;

  const originalUrl = originalFile ? URL.createObjectURL(originalFile) : null;
  const gradcamUrl = getStaticImageUrl(explanation?.gradcam_path);

  if (!isGradable) {
    return (
      <div className="card" style={{ borderLeft: "4px solid #ef4444" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem" }}>
          <QualityBadge quality={image_quality} />
          <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Case: <strong>{caseId}</strong></span>
        </div>

        <div style={{
          background: "rgba(239, 68, 68, 0.08)",
          border: "1px solid rgba(239, 68, 68, 0.25)",
          borderRadius: "0.75rem",
          padding: "1.5rem",
          marginBottom: "1.5rem"
        }}>
          <h3 style={{ color: "#ef4444", fontSize: "1.2rem", fontWeight: "700", marginBottom: "0.5rem" }}>
            ⚠️ Image Ungradable - DR Screening Aborted
          </h3>
          <p style={{ color: "var(--text-main)", fontSize: "0.95rem", lineHeight: "1.5" }}>
            The uploaded image does not meet the minimum image quality standards required for safe automated diagnosis.
          </p>

          {image_quality.issues.length > 0 && (
            <div style={{ marginTop: "1rem" }}>
              <div style={{ fontWeight: "700", fontSize: "0.85rem", color: "#ef4444", marginBottom: "0.4rem" }}>
                Detected Quality Deficiencies:
              </div>
              <ul style={{ paddingLeft: "1.25rem", color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: "1.5" }}>
                {image_quality.issues.map((issue, idx) => (
                  <li key={idx}>{issue}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div style={{
          background: "var(--bg-card-subtle)",
          borderRadius: "0.75rem",
          padding: "1.25rem",
          border: "1px solid var(--border-card)",
          marginBottom: "1.5rem"
        }}>
          <h4 style={{ color: "var(--primary)", fontSize: "0.95rem", fontWeight: "700", marginBottom: "0.4rem" }}>
            📷 Recapture Guidance
          </h4>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: "1.5" }}>
            {recommendation}
          </p>
        </div>

        {/* Telemedicine Recapture Card */}
        <div style={{
          background: "var(--bg-card-subtle)",
          border: "1px solid var(--border-card)",
          borderRadius: "0.85rem",
          padding: "1rem 1.25rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "1.5rem",
          flexWrap: "wrap",
          gap: "0.75rem"
        }}>
          <div>
            <div style={{ fontWeight: "700", color: "var(--text-main)", fontSize: "0.95rem" }}>
              📋 Recapture Request Logged in Telemedicine Queue
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Case ID: <strong style={{ color: "var(--primary)" }}>{caseId}</strong> • Status: RECAPTURE_REQUIRED
            </div>
          </div>
          <Link
            href="/dashboard"
            style={{
              background: "var(--bg-card)",
              color: "var(--primary)",
              border: "1px solid var(--border-card)",
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              fontSize: "0.85rem",
              fontWeight: "700",
              textDecoration: "none"
            }}
          >
            View in Telemedicine Dashboard →
          </Link>
        </div>

        <div style={{ fontSize: "0.8rem", color: "var(--text-subtle)", fontStyle: "italic", textAlign: "center" }}>
          {disclaimer}
        </div>
      </div>
    );
  }

  const gradeColor = dr_prediction ? GRADE_COLORS[dr_prediction.grade] : "var(--primary)";

  return (
    <div className="card">
      {/* Top Header Row */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem" }}>
        <QualityBadge quality={image_quality} />
        <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Case: <strong>{caseId}</strong></span>
      </div>

      {dr_prediction && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "1.5rem",
          marginBottom: "2rem"
        }}>
          {/* Diagnosis Badge Box */}
          <div style={{
            background: "var(--bg-card-subtle)",
            border: `1px solid ${gradeColor}50`,
            borderRadius: "1rem",
            padding: "1.5rem"
          }}>
            <div style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              DR Screening Prediction
            </div>
            <div style={{ fontSize: "1.85rem", fontWeight: "800", color: gradeColor, marginTop: "0.25rem" }}>
              Level {dr_prediction.grade}: {dr_prediction.label}
            </div>

            <div style={{ marginTop: "1rem", display: "flex", alignItems: "center", gap: "1rem" }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
                  <span style={{ color: "var(--text-muted)" }}>Calibrated Confidence:</span>
                  <span style={{ color: "var(--text-main)", fontWeight: "700" }}>{(dr_prediction.confidence * 100).toFixed(1)}%</span>
                </div>
                <div style={{ height: "8px", background: "var(--border-card)", borderRadius: "4px", overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${dr_prediction.confidence * 100}%`, backgroundColor: gradeColor, borderRadius: "4px" }} />
                </div>
              </div>
            </div>
          </div>

          {/* Uncertainty Metrics Box */}
          <div style={{
            background: "var(--bg-card-subtle)",
            border: "1px solid var(--border-card)",
            borderRadius: "1rem",
            padding: "1.5rem",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center"
          }}>
            <div style={{ fontSize: "0.85rem", fontWeight: "600", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Model Uncertainty Indicators
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.75rem", fontSize: "0.9rem" }}>
              <span style={{ color: "var(--text-muted)" }}>Shannon Entropy:</span>
              <span style={{ color: "var(--primary)", fontWeight: "700" }}>{dr_prediction.uncertainty.entropy.toFixed(3)}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.4rem", fontSize: "0.9rem" }}>
              <span style={{ color: "var(--text-muted)" }}>Prediction Margin:</span>
              <span style={{ color: "var(--accent-teal)", fontWeight: "700" }}>{(dr_prediction.uncertainty.margin * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Class Probabilities Bar Chart */}
      {dr_prediction && (
        <div style={{
          background: "var(--bg-card-subtle)",
          border: "1px solid var(--border-card)",
          borderRadius: "1rem",
          padding: "1.5rem",
          marginBottom: "2rem"
        }}>
          <h4 style={{ fontSize: "0.95rem", fontWeight: "700", color: "var(--text-main)", marginBottom: "1rem" }}>
            Class Probability Distribution
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {Object.entries(dr_prediction.probabilities).map(([clsLabel, prob]) => (
              <div key={clsLabel} style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                <div style={{ width: "130px", fontSize: "0.85rem", color: "var(--text-main)", fontWeight: "500" }}>
                  {clsLabel}
                </div>
                <div style={{ flex: 1, height: "10px", background: "var(--border-card)", borderRadius: "5px", overflow: "hidden" }}>
                  <div style={{
                    height: "100%",
                    width: `${prob * 100}%`,
                    background: clsLabel === dr_prediction.label ? gradeColor : "var(--primary)",
                    opacity: clsLabel === dr_prediction.label ? 1 : 0.45,
                    borderRadius: "5px",
                    transition: "width 0.5s ease"
                  }} />
                </div>
                <div style={{ width: "55px", fontSize: "0.85rem", color: "var(--text-muted)", textAlign: "right", fontWeight: "600" }}>
                  {(prob * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explainable AI Visual Heatmap Overlay */}
      <div style={{ marginBottom: "2rem" }}>
        <h4 style={{ fontSize: "1.1rem", fontWeight: "700", color: "var(--text-main)", marginBottom: "1rem" }}>
          Explainable AI (Grad-CAM Saliency Analysis)
        </h4>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "1.5rem"
        }}>
          {originalUrl && (
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.5rem", fontWeight: "600" }}>
                Original Fundus Image
              </div>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={originalUrl}
                alt="Original Fundus"
                style={{ width: "100%", maxHeight: "280px", objectFit: "contain", borderRadius: "0.75rem", border: "1px solid var(--border-card)", background: "#090d16" }}
              />
            </div>
          )}

          {gradcamUrl && (
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "0.85rem", color: "var(--primary)", marginBottom: "0.5rem", fontWeight: "600" }}>
                Grad-CAM Heatmap Overlay
              </div>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={gradcamUrl}
                alt="Grad-CAM Overlay"
                style={{ width: "100%", maxHeight: "280px", objectFit: "contain", borderRadius: "0.75rem", border: "1px solid var(--primary-glow)", background: "#090d16" }}
              />
            </div>
          )}
        </div>
      </div>

      {/* Specialist Referral Recommendation Box */}
      <div style={{
        background: "var(--primary-subtle)",
        border: "1px solid var(--primary-glow)",
        borderRadius: "0.85rem",
        padding: "1.25rem 1.5rem",
        marginBottom: "1.5rem"
      }}>
        <h4 style={{ color: "var(--primary)", fontSize: "0.95rem", fontWeight: "700", marginBottom: "0.4rem" }}>
          Clinical Action Recommendation
        </h4>
        <p style={{ color: "var(--text-main)", fontSize: "0.95rem", lineHeight: "1.5" }}>
          {recommendation}
        </p>
      </div>

      {/* Telemedicine Consultation Referral Card */}
      <div style={{
        background: "var(--bg-card-subtle)",
        border: "1px solid var(--border-card)",
        borderRadius: "0.85rem",
        padding: "1.25rem 1.5rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: "1.5rem",
        flexWrap: "wrap",
        gap: "1rem",
        boxShadow: "var(--card-shadow)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{
            width: "44px",
            height: "44px",
            borderRadius: "10px",
            background: "var(--primary-subtle)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "1.5rem",
            border: "1px solid var(--primary-glow)"
          }}>
            🏥
          </div>
          <div>
            <div style={{ fontWeight: "700", color: "var(--text-main)", fontSize: "1rem" }}>
              Case Enqueued in Rural Telemedicine Consultation Network
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
              Case ID: <strong style={{ color: "var(--primary)" }}>{caseId}</strong> • Status: <span style={{ color: "var(--accent-teal)", fontWeight: "600" }}>REQUIRES_SPECIALIST_REVIEW</span>
            </div>
          </div>
        </div>

        <Link
          href="/dashboard"
          style={{
            background: "linear-gradient(135deg, var(--primary), var(--accent-teal))",
            color: "#ffffff",
            padding: "0.7rem 1.4rem",
            borderRadius: "8px",
            fontSize: "0.9rem",
            fontWeight: "800",
            textDecoration: "none",
            boxShadow: "0 4px 15px var(--primary-glow)",
            transition: "all 0.2s ease",
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem"
          }}
        >
          <span>Open Case in Telemedicine Dashboard</span>
          <span>→</span>
        </Link>
      </div>

      {/* AI Disclaimer */}
      <div style={{ fontSize: "0.8rem", color: "var(--text-subtle)", fontStyle: "italic", textAlign: "center" }}>
        {disclaimer}
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";
import { Header } from "../../components/Header";
import { getStaticImageUrl } from "../../lib/api";

interface CaseItem {
  case_id: string;
  created_at: string;
  status: string;
  specialist_decision?: string;
  specialist_notes?: string;
  specialist_id?: string;
  screening_report: any;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function TelemedicineDashboard() {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<CaseItem | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [overrideGrade, setOverrideGrade] = useState<number>(1);
  const [reviewSubmitting, setReviewSubmitting] = useState(false);

  const fetchCases = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/cases`);
      if (res.ok) {
        const data: CaseItem[] = await res.json();
        // Sort cases with latest first
        data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        setCases(data);
        if (data.length > 0 && !selectedCase) {
          setSelectedCase(data[0]);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleReviewSubmit = async (decision: "confirm" | "override" | "request_recapture") => {
    if (!selectedCase) return;
    setReviewSubmitting(true);

    try {
      const payload = {
        decision,
        override_grade: decision === "override" ? overrideGrade : null,
        specialist_notes: reviewNotes,
        specialist_id: "dr_telemedicine_ophthalmologist",
      };

      const res = await fetch(`${API_BASE_URL}/api/cases/${selectedCase.case_id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const updated = await res.json();
        setSelectedCase(updated);
        fetchCases();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setReviewSubmitting(false);
    }
  };

  const originalImgUrl = selectedCase
    ? getStaticImageUrl(
        selectedCase.screening_report.original_image_path ||
        selectedCase.screening_report.explanation?.original_image_path
      )
    : null;

  const gradcamImgUrl = selectedCase
    ? getStaticImageUrl(selectedCase.screening_report.explanation?.gradcam_path)
    : null;

  return (
    <>
      <Header />
      <div className="container">
        <div className="header">
          <div className="badge">
            <span className="badge-dot" />
            Rural Telemedicine Network
          </div>
          <h1 className="title">Specialist Review Dashboard</h1>
          <p className="subtitle">
            Remote Ophthalmologist Consultation & AI Screening Verification Queue for Rural Health Centers.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "1.5rem" }}>
          {/* Cases Queue Sidebar */}
          <div className="card" style={{ padding: "1.25rem", height: "fit-content" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: "700", color: "var(--text-main)" }}>
                Screening Queue ({cases.length})
              </h3>
              <button
                type="button"
                onClick={fetchCases}
                style={{
                  background: "var(--primary-subtle)",
                  color: "var(--primary)",
                  border: "1px solid var(--primary-glow)",
                  borderRadius: "6px",
                  padding: "0.25rem 0.6rem",
                  fontSize: "0.75rem",
                  fontWeight: "600",
                  cursor: "pointer"
                }}
              >
                🔄 Refresh
              </button>
            </div>

            {loading ? (
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Loading queue...</div>
            ) : cases.length === 0 ? (
              <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", padding: "1rem 0", lineHeight: "1.5" }}>
                No active cases found. Upload a fundus scan in the <Link href="/screening" style={{ color: "var(--primary)", fontWeight: "700" }}>Screening Portal</Link> to create a case.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxHeight: "600px", overflowY: "auto" }}>
                {cases.map((c) => {
                  const isSelected = selectedCase?.case_id === c.case_id;
                  const isUngradable = c.screening_report.image_quality.status === "ungradable";

                  return (
                    <div
                      key={c.case_id}
                      onClick={() => {
                        setSelectedCase(c);
                        setReviewNotes(c.specialist_notes || "");
                      }}
                      style={{
                        padding: "0.85rem",
                        borderRadius: "0.5rem",
                        background: isSelected ? "var(--primary-subtle)" : "var(--bg-card-subtle)",
                        border: `1px solid ${isSelected ? "var(--primary)" : "var(--border-card)"}`,
                        cursor: "pointer",
                        transition: "all 0.2s ease"
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", color: "var(--text-muted)" }}>
                        <span style={{ fontWeight: "700" }}>{c.case_id}</span>
                        <span style={{
                          color: c.status === "SPECIALIST_REVIEWED" ? "var(--accent-teal)" : isUngradable ? "#ef4444" : "#d97706",
                          fontWeight: "700"
                        }}>
                          {c.status}
                        </span>
                      </div>
                      <div style={{ fontWeight: "700", fontSize: "0.9rem", color: "var(--text-main)", marginTop: "0.3rem" }}>
                        {isUngradable ? "⚠️ UNGRADABLE IMAGE" : c.screening_report.dr_prediction?.label}
                      </div>
                      {c.screening_report.dr_prediction && (
                        <div style={{ fontSize: "0.75rem", color: "var(--text-subtle)", marginTop: "0.2rem" }}>
                          Confidence: {(c.screening_report.dr_prediction.confidence * 100).toFixed(1)}%
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Main Case Detail View */}
          <div className="card">
            {selectedCase ? (
              <div>
                {/* Header info */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem" }}>
                  <div>
                    <h2 style={{ fontSize: "1.4rem", fontWeight: "800", color: "var(--text-main)" }}>
                      Case: {selectedCase.case_id}
                    </h2>
                    <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                      Created: {new Date(selectedCase.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div style={{
                    padding: "0.45rem 1rem",
                    borderRadius: "20px",
                    background: selectedCase.status === "SPECIALIST_REVIEWED" ? "rgba(5, 150, 105, 0.12)" : "rgba(217, 119, 6, 0.12)",
                    color: selectedCase.status === "SPECIALIST_REVIEWED" ? "var(--accent-teal)" : "#d97706",
                    fontSize: "0.85rem",
                    fontWeight: "800",
                    border: `1px solid ${selectedCase.status === "SPECIALIST_REVIEWED" ? "var(--accent-teal)" : "#d97706"}40`
                  }}>
                    {selectedCase.status}
                  </div>
                </div>

                {/* Retinal Imagery: Original scan & Grad-CAM Heatmap */}
                <div style={{ marginBottom: "1.75rem" }}>
                  <h4 style={{ fontSize: "1rem", fontWeight: "700", color: "var(--text-main)", marginBottom: "0.75rem" }}>
                    Patient Retinal Imagery & Visual Saliency
                  </h4>

                  <div style={{
                    display: "grid",
                    gridTemplateColumns: originalImgUrl && gradcamImgUrl ? "1fr 1fr" : "1fr",
                    gap: "1.25rem"
                  }}>
                    {originalImgUrl && (
                      <div style={{
                        background: "var(--bg-card-subtle)",
                        border: "1px solid var(--border-card)",
                        borderRadius: "0.75rem",
                        padding: "1rem",
                        textAlign: "center"
                      }}>
                        <div style={{ fontSize: "0.85rem", fontWeight: "700", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
                          Uploaded Retinal Fundus Scan
                        </div>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={originalImgUrl}
                          alt="Patient Retinal Scan"
                          style={{ maxHeight: "250px", maxWidth: "100%", objectFit: "contain", borderRadius: "0.5rem", background: "#090d16" }}
                        />
                      </div>
                    )}

                    {gradcamImgUrl && (
                      <div style={{
                        background: "var(--bg-card-subtle)",
                        border: "1px solid var(--primary-glow)",
                        borderRadius: "0.75rem",
                        padding: "1rem",
                        textAlign: "center"
                      }}>
                        <div style={{ fontSize: "0.85rem", fontWeight: "700", color: "var(--primary)", marginBottom: "0.5rem" }}>
                          AI Grad-CAM Saliency Map
                        </div>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={gradcamImgUrl}
                          alt="Grad-CAM Saliency Overlay"
                          style={{ maxHeight: "250px", maxWidth: "100%", objectFit: "contain", borderRadius: "0.5rem", background: "#090d16" }}
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* AI Screening Overview Metrics */}
                <div style={{
                  background: "var(--bg-card-subtle)",
                  borderRadius: "0.75rem",
                  padding: "1.25rem",
                  border: "1px solid var(--border-card)",
                  marginBottom: "1.5rem"
                }}>
                  <h4 style={{ color: "var(--primary)", fontSize: "0.95rem", fontWeight: "700", marginBottom: "0.75rem" }}>
                    AI Screening Report Overview
                  </h4>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem", fontSize: "0.9rem" }}>
                    <div>
                      <span style={{ color: "var(--text-muted)" }}>Quality Status: </span>
                      <strong style={{ color: selectedCase.screening_report.image_quality.status === "gradable" ? "var(--accent-teal)" : "#ef4444" }}>
                        {selectedCase.screening_report.image_quality.status.toUpperCase()}
                      </strong>
                    </div>
                    {selectedCase.screening_report.dr_prediction && (
                      <div>
                        <span style={{ color: "var(--text-muted)" }}>Predicted DR: </span>
                        <strong style={{ color: "var(--text-main)" }}>{selectedCase.screening_report.dr_prediction.label}</strong>
                      </div>
                    )}
                    {selectedCase.screening_report.dr_prediction && (
                      <div>
                        <span style={{ color: "var(--text-muted)" }}>Calibrated Confidence: </span>
                        <strong style={{ color: "var(--primary)" }}>{(selectedCase.screening_report.dr_prediction.confidence * 100).toFixed(1)}%</strong>
                      </div>
                    )}
                  </div>

                  {selectedCase.screening_report.recommendation && (
                    <div style={{ marginTop: "0.75rem", fontSize: "0.85rem", color: "var(--text-muted)", borderTop: "1px solid var(--border-card)", paddingTop: "0.75rem" }}>
                      <strong>Clinical Guidance:</strong> {selectedCase.screening_report.recommendation}
                    </div>
                  )}
                </div>

                {/* Specialist Review Actions & Notes */}
                <div style={{
                  background: "var(--bg-card-subtle)",
                  borderRadius: "0.75rem",
                  padding: "1.5rem",
                  border: "1px solid var(--border-card)"
                }}>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: "700", color: "var(--text-main)", marginBottom: "1rem" }}>
                    Remote Specialist Decision & Consultation Notes
                  </h3>

                  <div style={{ marginBottom: "1rem" }}>
                    <label style={{ display: "block", fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.4rem", fontWeight: "600" }}>
                      Ophthalmologist Clinical Observations:
                    </label>
                    <textarea
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      placeholder="Enter ophthalmologist findings, specific lesion notes, laser/anti-VEGF recommendation, or follow-up timeframe..."
                      rows={3}
                      style={{
                        width: "100%",
                        background: "var(--bg-card)",
                        border: "1px solid var(--border-card)",
                        borderRadius: "0.5rem",
                        padding: "0.75rem",
                        color: "var(--text-main)",
                        fontFamily: "inherit",
                        fontSize: "0.9rem"
                      }}
                    />
                  </div>

                  <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "center" }}>
                    <button
                      onClick={() => handleReviewSubmit("confirm")}
                      disabled={reviewSubmitting}
                      style={{
                        background: "var(--accent-teal)",
                        color: "#ffffff",
                        border: "none",
                        padding: "0.65rem 1.3rem",
                        borderRadius: "6px",
                        fontWeight: "700",
                        fontSize: "0.9rem",
                        cursor: "pointer",
                        boxShadow: "0 2px 10px rgba(5, 150, 105, 0.2)"
                      }}
                    >
                      ✓ Confirm AI Result
                    </button>

                    <div style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
                      <select
                        value={overrideGrade}
                        onChange={(e) => setOverrideGrade(Number(e.target.value))}
                        style={{
                          background: "var(--bg-card)",
                          color: "var(--text-main)",
                          border: "1px solid var(--border-card)",
                          padding: "0.6rem 0.6rem",
                          borderRadius: "6px",
                          fontSize: "0.85rem",
                          fontWeight: "600"
                        }}
                      >
                        <option value={0}>0: No DR</option>
                        <option value={1}>1: Mild DR</option>
                        <option value={2}>2: Moderate DR</option>
                        <option value={3}>3: Severe DR</option>
                        <option value={4}>4: Proliferative DR</option>
                      </select>
                      <button
                        onClick={() => handleReviewSubmit("override")}
                        disabled={reviewSubmitting}
                        style={{
                          background: "#d97706",
                          color: "#ffffff",
                          border: "none",
                          padding: "0.65rem 1.1rem",
                          borderRadius: "6px",
                          fontWeight: "700",
                          fontSize: "0.85rem",
                          cursor: "pointer"
                        }}
                      >
                        ✎ Override Grade
                      </button>
                    </div>

                    <button
                      onClick={() => handleReviewSubmit("request_recapture")}
                      disabled={reviewSubmitting}
                      style={{
                        background: "rgba(239, 68, 68, 0.12)",
                        color: "#ef4444",
                        border: "1px solid rgba(239, 68, 68, 0.3)",
                        padding: "0.65rem 1.2rem",
                        borderRadius: "6px",
                        fontWeight: "700",
                        fontSize: "0.85rem",
                        cursor: "pointer"
                      }}
                    >
                      📷 Request Recapture
                    </button>
                  </div>

                  {selectedCase.specialist_decision && (
                    <div style={{
                      marginTop: "1.25rem",
                      padding: "0.75rem 1rem",
                      background: "rgba(5, 150, 105, 0.08)",
                      border: "1px solid rgba(5, 150, 105, 0.2)",
                      borderRadius: "6px",
                      fontSize: "0.85rem",
                      color: "var(--accent-teal)"
                    }}>
                      ✓ Decision recorded: <strong>{selectedCase.specialist_decision.toUpperCase()}</strong> by {selectedCase.specialist_id}
                      {selectedCase.specialist_notes && (
                        <div style={{ marginTop: "0.25rem", color: "var(--text-main)" }}>
                          Note: &quot;{selectedCase.specialist_notes}&quot;
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "4rem 2rem", color: "var(--text-muted)" }}>
                Select a screening case from the queue to view details and submit remote specialist review.
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

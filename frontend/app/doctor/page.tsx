"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import React, { Suspense, useEffect, useState } from "react";
import { FullReportModal } from "../../components/FullReportModal";
import { Header } from "../../components/Header";
import { ToastContainer, ToastMessage } from "../../components/Toast";
import { UIModal } from "../../components/UIModal";
import {
  CaseHistoryItem,
  CaseItem,
  deleteAllCases,
  deleteCase,
  fetchTelemedicineCases,
  getStaticImageUrl,
  submitSpecialistReview,
} from "../../lib/api";

const GRADE_COLORS: Record<number, string> = {
  0: "#10b981",
  1: "#0284c7",
  2: "#d97706",
  3: "#ea580c",
  4: "#dc2626",
};

const GRADE_LABELS: Record<number, string> = {
  0: "No DR",
  1: "Mild NPDR",
  2: "Moderate NPDR",
  3: "Severe NPDR",
  4: "Proliferative DR",
};

function DoctorPortalContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialCaseId = searchParams.get("case_id");

  // Queue State
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<CaseItem | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"PENDING" | "COMPLETED">("PENDING");
  const [refreshing, setRefreshing] = useState(false);

  // Doctor Review Actions State
  const [doctorNotes, setDoctorNotes] = useState("");
  const [overrideGrade, setOverrideGrade] = useState<number>(1);
  const [showOverrideSelect, setShowOverrideSelect] = useState(false);
  const [submittingReview, setSubmittingReview] = useState(false);

  // Modals & Toasts
  const [showReportModal, setShowReportModal] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [confirmClearAllModal, setConfirmClearAllModal] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (type: "success" | "info" | "warning" | "error", message: string) => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
    setToasts((prev) => [...prev, { id, type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadQueue = async (selectId?: string) => {
    try {
      setRefreshing(true);
      const data = await fetchTelemedicineCases(true);
      data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setCases(data);

      const targetId = selectId || initialCaseId;
      if (targetId) {
        const found = data.find((c) => c.case_id === targetId);
        if (found) {
          setSelectedCase(found);
          return;
        }
      }

      if (data.length > 0 && !selectedCase) {
        setSelectedCase(data[0]);
      } else if (selectedCase) {
        const found = data.find((c) => c.case_id === selectedCase.case_id);
        setSelectedCase(found || (data.length > 0 ? data[0] : null));
      } else if (data.length > 0) {
        setSelectedCase(data[0]);
      }
    } catch (err) {
      console.error("Failed to load cases queue:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadQueue();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isCaseCompleted = (c: CaseItem): boolean => {
    if (
      c.status === "COMPLETED" ||
      c.status === "CONFIRMED" ||
      c.status === "OVERRIDDEN" ||
      c.status === "SPECIALIST_REVIEWED"
    ) {
      return true;
    }
    if (c.clinical_approval === "REJECTED") {
      return true;
    }
    return false;
  };

  const pendingCount = cases.filter((c) => !isCaseCompleted(c)).length;
  const completedCount = cases.filter((c) => isCaseCompleted(c)).length;

  const filteredCases = cases.filter((c) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchId = c.case_id.toLowerCase().includes(q);
      const matchName = (c.patient_name || c.screening_report?.patient_name || "").toLowerCase().includes(q);
      if (!matchId && !matchName) return false;
    }

    const completed = isCaseCompleted(c);
    if (statusFilter === "PENDING") {
      return !completed;
    } else {
      return completed;
    }
  });

  const handleDoctorDecision = async (
    decision: "CONFIRMED" | "OVERRIDDEN" | "REQUEST_RECAPTURE"
  ) => {
    if (!selectedCase) return;

    setSubmittingReview(true);
    try {
      const updated = await submitSpecialistReview(
        selectedCase.case_id,
        decision,
        decision === "OVERRIDDEN" ? overrideGrade : undefined,
        doctorNotes,
        "dr_ophthalmologist_01"
      );

      addToast("success", `Decision '${decision}' recorded for Case ${selectedCase.case_id}.`);
      setDoctorNotes("");
      setShowOverrideSelect(false);
      await loadQueue(updated.case_id);

      if (decision === "REQUEST_RECAPTURE") {
        router.push(`/screening?case_id=${updated.case_id}&recapture=true`);
      }
    } catch (err: any) {
      addToast("error", err.message || "Failed to submit review decision.");
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleDeleteCase = async (caseId: string) => {
    try {
      await deleteCase(caseId);
      addToast("success", `Case ${caseId} deleted.`);
      setDeleteTargetId(null);
      await loadQueue();
    } catch (err: any) {
      addToast("error", err.message || "Failed to delete case.");
    }
  };

  const handleClearAll = async () => {
    try {
      const res = await deleteAllCases();
      addToast("success", res.message || "All cases deleted.");
      setConfirmClearAllModal(false);
      setSelectedCase(null);
      await loadQueue();
    } catch (err: any) {
      addToast("error", err.message || "Failed to clear cases.");
    }
  };

  const report = selectedCase?.screening_report;
  const grade = selectedCase?.override_grade !== null && selectedCase?.override_grade !== undefined
    ? selectedCase.override_grade
    : report?.retinal_analysis?.dr_grade ?? report?.dr_prediction?.grade ?? 0;
  const gradeColor = GRADE_COLORS[grade] || "var(--primary)";

  const originalUrl = selectedCase
    ? getStaticImageUrl(report?.original_image_path || report?.explanation?.original_image_path)
    : null;
  const gradcamUrl = selectedCase
    ? getStaticImageUrl(report?.retinal_analysis?.gradcam_image || report?.explanation?.gradcam_path)
    : null;
  const heatmapUrl = selectedCase
    ? getStaticImageUrl(report?.retinal_analysis?.heatmap_image || report?.explanation?.heatmap_image_path) || gradcamUrl
    : null;

  const xaiData = report?.retinal_analysis?.xai_explanation || report?.explanation?.xai_explanation;
  const highlightedRegion = xaiData?.highlighted_region || report?.explanation?.highlighted_region || "Center Region";
  const whatHeatmapShows = xaiData?.what_heatmap_shows || "Warmer colors (red/yellow) indicate where deep learning activation was highest during screening.";
  const whyThisMatters = xaiData?.why_this_matters || "The highlighted region strongly influenced the AI prediction. It does not independently prove an anatomical lesion.";
  const modelInterpretation = xaiData?.model_interpretation || `Network attention aligned with features characteristic of Grade ${grade}.`;

  const isCompleted = selectedCase ? isCaseCompleted(selectedCase) : false;

  return (
    <>
      <Header />
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      <div className="container" style={{ maxWidth: "1280px", margin: "0 auto", padding: "1.5rem 1rem" }}>
        {/* Header Row */}
        <div style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.3rem 0.8rem", borderRadius: "20px", background: "rgba(2, 132, 199, 0.12)", color: "var(--primary)", fontWeight: "700", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--primary)" }} />
              Unified Doctor & Specialist Portal
            </div>
            <h1 style={{ fontSize: "2rem", fontWeight: "800", color: "var(--text-main)", margin: "0.25rem 0" }}>
              Doctor Portal
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", margin: 0 }}>
              Specialist consultation queue for reviewing clinically approved referrals and verified screenings.
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <button
              type="button"
              onClick={() => loadQueue(selectedCase?.case_id)}
              disabled={refreshing}
              style={{
                background: "var(--bg-card)",
                color: "var(--text-main)",
                border: "1px solid var(--border-card)",
                padding: "0.5rem 1rem",
                borderRadius: "8px",
                fontSize: "0.85rem",
                fontWeight: "700",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
              }}
            >
              <span style={{ display: "inline-block", transform: refreshing ? "rotate(360deg)" : "none", transition: "transform 0.6s ease" }}>🔄</span>
              <span>Refresh</span>
            </button>

            <button
              type="button"
              onClick={() => setConfirmClearAllModal(true)}
              disabled={cases.length === 0}
              style={{
                background: "rgba(220, 38, 38, 0.08)",
                color: cases.length === 0 ? "var(--text-muted)" : "#dc2626",
                border: "1px solid rgba(220, 38, 38, 0.25)",
                borderRadius: "8px",
                padding: "0.5rem 1rem",
                fontSize: "0.85rem",
                fontWeight: "700",
                cursor: cases.length === 0 ? "not-allowed" : "pointer",
              }}
            >
              🗑️ Clear All Cases
            </button>
          </div>
        </div>

        {/* Content Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "330px 1fr", gap: "1.5rem" }}>
          {/* Left Cases Queue Sidebar */}
          <div style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border-card)",
            borderRadius: "0.85rem",
            padding: "1.25rem",
            height: "fit-content",
          }}>
            {/* Search Box */}
            <input
              type="text"
              placeholder="🔍 Search patient or Case ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem 0.75rem",
                fontSize: "0.85rem",
                borderRadius: "6px",
                border: "1px solid var(--border-card)",
                background: "var(--bg-card-subtle)",
                color: "var(--text-main)",
                marginBottom: "0.75rem",
                boxSizing: "border-box",
              }}
            />

            {/* Two Clear Categories: Pending and Completed */}
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
              <button
                type="button"
                onClick={() => setStatusFilter("PENDING")}
                style={{
                  flex: 1,
                  background: statusFilter === "PENDING" ? "var(--primary)" : "var(--bg-card-subtle)",
                  color: statusFilter === "PENDING" ? "#ffffff" : "var(--text-muted)",
                  border: "1px solid var(--border-card)",
                  padding: "0.45rem 0.5rem",
                  borderRadius: "6px",
                  fontSize: "0.82rem",
                  fontWeight: "700",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "0.35rem",
                  transition: "all 0.15s ease",
                }}
              >
                <span>⏳ Pending</span>
                <span style={{
                  background: statusFilter === "PENDING" ? "rgba(255,255,255,0.25)" : "var(--border-card)",
                  padding: "0.1rem 0.4rem",
                  borderRadius: "10px",
                  fontSize: "0.72rem",
                }}>
                  {pendingCount}
                </span>
              </button>

              <button
                type="button"
                onClick={() => setStatusFilter("COMPLETED")}
                style={{
                  flex: 1,
                  background: statusFilter === "COMPLETED" ? "#10b981" : "var(--bg-card-subtle)",
                  color: statusFilter === "COMPLETED" ? "#ffffff" : "var(--text-muted)",
                  border: "1px solid var(--border-card)",
                  padding: "0.45rem 0.5rem",
                  borderRadius: "6px",
                  fontSize: "0.82rem",
                  fontWeight: "700",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "0.35rem",
                  transition: "all 0.15s ease",
                }}
              >
                <span>✓ Completed</span>
                <span style={{
                  background: statusFilter === "COMPLETED" ? "rgba(255,255,255,0.25)" : "var(--border-card)",
                  padding: "0.1rem 0.4rem",
                  borderRadius: "10px",
                  fontSize: "0.72rem",
                }}>
                  {completedCount}
                </span>
              </button>
            </div>

            {/* Cases List */}
            {loading ? (
              <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.88rem" }}>
                Loading queue...
              </div>
            ) : filteredCases.length === 0 ? (
              <div style={{
                padding: "2rem 1rem",
                textAlign: "center",
                color: "var(--text-muted)",
                fontSize: "0.85rem",
                background: "var(--bg-card-subtle)",
                borderRadius: "8px",
              }}>
                <div style={{ fontSize: "1.6rem", marginBottom: "0.5rem" }}>
                  {statusFilter === "PENDING" ? "🎉" : "📋"}
                </div>
                <strong>{statusFilter === "PENDING" ? "No Pending Cases" : "No Completed Cases"}</strong>
                <p style={{ margin: "0.25rem 0 0", fontSize: "0.8rem" }}>
                  {statusFilter === "PENDING"
                    ? "All referred screening cases have been reviewed."
                    : "Completed cases will appear here once reviewed."}
                </p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "680px", overflowY: "auto" }}>
                {filteredCases.map((c) => {
                  const isSelected = selectedCase?.case_id === c.case_id;
                  const cGrade = c.override_grade !== null && c.override_grade !== undefined
                    ? c.override_grade
                    : c.screening_report?.dr_prediction?.grade ?? 0;
                  const cColor = GRADE_COLORS[cGrade] || "var(--primary)";

                  return (
                    <div
                      key={c.case_id}
                      onClick={() => setSelectedCase(c)}
                      style={{
                        padding: "0.85rem",
                        borderRadius: "8px",
                        border: isSelected ? "2px solid var(--primary)" : "1px solid var(--border-card)",
                        background: isSelected ? "var(--primary-subtle)" : "var(--bg-card-subtle)",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                        position: "relative",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.25rem" }}>
                        <strong style={{ fontSize: "0.92rem", color: "var(--text-main)" }}>
                          {c.patient_name || c.screening_report?.patient_name || "Anonymous Patient"}
                        </strong>
                        <span style={{
                          fontSize: "0.72rem",
                          fontWeight: "800",
                          padding: "0.15rem 0.45rem",
                          borderRadius: "4px",
                          background: `${cColor}20`,
                          color: cColor,
                        }}>
                          Grade {cGrade}
                        </span>
                      </div>
                      <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                        {c.case_id} • {c.eye_examined || "OD"}
                      </div>

                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.35rem" }}>
                        <span style={{
                          fontSize: "0.72rem",
                          fontWeight: "700",
                          color: c.specialist_decision
                            ? "#10b981"
                            : c.clinical_approval === "APPROVED"
                              ? "var(--primary)"
                              : "var(--text-muted)",
                        }}>
                          {c.specialist_decision
                            ? `✓ ${c.specialist_decision}`
                            : c.clinical_approval === "APPROVED"
                              ? "✓ Clinically Approved"
                              : c.status}
                        </span>

                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteTargetId(c.case_id);
                          }}
                          title="Delete Case"
                          style={{
                            background: "transparent",
                            border: "none",
                            color: "var(--text-muted)",
                            cursor: "pointer",
                            fontSize: "0.85rem",
                            padding: "0.1rem 0.3rem",
                          }}
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Main Doctor Review Panel */}
          {selectedCase && report ? (
            <div style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-card)",
              borderRadius: "0.85rem",
              padding: "1.75rem",
              boxShadow: "var(--card-shadow)",
            }}>
              {/* Case Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
                    <h2 style={{ fontSize: "1.6rem", fontWeight: "800", color: "var(--text-main)", margin: 0 }}>
                      {selectedCase.patient_name || report.patient_name || "Anonymous Patient"}
                    </h2>
                    <span style={{
                      padding: "0.25rem 0.65rem",
                      borderRadius: "6px",
                      background: isCompleted ? "rgba(16, 185, 129, 0.12)" : "rgba(2, 132, 199, 0.12)",
                      color: isCompleted ? "#10b981" : "var(--primary)",
                      border: `1px solid ${isCompleted ? "rgba(16, 185, 129, 0.3)" : "rgba(2, 132, 199, 0.3)"}`,
                      fontSize: "0.82rem",
                      fontWeight: "800",
                    }}>
                      {isCompleted ? "✓ Review Completed" : "⏳ Pending Specialist Action"}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.35rem" }}>
                    Case ID: <strong style={{ color: "var(--primary)" }}>{selectedCase.case_id}</strong> • Patient ID: <strong>{selectedCase.patient_id || report.patient_id || "PAT-1001"}</strong>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <button
                    type="button"
                    onClick={() => setShowReportModal(true)}
                    style={{
                      background: "var(--bg-card-subtle)",
                      color: "var(--text-main)",
                      border: "1px solid var(--border-card)",
                      padding: "0.45rem 0.9rem",
                      borderRadius: "6px",
                      fontWeight: "700",
                      fontSize: "0.85rem",
                      cursor: "pointer",
                    }}
                  >
                    📋 View Full Report
                  </button>

                  <div style={{
                    padding: "0.45rem 0.95rem",
                    borderRadius: "8px",
                    background: `${gradeColor}18`,
                    border: `1px solid ${gradeColor}40`,
                    textAlign: "right",
                  }}>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: "700" }}>
                      DR SEVERITY
                    </div>
                    <div style={{ fontSize: "1.15rem", fontWeight: "800", color: gradeColor }}>
                      Level {grade}: {GRADE_LABELS[grade] || report.retinal_analysis?.severity || "DR"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Demographics Strip */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                gap: "1rem",
                padding: "1rem 1.25rem",
                background: "var(--bg-card-subtle)",
                borderRadius: "0.75rem",
                border: "1px solid var(--border-card)",
                marginBottom: "1.5rem",
              }}>
                <div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: "700" }}>AGE / GENDER</div>
                  <div style={{ fontSize: "0.92rem", fontWeight: "700", color: "var(--text-main)", marginTop: "0.2rem" }}>
                    {selectedCase.age || report.age || "N/A"} yrs • {selectedCase.gender || report.gender || "Unspecified"}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: "700" }}>EYE EXAMINED</div>
                  <div style={{ fontSize: "0.92rem", fontWeight: "700", color: "var(--primary)", marginTop: "0.2rem" }}>
                    {selectedCase.eye_examined || report.eye_examined || "OD"}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: "700" }}>MODEL CONFIDENCE</div>
                  <div style={{ fontSize: "0.92rem", fontWeight: "700", color: "var(--text-main)", marginTop: "0.2rem" }}>
                    {((report.retinal_analysis?.calibrated_confidence ?? report.dr_prediction?.confidence ?? 0.85) * 100).toFixed(1)}% (Algorithmic)
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: "700" }}>STATUS</div>
                  <div style={{ fontSize: "0.88rem", fontWeight: "800", color: isCompleted ? "#10b981" : "var(--primary)", marginTop: "0.2rem" }}>
                    {isCompleted ? "COMPLETED" : "PENDING ACTION"}
                  </div>
                </div>
              </div>

              {/* Exactly Three Main Images */}
              <div style={{ marginBottom: "1.75rem" }}>
                <h3 style={{ fontSize: "1.1rem", fontWeight: "800", color: "var(--text-main)", marginBottom: "0.75rem" }}>
                  Diagnostic Images
                </h3>
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
                  gap: "1.25rem",
                }}>
                  {/* 1. Original Image */}
                  <div style={{
                    background: "var(--bg-card-subtle)",
                    border: "1px solid var(--border-card)",
                    borderRadius: "0.75rem",
                    padding: "0.85rem",
                    display: "flex",
                    flexDirection: "column",
                  }}>
                    <div style={{ fontWeight: "700", fontSize: "0.85rem", color: "var(--text-main)", marginBottom: "0.5rem" }}>
                      📷 1. Original Retinal Image
                    </div>
                    <div style={{
                      height: "230px",
                      background: "#090d16",
                      borderRadius: "6px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      overflow: "hidden",
                    }}>
                      {originalUrl ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={originalUrl} alt="Original Retinal Scan" style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain" }} />
                      ) : (
                        <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>Image unavailable</span>
                      )}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
                      Uploaded patient color fundus photograph
                    </div>
                  </div>

                  {/* 2. Grad-CAM Image */}
                  <div style={{
                    background: "var(--bg-card-subtle)",
                    border: "1px solid var(--border-card)",
                    borderRadius: "0.75rem",
                    padding: "0.85rem",
                    display: "flex",
                    flexDirection: "column",
                  }}>
                    <div style={{ fontWeight: "700", fontSize: "0.85rem", color: "var(--primary)", marginBottom: "0.5rem" }}>
                      🔥 2. Grad-CAM Image
                    </div>
                    <div style={{
                      height: "230px",
                      background: "#090d16",
                      borderRadius: "6px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      overflow: "hidden",
                    }}>
                      {gradcamUrl ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={gradcamUrl} alt="Grad-CAM Image" style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain" }} />
                      ) : (
                        <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>Grad-CAM unavailable</span>
                      )}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
                      Grad-CAM explanation overlay on retinal scan
                    </div>
                  </div>

                  {/* 3. Heat Map Image */}
                  <div style={{
                    background: "var(--bg-card-subtle)",
                    border: "1px solid var(--border-card)",
                    borderRadius: "0.75rem",
                    padding: "0.85rem",
                    display: "flex",
                    flexDirection: "column",
                  }}>
                    <div style={{ fontWeight: "700", fontSize: "0.85rem", color: "#d97706", marginBottom: "0.5rem" }}>
                      🌡️ 3. Heat Map Image
                    </div>
                    <div style={{
                      height: "230px",
                      background: "#090d16",
                      borderRadius: "6px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      overflow: "hidden",
                    }}>
                      {heatmapUrl ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={heatmapUrl} alt="Heat Map Image" style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain" }} />
                      ) : (
                        <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>Heat map unavailable</span>
                      )}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
                      Color-mapped activation heat map
                    </div>
                  </div>
                </div>
              </div>

              {/* Explainable AI Summary */}
              <div style={{
                background: "var(--bg-card-subtle)",
                border: "1px solid var(--border-card)",
                borderRadius: "0.75rem",
                padding: "1rem 1.25rem",
                marginBottom: "1.5rem",
                fontSize: "0.85rem",
                lineHeight: "1.5",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem", flexWrap: "wrap", gap: "0.5rem" }}>
                  <strong style={{ color: "var(--text-main)" }}>💡 Explainable AI Analysis</strong>
                  <span style={{ color: "var(--primary)", fontWeight: "700" }}>
                    Highlighted Region: <strong>{highlightedRegion}</strong>
                  </span>
                </div>
                <p style={{ margin: "0.2rem 0", color: "var(--text-muted)" }}>{whatHeatmapShows}</p>
                <p style={{ margin: "0.2rem 0", color: "var(--text-muted)" }}>{whyThisMatters}</p>
                <div style={{ fontSize: "0.75rem", color: "var(--text-subtle)", fontStyle: "italic", marginTop: "0.3rem" }}>
                  Note: &apos;Image Left/Right&apos; denotes display coordinates and is distinct from anatomical eye laterality ({selectedCase.eye_examined || "OD"}).
                </div>
              </div>

              {/* Clinician Referral Details */}
              {selectedCase.clinical_approval && (
                <div style={{
                  background: "rgba(16, 185, 129, 0.08)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  borderRadius: "0.75rem",
                  padding: "1rem 1.25rem",
                  marginBottom: "1.5rem",
                  fontSize: "0.85rem",
                }}>
                  <div style={{ fontWeight: "800", color: "#10b981", marginBottom: "0.4rem" }}>
                    📋 Clinician Referral Approval
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.5rem", color: "var(--text-muted)" }}>
                    <div>Status: <strong style={{ color: "#10b981" }}>{selectedCase.clinical_approval} (Locked)</strong></div>
                    <div>Approved By: <strong style={{ color: "var(--text-main)" }}>{selectedCase.clinical_approved_by || "Clinician on duty"}</strong></div>
                    <div>Date: <strong style={{ color: "var(--text-main)" }}>{selectedCase.clinical_approved_at || selectedCase.updated_at || "Recent"}</strong></div>
                  </div>
                  {(selectedCase.clinical_approval_notes || selectedCase.referral_notes) && (
                    <div style={{ marginTop: "0.5rem", paddingTop: "0.5rem", borderTop: "1px dashed rgba(16, 185, 129, 0.3)" }}>
                      <span style={{ fontWeight: "700", color: "var(--text-main)" }}>Clinician Notes:</span>{" "}
                      <span style={{ color: "var(--text-muted)" }}>{selectedCase.clinical_approval_notes || selectedCase.referral_notes}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Doctor Review Decision Row */}
              <div style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-card)",
                borderRadius: "0.85rem",
                padding: "1.25rem",
              }}>
                <h4 style={{ fontSize: "1rem", fontWeight: "800", color: "var(--text-main)", margin: "0 0 0.5rem 0" }}>
                  Doctor Consultation & Assessment
                </h4>

                {/* If already reviewed, display record */}
                {selectedCase.specialist_decision ? (
                  <div style={{
                    padding: "0.85rem 1rem",
                    borderRadius: "8px",
                    background: "rgba(16, 185, 129, 0.1)",
                    border: "1px solid rgba(16, 185, 129, 0.3)",
                    marginTop: "0.5rem",
                  }}>
                    <div style={{ fontWeight: "800", color: "#10b981", fontSize: "0.92rem" }}>
                      ✓ Doctor Assessment Recorded: {selectedCase.specialist_decision}
                    </div>
                    {selectedCase.override_grade !== null && selectedCase.override_grade !== undefined && (
                      <div style={{ fontSize: "0.85rem", color: "var(--text-main)", marginTop: "0.2rem" }}>
                        Assigned Final Grade: <strong>Level {selectedCase.override_grade} ({GRADE_LABELS[selectedCase.override_grade]})</strong>
                      </div>
                    )}
                    {selectedCase.specialist_notes && (
                      <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                        Consultation Notes: {selectedCase.specialist_notes}
                      </div>
                    )}
                  </div>
                ) : (
                  <>
                    <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", margin: "0 0 0.75rem 0" }}>
                      Record specialist diagnosis for this referred screening case.
                    </p>

                    <input
                      type="text"
                      placeholder="Doctor consultation notes, treatment plan, or follow-up recommendation..."
                      value={doctorNotes}
                      onChange={(e) => setDoctorNotes(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "0.5rem 0.75rem",
                        fontSize: "0.85rem",
                        borderRadius: "6px",
                        border: "1px solid var(--border-card)",
                        background: "var(--bg-card-subtle)",
                        color: "var(--text-main)",
                        marginBottom: "0.75rem",
                        boxSizing: "border-box",
                      }}
                    />

                    {showOverrideSelect && (
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
                        <span style={{ fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)" }}>
                          Select Overridden Grade:
                        </span>
                        <select
                          value={overrideGrade}
                          onChange={(e) => setOverrideGrade(parseInt(e.target.value, 10))}
                          style={{
                            padding: "0.35rem 0.65rem",
                            borderRadius: "6px",
                            border: "1px solid var(--border-card)",
                            background: "var(--bg-card-subtle)",
                            color: "var(--text-main)",
                            fontSize: "0.85rem",
                            fontWeight: "700",
                          }}
                        >
                          <option value={0}>Level 0 — No DR</option>
                          <option value={1}>Level 1 — Mild NPDR</option>
                          <option value={2}>Level 2 — Moderate NPDR</option>
                          <option value={3}>Level 3 — Severe NPDR</option>
                          <option value={4}>Level 4 — Proliferative DR</option>
                        </select>
                      </div>
                    )}

                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                      <button
                        type="button"
                        onClick={() => handleDoctorDecision("CONFIRMED")}
                        disabled={submittingReview}
                        style={{
                          background: "#10b981",
                          color: "#ffffff",
                          border: "none",
                          padding: "0.55rem 1.2rem",
                          borderRadius: "6px",
                          fontSize: "0.85rem",
                          fontWeight: "800",
                          cursor: submittingReview ? "not-allowed" : "pointer",
                        }}
                      >
                        ✓ Confirm AI Assessment
                      </button>

                      {showOverrideSelect ? (
                        <button
                          type="button"
                          onClick={() => handleDoctorDecision("OVERRIDDEN")}
                          disabled={submittingReview}
                          style={{
                            background: "#d97706",
                            color: "#ffffff",
                            border: "none",
                            padding: "0.55rem 1.2rem",
                            borderRadius: "6px",
                            fontSize: "0.85rem",
                            fontWeight: "800",
                            cursor: submittingReview ? "not-allowed" : "pointer",
                          }}
                        >
                          Submit Override Grade
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setShowOverrideSelect(true)}
                          disabled={submittingReview}
                          style={{
                            background: "rgba(217, 119, 6, 0.15)",
                            color: "#d97706",
                            border: "1px solid #d97706",
                            padding: "0.55rem 1.2rem",
                            borderRadius: "6px",
                            fontSize: "0.85rem",
                            fontWeight: "800",
                            cursor: submittingReview ? "not-allowed" : "pointer",
                          }}
                        >
                          ✏️ Override DR Grade
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => handleDoctorDecision("REQUEST_RECAPTURE")}
                        disabled={submittingReview}
                        style={{
                          background: "rgba(239, 68, 68, 0.12)",
                          color: "#dc2626",
                          border: "1px solid rgba(239, 68, 68, 0.3)",
                          padding: "0.55rem 1.2rem",
                          borderRadius: "6px",
                          fontSize: "0.85rem",
                          fontWeight: "800",
                          cursor: submittingReview ? "not-allowed" : "pointer",
                        }}
                      >
                        📷 Request Recapture
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          ) : (
            <div style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-card)",
              borderRadius: "0.85rem",
              padding: "3rem",
              textAlign: "center",
              color: "var(--text-muted)",
            }}>
              <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>👈</div>
              Select a case from the queue to view retinal images, clinical notes, and record doctor consultation.
            </div>
          )}
        </div>
      </div>

      {/* Full Report Modal */}
      {selectedCase && report && (
        <FullReportModal
          isOpen={showReportModal}
          onClose={() => setShowReportModal(false)}
          report={report}
        />
      )}

      {/* Delete Single Case Modal */}
      <UIModal
        isOpen={Boolean(deleteTargetId)}
        type="confirm"
        confirmDanger={true}
        title="Delete Screening Case?"
        message={`Are you sure you want to permanently delete case '${deleteTargetId}'?`}
        confirmText="Delete Case"
        cancelText="Cancel"
        onConfirm={() => deleteTargetId && handleDeleteCase(deleteTargetId)}
        onCancel={() => setDeleteTargetId(null)}
      />

      {/* Clear All Cases Modal */}
      <UIModal
        isOpen={confirmClearAllModal}
        type="confirm"
        confirmDanger={true}
        title="Clear All Cases?"
        message="Are you sure you want to delete all screening cases from the queue? This action cannot be undone."
        confirmText="Delete All Cases"
        cancelText="Cancel"
        onConfirm={handleClearAll}
        onCancel={() => setConfirmClearAllModal(false)}
      />
    </>
  );
}

export default function DoctorPortalPage() {
  return (
    <Suspense fallback={<div style={{ padding: "2rem", textAlign: "center" }}>Loading Doctor Portal...</div>}>
      <DoctorPortalContent />
    </Suspense>
  );
}

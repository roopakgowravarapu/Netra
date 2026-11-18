"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import { Header } from "../../components/Header";
import { FullReportModal } from "../../components/FullReportModal";
import { ToastContainer, ToastMessage } from "../../components/Toast";
import { UIModal } from "../../components/UIModal";
import {
  getStaticImageUrl,
  CaseItem,
  CaseHistoryItem,
  deleteAllCases,
} from "../../lib/api";
import { Language, translations } from "../../lib/translations";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const DR_LABELS: Record<number, string> = {
  0: "No DR",
  1: "Mild DR",
  2: "Moderate DR",
  3: "Severe DR",
  4: "Proliferative DR",
};

export default function TelemedicineDashboard() {
  const router = useRouter();


  // Multi-lingual state
  const [lang, setLang] = useState<Language>("en");

  // Cases Queue States
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<CaseItem | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [overrideGrade, setOverrideGrade] = useState<number>(1);
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(true);
  const [deletingCaseId, setDeletingCaseId] = useState<string | null>(null);

  // Search & Filter state for queue
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "PENDING" | "URGENT" | "RECAPTURE" | "COMPLETED">("ALL");
  const [toasts, setToasts] = useState<ToastMessage[]>([]);



  const addToast = (type: "success" | "info" | "warning" | "error", message: string) => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
    setToasts((prev) => [...prev, { id, type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Custom UI Modal States
  const [deleteTargetCaseId, setDeleteTargetCaseId] = useState<string | null>(null);
  const [confirmDeleteAllCasesModal, setConfirmDeleteAllCasesModal] = useState(false);
  const [refreshingCases, setRefreshingCases] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [feedbackModal, setFeedbackModal] = useState<{
    isOpen: boolean;
    type: "success" | "error" | "info" | "warning";
    title: string;
    message: string;
  }>({ isOpen: false, type: "info", title: "", message: "" });

  useEffect(() => {
    const savedLang = (localStorage.getItem("netra_lang") as Language) || "en";
    setLang(savedLang);

    const handleLangChange = (e: any) => {
      setLang(e.detail || "en");
    };
    window.addEventListener("netra_language_changed", handleLangChange);
    return () => window.removeEventListener("netra_language_changed", handleLangChange);
  }, []);

  const t = translations[lang] || translations.en;

  const fetchCases = async (selectCaseId?: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/cases`);
      if (res.ok) {
        const data: CaseItem[] = await res.json();
        data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        setCases(data);

        if (selectCaseId) {
          const match = data.find((c) => c.case_id === selectCaseId);
          if (match) setSelectedCase(match);
        } else if (data.length > 0 && !selectedCase) {
          setSelectedCase(data[0]);
        } else if (selectedCase) {
          const updatedSelected = data.find((c) => c.case_id === selectedCase.case_id);
          if (updatedSelected) {
            setSelectedCase(updatedSelected);
          } else {
            setSelectedCase(data.length > 0 ? data[0] : null);
          }
        }
      }
    } catch (err) {
      console.error("Failed to fetch cases:", err);
    } finally {
      setLoading(false);
    }
  };

  const confirmDeleteCase = async (caseId: string) => {
    setDeletingCaseId(caseId);
    setDeleteTargetCaseId(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}`, {
        method: "DELETE",
      });

      if (res.ok || res.status === 404) {
        const remaining = cases.filter((c) => c.case_id !== caseId);
        setCases(remaining);
        if (selectedCase?.case_id === caseId) {
          setSelectedCase(remaining.length > 0 ? remaining[0] : null);
        }
        await fetchCases();
        setFeedbackModal({
          isOpen: true,
          type: "success",
          title: "Case Deleted",
          message: `Screening case '${caseId}' has been deleted successfully.`,
        });
      } else {
        const errJson = await res.json().catch(() => ({}));
        setFeedbackModal({
          isOpen: true,
          type: "error",
          title: "Deletion Failed",
          message: errJson.detail || `Unable to delete screening case '${caseId}'. Please try again.`,
        });
      }
    } catch (err: any) {
      console.error("Failed to delete case:", err);
      setFeedbackModal({
        isOpen: true,
        type: "error",
        title: "Network Error",
        message: `Could not reach backend server to delete case '${caseId}'.`,
      });
    } finally {
      setDeletingCaseId(null);
    }
  };

  const confirmDeleteAllCases = async () => {
    setConfirmDeleteAllCasesModal(false);
    try {
      const res = await deleteAllCases();
      setCases([]);
      setSelectedCase(null);
      addToast("success", `All ${res.count} cases cleared from queue.`);
      setFeedbackModal({
        isOpen: true,
        type: "success",
        title: "Telemedicine Queue Cleared",
        message: `Successfully deleted all ${res.count} screening cases from the review queue.`,
      });
    } catch (err: any) {
      console.error("Failed to delete all cases:", err);
      addToast("error", err.message || "Failed to clear cases queue.");
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleReviewSubmit = async (decision: "confirm" | "override" | "request_recapture") => {
    if (!selectedCase) return;
    setReviewSubmitting(true);
    setReviewError(null);

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

      if (!res.ok) {
        let errorMsg = "Review submission failed.";
        try {
          const errData = await res.json();
          errorMsg = errData.detail || errorMsg;
        } catch {}
        setReviewError(errorMsg);
        return;
      }

      const updatedCase: CaseItem = await res.json();
      setSelectedCase(updatedCase);
      await fetchCases(updatedCase.case_id);
      addToast("success", `Specialist decision '${decision.toUpperCase()}' saved for Case '${updatedCase.case_id}'`);

      if (decision === "request_recapture") {
        router.push(`/screening?case_id=${updatedCase.case_id}&recapture=true`);
      }
    } catch (err: any) {
      console.error(err);
      setReviewError(err.message || "An unexpected error occurred during review submission.");
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

  const canMakeDecision =
    selectedCase?.status === "REQUIRES_SPECIALIST_REVIEW" ||
    selectedCase?.status === "URGENT_SPECIALIST_REVIEW";

  const isConfirmed = selectedCase?.status === "CONFIRMED";
  const isOverridden = selectedCase?.status === "OVERRIDDEN";
  const isRecaptureRequired = selectedCase?.status === "RECAPTURE_REQUIRED";
  const isSpecialistReviewed = selectedCase?.status === "SPECIALIST_REVIEWED";

  const getStatusColor = (status: string) => {
    switch (status) {
      case "CONFIRMED":
      case "SPECIALIST_REVIEWED":
        return "var(--accent-teal)";
      case "OVERRIDDEN":
        return "#d97706";
      case "RECAPTURE_REQUIRED":
        return "#ef4444";
      case "REQUIRES_SPECIALIST_REVIEW":
        return "var(--primary)";
      case "URGENT_SPECIALIST_REVIEW":
        return "#dc2626";
      default:
        return "var(--text-muted)";
    }
  };

  const filteredCases = cases.filter((c) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchId = c.case_id.toLowerCase().includes(q);
      const matchName = (c.patient_name || c.screening_report.patient_name || "").toLowerCase().includes(q);
      if (!matchId && !matchName) return false;
    }

    if (statusFilter === "PENDING") {
      return c.status === "REQUIRES_SPECIALIST_REVIEW";
    } else if (statusFilter === "URGENT") {
      return c.status === "URGENT_SPECIALIST_REVIEW";
    } else if (statusFilter === "RECAPTURE") {
      return c.status === "RECAPTURE_REQUIRED";
    } else if (statusFilter === "COMPLETED") {
      return c.status === "CONFIRMED" || c.status === "OVERRIDDEN" || c.status === "SPECIALIST_REVIEWED";
    }
    return true;
  });

  return (
    <>
      <Header />
      <div className="container" style={{ maxWidth: "1280px", margin: "0 auto", padding: "1.5rem 1rem" }}>
        {/* Dashboard Header */}
        <div className="header" style={{ marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
            <div>
              <div className="badge" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.3rem 0.8rem", borderRadius: "20px", background: "rgba(2, 132, 199, 0.1)", color: "var(--primary)", fontWeight: "700", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
                <span className="badge-dot" style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--primary)" }} />
                Clinical Decision Support
              </div>
              <h1 className="title" style={{ fontSize: "2rem", fontWeight: "800", color: "var(--text-main)", margin: "0.25rem 0" }}>
                {t.navDashboard}
              </h1>
              <p className="subtitle" style={{ color: "var(--text-muted)", fontSize: "0.95rem", margin: 0 }}>
                Remote Ophthalmologist Review Queue & Longitudinal Retinal Progression Tracking
              </p>
            </div>

            {/* Specialist Queue Header Status */}
            <div style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.6rem",
              background: "var(--primary-subtle)",
              border: "1px solid var(--primary-glow)",
              padding: "0.5rem 1.1rem",
              borderRadius: "10px",
              color: "var(--primary)",
              fontWeight: "700",
              fontSize: "0.9rem",
            }}>
              <span>📋</span>
              <span>{t.specialistQueue} ({cases.length} active cases)</span>
            </div>
          </div>
        </div>

        {/* SPECIALIST REVIEW QUEUE */}
          <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "1.5rem" }}>
            {/* Cases Queue Sidebar */}
            <div className="card" style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-card)",
              borderRadius: "0.75rem",
              padding: "1.25rem",
              height: "fit-content",
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.75rem", gap: "0.5rem" }}>
                <h3 style={{ fontSize: "1.05rem", fontWeight: "700", color: "var(--text-main)", margin: 0 }}>
                  Queue ({filteredCases.length})
                </h3>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <button
                    type="button"
                    onClick={() => {
                      setRefreshingCases(true);
                      fetchCases().finally(() => setTimeout(() => setRefreshingCases(false), 600));
                    }}
                    disabled={refreshingCases}
                    title="Refresh Telemedicine Queue"
                    style={{
                      background: "var(--primary-subtle)",
                      color: "var(--primary)",
                      border: "1px solid var(--primary-glow)",
                      borderRadius: "6px",
                      padding: "0.25rem 0.55rem",
                      fontSize: "0.75rem",
                      fontWeight: "600",
                      cursor: "pointer",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.3rem",
                      transition: "all 0.2s ease",
                    }}
                  >
                    <span
                      style={{
                        display: "inline-block",
                        animation: refreshingCases ? "netra-spin 0.8s linear infinite" : "none",
                        transition: "transform 0.3s ease",
                      }}
                    >
                      🔄
                    </span>
                    <span>Refresh</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDeleteAllCasesModal(true)}
                    disabled={cases.length === 0}
                    title="Delete all cases in telemedicine queue"
                    style={{
                      background: "rgba(220, 38, 38, 0.08)",
                      color: cases.length === 0 ? "var(--text-muted)" : "#dc2626",
                      border: "1px solid rgba(220, 38, 38, 0.25)",
                      borderRadius: "6px",
                      padding: "0.25rem 0.55rem",
                      fontSize: "0.75rem",
                      fontWeight: "600",
                      cursor: cases.length === 0 ? "not-allowed" : "pointer",
                      opacity: cases.length === 0 ? 0.6 : 1,
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.25rem",
                      transition: "all 0.2s ease",
                    }}
                  >
                    <span>🗑️</span>
                    <span>Clear All</span>
                  </button>
                </div>
              </div>

              {/* Queue Search & Category Filter */}
              <div style={{ marginBottom: "1rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <input
                  type="text"
                  placeholder="🔍 Search patient name or case ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.45rem 0.75rem",
                    fontSize: "0.82rem",
                    borderRadius: "6px",
                    border: "1px solid var(--border-card)",
                    background: "var(--bg-card-subtle)",
                    color: "var(--text-main)",
                    outline: "none",
                  }}
                />
                <div style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap" }}>
                  {[
                    { id: "ALL", label: "All" },
                    { id: "PENDING", label: "Pending" },
                    { id: "URGENT", label: "Urgent" },
                    { id: "RECAPTURE", label: "Recapture" },
                    { id: "COMPLETED", label: "Done" },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setStatusFilter(tab.id as any)}
                      style={{
                        background: statusFilter === tab.id ? "var(--primary)" : "var(--bg-card-subtle)",
                        color: statusFilter === tab.id ? "#ffffff" : "var(--text-muted)",
                        border: "1px solid var(--border-card)",
                        padding: "0.2rem 0.5rem",
                        borderRadius: "4px",
                        fontSize: "0.72rem",
                        fontWeight: "700",
                        cursor: "pointer",
                      }}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              {loading ? (
                <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Loading queue...</div>
              ) : filteredCases.length === 0 ? (
                <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", padding: "1rem 0", lineHeight: "1.5" }}>
                  No matching cases found. Upload a fundus scan in the <Link href="/screening" style={{ color: "var(--primary)", fontWeight: "700" }}>Screening Portal</Link> to create a case.
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxHeight: "650px", overflowY: "auto" }}>
                  {filteredCases.map((c) => {
                    const isSelected = selectedCase?.case_id === c.case_id;
                    const isUngradable = c.screening_report.image_quality?.status === "ungradable";
                    const attemptCount = c.history ? c.history.length : (c.attempt || 1);

                    return (
                      <div
                        key={c.case_id}
                        onClick={() => {
                          setSelectedCase(c);
                          setReviewNotes(c.specialist_notes || "");
                          setReviewError(null);
                        }}
                        style={{
                          padding: "0.85rem",
                          borderRadius: "0.5rem",
                          background: isSelected ? "var(--primary-subtle)" : "var(--bg-card-subtle)",
                          border: `1px solid ${isSelected ? "var(--primary)" : "var(--border-card)"}`,
                          cursor: "pointer",
                          transition: "all 0.2s ease",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.78rem", color: "var(--text-muted)" }}>
                          <span style={{ fontWeight: "700" }}>{c.case_id}</span>
                          <div style={{ display: "flex", gap: "0.35rem", alignItems: "center" }}>
                            {attemptCount > 1 && (
                              <span style={{
                                fontSize: "0.7rem",
                                background: "rgba(99, 102, 241, 0.15)",
                                color: "#818cf8",
                                padding: "0.1rem 0.4rem",
                                borderRadius: "10px",
                                fontWeight: "700",
                              }}>
                                Att #{attemptCount}
                              </span>
                            )}
                            <span style={{
                              color: getStatusColor(c.status),
                              fontWeight: "800",
                              fontSize: "0.75rem",
                            }}>
                              {c.status}
                            </span>
                            <button
                              type="button"
                              title={`Delete Case ${c.case_id}`}
                              onClick={(e) => {
                                e.stopPropagation();
                                setDeleteTargetCaseId(c.case_id);
                              }}
                              disabled={deletingCaseId === c.case_id}
                              style={{
                                background: "rgba(239, 68, 68, 0.08)",
                                border: "1px solid rgba(239, 68, 68, 0.2)",
                                color: "#ef4444",
                                cursor: "pointer",
                                padding: "0.15rem 0.4rem",
                                borderRadius: "4px",
                                fontSize: "0.75rem",
                                lineHeight: 1,
                                display: "inline-flex",
                                alignItems: "center",
                              }}
                            >
                              🗑️
                            </button>
                          </div>
                        </div>

                        <div style={{ fontWeight: "700", fontSize: "0.9rem", color: "var(--text-main)", marginTop: "0.3rem" }}>
                          👤 {c.patient_name || c.screening_report.patient_name || "Anonymous Patient"}
                        </div>

                        <div style={{ fontSize: "0.8rem", color: "var(--primary)", fontWeight: "600", marginTop: "0.2rem" }}>
                          {isUngradable ? "⚠️ UNGRADABLE IMAGE" : c.screening_report.dr_prediction?.label || "Pending Analysis"}
                        </div>

                        <div style={{ fontSize: "0.74rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                          📅 {c.screening_report.screening_date || new Date(c.created_at).toLocaleDateString("en-IN")} • Eye: {c.eye_examined || c.screening_report.eye_examined || "OD"}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Main Case Detail View */}
            <div className="card" style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-card)",
              borderRadius: "0.75rem",
              padding: "1.5rem",
            }}>
              {selectedCase ? (
                <div>
                  {/* Case Header with Demographics Bar */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem", flexWrap: "wrap", gap: "1rem" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                        <h2 style={{ fontSize: "1.35rem", fontWeight: "800", color: "var(--text-main)", margin: 0 }}>
                          Case: {selectedCase.case_id}
                        </h2>
                        {(selectedCase.history?.length || selectedCase.attempt || 1) > 1 && (
                          <span style={{
                            background: "rgba(99, 102, 241, 0.15)",
                            color: "#818cf8",
                            border: "1px solid rgba(99, 102, 241, 0.3)",
                            padding: "0.2rem 0.6rem",
                            borderRadius: "12px",
                            fontSize: "0.8rem",
                            fontWeight: "700",
                          }}>
                            Attempt #{selectedCase.history?.length || selectedCase.attempt}
                          </span>
                        )}
                      </div>

                      {/* Patient Demographics Pill */}
                      <div style={{
                        marginTop: "0.5rem",
                        padding: "0.35rem 0.75rem",
                        background: "var(--bg-card-subtle)",
                        borderRadius: "6px",
                        border: "1px solid var(--border-card)",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.8rem",
                        fontSize: "0.82rem",
                        color: "var(--text-main)",
                        flexWrap: "wrap",
                      }}>
                        <span><strong>{t.patientName}:</strong> {selectedCase.patient_name || selectedCase.screening_report.patient_name || "Anonymous"}</span>
                        <span>•</span>
                        <span><strong>{t.patientId}:</strong> {selectedCase.patient_id || selectedCase.screening_report.patient_id || "N/A"}</span>
                        <span>•</span>
                        <span><strong>{t.age}:</strong> {selectedCase.age || selectedCase.screening_report.age || "N/A"}</span>
                        <span>•</span>
                        <span><strong>{t.gender}:</strong> {selectedCase.gender || selectedCase.screening_report.gender || "Unknown"}</span>
                        <span>•</span>
                        <span><strong>{t.eyeExamined}:</strong> <span style={{ color: "var(--primary)", fontWeight: "800" }}>{selectedCase.eye_examined || selectedCase.screening_report.eye_examined || "OD"}</span></span>
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
                      <button
                        type="button"
                        onClick={() => setShowReportModal(true)}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.35rem",
                          background: "linear-gradient(135deg, var(--primary), var(--accent-teal))",
                          color: "#ffffff",
                          border: "none",
                          padding: "0.45rem 0.95rem",
                          borderRadius: "8px",
                          fontSize: "0.85rem",
                          fontWeight: "700",
                          cursor: "pointer",
                          boxShadow: "0 2px 10px var(--primary-glow)",
                        }}
                      >
                        <span>📋</span>
                        <span>View Full Clinical Report</span>
                      </button>
                      <button
                        type="button"
                        title={`Delete Case ${selectedCase.case_id}`}
                        onClick={() => setDeleteTargetCaseId(selectedCase.case_id)}
                        disabled={deletingCaseId === selectedCase.case_id}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.35rem",
                          background: "rgba(239, 68, 68, 0.08)",
                          color: "#ef4444",
                          border: "1px solid rgba(239, 68, 68, 0.3)",
                          padding: "0.42rem 0.85rem",
                          borderRadius: "8px",
                          fontSize: "0.82rem",
                          fontWeight: "700",
                          cursor: "pointer",
                        }}
                      >
                        <span>🗑️</span>
                        <span>Delete</span>
                      </button>
                      <div style={{
                        padding: "0.45rem 1rem",
                        borderRadius: "20px",
                        background: `${getStatusColor(selectedCase.status)}18`,
                        color: getStatusColor(selectedCase.status),
                        fontSize: "0.85rem",
                        fontWeight: "800",
                        border: `1px solid ${getStatusColor(selectedCase.status)}40`,
                      }}>
                        {selectedCase.status}
                      </div>
                    </div>
                  </div>

                  {/* Retinal Imagery: Original scan & Grad-CAM Heatmap */}
                  <div style={{ marginBottom: "1.5rem" }}>
                    <h4 style={{ fontSize: "0.95rem", fontWeight: "700", color: "var(--text-main)", marginBottom: "0.75rem" }}>
                      Patient Retinal Imagery & Deep Saliency
                    </h4>

                    <div style={{
                      display: "grid",
                      gridTemplateColumns: originalImgUrl && gradcamImgUrl ? "1fr 1fr" : "1fr",
                      gap: "1.25rem",
                    }}>
                      {originalImgUrl && (
                        <div style={{
                          background: "var(--bg-card-subtle)",
                          border: "1px solid var(--border-card)",
                          borderRadius: "0.75rem",
                          padding: "1rem",
                          textAlign: "center",
                        }}>
                          <div style={{ fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
                            {t.originalScan} ({selectedCase.eye_examined || "OD"})
                          </div>
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={originalImgUrl}
                            alt="Patient Retinal Scan"
                            style={{ maxHeight: "240px", maxWidth: "100%", objectFit: "contain", borderRadius: "0.5rem", background: "#090d16" }}
                          />
                        </div>
                      )}

                      {gradcamImgUrl && (
                        <div style={{
                          background: "var(--bg-card-subtle)",
                          border: "1px solid var(--primary-glow)",
                          borderRadius: "0.75rem",
                          padding: "1rem",
                          textAlign: "center",
                        }}>
                          <div style={{ fontSize: "0.82rem", fontWeight: "700", color: "var(--primary)", marginBottom: "0.5rem" }}>
                            {t.gradcamHeatmap}
                          </div>
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={gradcamImgUrl}
                            alt="Grad-CAM Saliency Overlay"
                            style={{ maxHeight: "240px", maxWidth: "100%", objectFit: "contain", borderRadius: "0.5rem", background: "#090d16" }}
                          />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* AI Prediction & Confidence Overview */}
                  <div style={{
                    background: "var(--bg-card-subtle)",
                    borderRadius: "0.75rem",
                    padding: "1.25rem",
                    border: "1px solid var(--border-card)",
                    marginBottom: "1.5rem",
                  }}>
                    <h4 style={{ color: "var(--primary)", fontSize: "0.92rem", fontWeight: "700", marginBottom: "0.75rem" }}>
                      AI Automated Screening Findings
                    </h4>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem", fontSize: "0.88rem" }}>
                      <div>
                        <span style={{ color: "var(--text-muted)" }}>Quality Gate: </span>
                        <strong style={{ color: selectedCase.screening_report.image_quality?.status === "gradable" ? "var(--accent-teal)" : "#ef4444" }}>
                          {selectedCase.screening_report.image_quality?.status?.toUpperCase() || "UNKNOWN"}
                        </strong>
                      </div>
                      {selectedCase.screening_report.dr_prediction && (
                        <div>
                          <span style={{ color: "var(--text-muted)" }}>AI Predicted Grade: </span>
                          <strong style={{ color: "var(--text-main)" }}>{selectedCase.screening_report.dr_prediction.label}</strong>
                        </div>
                      )}
                      {selectedCase.screening_report.dr_prediction && (
                        <div>
                          <span style={{ color: "var(--text-muted)" }}>{t.confidence}: </span>
                          <strong style={{ color: "var(--primary)" }}>{(selectedCase.screening_report.dr_prediction.confidence * 100).toFixed(1)}%</strong>
                        </div>
                      )}
                    </div>

                    {selectedCase.screening_report.dr_prediction?.uncertain_prediction && (
                      <div style={{
                        marginTop: "0.75rem",
                        padding: "0.6rem 0.9rem",
                        background: "rgba(217, 119, 6, 0.12)",
                        border: "1px solid rgba(217, 119, 6, 0.3)",
                        borderRadius: "6px",
                        color: "#d97706",
                        fontSize: "0.82rem",
                      }}>
                        ⚠️ {t.specialistReviewAdvised}
                      </div>
                    )}
                  </div>

                  {/* Specialist Review Actions & State Banners */}
                  <div style={{
                    background: "var(--bg-card-subtle)",
                    borderRadius: "0.75rem",
                    padding: "1.25rem",
                    border: "1px solid var(--border-card)",
                    marginBottom: "1.5rem",
                  }}>
                    <h3 style={{ fontSize: "1.05rem", fontWeight: "700", color: "var(--text-main)", marginBottom: "0.75rem" }}>
                      Specialist Decision & Clinical Action
                    </h3>

                    {reviewError && (
                      <div style={{
                        padding: "0.6rem 0.9rem",
                        background: "rgba(239, 68, 68, 0.1)",
                        border: "1px solid rgba(239, 68, 68, 0.3)",
                        borderRadius: "6px",
                        color: "#ef4444",
                        fontSize: "0.85rem",
                        marginBottom: "1rem",
                      }}>
                        ⚠️ {reviewError}
                      </div>
                    )}

                    {isConfirmed && (
                      <div style={{
                        padding: "1rem",
                        background: "rgba(5, 150, 105, 0.12)",
                        border: "1px solid rgba(5, 150, 105, 0.35)",
                        borderRadius: "8px",
                        color: "var(--accent-teal)",
                      }}>
                        <div style={{ fontWeight: "800", fontSize: "1rem" }}>
                          ✓ AI Assessment Confirmed by {selectedCase.specialist_id}
                        </div>
                        {selectedCase.specialist_notes && (
                          <div style={{ marginTop: "0.3rem", fontSize: "0.85rem", color: "var(--text-main)" }}>
                            Note: &quot;{selectedCase.specialist_notes}&quot;
                          </div>
                        )}
                      </div>
                    )}

                    {isOverridden && (
                      <div style={{
                        padding: "1rem",
                        background: "rgba(217, 119, 6, 0.12)",
                        border: "1px solid rgba(217, 119, 6, 0.35)",
                        borderRadius: "8px",
                        color: "#d97706",
                      }}>
                        <div style={{ fontWeight: "800", fontSize: "1rem" }}>
                          ✎ Grade Overridden to Grade {selectedCase.override_grade} ({DR_LABELS[selectedCase.override_grade ?? 0]})
                        </div>
                        <div style={{ marginTop: "0.2rem", fontSize: "0.85rem", color: "var(--text-subtle)" }}>
                          Original AI Grade: Grade {selectedCase.screening_report.dr_prediction?.grade ?? 0} (Preserved in records)
                        </div>
                        {selectedCase.specialist_notes && (
                          <div style={{ marginTop: "0.3rem", fontSize: "0.85rem", color: "var(--text-main)" }}>
                            Clinical Note: &quot;{selectedCase.specialist_notes}&quot;
                          </div>
                        )}
                      </div>
                    )}

                    {isRecaptureRequired && (
                      <div style={{
                        padding: "1rem",
                        background: "rgba(239, 68, 68, 0.1)",
                        border: "1px solid rgba(239, 68, 68, 0.35)",
                        borderRadius: "8px",
                        color: "#ef4444",
                      }}>
                        <div style={{ fontWeight: "800", fontSize: "1rem" }}>
                          📷 Replacement Scan Requested
                        </div>
                        <p style={{ margin: "0.3rem 0 0.75rem", fontSize: "0.88rem", color: "var(--text-main)" }}>
                          Case is awaiting image recapture with improved focus and lighting.
                        </p>
                        <Link
                          href={`/screening?case_id=${selectedCase.case_id}&recapture=true`}
                          style={{
                            display: "inline-block",
                            background: "#ef4444",
                            color: "#ffffff",
                            padding: "0.5rem 1rem",
                            borderRadius: "6px",
                            fontWeight: "700",
                            fontSize: "0.85rem",
                            textDecoration: "none",
                          }}
                        >
                          Go to Screening Portal to Upload Replacement Scan →
                        </Link>
                      </div>
                    )}

                    {canMakeDecision && (
                      <div>
                        <div style={{ marginBottom: "1rem" }}>
                          <label style={{ display: "block", fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.4rem", fontWeight: "600" }}>
                            {t.clinicalNotes}:
                          </label>
                          <textarea
                            value={reviewNotes}
                            onChange={(e) => setReviewNotes(e.target.value)}
                            placeholder="Enter ophthalmologist findings, macular evaluation, or treatment recommendation..."
                            rows={3}
                            style={{
                              width: "100%",
                              background: "var(--bg-card)",
                              border: "1px solid var(--border-card)",
                              borderRadius: "0.5rem",
                              padding: "0.75rem",
                              color: "var(--text-main)",
                              fontFamily: "inherit",
                              fontSize: "0.88rem",
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
                              padding: "0.6rem 1.2rem",
                              borderRadius: "6px",
                              fontWeight: "700",
                              fontSize: "0.88rem",
                              cursor: "pointer",
                            }}
                          >
                            ✓ {t.confirmGrade}
                          </button>

                          <div style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
                            <select
                              value={overrideGrade}
                              onChange={(e) => setOverrideGrade(Number(e.target.value))}
                              style={{
                                background: "var(--bg-card)",
                                color: "var(--text-main)",
                                border: "1px solid var(--border-card)",
                                padding: "0.55rem 0.6rem",
                                borderRadius: "6px",
                                fontSize: "0.85rem",
                                fontWeight: "600",
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
                                padding: "0.6rem 1.1rem",
                                borderRadius: "6px",
                                fontWeight: "700",
                                fontSize: "0.85rem",
                                cursor: "pointer",
                              }}
                            >
                              ✎ {t.overrideGrade}
                            </button>
                          </div>

                          <button
                            onClick={() => handleReviewSubmit("request_recapture")}
                            disabled={reviewSubmitting}
                            style={{
                              background: "rgba(239, 68, 68, 0.12)",
                              color: "#ef4444",
                              border: "1px solid rgba(239, 68, 68, 0.3)",
                              padding: "0.6rem 1.1rem",
                              borderRadius: "6px",
                              fontWeight: "700",
                              fontSize: "0.85rem",
                              cursor: "pointer",
                            }}
                          >
                            📷 {t.requestRecapture}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Audit Trail & History */}
                  {selectedCase.audit_trail && selectedCase.audit_trail.length > 0 && (
                    <div style={{
                      background: "var(--bg-card-subtle)",
                      borderRadius: "0.75rem",
                      padding: "1rem 1.25rem",
                      border: "1px solid var(--border-card)",
                    }}>
                      <h4 style={{ fontSize: "0.92rem", fontWeight: "700", color: "var(--text-main)", margin: "0 0 0.75rem 0" }}>
                        🔒 {t.auditTrail} ({selectedCase.audit_trail.length} events recorded)
                      </h4>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                        {selectedCase.audit_trail.map((entry, idx) => (
                          <div
                            key={idx}
                            style={{
                              padding: "0.5rem 0.75rem",
                              borderRadius: "6px",
                              background: "var(--bg-card)",
                              border: "1px solid var(--border-card)",
                              fontSize: "0.8rem",
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              flexWrap: "wrap",
                              gap: "0.5rem",
                            }}
                          >
                            <div>
                              <strong style={{ color: "var(--primary)" }}>{entry.action}</strong>
                              <span style={{ color: "var(--text-muted)", marginLeft: "0.5rem" }}>by {entry.actor}</span>
                              {entry.details && (
                                <div style={{ color: "var(--text-subtle)", fontSize: "0.76rem", marginTop: "0.15rem" }}>
                                  {entry.details}
                                </div>
                              )}
                            </div>
                            <span style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>
                              {new Date(entry.timestamp).toLocaleString()}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: "4rem 2rem", color: "var(--text-muted)" }}>
                  Select a screening case from the queue to view details and submit remote specialist review.
                </div>
              )}
            </div>
          </div>

        {/* Delete Single Case Confirmation Modal */}
        <UIModal
          isOpen={deleteTargetCaseId !== null}
          type="confirm"
          confirmDanger={true}
          title="Delete Screening Case?"
          message={`Are you sure you want to delete screening case '${deleteTargetCaseId}'? This action cannot be undone.`}
          confirmText="Delete Case"
          cancelText="Cancel"
          onConfirm={() => {
            if (deleteTargetCaseId) confirmDeleteCase(deleteTargetCaseId);
          }}
          onCancel={() => setDeleteTargetCaseId(null)}
        />

        {/* Delete All Cases Confirmation Modal */}
        <UIModal
          isOpen={confirmDeleteAllCasesModal}
          type="confirm"
          confirmDanger={true}
          title="Clear Telemedicine Queue?"
          message={`Are you sure you want to delete all ${cases.length} screening cases from the queue? This action cannot be undone.`}
          confirmText="Delete All Cases"
          cancelText="Cancel"
          onConfirm={confirmDeleteAllCases}
          onCancel={() => setConfirmDeleteAllCasesModal(false)}
        />

        {/* Feedback Modal */}
        <UIModal
          isOpen={feedbackModal.isOpen}
          type={feedbackModal.type}
          title={feedbackModal.title}
          message={feedbackModal.message}
          confirmText="OK"
          onConfirm={() => setFeedbackModal((prev) => ({ ...prev, isOpen: false }))}
        />

        {/* Full A4 Screening Report Modal */}
        {selectedCase && (
          <FullReportModal
            isOpen={showReportModal}
            onClose={() => setShowReportModal(false)}
            report={selectedCase.screening_report}
            caseItem={selectedCase}
          />
        )}

        {/* Toast Container */}
        <ToastContainer toasts={toasts} onDismiss={removeToast} />

        {/* Keyframe animation for spinning refresh button */}
        <style jsx global>{`
          @keyframes netra-spin {
            0% {
              transform: rotate(0deg);
            }
            100% {
              transform: rotate(360deg);
            }
          }
        `}</style>
      </div>
    </>
  );
}

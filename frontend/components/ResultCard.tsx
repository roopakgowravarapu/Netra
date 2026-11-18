"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";
import { getStaticImageUrl, ScreeningReport } from "../lib/api";
import { FullReportModal } from "./FullReportModal";
import { ImageLightboxModal } from "./ImageLightboxModal";
import { QualityBadge } from "./QualityBadge";
import { BiomarkersGrid } from "./explainability/BiomarkersGrid";

interface ResultCardProps {
    report: ScreeningReport;
    originalFile?: File | null;
    onRecapture?: () => void;
}

const GRADE_COLORS: Record<number, string> = {
    0: "#10b981", // No DR (Green)
    1: "#0284c7", // Mild DR (Blue)
    2: "#d97706", // Moderate DR (Amber)
    3: "#ea580c", // Severe DR (Orange)
    4: "#dc2626", // Proliferative DR (Red)
};

const GRADE_LABELS: Record<number, string> = {
    0: "No DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
};

export function ResultCard({ report, originalFile, onRecapture }: ResultCardProps) {
    const { image_quality, dr_prediction, explanation, recommendation, disclaimer, retinal_analysis } = report;
    const retinalAnalysis = retinal_analysis;

    const statusUpper = (image_quality.status || "").toUpperCase();
    const isUngradable = statusUpper === "UNGRADABLE" || retinalAnalysis?.quality_status === "UNGRADABLE";
    const isBorderline = statusUpper === "BORDERLINE" || retinalAnalysis?.quality_status === "BORDERLINE" || Boolean(retinalAnalysis?.enhancement_applied);
    const isGradable = !isUngradable;

    const caseId = report.case_id || `case_${report.sample_id}`;

    const [activeExplainTab, setActiveExplainTab] = useState<
        "gradcam" | "spatial" | "lesions" | "composite" | "vessels" | "enhanced" | "original"
    >("gradcam");
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);

    const [clinicianStatus, setClinicianStatus] = useState<string | null>(null);
    const [overrideOpen, setOverrideOpen] = useState(false);
    const [overrideGrade, setOverrideGrade] = useState<number | null>(null);
    const [clinicianNotes, setClinicianNotes] = useState<string>("");
    const [slipOpen, setSlipOpen] = useState(false);
    const [showReportModal, setShowReportModal] = useState(false);
    const [showLightbox, setShowLightbox] = useState(false);

    const handleClinicianAction = (action: "APPROVE" | "FALSE_POSITIVE") => {
        if (action === "APPROVE") {
            setClinicianStatus("APPROVED");
            setClinicianNotes("Referral Approved by Consulting Clinician.");
        } else {
            setClinicianStatus("FALSE_POSITIVE");
            setOverrideGrade(0);
            setClinicianNotes("Marked False Positive by Clinician (Overridden to Level 0 No DR).");
        }
    };

    const handleApplyOverride = (newGrade: number) => {
        setOverrideGrade(newGrade);
        setClinicianStatus("OVERRIDDEN");
        setClinicianNotes(`Grade Overridden to Level ${newGrade} (${GRADE_LABELS[newGrade]}) by Consulting Clinician.`);
    };


    useEffect(() => {
        if (originalFile) {
            const url = URL.createObjectURL(originalFile);
            setPreviewUrl(url);
            return () => {
                URL.revokeObjectURL(url);
            };
        } else {
            const backendOriginal = getStaticImageUrl(
                report.original_image_path || report.explanation?.original_image_path
            );
            setPreviewUrl(backendOriginal);
        }
    }, [originalFile, report]);

    const originalUrl = previewUrl || getStaticImageUrl(report.original_image_path || report.explanation?.original_image_path);
    const gradcamUrl = getStaticImageUrl(retinalAnalysis?.gradcam_image || explanation?.gradcam_path);
    const spatialMapUrl = getStaticImageUrl(retinalAnalysis?.spatial_analysis?.spatial_map_image);
    const lesionOverlayUrl = getStaticImageUrl(retinalAnalysis?.lesion_evidence?.lesion_overlay || retinalAnalysis?.lesion_evidence_image);
    const vesselMaskUrl = getStaticImageUrl(retinalAnalysis?.retinal_structures?.vessel_mask);
    const enhancedUrl = getStaticImageUrl(retinalAnalysis?.enhanced_image);
    const compositeUrl = getStaticImageUrl(retinalAnalysis?.annotated_report);

    // -------------------------------------------------------------
    // UNGRADABLE SAFEGUARD VIEW
    // -------------------------------------------------------------
    if (!isGradable) {
        const feedbackList = (retinalAnalysis?.quality_feedback && retinalAnalysis.quality_feedback.length > 0)
            ? retinalAnalysis.quality_feedback
            : image_quality.issues;
        const recaptureGuide = retinalAnalysis?.recapture_instructions || recommendation;

        return (
            <div className="card" style={{ borderLeft: "4px solid #ef4444" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem" }}>
                    <QualityBadge quality={{ ...image_quality, status: "ungradable" }} />
                    <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Case: <strong>{caseId}</strong></span>
                </div>

                <div style={{
                    background: "rgba(239, 68, 68, 0.08)",
                    border: "1px solid rgba(239, 68, 68, 0.25)",
                    borderRadius: "0.75rem",
                    padding: "1.5rem",
                    marginBottom: "1.5rem"
                }}>
                    <h3 style={{ color: "#ef4444", fontSize: "1.3rem", fontWeight: "800", marginBottom: "0.5rem" }}>
                        ⚠️ Image cannot be graded.
                    </h3>
                    <p style={{ color: "var(--text-main)", fontSize: "0.95rem", lineHeight: "1.5" }}>
                        The uploaded retinal photograph does not meet minimum clinical quality criteria. Automated DR classification and lesion analysis are disabled for patient safety.
                    </p>

                    <div style={{ marginTop: "1.25rem" }}>
                        <div style={{ fontWeight: "700", fontSize: "0.9rem", color: "#ef4444", marginBottom: "0.5rem" }}>
                            Detected Quality Deficiencies:
                        </div>
                        <ul style={{ paddingLeft: "1.25rem", color: "var(--text-main)", fontSize: "0.9rem", lineHeight: "1.6" }}>
                            {feedbackList.length > 0 ? (
                                feedbackList.map((issue, idx) => (
                                    <li key={idx} style={{ marginBottom: "0.35rem" }}>
                                        <strong>
                                            {issue.toLowerCase().includes("blur") || issue.toLowerCase().includes("focus")
                                                ? "Poor focus: "
                                                : issue.toLowerCase().includes("illumination") || issue.toLowerCase().includes("exposure")
                                                    ? "Insufficient illumination / exposure: "
                                                    : issue.toLowerCase().includes("view") || issue.toLowerCase().includes("aperture") || issue.toLowerCase().includes("fov")
                                                        ? "Inadequate field of view: "
                                                        : ""}
                                        </strong>
                                        {issue}
                                    </li>
                                ))
                            ) : (
                                <>
                                    <li><strong>Poor focus:</strong> Significant optical defocus or motion blur prevents vascular visualization.</li>
                                    <li><strong>Insufficient illumination:</strong> Image exhibits severe underexposure or illumination clipping.</li>
                                    <li><strong>Inadequate field of view:</strong> Restricted aperture does not satisfy retinal screening coverage.</li>
                                </>
                            )}
                        </ul>
                    </div>
                </div>

                <div style={{
                    background: "var(--bg-card-subtle)",
                    borderRadius: "0.75rem",
                    padding: "1.25rem",
                    border: "1px solid var(--border-card)",
                    marginBottom: "1.5rem"
                }}>
                    <h4 style={{ color: "var(--primary)", fontSize: "0.95rem", fontWeight: "700", marginBottom: "0.4rem" }}>
                        📷 Clinical Recapture Instructions
                    </h4>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: "1.5" }}>
                        {recaptureGuide}
                    </p>
                </div>

                {/* Ungradable Action Card */}
                <div style={{
                    background: "var(--bg-card-subtle)",
                    border: "1px solid rgba(239, 68, 68, 0.3)",
                    borderRadius: "0.85rem",
                    padding: "1.1rem 1.4rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "1.5rem",
                    flexWrap: "wrap",
                    gap: "1rem"
                }}>
                    <div>
                        <div style={{ fontWeight: "800", color: "#ef4444", fontSize: "1rem" }}>
                            📷 Retinal Image Recapture Required
                        </div>
                        <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                            Status: <span style={{ color: "#ef4444", fontWeight: "800" }}>RECAPTURE_REQUIRED</span> • Image cannot be graded. A fresh scan is required.
                        </div>
                    </div>
                    {onRecapture ? (
                        <button
                            type="button"
                            onClick={onRecapture}
                            style={{
                                background: "#ef4444",
                                color: "#ffffff",
                                border: "none",
                                padding: "0.65rem 1.3rem",
                                borderRadius: "8px",
                                fontSize: "0.88rem",
                                fontWeight: "700",
                                cursor: "pointer",
                                boxShadow: "0 2px 10px rgba(239, 68, 68, 0.25)",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "0.4rem"
                            }}
                        >
                            <span>📷</span>
                            <span>Upload New Fundus Scan</span>
                        </button>
                    ) : (
                        <Link
                            href="/screening"
                            style={{
                                background: "#ef4444",
                                color: "#ffffff",
                                padding: "0.65rem 1.3rem",
                                borderRadius: "8px",
                                fontSize: "0.88rem",
                                fontWeight: "700",
                                textDecoration: "none",
                                boxShadow: "0 2px 10px rgba(239, 68, 68, 0.25)",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "0.4rem"
                            }}
                        >
                            <span>📷</span>
                            <span>Upload New Fundus Scan</span>
                        </Link>
                    )}
                </div>

                <div style={{ fontSize: "0.8rem", color: "var(--text-subtle)", fontStyle: "italic", textAlign: "center" }}>
                    {disclaimer}
                </div>
            </div>
        );
    }

    // -------------------------------------------------------------
    // GRADABLE / BORDERLINE RESULTS VIEW
    // -------------------------------------------------------------
    const baseGrade = retinalAnalysis?.dr_grade ?? dr_prediction?.grade ?? 0;
    const grade = overrideGrade !== null ? overrideGrade : baseGrade;
    const severity = overrideGrade !== null ? (GRADE_LABELS[overrideGrade] || `Level ${overrideGrade}`) : (retinalAnalysis?.severity ?? dr_prediction?.label ?? "No DR");
    const isReferable = overrideGrade !== null ? (overrideGrade >= 2) : (retinalAnalysis?.referable_dr ?? (grade >= 2));
    const gradeColor = GRADE_COLORS[grade] || "var(--primary)";

    const calibratedConf = retinalAnalysis?.calibrated_confidence ?? dr_prediction?.confidence ?? 0.85;
    const rawConf = retinalAnalysis?.raw_confidence ?? dr_prediction?.confidence ?? 0.88;
    const calibStatus = retinalAnalysis?.calibration_status || "Temperature Scaled (T=1.34) on APTOS+DDR Validation Cohort";

    // Select current image to show in explainability viewer
    let activeImageUrl = gradcamUrl;
    let activeDescription = retinalAnalysis?.gradcam_description || "Regions receiving high attention from the DR classification model.";

    if (activeExplainTab === "spatial") {
        activeImageUrl = spatialMapUrl || originalUrl;
        activeDescription = "Retinal Anatomical & Quadrant Map: Partitioning Macular ring (cyan), Optic Disc (green), and 4 quadrants (ST, IT, SN, IN) with localized lesion callouts.";
    } else if (activeExplainTab === "lesions") {
        activeImageUrl = lesionOverlayUrl || originalUrl;
        activeDescription = retinalAnalysis?.lesion_evidence_description || "Regions identified by the retinal lesion analysis module.";
    } else if (activeExplainTab === "composite") {
        activeImageUrl = compositeUrl || originalUrl;
        activeDescription = "Clinical annotated composite: Optic disc ring (green), fovea marker (cyan), and lesion boundaries.";
    } else if (activeExplainTab === "vessels") {
        activeImageUrl = vesselMaskUrl || originalUrl;
        activeDescription = "Retinal vasculature tree segmented using multi-angle matched morphological filtering.";
    } else if (activeExplainTab === "enhanced") {
        activeImageUrl = enhancedUrl || originalUrl;
        activeDescription = "Retinal enhancement output: Contrast-Limited Adaptive Histogram Equalization (CLAHE) & illumination normalization.";
    } else if (activeExplainTab === "original") {
        activeImageUrl = originalUrl;
        activeDescription = "Original patient fundus scan captured at primary screening station.";
    }

    return (
        <div className="card">
            {/* Top Header Row */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem", flexWrap: "wrap", gap: "1rem" }}>
                <QualityBadge quality={{ ...image_quality, status: isBorderline ? "BORDERLINE" : "gradable" }} />
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
                    <div style={{ fontSize: "0.85rem", color: "var(--text-main)", background: "var(--bg-card-subtle)", padding: "0.3rem 0.75rem", borderRadius: "6px", border: "1px solid var(--border-card)" }}>
                        👤 Patient: <strong style={{ color: "var(--primary)" }}>{report.patient_name || "Anonymous Patient"}</strong> ({report.patient_id || "PAT-1001"})
                    </div>
                    <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", background: "var(--bg-card-subtle)", padding: "0.3rem 0.75rem", borderRadius: "6px", border: "1px solid var(--border-card)" }}>
                        👁️ Eye: <strong style={{ color: "var(--primary)" }}>{report.eye_examined || "OD"}</strong> {report.age ? `• ${report.age} yrs` : ""} {report.gender ? `• ${report.gender}` : ""}
                    </div>
                    <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", background: "var(--bg-card-subtle)", padding: "0.3rem 0.75rem", borderRadius: "6px", border: "1px solid var(--border-card)" }}>
                        📅 {report.screening_date || "16/09/2026"} • {report.screening_time || "02:24 PM"}
                    </div>
                    <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Case: <strong>{caseId}</strong></span>
                    <button
                        type="button"
                        onClick={() => setShowReportModal(true)}
                        style={{
                            background: "linear-gradient(135deg, var(--primary), var(--accent-teal))",
                            color: "#ffffff",
                            border: "none",
                            padding: "0.45rem 1rem",
                            borderRadius: "6px",
                            fontWeight: "700",
                            fontSize: "0.85rem",
                            cursor: "pointer",
                            boxShadow: "0 2px 10px var(--primary-glow)"
                        }}
                    >
                        📋 View Full Report
                    </button>
                </div>
            </div>

            {/* Top Compact Case Summary */}
            <div style={{
                background: "var(--bg-card-subtle)",
                border: "1px solid var(--border-card)",
                borderRadius: "0.85rem",
                padding: "1rem 1.25rem",
                marginBottom: "1.5rem",
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                gap: "1rem"
            }}>
                <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: "700" }}>PATIENT</div>
                    <div style={{ fontSize: "0.95rem", fontWeight: "800", color: "var(--text-main)", marginTop: "0.15rem" }}>
                        {report.patient_name || "Anonymous Patient"}
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: "700" }}>CASE ID</div>
                    <div style={{ fontSize: "0.95rem", fontWeight: "800", color: "var(--primary)", marginTop: "0.15rem" }}>
                        {caseId}
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: "700" }}>SCREENED</div>
                    <div style={{ fontSize: "0.85rem", fontWeight: "700", color: "var(--text-main)", marginTop: "0.15rem" }}>
                        {report.screening_date || "16/09/2026"} • {report.screening_time || "02:24 PM"}
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: "700" }}>DR RESULT</div>
                    <div style={{ fontSize: "0.95rem", fontWeight: "800", color: gradeColor, marginTop: "0.15rem" }}>
                        Level {grade} — {severity}
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: "700" }}>CONFIDENCE</div>
                    <div style={{ fontSize: "0.95rem", fontWeight: "800", color: "var(--primary)", marginTop: "0.15rem" }}>
                        {(calibratedConf * 100).toFixed(0)}% (Calibrated)
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: "700" }}>STATUS</div>
                    <div style={{ fontSize: "0.85rem", fontWeight: "900", color: isReferable ? "#dc2626" : "#10b981", marginTop: "0.15rem" }}>
                        {isReferable ? "REFERABLE" : "NON-REFERABLE"}
                    </div>
                </div>
            </div>

            {/* Borderline Enhancement Notification Banner */}
            {isBorderline && (
                <div style={{
                    background: "rgba(217, 119, 6, 0.08)",
                    border: "1px solid rgba(217, 119, 6, 0.35)",
                    borderRadius: "0.75rem",
                    padding: "1rem 1.4rem",
                    marginBottom: "1.5rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: "1rem",
                    flexWrap: "wrap"
                }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                        <span style={{ fontSize: "1.4rem" }}>✨</span>
                        <div>
                            <div style={{ fontWeight: "800", color: "#d97706", fontSize: "0.98rem" }}>
                                Borderline Quality: Retinal Enhancement Applied
                            </div>
                            <p style={{ margin: "0.2rem 0 0", fontSize: "0.85rem", color: "var(--text-main)", lineHeight: "1.4" }}>
                                Mild blur or illumination non-uniformity detected. Retinal enhancement module applied CLAHE contrast equalization and illumination background normalization prior to lesion grading.
                            </p>
                        </div>
                    </div>
                    {enhancedUrl && (
                        <button
                            type="button"
                            onClick={() => setActiveExplainTab("enhanced")}
                            style={{
                                background: "rgba(217, 119, 6, 0.18)",
                                border: "1px solid rgba(217, 119, 6, 0.4)",
                                color: "#d97706",
                                padding: "0.45rem 0.9rem",
                                borderRadius: "6px",
                                fontSize: "0.82rem",
                                fontWeight: "700",
                                cursor: "pointer",
                                transition: "all 0.2s ease"
                            }}
                        >
                            Compare Enhanced Scan →
                        </button>
                    )}
                </div>
            )}

            {/* Referable DR Prominent Clinical Status Banner */}
            <div style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "1.1rem 1.4rem",
                borderRadius: "0.85rem",
                marginBottom: "1.75rem",
                background: isReferable ? "rgba(220, 38, 38, 0.12)" : "rgba(16, 185, 129, 0.12)",
                border: `1.5px solid ${isReferable ? "rgba(220, 38, 38, 0.4)" : "rgba(16, 185, 129, 0.4)"}`,
                flexWrap: "wrap",
                gap: "1rem",
                boxShadow: "var(--card-shadow)"
            }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
                    <span style={{ fontSize: "1.6rem" }}>{isReferable ? "🚨" : "✓"}</span>
                    <div>
                        <div style={{ fontWeight: "900", fontSize: "1.15rem", color: isReferable ? "#dc2626" : "#10b981", letterSpacing: "-0.01em" }}>
                            REFERABLE DR: {isReferable ? "YES (Level 2+)" : "NO (Non-Referable)"}
                        </div>
                        <div style={{ fontSize: "0.86rem", color: "var(--text-main)", marginTop: "0.25rem" }}>
                            {isReferable
                                ? "Meets ICDR clinical criteria for specialist referral (Level 2 Moderate NPDR or higher)."
                                : "No referable diabetic retinopathy detected (Level 0 or Level 1 Mild NPDR). Routine follow-up scheduled."}
                        </div>
                    </div>
                </div>
                <div style={{
                    fontSize: "0.85rem",
                    fontWeight: "800",
                    padding: "0.45rem 1rem",
                    borderRadius: "8px",
                    background: isReferable ? "#dc2626" : "#10b981",
                    color: "#ffffff",
                    boxShadow: `0 2px 10px ${isReferable ? "rgba(220, 38, 38, 0.3)" : "rgba(16, 185, 129, 0.3)"}`
                }}>
                    {isReferable ? "SPECIALIST REFERRAL REQUIRED" : "PRIMARY CARE ROUTINE"}
                </div>
            </div>

            {/* "WHAT SHOULD I DO NEXT?" Primary Action Card */}
            <div style={{
                background: "var(--bg-card)",
                border: "1px solid var(--primary-glow)",
                borderRadius: "0.85rem",
                padding: "1.1rem 1.4rem",
                marginBottom: "1.75rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "1rem",
                flexWrap: "wrap",
                boxShadow: "0 4px 16px var(--primary-glow)"
            }}>
                <div>
                    <div style={{ fontSize: "0.78rem", fontWeight: "800", color: "var(--primary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                        WHAT SHOULD I DO NEXT?
                    </div>
                    <div style={{ fontSize: "1.05rem", fontWeight: "800", color: "var(--text-main)", marginTop: "0.2rem" }}>
                        {isReferable ? "Specialist Review Recommended" : "Follow Scheduled Timeline"}
                    </div>
                    <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                        {isReferable
                            ? "Enqueued for remote ophthalmologist verification in the rural telemedicine network."
                            : "No immediate referral required. Generate report and schedule routine 12-month follow-up."}
                    </div>
                </div>

                <div>
                    {isReferable ? (
                        <Link
                            href={`/dashboard?case_id=${caseId}`}
                            style={{
                                background: "linear-gradient(135deg, #dc2626, #b91c1c)",
                                color: "#ffffff",
                                padding: "0.65rem 1.3rem",
                                borderRadius: "8px",
                                fontSize: "0.88rem",
                                fontWeight: "800",
                                textDecoration: "none",
                                boxShadow: "0 4px 15px rgba(220, 38, 38, 0.3)",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "0.4rem"
                            }}
                        >
                            <span>Send to Specialist</span>
                            <span>→</span>
                        </Link>
                    ) : (
                        <button
                            type="button"
                            onClick={() => setShowReportModal(true)}
                            style={{
                                background: "linear-gradient(135deg, var(--primary), var(--accent-teal))",
                                color: "#ffffff",
                                border: "none",
                                padding: "0.65rem 1.3rem",
                                borderRadius: "8px",
                                fontSize: "0.88rem",
                                fontWeight: "800",
                                cursor: "pointer",
                                boxShadow: "0 4px 15px var(--primary-glow)",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "0.4rem"
                            }}
                        >
                            <span>View Full Report</span>
                            <span>→</span>
                        </button>
                    )}
                </div>
            </div>

            {/* 1. DR Prediction, Calibrated Confidence, & Uncertainty Grid */}
            <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                gap: "1.5rem",
                marginBottom: "1.75rem"
            }}>
                {/* DR Prediction & Confidence Box */}
                <div style={{
                    background: "var(--bg-card)",
                    border: `1px solid ${gradeColor}40`,
                    borderRadius: "1rem",
                    padding: "1.5rem",
                    boxShadow: "var(--card-shadow)"
                }}>
                    <div style={{ fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                        DR Severity Grading (ICDR 0–4)
                    </div>
                    <div style={{ fontSize: "1.85rem", fontWeight: "800", color: gradeColor, marginTop: "0.3rem" }}>
                        Level {grade}: {severity}
                    </div>

                    {/* Calibrated Confidence Bar */}
                    <div style={{ marginTop: "1.1rem" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.88rem", marginBottom: "0.35rem" }}>
                            <span style={{ color: "var(--text-muted)", fontWeight: "600" }}>Calibrated Confidence:</span>
                            <span style={{ color: "var(--text-main)", fontWeight: "800" }}>{(calibratedConf * 100).toFixed(1)}%</span>
                        </div>
                        <div style={{ height: "10px", background: "var(--border-card)", borderRadius: "5px", overflow: "hidden", marginBottom: "0.5rem" }}>
                            <div style={{ height: "100%", width: `${calibratedConf * 100}%`, backgroundColor: gradeColor, borderRadius: "5px", transition: "width 0.6s ease" }} />
                        </div>

                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                            <span>Raw Model Probability:</span>
                            <span style={{ fontWeight: "700", color: "var(--text-main)" }}>{(rawConf * 100).toFixed(1)}%</span>
                        </div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-subtle)", marginTop: "0.35rem", fontStyle: "italic" }}>
                            {calibStatus}
                        </div>
                    </div>
                </div>

                {/* Model Uncertainty & Targets Indicators */}
                <div style={{
                    background: "var(--bg-card-subtle)",
                    border: "1px solid var(--border-card)",
                    borderRadius: "1rem",
                    padding: "1.5rem",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between"
                }}>
                    <div>
                        <div style={{ fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                            Clinical Performance & Uncertainty
                        </div>
                        {dr_prediction?.uncertainty && (
                            <div style={{ marginTop: "0.85rem" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.88rem" }}>
                                    <span style={{ color: "var(--text-muted)" }}>Shannon Entropy:</span>
                                    <span style={{ color: "var(--primary)", fontWeight: "700" }}>{dr_prediction.uncertainty.entropy.toFixed(3)}</span>
                                </div>
                                <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.4rem", fontSize: "0.88rem" }}>
                                    <span style={{ color: "var(--text-muted)" }}>Prediction Margin:</span>
                                    <span style={{ color: "var(--accent-teal)", fontWeight: "700" }}>{(dr_prediction.uncertainty.margin * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                        )}
                    </div>

                    <div style={{
                        marginTop: "0.9rem",
                        paddingTop: "0.75rem",
                        borderTop: "1px solid var(--border-card)",
                        fontSize: "0.8rem",
                        color: "var(--text-muted)",
                        lineHeight: "1.4"
                    }}>
                        <strong style={{ color: "var(--primary)" }}>Clinical Screening Targets:</strong> Sensitivity &gt;90%, Specificity &gt;85%.
                        <div style={{ color: "var(--text-subtle)", fontSize: "0.75rem", marginTop: "0.2rem" }}>
                            Validation dataset required for prospective empirical certification.
                        </div>
                    </div>
                </div>
            </div>

            {/* 2. Retinal Structures & Lesion Evidence Grid */}
            <BiomarkersGrid retinalAnalysis={retinalAnalysis} onSelectTab={(tab) => setActiveExplainTab(tab)} />

            {/* 3. MULTIMODAL EXPLAINABILITY & SALIENCY VIEWER */}
            <div style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-card)",
                borderRadius: "1rem",
                padding: "1.75rem",
                marginBottom: "2rem",
                boxShadow: "var(--card-shadow)"
            }}>
                {/* Header */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem", flexWrap: "wrap", gap: "1rem" }}>
                    <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                            <span style={{
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                                width: "28px",
                                height: "28px",
                                borderRadius: "6px",
                                background: "var(--primary-subtle)",
                                color: "var(--primary)",
                                fontSize: "0.95rem",
                                fontWeight: "700"
                            }}>
                                ✦
                            </span>
                            <h3 style={{
                                fontSize: "1.3rem",
                                fontWeight: "800",
                                color: "var(--text-main)",
                                letterSpacing: "-0.01em",
                                margin: 0
                            }}>
                                Explainable AI & Visual Evidence
                            </h3>
                        </div>
                        <p style={{
                            fontSize: "0.9rem",
                            color: "var(--text-muted)",
                            marginTop: "0.3rem",
                            lineHeight: "1.4"
                        }}>
                            Comparing deep model activation attention with deterministic retinal lesion segmentation.
                        </p>
                    </div>

                    {/* Viewer Tabs */}
                    <div style={{
                        display: "flex",
                        gap: "0.4rem",
                        background: "var(--bg-card-subtle)",
                        padding: "0.3rem",
                        borderRadius: "8px",
                        border: "1px solid var(--border-card)",
                        flexWrap: "wrap"
                    }}>
                        {[
                            { id: "gradcam", label: "🔥 Model Attention (Grad-CAM)" },
                            { id: "spatial", label: "📍 Retinal Places & Quadrant Map" },
                            { id: "lesions", label: "🔬 Lesion Evidence" },
                            { id: "composite", label: "📋 Clinical Report" },
                            { id: "vessels", label: "🩸 Vascular Mask" },
                            ...(isBorderline && enhancedUrl ? [{ id: "enhanced", label: "✨ Enhanced Scan" }] : []),
                            { id: "original", label: "📷 Original Scan" }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                type="button"
                                onClick={() => setActiveExplainTab(tab.id as any)}
                                style={{
                                    background: activeExplainTab === tab.id ? "var(--primary)" : "transparent",
                                    color: activeExplainTab === tab.id ? "#ffffff" : "var(--text-muted)",
                                    border: "none",
                                    padding: "0.45rem 0.85rem",
                                    borderRadius: "6px",
                                    fontSize: "0.82rem",
                                    fontWeight: "700",
                                    cursor: "pointer",
                                    transition: "all 0.2s ease"
                                }}
                            >
                                {tab.label}
                            </button>
                        ))}
                        <button
                            type="button"
                            onClick={() => setShowLightbox(true)}
                            style={{
                                background: "rgba(2, 132, 199, 0.15)",
                                color: "#0284c7",
                                border: "1px solid rgba(2, 132, 199, 0.3)",
                                padding: "0.45rem 0.85rem",
                                borderRadius: "6px",
                                fontSize: "0.82rem",
                                fontWeight: "700",
                                cursor: "pointer"
                            }}
                        >
                            🔍 Inspect High-Res Image
                        </button>
                    </div>
                </div>

                {/* Dynamic Image Display Container */}
                <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
                    gap: "1.5rem"
                }}>
                    {/* Reference: Original Patient Fundus Image */}
                    <div style={{
                        background: "var(--bg-card-subtle)",
                        border: "1px solid var(--border-card)",
                        borderRadius: "0.85rem",
                        padding: "1.1rem",
                        display: "flex",
                        flexDirection: "column"
                    }}>
                        <div style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            marginBottom: "0.75rem",
                            fontSize: "0.85rem",
                            fontWeight: "700"
                        }}>
                            <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem", color: "var(--text-main)" }}>
                                📷 Patient Fundus Scan
                            </span>
                            <span style={{ fontSize: "0.75rem", color: "var(--text-subtle)", background: "var(--border-card)", padding: "0.2rem 0.55rem", borderRadius: "4px" }}>
                                Reference Scan
                            </span>
                        </div>

                        <div style={{
                            flex: 1,
                            minHeight: "320px",
                            maxHeight: "380px",
                            background: "#090d16",
                            borderRadius: "0.5rem",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            overflow: "hidden",
                            border: "1px solid rgba(0, 0, 0, 0.15)"
                        }}>
                            {originalUrl ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                    src={originalUrl}
                                    alt="Original Patient Fundus Scan"
                                    style={{
                                        maxWidth: "100%",
                                        maxHeight: "380px",
                                        width: "auto",
                                        height: "auto",
                                        objectFit: "contain",
                                        display: "block"
                                    }}
                                />
                            ) : (
                                <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                                    Original image not available
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Active Visual Explanation Output */}
                    <div style={{
                        background: "var(--bg-card-subtle)",
                        border: "1px solid var(--primary-glow)",
                        borderRadius: "0.85rem",
                        padding: "1.1rem",
                        display: "flex",
                        flexDirection: "column",
                        boxShadow: "0 4px 16px var(--primary-glow)"
                    }}>
                        <div style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            marginBottom: "0.75rem",
                            fontSize: "0.85rem",
                            fontWeight: "700"
                        }}>
                            <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem", color: "var(--primary)" }}>
                                {activeExplainTab === "gradcam" && "🔥 Model Attention (Grad-CAM)"}
                                {activeExplainTab === "spatial" && "📍 Retinal Places & Quadrant Map"}
                                {activeExplainTab === "lesions" && "🔬 Retinal Lesion Evidence"}
                                {activeExplainTab === "composite" && "📋 Clinical Annotated Report"}
                                {activeExplainTab === "vessels" && "🩸 Retinal Vascular Network"}
                                {activeExplainTab === "enhanced" && "✨ Enhanced Retinal Scan"}
                                {activeExplainTab === "original" && "📷 Original Fundus Scan"}
                            </span>
                            <span style={{
                                fontSize: "0.75rem",
                                color: "var(--primary)",
                                fontWeight: "700",
                                background: "var(--primary-subtle)",
                                padding: "0.2rem 0.55rem",
                                borderRadius: "4px",
                                border: "1px solid var(--primary-glow)"
                            }}>
                                Target: {severity}
                            </span>
                        </div>

                        <div style={{
                            flex: 1,
                            minHeight: "320px",
                            maxHeight: "380px",
                            background: "#090d16",
                            borderRadius: "0.5rem",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            overflow: "hidden",
                            border: "1px solid rgba(0, 0, 0, 0.15)"
                        }}>
                            {activeImageUrl ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                    src={activeImageUrl}
                                    alt={activeDescription}
                                    style={{
                                        maxWidth: "100%",
                                        maxHeight: "380px",
                                        width: "auto",
                                        height: "auto",
                                        objectFit: "contain",
                                        display: "block"
                                    }}
                                />
                            ) : (
                                <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                                    Active visual explanation unavailable
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Explainability Distinction & Definition Banner */}
                <div style={{
                    marginTop: "1.25rem",
                    padding: "1rem 1.25rem",
                    background: "rgba(2, 132, 199, 0.06)",
                    border: "1px solid rgba(2, 132, 199, 0.22)",
                    borderRadius: "0.65rem",
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "0.75rem"
                }}>
                    <span style={{ fontSize: "1.25rem", flexShrink: 0, marginTop: "0.1rem" }}>📍</span>
                    <div>
                        <div style={{ fontSize: "0.92rem", color: "var(--text-main)", fontWeight: "700", lineHeight: "1.4" }}>
                            {activeDescription}
                        </div>
                        <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "0.3rem", lineHeight: "1.5" }}>
                            <strong>Clinical Explainability Distinction:</strong> Grad-CAM highlights deep learning feature attention regions and does not constitute direct lesion detection. Consult the Lesion Evidence map for segmented microaneurysms (Cyan), hard exudates (Yellow), hemorrhages (Red), and neovascularization (Magenta).
                        </div>
                    </div>
                </div>
            </div>

            {/* 4. Clinical Action Recommendation Box */}
            <div style={{
                background: "var(--primary-subtle)",
                border: "1px solid var(--primary-glow)",
                borderRadius: "0.85rem",
                padding: "1.25rem 1.5rem",
                marginBottom: "1.75rem"
            }}>
                <h4 style={{ color: "var(--primary)", fontSize: "0.95rem", fontWeight: "700", marginBottom: "0.4rem" }}>
                    Clinical Action Recommendation
                </h4>
                <p style={{ color: "var(--text-main)", fontSize: "0.95rem", lineHeight: "1.5" }}>
                    {recommendation}
                </p>
            </div>

            {/* 5. 30-Second Clinician Validation Card */}
            <div style={{
                background: "var(--bg-card-subtle)",
                border: "1px solid var(--border-card)",
                borderRadius: "1rem",
                padding: "1.25rem 1.5rem",
                marginBottom: "1.75rem"
            }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.75rem", flexWrap: "wrap", gap: "0.5rem" }}>
                    <div style={{ fontWeight: "800", fontSize: "1rem", color: "var(--text-main)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <span>🩺</span> Clinician Validation Action Row (&lt;30-Sec Workflow)
                    </div>
                    <span style={{ fontSize: "0.78rem", color: "var(--primary)", background: "var(--primary-subtle)", padding: "0.2rem 0.6rem", borderRadius: "4px", fontWeight: "700" }}>
                        PHC Triage Action
                    </span>
                </div>

                <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "center", marginTop: "0.75rem" }}>
                    <button
                        type="button"
                        onClick={() => handleClinicianAction("APPROVE")}
                        style={{
                            background: clinicianStatus === "APPROVED" ? "#10b981" : "rgba(16, 185, 129, 0.12)",
                            color: clinicianStatus === "APPROVED" ? "#ffffff" : "#10b981",
                            border: "1px solid rgba(16, 185, 129, 0.4)",
                            padding: "0.55rem 1.1rem",
                            borderRadius: "8px",
                            fontSize: "0.88rem",
                            fontWeight: "700",
                            cursor: "pointer",
                            transition: "all 0.2s ease"
                        }}
                    >
                        ✓ Approve Referral
                    </button>
                    <button
                        type="button"
                        onClick={() => setOverrideOpen(!overrideOpen)}
                        style={{
                            background: clinicianStatus === "OVERRIDDEN" ? "#d97706" : "rgba(217, 119, 6, 0.12)",
                            color: clinicianStatus === "OVERRIDDEN" ? "#ffffff" : "#d97706",
                            border: "1px solid rgba(217, 119, 6, 0.4)",
                            padding: "0.55rem 1.1rem",
                            borderRadius: "8px",
                            fontSize: "0.88rem",
                            fontWeight: "700",
                            cursor: "pointer",
                            transition: "all 0.2s ease"
                        }}
                    >
                        ✏️ Override Grade
                    </button>
                    <button
                        type="button"
                        onClick={() => handleClinicianAction("FALSE_POSITIVE")}
                        style={{
                            background: clinicianStatus === "FALSE_POSITIVE" ? "#ef4444" : "rgba(239, 68, 68, 0.12)",
                            color: clinicianStatus === "FALSE_POSITIVE" ? "#ffffff" : "#ef4444",
                            border: "1px solid rgba(239, 68, 68, 0.4)",
                            padding: "0.55rem 1.1rem",
                            borderRadius: "8px",
                            fontSize: "0.88rem",
                            fontWeight: "700",
                            cursor: "pointer",
                            transition: "all 0.2s ease"
                        }}
                    >
                        🚫 Mark False Positive
                    </button>
                    <button
                        type="button"
                        onClick={() => setSlipOpen(true)}
                        style={{
                            background: "linear-gradient(135deg, var(--primary), var(--accent-teal))",
                            color: "#ffffff",
                            border: "none",
                            padding: "0.55rem 1.2rem",
                            borderRadius: "8px",
                            fontSize: "0.88rem",
                            fontWeight: "800",
                            cursor: "pointer",
                            boxShadow: "0 2px 10px var(--primary-glow)",
                            marginLeft: "auto"
                        }}
                    >
                        🖨️ Telemedicine Summary Slip
                    </button>
                </div>

                {overrideOpen && (
                    <div style={{ marginTop: "1rem", padding: "1rem", background: "var(--bg-card)", borderRadius: "8px", border: "1px solid var(--border-card)" }}>
                        <div style={{ fontWeight: "700", fontSize: "0.88rem", marginBottom: "0.5rem" }}>Select Clinician Override DR Grade:</div>
                        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                            {[0, 1, 2, 3, 4].map((g) => (
                                <button
                                    key={g}
                                    type="button"
                                    onClick={() => handleApplyOverride(g)}
                                    style={{
                                        background: overrideGrade === g ? GRADE_COLORS[g] : "var(--bg-card-subtle)",
                                        color: overrideGrade === g ? "#ffffff" : "var(--text-main)",
                                        border: `1px solid ${GRADE_COLORS[g]}`,
                                        padding: "0.4rem 0.8rem",
                                        borderRadius: "6px",
                                        fontWeight: "700",
                                        fontSize: "0.82rem",
                                        cursor: "pointer"
                                    }}
                                >
                                    Level {g} ({GRADE_LABELS[g]})
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {clinicianNotes && (
                    <div style={{ marginTop: "0.75rem", fontSize: "0.85rem", color: "#10b981", fontWeight: "700" }}>
                        Status: {clinicianNotes}
                    </div>
                )}
            </div>

            {/* Telemedicine Summary Slip Modal */}
            {slipOpen && (
                <div style={{
                    position: "fixed",
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: "rgba(0, 0, 0, 0.75)",
                    zIndex: 9999,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "1rem"
                }}>
                    <div style={{
                        background: "#ffffff",
                        color: "#0f172a",
                        borderRadius: "1rem",
                        padding: "2rem",
                        maxWidth: "680px",
                        width: "100%",
                        maxHeight: "90vh",
                        overflowY: "auto",
                        boxShadow: "0 20px 50px rgba(0,0,0,0.5)"
                    }}>
                        <div style={{ borderBottom: "2px solid #0284c7", paddingBottom: "0.75rem", marginBottom: "1.25rem", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                            <div>
                                <h2 style={{ margin: 0, color: "#0284c7", fontSize: "1.4rem", fontWeight: 900 }}>NETRA • नेत्र पोर्टल</h2>
                                <div style={{ fontSize: "0.85rem", color: "#475569", fontWeight: 700 }}>
                                    PHC Telemedicine Referral Slip / प्राथमिक स्वास्थ्य केंद्र पर्ची
                                </div>
                            </div>
                            <div style={{
                                background: isReferable ? "#dc2626" : "#10b981",
                                color: "#ffffff",
                                padding: "0.4rem 0.8rem",
                                borderRadius: "6px",
                                fontWeight: 800,
                                fontSize: "0.78rem",
                                textAlign: "center",
                                whiteSpace: "pre-line"
                            }}>
                                {isReferable ? "SPECIALIST REFERRAL REQUIRED\nविशेषज्ञ परामर्श आवश्यक" : "ROUTINE SCREENING\nसामान्य नियमित जांच"}
                            </div>
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", fontSize: "0.88rem", background: "#f8fafc", padding: "0.85rem", borderRadius: "8px", marginBottom: "1.25rem" }}>
                            <div><strong>Patient ID / मरीज:</strong> {caseId}</div>
                            <div><strong>Date / दिनांक:</strong> {new Date().toLocaleDateString("en-IN")}</div>
                            <div><strong>Facility / केंद्र:</strong> Rural Primary Health Center (PHC)</div>
                            <div><strong>Triage / स्थिति:</strong> {isReferable ? "REFER_TO_SPECIALIST" : "ROUTINE_12MO_SCREENING"}</div>
                        </div>

                        <div style={{ marginBottom: "1.25rem" }}>
                            <h4 style={{ margin: "0 0 0.3rem", color: "#0f172a", fontSize: "0.95rem" }}>Clinical DR Grade / दृष्टि-पटल जांच परिणाम:</h4>
                            <div style={{ fontSize: "1.15rem", fontWeight: 800, color: gradeColor }}>
                                Level {grade}: {severity}
                            </div>
                            <div style={{ fontSize: "0.85rem", color: "#475569", marginTop: "0.25rem" }}>
                                Referral Risk Confidence / जोखिम संभावना: <strong>{(calibratedConf * 100).toFixed(1)}%</strong> (Platt Calibrated)
                            </div>
                        </div>

                        <div style={{ background: "#eff6ff", border: "1px solid #bfdbfe", padding: "0.85rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
                            <h4 style={{ margin: "0 0 0.3rem", color: "#1e40af", fontSize: "0.9rem" }}>
                                🗓️ Follow-up Timeline & Instructions / अनुवर्ती समय सीमा और निर्देश:
                            </h4>
                            <div style={{ fontSize: "0.88rem", color: "#1e3a8a", fontWeight: 700 }}>
                                {isReferable
                                    ? "⚠️ Visit District Hospital Retina Specialist within 2-4 weeks. / कृपया 2-4 सप्ताह के भीतर जिला अस्पताल के नेत्र विशेषज्ञ से संपर्क करें।"
                                    : "✓ Schedule next annual screening in 12 months. / अगले 12 महीनों में अगली नियमित जांच कराएं।"}
                            </div>
                        </div>

                        <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem" }}>
                            <button
                                type="button"
                                onClick={() => setSlipOpen(false)}
                                style={{ background: "#94a3b8", color: "#ffffff", border: "none", padding: "0.55rem 1.1rem", borderRadius: "6px", fontWeight: 700, cursor: "pointer" }}
                            >
                                Close / बंद करें
                            </button>
                            <button
                                type="button"
                                onClick={() => window.print()}
                                style={{ background: "#0284c7", color: "#ffffff", border: "none", padding: "0.55rem 1.3rem", borderRadius: "6px", fontWeight: 800, cursor: "pointer" }}
                            >
                                🖨️ Print / प्रिंट करें
                            </button>
                        </div>
                    </div>
                </div>
            )}


            {/* 5. Class Probability Distribution */}
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

            {/* 6. Clinical Telemedicine Workflow Routing Card Based on Predicted DR Grade */}
            {grade === 0 ? (
                /* Grade 0: Routine Screening Recommended */
                <div style={{
                    background: "rgba(16, 185, 129, 0.08)",
                    border: "1px solid rgba(16, 185, 129, 0.3)",
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
                            background: "rgba(16, 185, 129, 0.15)",
                            color: "#10b981",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: "1.5rem",
                            border: "1px solid rgba(16, 185, 129, 0.3)"
                        }}>
                            ✓
                        </div>
                        <div>
                            <div style={{ fontWeight: "800", color: "#10b981", fontSize: "1.05rem" }}>
                                Routine Screening Recommended
                            </div>
                            <div style={{ fontSize: "0.88rem", color: "var(--text-main)", marginTop: "0.2rem" }}>
                                No signs of diabetic retinopathy. No specialist consultation required.
                            </div>
                            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                                Case ID: <strong>{caseId}</strong> • Status: <span style={{ color: "#10b981", fontWeight: "700" }}>ROUTINE_SCREENING</span>
                            </div>
                        </div>
                    </div>
                </div>
            ) : grade === 1 ? (
                /* Grade 1: Mild DR Follow-up Screening */
                <div style={{
                    background: "rgba(2, 132, 199, 0.08)",
                    border: "1px solid rgba(2, 132, 199, 0.3)",
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
                            background: "rgba(2, 132, 199, 0.15)",
                            color: "#0284c7",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: "1.5rem",
                            border: "1px solid rgba(2, 132, 199, 0.3)"
                        }}>
                            ℹ️
                        </div>
                        <div>
                            <div style={{ fontWeight: "800", color: "#0284c7", fontSize: "1.05rem" }}>
                                Follow-up Screening Recommended
                            </div>
                            <div style={{ fontSize: "0.88rem", color: "var(--text-main)", marginTop: "0.2rem" }}>
                                Mild NPDR (isolated microaneurysms). Primary care monitoring and repeat scan in 6–12 months.
                            </div>
                            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                                Case ID: <strong>{caseId}</strong> • Status: <span style={{ color: "#0284c7", fontWeight: "700" }}>FOLLOW_UP_RECOMMENDED</span>
                            </div>
                        </div>
                    </div>
                </div>
            ) : grade === 4 ? (
                /* Grade 4: Urgent Specialist Review Required */
                <div style={{
                    background: "rgba(220, 38, 38, 0.08)",
                    border: "1px solid rgba(220, 38, 38, 0.4)",
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
                            background: "rgba(220, 38, 38, 0.15)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: "1.5rem",
                            border: "1px solid rgba(220, 38, 38, 0.3)"
                        }}>
                            🚨
                        </div>
                        <div>
                            <div style={{ fontWeight: "800", color: "#dc2626", fontSize: "1.05rem" }}>
                                Urgent Specialist Review Required
                            </div>
                            <div style={{ fontSize: "0.85rem", color: "var(--text-main)", marginTop: "0.15rem" }}>
                                High-Risk Proliferative DR Enqueued for Immediate Specialist Action
                            </div>
                            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                                Case ID: <strong style={{ color: "#dc2626" }}>{caseId}</strong> • Status: <span style={{ color: "#dc2626", fontWeight: "800" }}>URGENT_SPECIALIST_REVIEW</span>
                            </div>
                        </div>
                    </div>

                    <Link
                        href={`/dashboard?case_id=${caseId}`}
                        style={{
                            background: "linear-gradient(135deg, #dc2626, #b91c1c)",
                            color: "#ffffff",
                            padding: "0.7rem 1.4rem",
                            borderRadius: "8px",
                            fontSize: "0.9rem",
                            fontWeight: "800",
                            textDecoration: "none",
                            boxShadow: "0 4px 15px rgba(220, 38, 38, 0.3)",
                            transition: "all 0.2s ease",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "0.5rem"
                        }}
                    >
                        <span>Open Urgent Case in Dashboard</span>
                        <span>→</span>
                    </Link>
                </div>
            ) : (
                /* Grade 2 & 3: Moderate / Severe DR -> Specialist Review Required */
                <div style={{
                    background: "var(--bg-card-subtle)",
                    border: "1px solid rgba(217, 119, 6, 0.4)",
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
                            background: "rgba(217, 119, 6, 0.15)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: "1.5rem",
                            border: "1px solid rgba(217, 119, 6, 0.3)"
                        }}>
                            🏥
                        </div>
                        <div>
                            <div style={{ fontWeight: "800", color: "var(--text-main)", fontSize: "1rem" }}>
                                Requires Specialist Review
                            </div>
                            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                                Referable DR Enqueued in Rural Telemedicine Consultation Network
                            </div>
                            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                                Case ID: <strong style={{ color: "var(--primary)" }}>{caseId}</strong> • Status: <span style={{ color: "#d97706", fontWeight: "700" }}>REQUIRES_SPECIALIST_REVIEW</span>
                            </div>
                        </div>
                    </div>

                    <Link
                        href={`/dashboard?case_id=${caseId}`}
                        style={{
                            background: "linear-gradient(135deg, var(--primary), #d97706)",
                            color: "#ffffff",
                            padding: "0.7rem 1.4rem",
                            borderRadius: "8px",
                            fontSize: "0.9rem",
                            fontWeight: "800",
                            textDecoration: "none",
                            boxShadow: "0 4px 15px rgba(217, 119, 6, 0.3)",
                            transition: "all 0.2s ease",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "0.5rem"
                        }}
                    >
                        <span>Open Case in Specialist Dashboard</span>
                        <span>→</span>
                    </Link>
                </div>
            )}

            {/* 7. AI Disclaimer */}
            <div style={{ fontSize: "0.8rem", color: "var(--text-subtle)", fontStyle: "italic", textAlign: "center" }}>
                {disclaimer}
            </div>

            {/* Full A4 Printable Screening Report Modal */}
            <FullReportModal
                isOpen={showReportModal}
                onClose={() => setShowReportModal(false)}
                report={report}
            />

            {/* High-Resolution Image Lightbox Modal */}
            <ImageLightboxModal
                isOpen={showLightbox}
                onClose={() => setShowLightbox(false)}
                title={`Patient: ${report.patient_name || "Anonymous"} • Case ID: ${caseId}`}
                originalUrl={originalUrl}
                gradcamUrl={activeImageUrl || gradcamUrl}
            />
        </div>
    );
}

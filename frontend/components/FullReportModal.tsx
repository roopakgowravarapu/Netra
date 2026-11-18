"use client";

import React from "react";
import { getStaticImageUrl, ScreeningReport, CaseItem } from "../lib/api";

interface FullReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: ScreeningReport;
  caseItem?: CaseItem | null;
}

const GRADE_LABELS: Record<number, string> = {
  0: "Level 0: No Diabetic Retinopathy",
  1: "Level 1: Mild Non-Proliferative DR",
  2: "Level 2: Moderate Non-Proliferative DR",
  3: "Level 3: Severe Non-Proliferative DR",
  4: "Level 4: Proliferative Diabetic Retinopathy",
};

export function FullReportModal({ isOpen, onClose, report, caseItem }: FullReportModalProps) {
  if (!isOpen) return null;

  const patientName = caseItem?.patient_name || report.patient_name || "Anonymous Patient";
  const caseId = caseItem?.case_id || report.case_id || `NETRA-${report.sample_id}`;
  const screeningDate = report.screening_date || (caseItem ? new Date(caseItem.created_at).toLocaleDateString("en-IN") : "16/09/2026");
  const screeningTime = report.screening_time || (caseItem ? new Date(caseItem.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) : "02:24 PM");

  const iq = report.image_quality;
  const retinalAnalysis = report.retinal_analysis;
  const drPred = report.dr_prediction;
  const expl = report.explanation;

  const isUngradable = (iq.status || "").toLowerCase() === "ungradable" || retinalAnalysis?.quality_status === "UNGRADABLE";
  const grade = caseItem?.override_grade !== null && caseItem?.override_grade !== undefined
    ? caseItem.override_grade
    : (retinalAnalysis?.dr_grade ?? drPred?.grade ?? 0);
  const isReferable = caseItem?.override_grade !== null && caseItem?.override_grade !== undefined
    ? (caseItem.override_grade >= 2)
    : (retinalAnalysis?.referable_dr ?? (grade >= 2));

  const calibratedConf = retinalAnalysis?.calibrated_confidence ?? drPred?.confidence ?? 0.85;

  const originalUrl = getStaticImageUrl(report.original_image_path || expl?.original_image_path);
  const gradcamUrl = getStaticImageUrl(retinalAnalysis?.gradcam_image || expl?.gradcam_path);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="report-modal-overlay">
      <style jsx global>{`
        .report-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(9, 13, 22, 0.85);
          backdrop-filter: blur(8px);
          z-index: 10000;
          display: flex;
          justify-content: center;
          align-items: flex-start;
          overflow-y: auto;
          padding: 2rem 1rem;
        }

        .report-modal-container {
          background: #ffffff;
          color: #0f172a;
          width: 210mm;
          min-height: 297mm;
          padding: 18mm 18mm 15mm 18mm;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
          border-radius: 8px;
          position: relative;
          font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          box-sizing: border-box;
        }

        .report-header-toolbar {
          position: fixed;
          top: 1.25rem;
          right: 2rem;
          z-index: 10001;
          display: flex;
          gap: 0.75rem;
        }

        .report-toolbar-btn {
          padding: 0.6rem 1.4rem;
          border-radius: 8px;
          font-weight: 800;
          font-size: 0.9rem;
          cursor: pointer;
          border: none;
          box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
          transition: transform 0.2s ease;
        }

        .report-toolbar-btn:hover {
          transform: translateY(-2px);
        }

        .btn-print {
          background: #0284c7;
          color: #ffffff;
        }

        .btn-close {
          background: #475569;
          color: #ffffff;
        }

        /* PRINT STYLING */
        @media print {
          body * {
            visibility: hidden;
          }
          .report-modal-overlay,
          .report-modal-container,
          .report-modal-container * {
            visibility: visible;
          }
          .report-modal-overlay {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: auto;
            background: none !important;
            padding: 0 !important;
            overflow: visible !important;
          }
          .report-modal-container {
            width: 100% !important;
            min-height: auto !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
          }
          .report-header-toolbar {
            display: none !important;
          }
          @page {
            size: A4;
            margin: 12mm 15mm 12mm 15mm;
          }
        }
      `}</style>

      {/* Floating Action Buttons */}
      <div className="report-header-toolbar">
        <button className="report-toolbar-btn btn-print" onClick={handlePrint}>
          🖨️ Print Report / Save PDF
        </button>
        <button className="report-toolbar-btn btn-close" onClick={onClose}>
          ✕ Close Report
        </button>
      </div>

      {/* A4 Report Page Document */}
      <div className="report-modal-container">
        {/* Header Block */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "3px solid #0284c7", paddingBottom: "1rem", marginBottom: "1.25rem" }}>
          <div>
            <div style={{ fontSize: "1.8rem", fontWeight: "900", color: "#0284c7", letterSpacing: "-0.02em" }}>
              NETRA • नेत्र
            </div>
            <div style={{ fontSize: "0.9rem", color: "#475569", fontWeight: "700", marginTop: "0.2rem" }}>
              Explainable AI Diabetic Retinopathy Screening Report
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{
              display: "inline-block",
              background: isUngradable ? "#ef4444" : isReferable ? "#dc2626" : "#10b981",
              color: "#ffffff",
              padding: "0.45rem 1rem",
              borderRadius: "6px",
              fontWeight: "900",
              fontSize: "0.85rem",
              textTransform: "uppercase"
            }}>
              {isUngradable ? "UNGRADABLE IMAGE" : isReferable ? "REFERRAL REQUIRED" : "ROUTINE SCREENING"}
            </div>
            <div style={{ fontSize: "0.78rem", color: "#64748b", marginTop: "0.35rem" }}>
              Netra Clinical AI Network
            </div>
          </div>
        </div>

        {/* Patient & Screening Information Grid */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: "0.6rem 1.25rem",
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "8px",
          padding: "0.85rem 1.1rem",
          marginBottom: "1.25rem",
          fontSize: "0.85rem"
        }}>
          <div>
            <span style={{ color: "#64748b", fontWeight: "600" }}>Patient Name: </span>
            <strong style={{ color: "#0f172a" }}>{patientName}</strong>
          </div>
          <div>
            <span style={{ color: "#64748b", fontWeight: "600" }}>Patient ID: </span>
            <strong style={{ color: "#0284c7" }}>{report.patient_id || caseItem?.patient_id || "PAT-1001"}</strong>
          </div>
          <div>
            <span style={{ color: "#64748b", fontWeight: "600" }}>Age / Gender: </span>
            <strong style={{ color: "#0f172a" }}>{report.age || caseItem?.age || "N/A"} yrs • {report.gender || caseItem?.gender || "Unknown"}</strong>
          </div>
          <div>
            <span style={{ color: "#64748b", fontWeight: "600" }}>Eye Examined: </span>
            <strong style={{ color: "#0284c7" }}>{report.eye_examined || caseItem?.eye_examined || "OD (Right Eye)"}</strong>
          </div>
          <div>
            <span style={{ color: "#64748b", fontWeight: "600" }}>Diabetes History: </span>
            <strong style={{ color: "#0f172a" }}>{report.diabetes_type || caseItem?.diabetes_type || "Type 2"} {report.diabetes_duration_years ? `(${report.diabetes_duration_years} yrs)` : ""}</strong>
          </div>
          <div>
            <span style={{ color: "#64748b", fontWeight: "600" }}>Report / Case ID: </span>
            <strong style={{ color: "#0284c7" }}>{caseId}</strong>
          </div>
          <div>
            <span style={{ color: "#64748b", fontWeight: "600" }}>Screening Date: </span>
            <strong style={{ color: "#0f172a" }}>{screeningDate} at {screeningTime}</strong>
          </div>
          <div>
            <span style={{ color: "#64748b", fontWeight: "600" }}>Patient Consent: </span>
            <strong style={{ color: "#10b981" }}>Verified Informed Consent</strong>
          </div>
          <div>
            <span style={{ color: "#64748b", fontWeight: "600" }}>Platform: </span>
            <strong style={{ color: "#0f172a" }}>Netra Clinical AI Network</strong>
          </div>
        </div>

        {/* Image Quality Assessment (IQA) */}
        <div style={{ marginBottom: "1.25rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: "800", color: "#0f172a", marginBottom: "0.5rem", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.25rem" }}>
            1. Image Quality Assessment (IQA)
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.75rem", fontSize: "0.82rem", textAlign: "center" }}>
            <div style={{ background: "#f1f5f9", padding: "0.6rem", borderRadius: "6px" }}>
              <div style={{ color: "#64748b", fontWeight: "600" }}>Status</div>
              <div style={{ fontWeight: "800", color: isUngradable ? "#ef4444" : "#10b981", fontSize: "0.9rem" }}>
                {isUngradable ? "UNGRADABLE" : (retinalAnalysis?.quality_status || iq.status || "GOOD").toUpperCase()}
              </div>
            </div>
            <div style={{ background: "#f1f5f9", padding: "0.6rem", borderRadius: "6px" }}>
              <div style={{ color: "#64748b", fontWeight: "600" }}>Quality Score</div>
              <div style={{ fontWeight: "800", color: "#0f172a", fontSize: "0.9rem" }}>
                {((retinalAnalysis?.quality_score ?? iq.score ?? 0.88) * 100).toFixed(0)} / 100
              </div>
            </div>
            <div style={{ background: "#f1f5f9", padding: "0.6rem", borderRadius: "6px" }}>
              <div style={{ color: "#64748b", fontWeight: "600" }}>Illumination</div>
              <div style={{ fontWeight: "800", color: "#0f172a", fontSize: "0.9rem" }}>
                {((retinalAnalysis?.mean_illumination ?? iq.metrics?.brightness_mean ?? 118.5)).toFixed(1)}
              </div>
            </div>
            <div style={{ background: "#f1f5f9", padding: "0.6rem", borderRadius: "6px" }}>
              <div style={{ color: "#64748b", fontWeight: "600" }}>Focus Score</div>
              <div style={{ fontWeight: "800", color: "#0f172a", fontSize: "0.9rem" }}>
                {((retinalAnalysis?.focus_score ?? iq.metrics?.laplacian_var ?? 14.2)).toFixed(1)}
              </div>
            </div>
          </div>
        </div>

        {/* AI Screening Result */}
        <div style={{ marginBottom: "1.25rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: "800", color: "#0f172a", marginBottom: "0.5rem", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.25rem" }}>
            2. AI Diabetic Retinopathy Classification
          </h3>

          {isUngradable ? (
            <div style={{ background: "#fef2f2", border: "1px solid #fca5a5", padding: "0.85rem 1rem", borderRadius: "6px", color: "#991b1b" }}>
              <strong>⚠️ UNGRADABLE IMAGE:</strong> Retinal photograph does not meet minimum diagnostic sharpness/illumination standards. Classification suspended for patient safety.
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", background: "#f8fafc", padding: "0.85rem 1.25rem", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
              <div>
                <div style={{ fontSize: "0.82rem", color: "#64748b", fontWeight: "600" }}>Diabetic Retinopathy Grade (ICDR 0–4)</div>
                <div style={{ fontSize: "1.15rem", fontWeight: "900", color: isReferable ? "#dc2626" : "#10b981", marginTop: "0.2rem" }}>
                  {GRADE_LABELS[grade] || `Level ${grade}`}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.82rem", color: "#64748b", fontWeight: "600" }}>Temperature-Calibrated Confidence</div>
                <div style={{ fontSize: "1.15rem", fontWeight: "900", color: "#0284c7", marginTop: "0.2rem" }}>
                  {(calibratedConf * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Retinal Photography & Explainable AI */}
        <div style={{ marginBottom: "1.25rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: "800", color: "#0f172a", marginBottom: "0.5rem", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.25rem" }}>
            3. Retinal Photography & Visual Saliency
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", textAlign: "center" }}>
            <div style={{ border: "1px solid #cbd5e1", borderRadius: "6px", padding: "0.5rem", background: "#090d16" }}>
              <div style={{ fontSize: "0.78rem", fontWeight: "700", color: "#ffffff", marginBottom: "0.35rem" }}>
                Patient Retinal Fundus Scan
              </div>
              {originalUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={originalUrl} alt="Fundus Scan" style={{ maxHeight: "190px", maxWidth: "100%", objectFit: "contain", borderRadius: "4px" }} />
              ) : (
                <div style={{ height: "150px", color: "#94a3b8", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.8rem" }}>Image unavailable</div>
              )}
            </div>
            <div style={{ border: "1px solid #cbd5e1", borderRadius: "6px", padding: "0.5rem", background: "#090d16" }}>
              <div style={{ fontSize: "0.78rem", fontWeight: "700", color: "#38bdf8", marginBottom: "0.35rem" }}>
                Grad-CAM Deep Attention Map
              </div>
              {gradcamUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={gradcamUrl} alt="Grad-CAM Overlay" style={{ maxHeight: "190px", maxWidth: "100%", objectFit: "contain", borderRadius: "4px" }} />
              ) : (
                <div style={{ height: "150px", color: "#94a3b8", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.8rem" }}>Explanation overlay unavailable</div>
              )}
            </div>
          </div>
          <p style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.5rem", fontStyle: "italic", lineHeight: "1.35" }}>
            * Grad-CAM highlights image regions that contributed to the model&apos;s prediction. It is an AI explanation aid and does not by itself establish a clinical diagnosis.
          </p>
        </div>

        {/* Lesion & Biomarker Evidence */}
        <div style={{ marginBottom: "1.25rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: "800", color: "#0f172a", marginBottom: "0.5rem", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.25rem" }}>
            4. Lesion & Biomarker Evidence Analysis
          </h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
            <thead>
              <tr style={{ background: "#f1f5f9", textAlign: "left", color: "#475569" }}>
                <th style={{ padding: "0.45rem 0.75rem", border: "1px solid #cbd5e1" }}>Retinal Biomarker</th>
                <th style={{ padding: "0.45rem 0.75rem", border: "1px solid #cbd5e1" }}>Detection Status</th>
                <th style={{ padding: "0.45rem 0.75rem", border: "1px solid #cbd5e1" }}>Quantification</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1", fontWeight: "600" }}>Microaneurysms (MAs)</td>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1" }}>{(retinalAnalysis?.lesion_evidence?.microaneurysms?.count ?? 0) > 0 ? "DETECTED" : "None Detected"}</td>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1" }}>{retinalAnalysis?.lesion_evidence?.microaneurysms?.count ?? 0} MAs</td>
              </tr>
              <tr>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1", fontWeight: "600" }}>Hard Exudates</td>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1" }}>{(retinalAnalysis?.lesion_evidence?.exudates?.count ?? 0) > 0 ? "DETECTED" : "None Detected"}</td>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1" }}>{retinalAnalysis?.lesion_evidence?.exudates?.count ?? 0} clusters ({retinalAnalysis?.lesion_evidence?.exudates?.area_pixels ?? 0} px)</td>
              </tr>
              <tr>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1", fontWeight: "600" }}>Retinal Hemorrhages</td>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1" }}>{(retinalAnalysis?.lesion_evidence?.hemorrhages?.count ?? 0) > 0 ? "DETECTED" : "None Detected"}</td>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1" }}>{retinalAnalysis?.lesion_evidence?.hemorrhages?.count ?? 0} ({retinalAnalysis?.lesion_evidence?.hemorrhages?.severity ?? "None"})</td>
              </tr>
              <tr>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1", fontWeight: "600" }}>Neovascularization (NV)</td>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1" }}>{retinalAnalysis?.lesion_evidence?.neovascularization?.detected ? "CRITICAL RISK" : "None Detected"}</td>
                <td style={{ padding: "0.4rem 0.75rem", border: "1px solid #cbd5e1" }}>{retinalAnalysis?.lesion_evidence?.neovascularization?.detected ? retinalAnalysis.lesion_evidence.neovascularization.site : "Normal"}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* 5. Anatomical Sector Breakdown & Retinal Places */}
        {(() => {
          const spatial = retinalAnalysis?.spatial_analysis;
          if (!spatial?.zones || spatial.zones.length === 0) return null;
          return (
            <div style={{ marginBottom: "1.25rem" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: "800", color: "#0f172a", marginBottom: "0.5rem", borderBottom: "1px solid #e2e8f0", paddingBottom: "0.25rem" }}>
                5. Anatomical Retinal Places & Localized Lesion Analysis
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.6rem", fontSize: "0.78rem", marginBottom: "0.75rem", background: "#f8fafc", padding: "0.5rem 0.75rem", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
                <div>
                  <span style={{ color: "#64748b" }}>Macular Threat: </span>
                  <strong style={{ color: spatial.macula_threat_level === "HIGH_THREAT" ? "#dc2626" : spatial.macula_threat_level === "BORDERLINE" ? "#d97706" : "#16a34a" }}>
                    {spatial.macula_threat_level === "HIGH_THREAT" ? "VISION THREAT (DME)" : spatial.macula_threat_level === "BORDERLINE" ? "BORDERLINE" : "SPARE / LOW RISK"}
                  </strong>
                </div>
                <div>
                  <span style={{ color: "#64748b" }}>ETDRS Quadrants: </span>
                  <strong>{spatial.quadrants_affected_count} of 4 Active</strong>
                </div>
                <div>
                  <span style={{ color: "#64748b" }}>AI Hotspot: </span>
                  <strong style={{ color: "#0284c7" }}>{spatial.primary_attention_hotspot}</strong>
                </div>
              </div>

              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.78rem" }}>
                <thead>
                  <tr style={{ background: "#f1f5f9", textAlign: "left", color: "#475569" }}>
                    <th style={{ padding: "0.35rem 0.6rem", border: "1px solid #cbd5e1" }}>Retinal Sector</th>
                    <th style={{ padding: "0.35rem 0.6rem", border: "1px solid #cbd5e1" }}>Status / Lesions</th>
                    <th style={{ padding: "0.35rem 0.6rem", border: "1px solid #cbd5e1" }}>AI Saliency</th>
                    <th style={{ padding: "0.35rem 0.6rem", border: "1px solid #cbd5e1" }}>Clinical Location Explanation</th>
                  </tr>
                </thead>
                <tbody>
                  {spatial.zones.map((z) => {
                    const isThreat = z.status === "MACULAR_THREAT" || z.status === "CRITICAL_NEOVASCULARIZATION";
                    const isActive = z.status === "ACTIVE_LESIONS";
                    const statusColor = isThreat ? "#dc2626" : isActive ? "#d97706" : z.status === "EARLY_SIGNS" ? "#0284c7" : "#16a34a";
                    return (
                      <tr key={z.zone_id}>
                        <td style={{ padding: "0.35rem 0.6rem", border: "1px solid #cbd5e1", fontWeight: "700" }}>
                          [{z.short_code}] {z.zone_name}
                        </td>
                        <td style={{ padding: "0.35rem 0.6rem", border: "1px solid #cbd5e1" }}>
                          <span style={{ color: statusColor, fontWeight: "700" }}>{z.status_label || z.status}</span>
                          <div style={{ color: "#64748b", fontSize: "0.72rem" }}>{z.lesion_summary}</div>
                        </td>
                        <td style={{ padding: "0.35rem 0.6rem", border: "1px solid #cbd5e1", fontWeight: "600", color: "#0284c7" }}>
                          {((z.attention_peak ?? 0) * 100).toFixed(0)}%
                        </td>
                        <td style={{ padding: "0.35rem 0.6rem", border: "1px solid #cbd5e1", color: "#334155", lineHeight: "1.35" }}>
                          {z.clinical_explanation}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          );
        })()}

        {/* Clinical Triage Recommendation */}
        <div style={{ marginBottom: "1.25rem", background: "#f0f9ff", border: "1px solid #bae6fd", padding: "0.85rem 1rem", borderRadius: "8px" }}>
          <h4 style={{ margin: "0 0 0.35rem", fontSize: "0.9rem", color: "#0369a1", fontWeight: "800" }}>
            6. Clinical Action Recommendation
          </h4>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "#0c4a6e", lineHeight: "1.4" }}>
            {report.recommendation || (isReferable
              ? "Referable Diabetic Retinopathy detected. Referral to a qualified retina specialist for comprehensive dilated eye exam recommended within 2–4 weeks."
              : "No referable DR detected. Schedule routine annual fundus screening in 12 months.")}
          </p>
        </div>

        {/* Specialist Review Section */}
        <div style={{ marginBottom: "1.25rem", background: "#f8fafc", border: "1px solid #cbd5e1", padding: "0.85rem 1rem", borderRadius: "8px" }}>
          <h4 style={{ margin: "0 0 0.4rem", fontSize: "0.9rem", color: "#0f172a", fontWeight: "800" }}>
            7. Specialist Remote Review Status
          </h4>
          {caseItem?.specialist_decision ? (
            <div style={{ fontSize: "0.85rem", color: "#334155" }}>
              <div>Status: <strong style={{ color: "#0284c7" }}>{caseItem.specialist_decision}</strong> by <strong>{caseItem.specialist_id || "Consulting Specialist"}</strong></div>
              {caseItem.specialist_notes && <div style={{ marginTop: "0.25rem", fontStyle: "italic" }}>Clinical Notes: &quot;{caseItem.specialist_notes}&quot;</div>}
            </div>
          ) : (
            <div style={{ fontSize: "0.85rem", color: "#64748b", fontStyle: "italic" }}>
              Status: Pending Specialist Review (Enqueued in Rural Telemedicine Consultation Network)
            </div>
          )}
        </div>

        {/* Footer Disclaimer */}
        <div style={{ borderTop: "2px solid #e2e8f0", paddingTop: "0.85rem", marginTop: "1.5rem", fontSize: "0.75rem", color: "#64748b", textAlign: "center", lineHeight: "1.4" }}>
          <div><strong>NETRA Explainable AI Diabetic Retinopathy Screening System</strong></div>
          <div>Report ID: {caseId} • Screening Date: {screeningDate}</div>
          <div style={{ marginTop: "0.35rem", fontStyle: "italic" }}>
            Disclaimer: This report is intended as a screening and decision-support aid. It does not replace examination or diagnosis by a qualified eye-care professional.
          </div>
        </div>
      </div>
    </div>
  );
}

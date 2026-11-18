"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import React, { Suspense, useEffect, useState } from "react";
import { Header } from "../../components/Header";
import { ResultCard } from "../../components/ResultCard";
import { UIModal } from "../../components/UIModal";
import { UploadZone } from "../../components/UploadZone";
import { checkBackendHealth, PatientIntakePayload, ScreeningReport, uploadAndAnalyzeImage } from "../../lib/api";
import { Language, translations } from "../../lib/translations";

function ScreeningContent() {
  const searchParams = useSearchParams();
  const caseId = searchParams.get("case_id");
  const isRecapture = searchParams.get("recapture") === "true";

  // Language state
  const [lang, setLang] = useState<Language>("en");

  // Patient Intake States
  const [patientId, setPatientId] = useState<string>("");
  const [patientName, setPatientName] = useState("");
  const [age, setAge] = useState<string>("");
  const [gender, setGender] = useState<string>("Male");
  const [diabetesType, setDiabetesType] = useState<string>("Type 2");
  const [diabetesDuration, setDiabetesDuration] = useState<string>("");
  const [eyeExamined, setEyeExamined] = useState<string>("OD");
  const [patientConsent, setPatientConsent] = useState<boolean>(true);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ScreeningReport | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [isClientOnline, setIsClientOnline] = useState<boolean>(true);
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [validationErrorMsg, setValidationErrorMsg] = useState("");

  useEffect(() => {
    // Generate initial Patient ID
    setPatientId(`PAT-${Math.random().toString(36).substring(2, 8).toUpperCase()}`);

    // Load initial language
    const savedLang = (localStorage.getItem("netra_lang") as Language) || "en";
    setLang(savedLang);

    const handleLangChange = (e: any) => {
      setLang(e.detail || "en");
    };
    window.addEventListener("netra_language_changed", handleLangChange);

    // Online check
    setIsClientOnline(typeof navigator !== "undefined" ? navigator.onLine : true);
    const handleOnline = () => setIsClientOnline(true);
    const handleOffline = () => setIsClientOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    let isMounted = true;
    const verifyHealth = async () => {
      const online = await checkBackendHealth();
      if (isMounted) {
        setBackendOnline(online);
      }
    };

    verifyHealth();
    const interval = setInterval(verifyHealth, 6000);

    return () => {
      isMounted = false;
      clearInterval(interval);
      window.removeEventListener("netra_language_changed", handleLangChange);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Global window drag & drop event handling
  useEffect(() => {
    const handleWindowDragOver = (e: DragEvent) => {
      e.preventDefault();
      if (e.dataTransfer) {
        e.dataTransfer.dropEffect = "copy";
      }
    };

    const handleWindowDrop = (e: DragEvent) => {
      e.preventDefault();
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        if (file.type.startsWith("image/") || /\.(jpe?g|png|bmp|webp)$/i.test(file.name)) {
          handleFileSelect(file);
        }
      }
    };

    window.addEventListener("dragover", handleWindowDragOver);
    window.addEventListener("drop", handleWindowDrop);
    return () => {
      window.removeEventListener("dragover", handleWindowDragOver);
      window.removeEventListener("drop", handleWindowDrop);
    };
  }, []);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setError(null);
    setReport(null);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setError(null);
    setReport(null);
  };

  const handleLoadSample = async (samplePath: string, filename: string) => {
    try {
      const res = await fetch(samplePath);
      const blob = await res.blob();
      const mimeType = filename.endsWith(".jpg") || filename.endsWith(".jpeg") ? "image/jpeg" : "image/png";
      const file = new File([blob], filename, { type: mimeType });
      handleFileSelect(file);
    } catch (err) {
      console.error("Failed to load sample image", err);
    }
  };

  const t = translations[lang] || translations.en;

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    if (!patientName.trim()) {
      setValidationErrorMsg(t.patientName + " is required.");
      setShowValidationModal(true);
      return;
    }

    if (!patientConsent) {
      setValidationErrorMsg(t.informedConsentRequired);
      setShowValidationModal(true);
      return;
    }

    if (!isClientOnline || backendOnline === false) {
      setError(t.offlineBanner);
      return;
    }

    setLoading(true);
    setError(null);
    setReport(null);

    const intake: PatientIntakePayload = {
      patient_id: patientId.trim() || undefined,
      patient_name: patientName.trim(),
      age: age ? parseInt(age, 10) : undefined,
      gender,
      diabetes_type: diabetesType,
      diabetes_duration_years: diabetesDuration ? parseFloat(diabetesDuration) : undefined,
      eye_examined: eyeExamined,
      patient_consent: patientConsent,
      case_id: caseId || undefined,
    };

    try {
      const resReport = await uploadAndAnalyzeImage(selectedFile, intake);
      setReport(resReport);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred during retinal screening analysis.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Header />
      <div className="container" style={{ maxWidth: "1100px", margin: "0 auto", padding: "1.5rem 1rem" }}>
        <div className="header" style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          <div className="badge" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.3rem 0.8rem", borderRadius: "20px", background: "rgba(2, 132, 199, 0.1)", color: "var(--primary)", fontWeight: "700", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
            <span className="badge-dot" style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--primary)" }} />
            {t.navScreening}
          </div>
          <h1 className="title" style={{ fontSize: "2rem", fontWeight: "800", color: "var(--text-main)", margin: "0.25rem 0" }}>
            {t.uploadFundusScan}
          </h1>
          <p className="subtitle" style={{ color: "var(--text-muted)", fontSize: "0.95rem", maxWidth: "650px", margin: "0 auto" }}>
            {t.tagline}
          </p>
        </div>

        {/* Offline / Connectivity Banner */}
        {(!isClientOnline || backendOnline === false) && (
          <div style={{
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.35)",
            borderRadius: "0.75rem",
            padding: "0.9rem 1.25rem",
            marginBottom: "1.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "1rem",
            flexWrap: "wrap",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <span style={{ fontSize: "1.2rem" }}>📡</span>
              <div>
                <strong style={{ color: "#ef4444", fontSize: "0.92rem" }}>
                  {!isClientOnline ? t.offline : "Backend Service Offline"}
                </strong>
                <p style={{ margin: "0.15rem 0 0", fontSize: "0.85rem", color: "var(--text-main)" }}>
                  {t.offlineBanner}
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                setIsClientOnline(navigator.onLine);
                checkBackendHealth().then((online) => setBackendOnline(online));
              }}
              style={{
                background: "#ef4444",
                color: "#ffffff",
                border: "none",
                padding: "0.45rem 0.9rem",
                borderRadius: "6px",
                fontSize: "0.82rem",
                fontWeight: "700",
                cursor: "pointer",
              }}
            >
              {t.retryUpload}
            </button>
          </div>
        )}

        {/* Recapture Mode Alert Banner */}
        {isRecapture && caseId && (
          <div style={{
            background: "rgba(239, 68, 68, 0.08)",
            border: "1px solid rgba(239, 68, 68, 0.35)",
            borderRadius: "0.75rem",
            padding: "1rem 1.25rem",
            marginBottom: "1.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "1rem",
            flexWrap: "wrap",
          }}>
            <div>
              <div style={{ fontWeight: "800", color: "#ef4444", fontSize: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                📷 {t.requestRecapture}: {caseId}
              </div>
              <p style={{ margin: "0.25rem 0 0", fontSize: "0.88rem", color: "var(--text-main)" }}>
                The consulting ophthalmologist requested a replacement retinal scan with improved focus and lighting.
              </p>
            </div>
            <Link
              href="/doctor"
              style={{
                background: "var(--primary-subtle)",
                color: "var(--primary)",
                border: "1px solid var(--primary-glow)",
                padding: "0.45rem 0.9rem",
                borderRadius: "6px",
                fontSize: "0.85rem",
                fontWeight: "700",
                textDecoration: "none",
              }}
            >
              ← Doctor Portal
            </Link>
          </div>
        )}

        {/* Patient Demographics & Intake Card */}
        <div className="card" style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-card)",
          borderRadius: "0.75rem",
          padding: "1.25rem 1.5rem",
          marginBottom: "1.5rem",
          boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem", borderBottom: "1px solid var(--border-card)", paddingBottom: "0.5rem" }}>
            <span style={{ fontSize: "1.2rem" }}>👤</span>
            <h3 style={{ fontSize: "1.05rem", fontWeight: "800", color: "var(--text-main)", margin: 0 }}>
              {t.patientDetailsTitle}
            </h3>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
            {/* Patient ID */}
            <div>
              <label htmlFor="patient-id-input" style={{ display: "block", fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                {t.patientId}
              </label>
              <input
                id="patient-id-input"
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder="PAT-1001"
                style={{
                  width: "100%",
                  padding: "0.55rem 0.8rem",
                  borderRadius: "6px",
                  border: "1px solid var(--border-card)",
                  background: "var(--bg-card-subtle)",
                  color: "var(--text-main)",
                  fontSize: "0.88rem",
                }}
              />
            </div>

            {/* Patient Name */}
            <div>
              <label htmlFor="patient-name-input" style={{ display: "block", fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                {t.patientName} <span style={{ color: "#ef4444" }}>*</span>
              </label>
              <input
                id="patient-name-input"
                type="text"
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
                placeholder="e.g. Ramesh Kumar"
                style={{
                  width: "100%",
                  padding: "0.55rem 0.8rem",
                  borderRadius: "6px",
                  border: "1px solid var(--border-card)",
                  background: "var(--bg-card-subtle)",
                  color: "var(--text-main)",
                  fontSize: "0.88rem",
                }}
              />
            </div>

            {/* Age */}
            <div>
              <label htmlFor="patient-age-input" style={{ display: "block", fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                {t.age}
              </label>
              <input
                id="patient-age-input"
                type="number"
                min="1"
                max="120"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="e.g. 54"
                style={{
                  width: "100%",
                  padding: "0.55rem 0.8rem",
                  borderRadius: "6px",
                  border: "1px solid var(--border-card)",
                  background: "var(--bg-card-subtle)",
                  color: "var(--text-main)",
                  fontSize: "0.88rem",
                }}
              />
            </div>

            {/* Gender */}
            <div>
              <label htmlFor="patient-gender-select" style={{ display: "block", fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                {t.gender}
              </label>
              <select
                id="patient-gender-select"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.55rem 0.8rem",
                  borderRadius: "6px",
                  border: "1px solid var(--border-card)",
                  background: "var(--bg-card-subtle)",
                  color: "var(--text-main)",
                  fontSize: "0.88rem",
                }}
              >
                <option value="Male">{t.male}</option>
                <option value="Female">{t.female}</option>
                <option value="Other">{t.other}</option>
              </select>
            </div>

            {/* Diabetes Classification */}
            <div>
              <label htmlFor="patient-diabetes-type" style={{ display: "block", fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                {t.diabetesType}
              </label>
              <select
                id="patient-diabetes-type"
                value={diabetesType}
                onChange={(e) => setDiabetesType(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.55rem 0.8rem",
                  borderRadius: "6px",
                  border: "1px solid var(--border-card)",
                  background: "var(--bg-card-subtle)",
                  color: "var(--text-main)",
                  fontSize: "0.88rem",
                }}
              >
                <option value="Type 2">{t.type2}</option>
                <option value="Type 1">{t.type1}</option>
                <option value="Gestational">{t.gestational}</option>
                <option value="None">{t.none}</option>
              </select>
            </div>

            {/* Duration of Diabetes */}
            <div>
              <label htmlFor="patient-duration-input" style={{ display: "block", fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                {t.diabetesDuration}
              </label>
              <input
                id="patient-duration-input"
                type="number"
                step="0.5"
                min="0"
                value={diabetesDuration}
                onChange={(e) => setDiabetesDuration(e.target.value)}
                placeholder="e.g. 8.5"
                style={{
                  width: "100%",
                  padding: "0.55rem 0.8rem",
                  borderRadius: "6px",
                  border: "1px solid var(--border-card)",
                  background: "var(--bg-card-subtle)",
                  color: "var(--text-main)",
                  fontSize: "0.88rem",
                }}
              />
            </div>

            {/* Eye Examined */}
            <div>
              <label htmlFor="patient-eye-select" style={{ display: "block", fontSize: "0.82rem", fontWeight: "700", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                {t.eyeExamined}
              </label>
              <select
                id="patient-eye-select"
                value={eyeExamined}
                onChange={(e) => setEyeExamined(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.55rem 0.8rem",
                  borderRadius: "6px",
                  border: "1px solid var(--border-card)",
                  background: "var(--bg-card-subtle)",
                  color: "var(--text-main)",
                  fontSize: "0.88rem",
                  fontWeight: "700",
                }}
              >
                <option value="OD">{t.rightEyeOD}</option>
                <option value="OS">{t.leftEyeOS}</option>
              </select>
            </div>
          </div>

          {/* Informed Consent Toggle */}
          <div style={{ marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px dashed var(--border-card)" }}>
            <label style={{ display: "flex", alignItems: "flex-start", gap: "0.6rem", cursor: "pointer", fontSize: "0.88rem", color: "var(--text-main)" }}>
              <input
                type="checkbox"
                checked={patientConsent}
                onChange={(e) => setPatientConsent(e.target.checked)}
                style={{ width: "17px", height: "17px", marginTop: "2px", accentColor: "var(--primary)" }}
              />
              <span>
                <strong>{t.informedConsentLabel}</strong>
                <span style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                  Verified compliance with clinical data privacy protocols. No personally identifiable medical data is shared externally.
                </span>
              </span>
            </label>
          </div>
        </div>

        {/* Upload Zone Card */}
        <div className="card" style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-card)",
          borderRadius: "0.75rem",
          padding: "1.5rem",
          marginBottom: "1.5rem",
        }}>
          <UploadZone
            selectedFile={selectedFile}
            onFileSelect={handleFileSelect}
            onClear={handleClear}
            loading={loading}
          />

          {/* Sample Fundus Image Preload Shortcuts */}
          <div style={{ marginTop: "1.25rem", padding: "0.85rem 1rem", background: "var(--bg-card-subtle)", borderRadius: "8px", border: "1px solid var(--border-card)" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
              <span style={{ fontSize: "0.82rem", color: "var(--text-main)", fontWeight: "700" }}>
                🧪 Quick Test Samples (Click to load & test):
              </span>
              <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                Also available in <code>sample_test_images/</code> folder
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
              <button
                type="button"
                onClick={() => handleLoadSample("/sample_images/01_Real_Patient_Grade0_No_DR.png", "01_Real_Patient_Grade0_No_DR.png")}
                style={{
                  background: "rgba(16, 185, 129, 0.12)",
                  color: "#059669",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  padding: "0.3rem 0.65rem",
                  borderRadius: "6px",
                  fontSize: "0.76rem",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                🟢 Real Patient: Grade 0 (No DR)
              </button>
              <button
                type="button"
                onClick={() => handleLoadSample("/sample_images/02_Real_Patient_Grade1_Mild_NPDR.png", "02_Real_Patient_Grade1_Mild_NPDR.png")}
                style={{
                  background: "rgba(2, 132, 199, 0.12)",
                  color: "#0284c7",
                  border: "1px solid rgba(2, 132, 199, 0.3)",
                  padding: "0.3rem 0.65rem",
                  borderRadius: "6px",
                  fontSize: "0.76rem",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                🔵 Real Patient: Grade 1 (Mild)
              </button>
              <button
                type="button"
                onClick={() => handleLoadSample("/sample_images/03_Real_Patient_Grade2_Moderate_NPDR.png", "03_Real_Patient_Grade2_Moderate_NPDR.png")}
                style={{
                  background: "rgba(217, 119, 6, 0.12)",
                  color: "#d97706",
                  border: "1px solid rgba(217, 119, 6, 0.3)",
                  padding: "0.3rem 0.65rem",
                  borderRadius: "6px",
                  fontSize: "0.76rem",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                🟠 Real Patient: Grade 2 (Moderate)
              </button>
              <button
                type="button"
                onClick={() => handleLoadSample("/sample_images/04_Real_Patient_Grade3_Severe_NPDR.png", "04_Real_Patient_Grade3_Severe_NPDR.png")}
                style={{
                  background: "rgba(234, 88, 12, 0.12)",
                  color: "#ea580c",
                  border: "1px solid rgba(234, 88, 12, 0.3)",
                  padding: "0.3rem 0.65rem",
                  borderRadius: "6px",
                  fontSize: "0.76rem",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                🔴 Real Patient: Grade 3 (Severe)
              </button>
              <button
                type="button"
                onClick={() => handleLoadSample("/sample_images/05_Real_Patient_Grade4_Proliferative_PDR.png", "05_Real_Patient_Grade4_Proliferative_PDR.png")}
                style={{
                  background: "rgba(220, 38, 38, 0.12)",
                  color: "#dc2626",
                  border: "1px solid rgba(220, 38, 38, 0.3)",
                  padding: "0.3rem 0.65rem",
                  borderRadius: "6px",
                  fontSize: "0.76rem",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                🚨 Real Patient: Grade 4 (PDR)
              </button>
              <button
                type="button"
                onClick={() => handleLoadSample("/sample_images/06_Real_Hospital_Camera_Healthy_Eye.jpg", "06_Real_Hospital_Camera_Healthy_Eye.jpg")}
                style={{
                  background: "rgba(13, 148, 136, 0.12)",
                  color: "#0d9488",
                  border: "1px solid rgba(13, 148, 136, 0.3)",
                  padding: "0.3rem 0.65rem",
                  borderRadius: "6px",
                  fontSize: "0.76rem",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                📸 2880px Real Camera: Healthy
              </button>
              <button
                type="button"
                onClick={() => handleLoadSample("/sample_images/07_Real_Hospital_Camera_Moderate_DR.jpg", "07_Real_Hospital_Camera_Moderate_DR.jpg")}
                style={{
                  background: "rgba(217, 119, 6, 0.12)",
                  color: "#d97706",
                  border: "1px solid rgba(217, 119, 6, 0.3)",
                  padding: "0.3rem 0.65rem",
                  borderRadius: "6px",
                  fontSize: "0.76rem",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                📸 2880px Real Camera: Moderate DR
              </button>
              <button
                type="button"
                onClick={() => handleLoadSample("/sample_images/09_Real_Hospital_Camera_Proliferative_DR.jpg", "09_Real_Hospital_Camera_Proliferative_DR.jpg")}
                style={{
                  background: "rgba(220, 38, 38, 0.12)",
                  color: "#dc2626",
                  border: "1px solid rgba(220, 38, 38, 0.3)",
                  padding: "0.3rem 0.65rem",
                  borderRadius: "6px",
                  fontSize: "0.76rem",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                📸 2880px Real Camera: PDR
              </button>
              <button
                type="button"
                onClick={() => handleLoadSample("/sample_images/10_Quality_Rejection_Severe_Defocus.jpg", "10_Quality_Rejection_Severe_Defocus.jpg")}
                style={{
                  background: "rgba(100, 116, 139, 0.12)",
                  color: "#475569",
                  border: "1px solid rgba(100, 116, 139, 0.3)",
                  padding: "0.3rem 0.65rem",
                  borderRadius: "6px",
                  fontSize: "0.76rem",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                🌫️ IQA Rejection Test (Blur)
              </button>
            </div>
          </div>

          {/* Analyze Action Button */}
          <div style={{ marginTop: "1.25rem", display: "flex", justifyContent: "flex-end", gap: "0.75rem" }}>
            {selectedFile && (
              <button
                type="button"
                onClick={handleClear}
                disabled={loading}
                style={{
                  background: "transparent",
                  color: "var(--text-muted)",
                  border: "1px solid var(--border-card)",
                  padding: "0.6rem 1.2rem",
                  borderRadius: "6px",
                  fontSize: "0.9rem",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                Clear
              </button>
            )}
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={!selectedFile || loading}
              style={{
                background: selectedFile && !loading ? "var(--primary)" : "var(--border-card)",
                color: "#ffffff",
                border: "none",
                padding: "0.65rem 1.5rem",
                borderRadius: "6px",
                fontSize: "0.95rem",
                fontWeight: "700",
                cursor: selectedFile && !loading ? "pointer" : "not-allowed",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                boxShadow: selectedFile && !loading ? "0 2px 10px rgba(2, 132, 199, 0.3)" : "none",
              }}
            >
              {loading ? (
                <>
                  <span className="spinner" style={{ width: "16px", height: "16px", border: "2px solid #ffffff", borderTopColor: "transparent", borderRadius: "50%", display: "inline-block", animation: "spin 0.8s linear infinite" }} />
                  <span>{t.screeningInProgress}</span>
                </>
              ) : (
                <span>{t.startScreening} →</span>
              )}
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div style={{
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "0.5rem",
            padding: "1rem",
            color: "#ef4444",
            fontSize: "0.9rem",
            marginBottom: "1.5rem",
          }}>
            <strong>Analysis Warning:</strong> {error}
          </div>
        )}

        {/* Results Section */}
        {report && (
          <div style={{ marginTop: "1.5rem" }}>
            <ResultCard report={report} originalFile={selectedFile} />
          </div>
        )}

        {/* Clinical Disclaimer Footer */}
        <div style={{
          marginTop: "2.5rem",
          padding: "1rem",
          textAlign: "center",
          fontSize: "0.8rem",
          color: "var(--text-muted)",
          borderTop: "1px solid var(--border-card)",
        }}>
          <p style={{ margin: 0 }}>
            ⚕️ <em>{t.clinicalDisclaimer}</em>
          </p>
        </div>
      </div>

      {/* Validation Alert Modal */}
      <UIModal
        isOpen={showValidationModal}
        type="warning"
        title="Required Information Missing"
        message={validationErrorMsg || t.patientName + " is required to proceed with diagnostic screening."}
        confirmText="Understood"
        onConfirm={() => setShowValidationModal(false)}
      />
    </>
  );
}

export default function ScreeningPage() {
  return (
    <Suspense fallback={<div style={{ padding: "2rem", textAlign: "center" }}>Loading Screening Portal...</div>}>
      <ScreeningContent />
    </Suspense>
  );
}

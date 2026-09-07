"use client";

import React, { useEffect, useState } from "react";
import { Header } from "../../components/Header";
import { ResultCard } from "../../components/ResultCard";
import { UploadZone } from "../../components/UploadZone";
import { checkBackendHealth, ScreeningReport, uploadAndAnalyzeImage } from "../../lib/api";

export default function ScreeningPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ScreeningReport | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    checkBackendHealth().then((online) => setBackendOnline(online));
  }, []);

  // Global window drag & drop event handling: prevents browser from navigating away and catches dropped files anywhere
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
      const file = new File([blob], filename, { type: "image/png" });
      handleFileSelect(file);
    } catch (err) {
      console.error("Failed to load sample image", err);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const resReport = await uploadAndAnalyzeImage(selectedFile);
      setReport(resReport);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred during image screening analysis.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Header />
      <div className="container">
        <div className="header">
          <div className="badge">
            <span className="badge-dot" />
            Screening Portal
          </div>
          <h1 className="title">Fundus Image Analysis</h1>
          <p className="subtitle">
            Automated Image Quality Assessment, Explainable DR Grading, Temperature-Calibrated Confidence, and Visual Saliency Maps.
          </p>
        </div>

        {/* Backend Connectivity Status */}
        <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          {backendOnline === true && (
            <span style={{ fontSize: "0.85rem", color: "#10b981", background: "rgba(16, 185, 129, 0.1)", padding: "0.4rem 0.9rem", borderRadius: "20px", border: "1px solid rgba(16, 185, 129, 0.3)" }}>
              ● FastAPI Backend Online (http://localhost:8000)
            </span>
          )}
          {backendOnline === false && (
            <span style={{ fontSize: "0.85rem", color: "#ef4444", background: "rgba(239, 68, 68, 0.1)", padding: "0.4rem 0.9rem", borderRadius: "20px", border: "1px solid rgba(239, 68, 68, 0.3)" }}>
              ⚠️ FastAPI Backend Offline or Unreachable
            </span>
          )}
        </div>

        {/* Upload Card */}
        <div className="card" style={{ marginBottom: "2rem" }}>
          <UploadZone
            onFileSelect={handleFileSelect}
            selectedFile={selectedFile}
            onClear={handleClear}
          />

          {!selectedFile && (
            <div style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.75rem",
              marginTop: "1.25rem",
              flexWrap: "wrap"
            }}>
              <span style={{ fontSize: "0.85rem", color: "var(--text-subtle)" }}>Quick Demo:</span>
              <button
                type="button"
                onClick={() => handleLoadSample("/samples/sample_fundus.png", "sample_fundus_retina.png")}
                style={{
                  background: "var(--primary-subtle)",
                  color: "var(--primary)",
                  border: "1px solid var(--primary-glow)",
                  padding: "0.4rem 0.9rem",
                  borderRadius: "6px",
                  fontSize: "0.85rem",
                  fontWeight: "600",
                  cursor: "pointer",
                  transition: "all 0.2s ease"
                }}
              >
                🧪 Try Fundus Sample 1
              </button>
              <button
                type="button"
                onClick={() => handleLoadSample("/samples/sample_normal.png", "sample_fundus_normal.png")}
                style={{
                  background: "rgba(5, 150, 105, 0.08)",
                  color: "var(--accent-teal)",
                  border: "1px solid rgba(5, 150, 105, 0.25)",
                  padding: "0.4rem 0.9rem",
                  borderRadius: "6px",
                  fontSize: "0.85rem",
                  fontWeight: "600",
                  cursor: "pointer",
                  transition: "all 0.2s ease"
                }}
              >
                🧪 Try Fundus Sample 2
              </button>
            </div>
          )}

          {selectedFile && !loading && !report && (
            <div style={{ textAlign: "center", marginTop: "1.5rem" }}>
              <button
                onClick={handleAnalyze}
                type="button"
                style={{
                  background: "linear-gradient(135deg, var(--primary), var(--accent-teal))",
                  color: "#ffffff",
                  border: "none",
                  padding: "0.85rem 2.5rem",
                  borderRadius: "10px",
                  fontWeight: "800",
                  fontSize: "1.05rem",
                  cursor: "pointer",
                  boxShadow: "0 4px 20px var(--primary-glow)",
                  transition: "all 0.3s ease"
                }}
              >
                Analyze Fundus Image
              </button>
            </div>
          )}
        </div>

        {/* Loading Spinner State */}
        {loading && (
          <div className="card" style={{ textAlign: "center", padding: "3.5rem 2rem", marginBottom: "2rem" }}>
            <div style={{
              width: "50px",
              height: "50px",
              border: "4px solid var(--primary-glow)",
              borderTopColor: "var(--primary)",
              borderRadius: "50%",
              margin: "0 auto 1.5rem",
              animation: "spin 1s linear infinite"
            }} />
            <style jsx>{`
              @keyframes spin {
                to { transform: rotate(360deg); }
              }
            `}</style>
            <h3 style={{ color: "var(--text-main)", fontSize: "1.2rem", fontWeight: "700", marginBottom: "0.5rem" }}>
              Executing AI Screening Pipeline...
            </h3>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
              Evaluating Image Quality (IQA) → Inferring DR Class → Calibrating Confidence → Generating Grad-CAM Heatmap
            </p>
          </div>
        )}

        {/* Error Alert State */}
        {error && (
          <div style={{
            background: "rgba(239, 68, 68, 0.08)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "1rem",
            padding: "1.5rem",
            color: "#ef4444",
            marginBottom: "2rem"
          }}>
            <h3 style={{ fontWeight: "700", fontSize: "1.1rem", marginBottom: "0.4rem" }}>Analysis Error</h3>
            <p style={{ color: "var(--text-main)", fontSize: "0.95rem" }}>{error}</p>
          </div>
        )}

        {/* Report Output Card */}
        {report && <ResultCard report={report} originalFile={selectedFile} />}
      </div>
    </>
  );
}

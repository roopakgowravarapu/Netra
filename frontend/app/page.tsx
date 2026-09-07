"use client";

import Link from "next/link";
import { Header } from "../components/Header";

export default function HomePage() {
  return (
    <>
      <Header />
      <main className="container">
        <div className="header">
          <div className="badge">
            <span className="badge-dot" />
            Smart India Hackathon 2026
          </div>
          <h1 className="title">NETRA</h1>
          <p className="subtitle">
            Explainable AI Screening Platform for Diabetic Retinopathy Detection in Rural & Resource-Constrained Healthcare Settings.
          </p>

          <div style={{ marginTop: "2rem", display: "flex", justifyContent: "center", gap: "1rem", flexWrap: "wrap" }}>
            <Link
              href="/screening"
              style={{
                background: "linear-gradient(135deg, var(--primary), var(--accent-teal))",
                color: "#ffffff",
                padding: "0.85rem 2rem",
                borderRadius: "10px",
                fontWeight: "800",
                fontSize: "1.05rem",
                textDecoration: "none",
                boxShadow: "0 4px 20px var(--primary-glow)",
                transition: "all 0.3s ease"
              }}
            >
              Launch Screening Portal →
            </Link>
            <Link
              href="/dashboard"
              style={{
                background: "var(--bg-card)",
                color: "var(--text-main)",
                border: "1px solid var(--border-card)",
                padding: "0.85rem 2rem",
                borderRadius: "10px",
                fontWeight: "600",
                fontSize: "1.05rem",
                textDecoration: "none",
                boxShadow: "var(--card-shadow)",
                transition: "all 0.3s ease"
              }}
            >
              Telemedicine Dashboard
            </Link>
          </div>
        </div>

        {/* System Architecture Section */}
        <div className="card" style={{ marginBottom: "2.5rem" }}>
          <h2 style={{ fontSize: "1.5rem", fontWeight: "700", marginBottom: "1.25rem", color: "var(--text-main)", textAlign: "center" }}>
            End-to-End AI Pipeline Architecture
          </h2>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "1rem",
            textIndent: 0
          }}>
            {[
              { step: "1", title: "Image Upload", desc: "Fundus image capture & validation" },
              { step: "2", title: "Quality Check (IQA)", desc: "Blur, brightness, FOV evaluation" },
              { step: "3", title: "DR Classifier", desc: "EfficientNet-B0 5-class grading" },
              { step: "4", title: "Confidence Calibration", desc: "Temperature-scaled probabilities" },
              { step: "5", title: "Grad-CAM Saliency", desc: "Model interpretability heatmaps" },
              { step: "6", title: "Screening Report", desc: "Actionable referral generation" },
            ].map((item) => (
              <div key={item.step} style={{
                background: "var(--bg-card-subtle)",
                border: "1px solid var(--border-card)",
                borderRadius: "0.75rem",
                padding: "1.25rem",
                textAlign: "center"
              }}>
                <div style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "50%",
                  background: "var(--primary-subtle)",
                  color: "var(--primary)",
                  fontWeight: "800",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 0.75rem"
                }}>
                  {item.step}
                </div>
                <h3 style={{ fontSize: "0.95rem", fontWeight: "700", color: "var(--text-main)", marginBottom: "0.25rem" }}>
                  {item.title}
                </h3>
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: "1.4" }}>
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className="info-grid">
          <div className="info-card">
            <span className="info-icon">🔍</span>
            <div className="info-text">
              <h4>Image Quality Safeguard</h4>
              <p>Detects blur, dark/overexposed frames, and obscured FOVs to prevent invalid clinical recommendations.</p>
            </div>
          </div>
          <div className="info-card">
            <span className="info-icon">🎯</span>
            <div className="info-text">
              <h4>Temperature Calibration</h4>
              <p>Aligns neural network output probabilities with empirical clinical precision to quantify uncertainty.</p>
            </div>
          </div>
          <div className="info-card">
            <span className="info-icon">🧠</span>
            <div className="info-text">
              <h4>Visual Explainability</h4>
              <p>Grad-CAM heatmaps highlight focal optic disk and lesion regions for complete model transparency.</p>
            </div>
          </div>
        </div>
      </main>

      <footer>
        <p>© 2026 Netra AI Platform • Smart India Hackathon • For AI-Assisted Clinical Screening Support</p>
      </footer>
    </>
  );
}

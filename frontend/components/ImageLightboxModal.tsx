"use client";

import React, { useState } from "react";

interface ImageLightboxModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  originalUrl?: string | null;
  gradcamUrl?: string | null;
}

export function ImageLightboxModal({ isOpen, onClose, title, originalUrl, gradcamUrl }: ImageLightboxModalProps) {
  const [activeView, setActiveView] = useState<"side-by-side" | "original" | "gradcam">("side-by-side");
  const [zoom, setZoom] = useState(1);

  if (!isOpen) return null;

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: "rgba(9, 13, 22, 0.92)",
      backdropFilter: "blur(10px)",
      zIndex: 10005,
      display: "flex",
      flexDirection: "column",
      padding: "1.5rem"
    }}>
      {/* Top Toolbar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1.2rem", fontWeight: "800", color: "#ffffff" }}>
            🔍 Image Inspector & Saliency Viewer
          </h3>
          <div style={{ fontSize: "0.85rem", color: "#94a3b8", marginTop: "0.25rem" }}>
            {title}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {/* View Toggles */}
          <div style={{ display: "flex", gap: "0.25rem", background: "#1e293b", padding: "0.25rem", borderRadius: "8px" }}>
            <button
              onClick={() => setActiveView("side-by-side")}
              style={{
                background: activeView === "side-by-side" ? "#0284c7" : "transparent",
                color: "#ffffff",
                border: "none",
                padding: "0.4rem 0.8rem",
                borderRadius: "6px",
                fontSize: "0.8rem",
                fontWeight: "700",
                cursor: "pointer"
              }}
            >
              Side-by-Side
            </button>
            <button
              onClick={() => setActiveView("original")}
              style={{
                background: activeView === "original" ? "#0284c7" : "transparent",
                color: "#ffffff",
                border: "none",
                padding: "0.4rem 0.8rem",
                borderRadius: "6px",
                fontSize: "0.8rem",
                fontWeight: "700",
                cursor: "pointer"
              }}
            >
              Original Scan
            </button>
            <button
              onClick={() => setActiveView("gradcam")}
              style={{
                background: activeView === "gradcam" ? "#0284c7" : "transparent",
                color: "#ffffff",
                border: "none",
                padding: "0.4rem 0.8rem",
                borderRadius: "6px",
                fontSize: "0.8rem",
                fontWeight: "700",
                cursor: "pointer"
              }}
            >
              Grad-CAM
            </button>
          </div>

          {/* Zoom controls */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", background: "#1e293b", padding: "0.25rem 0.6rem", borderRadius: "8px" }}>
            <button
              onClick={() => setZoom((z) => Math.max(0.8, z - 0.2))}
              style={{ background: "transparent", border: "none", color: "#ffffff", fontWeight: "800", cursor: "pointer", fontSize: "1.1rem" }}
            >
              -
            </button>
            <span style={{ fontSize: "0.8rem", color: "#cbd5e1", fontWeight: "700", minWidth: "45px", textAlign: "center" }}>
              {(zoom * 100).toFixed(0)}%
            </span>
            <button
              onClick={() => setZoom((z) => Math.min(2.5, z + 0.2))}
              style={{ background: "transparent", border: "none", color: "#ffffff", fontWeight: "800", cursor: "pointer", fontSize: "1.1rem" }}
            >
              +
            </button>
            <button
              onClick={() => setZoom(1)}
              style={{ background: "#334155", border: "none", color: "#ffffff", fontSize: "0.75rem", padding: "0.25rem 0.5rem", borderRadius: "4px", cursor: "pointer" }}
            >
              Reset
            </button>
          </div>

          <button
            onClick={onClose}
            style={{
              background: "#ef4444",
              color: "#ffffff",
              border: "none",
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              fontWeight: "800",
              cursor: "pointer",
              fontSize: "0.9rem"
            }}
          >
            ✕ Close
          </button>
        </div>
      </div>

      {/* Main Lightbox Display Area */}
      <div style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "auto",
        background: "#090d16",
        borderRadius: "12px",
        border: "1px solid #1e293b",
        padding: "1.5rem"
      }}>
        <div style={{
          display: "grid",
          gridTemplateColumns: activeView === "side-by-side" ? "1fr 1fr" : "1fr",
          gap: "1.5rem",
          maxWidth: "100%",
          maxHeight: "100%",
          transform: `scale(${zoom})`,
          transition: "transform 0.2s ease",
          transformOrigin: "center center"
        }}>
          {(activeView === "side-by-side" || activeView === "original") && (
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "0.85rem", color: "#94a3b8", fontWeight: "700", marginBottom: "0.5rem" }}>
                Patient Retinal Scan (Original)
              </div>
              {originalUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={originalUrl}
                  alt="Original Retinal Scan"
                  style={{ maxHeight: "70vh", maxWidth: "100%", objectFit: "contain", borderRadius: "8px" }}
                />
              ) : (
                <div style={{ color: "#64748b", padding: "4rem" }}>Original scan unavailable</div>
              )}
            </div>
          )}

          {(activeView === "side-by-side" || activeView === "gradcam") && (
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "0.85rem", color: "#38bdf8", fontWeight: "700", marginBottom: "0.5rem" }}>
                AI Grad-CAM Saliency Overlay
              </div>
              {gradcamUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={gradcamUrl}
                  alt="Grad-CAM Saliency Overlay"
                  style={{ maxHeight: "70vh", maxWidth: "100%", objectFit: "contain", borderRadius: "8px" }}
                />
              ) : (
                <div style={{ color: "#64748b", padding: "4rem" }}>Grad-CAM heatmap unavailable</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

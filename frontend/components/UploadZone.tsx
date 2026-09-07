"use client";

import React, { useRef, useState, useEffect } from "react";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onClear: () => void;
}

export function UploadZone({ onFileSelect, selectedFile, onClear }: UploadZoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const dragCounter = useRef(0);

  useEffect(() => {
    if (selectedFile) {
      const url = URL.createObjectURL(selectedFile);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewUrl(null);
    }
  }, [selectedFile]);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current += 1;
    if (e.dataTransfer && e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragOver(true);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = "copy";
    }
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current -= 1;
    if (dragCounter.current <= 0) {
      dragCounter.current = 0;
      setIsDragOver(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current = 0;
    setIsDragOver(false);

    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith("image/") || /\.(jpe?g|png|bmp|webp)$/i.test(file.name)) {
        onFileSelect(file);
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
    // Reset value so same file re-selection fires onChange
    e.target.value = "";
  };

  if (selectedFile && previewUrl) {
    return (
      <div style={{
        background: "var(--bg-card-subtle)",
        border: "1px solid var(--border-card)",
        borderRadius: "1rem",
        padding: "1.5rem",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "1.25rem",
        boxShadow: "var(--card-shadow)"
      }}>
        <div style={{
          position: "relative",
          width: "100%",
          maxHeight: "320px",
          display: "flex",
          justifyContent: "center",
          overflow: "hidden",
          borderRadius: "0.75rem",
          background: "#090d16"
        }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt="Fundus Preview"
            style={{ maxHeight: "320px", objectFit: "contain", borderRadius: "0.75rem" }}
          />
        </div>

        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          background: "var(--bg-card)",
          padding: "0.75rem 1.25rem",
          borderRadius: "0.5rem",
          border: "1px solid var(--border-card)"
        }}>
          <div>
            <div style={{ fontWeight: "600", fontSize: "0.95rem", color: "var(--text-main)" }}>{selectedFile.name}</div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
            </div>
          </div>
          <button
            onClick={onClear}
            type="button"
            style={{
              background: "rgba(239, 68, 68, 0.12)",
              color: "#ef4444",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              padding: "0.4rem 0.9rem",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: "600",
              fontSize: "0.85rem"
            }}
          >
            Remove / Replace
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="upload-zone"
      style={{
        position: "relative",
        borderColor: isDragOver ? "var(--primary)" : "var(--border-card)",
        background: isDragOver ? "var(--primary-subtle)" : "var(--bg-card-subtle)",
        boxShadow: isDragOver ? "0 0 35px var(--primary-glow)" : "none",
        cursor: "pointer",
        transition: "all 0.2s ease"
      }}
    >
      {/* Invisible full-area native file input to receive native clicks and drops reliably */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/bmp,image/jpg,.jpg,.jpeg,.png,.bmp"
        onChange={handleChange}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          opacity: 0,
          cursor: "pointer",
          zIndex: 10
        }}
      />

      <div className="upload-icon-wrapper" style={{ pointerEvents: "none" }}>
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
      </div>

      <div style={{ pointerEvents: "none" }}>
        <div className="upload-title" style={{ fontSize: "1.3rem" }}>
          {isDragOver ? "Drop Retinal Image Now" : "Drag & Drop Retinal Image Here"}
        </div>
        <div className="upload-desc" style={{ marginTop: "0.5rem" }}>
          or click anywhere in this box to select a fundus photography image file.
        </div>
      </div>

      <div
        style={{
          background: "var(--primary-subtle)",
          color: "var(--primary)",
          border: "1px solid var(--primary-glow)",
          padding: "0.6rem 1.5rem",
          borderRadius: "8px",
          fontWeight: "700",
          fontSize: "0.95rem",
          marginTop: "0.5rem",
          pointerEvents: "none",
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem"
        }}
      >
        <span>📁</span> Browse Files
      </div>

      <div className="upload-meta" style={{ pointerEvents: "none" }}>
        Supported: JPEG, JPG, PNG, BMP (Max 15MB)
      </div>
    </div>
  );
}

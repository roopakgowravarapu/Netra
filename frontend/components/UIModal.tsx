"use client";

import React from "react";

export type ModalType = "success" | "error" | "warning" | "info" | "confirm";

export interface UIModalProps {
  isOpen: boolean;
  type?: ModalType;
  title: string;
  message: string | React.ReactNode;
  confirmText?: string;
  cancelText?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  confirmDanger?: boolean;
}

export function UIModal({
  isOpen,
  type = "info",
  title,
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
  confirmDanger = false,
}: UIModalProps) {
  if (!isOpen) return null;

  const isConfirm = type === "confirm" || onCancel !== undefined;

  const getBadgeColor = () => {
    switch (type) {
      case "success":
        return { bg: "rgba(16, 185, 129, 0.12)", color: "#10b981", border: "rgba(16, 185, 129, 0.3)", icon: "✓" };
      case "error":
        return { bg: "rgba(239, 68, 68, 0.12)", color: "#ef4444", border: "rgba(239, 68, 68, 0.3)", icon: "✕" };
      case "warning":
        return { bg: "rgba(245, 158, 11, 0.12)", color: "#f59e0b", border: "rgba(245, 158, 11, 0.3)", icon: "⚠️" };
      case "confirm":
        return confirmDanger
          ? { bg: "rgba(239, 68, 68, 0.12)", color: "#ef4444", border: "rgba(239, 68, 68, 0.3)", icon: "🗑️" }
          : { bg: "var(--primary-subtle, rgba(2, 132, 199, 0.12))", color: "var(--primary, #0284c7)", border: "var(--primary-glow, rgba(2, 132, 199, 0.3))", icon: "❓" };
      default:
        return { bg: "rgba(2, 132, 199, 0.12)", color: "#0284c7", border: "rgba(2, 132, 199, 0.3)", icon: "ℹ️" };
    }
  };

  const badge = getBadgeColor();

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(9, 13, 22, 0.75)",
        backdropFilter: "blur(6px)",
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
        animation: "fadeIn 0.2s ease-out",
      }}
    >
      <div
        style={{
          background: "var(--bg-card, #ffffff)",
          border: "1px solid var(--border-card, #e2e8f0)",
          borderRadius: "1.25rem",
          maxWidth: "480px",
          width: "100%",
          padding: "1.75rem",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          color: "var(--text-main, #0f172a)",
          display: "flex",
          flexDirection: "column",
          gap: "1.25rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", gap: "1rem" }}>
          <div
            style={{
              width: "42px",
              height: "42px",
              borderRadius: "50%",
              background: badge.bg,
              color: badge.color,
              border: `1px solid ${badge.border}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.25rem",
              fontWeight: "700",
              flexShrink: 0,
            }}
          >
            {badge.icon}
          </div>
          <div>
            <h3 style={{ fontSize: "1.2rem", fontWeight: "700", color: "var(--text-main, #0f172a)", marginBottom: "0.4rem" }}>
              {title}
            </h3>
            <div style={{ fontSize: "0.95rem", color: "var(--text-muted, #475569)", lineHeight: "1.5" }}>
              {message}
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "0.75rem", marginTop: "0.5rem" }}>
          {isConfirm && onCancel && (
            <button
              onClick={onCancel}
              type="button"
              style={{
                background: "var(--bg-card-subtle, #f8fafc)",
                color: "var(--text-main, #0f172a)",
                border: "1px solid var(--border-card, #e2e8f0)",
                padding: "0.6rem 1.25rem",
                borderRadius: "8px",
                fontWeight: "600",
                fontSize: "0.9rem",
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
            >
              {cancelText}
            </button>
          )}
          <button
            onClick={() => {
              if (onConfirm) onConfirm();
              else if (onCancel) onCancel();
            }}
            type="button"
            style={{
              background: confirmDanger ? "#ef4444" : "var(--primary, #0284c7)",
              color: "#ffffff",
              border: "none",
              padding: "0.6rem 1.5rem",
              borderRadius: "8px",
              fontWeight: "700",
              fontSize: "0.9rem",
              cursor: "pointer",
              boxShadow: confirmDanger ? "0 4px 14px rgba(239, 68, 68, 0.3)" : "0 4px 14px rgba(2, 132, 199, 0.3)",
              transition: "all 0.2s ease",
            }}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

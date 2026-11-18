"use client";

import React, { useEffect } from "react";

export type ToastType = "success" | "info" | "warning" | "error";

export interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastProps) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div style={{
      position: "fixed",
      bottom: "2rem",
      right: "2rem",
      zIndex: 10000,
      display: "flex",
      flexDirection: "column",
      gap: "0.75rem",
      maxWidth: "380px",
      width: "100%",
      pointerEvents: "none"
    }}>
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onDismiss }: { toast: ToastMessage; onDismiss: (id: string) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, 4000);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  const getStyle = () => {
    switch (toast.type) {
      case "success":
        return { bg: "#064e3b", border: "#10b981", color: "#ecfdf5", icon: "✓" };
      case "error":
        return { bg: "#7f1d1d", border: "#ef4444", color: "#fef2f2", icon: "✕" };
      case "warning":
        return { bg: "#78350f", border: "#f59e0b", color: "#fffbeb", icon: "⚠️" };
      default:
        return { bg: "#0c4a6e", border: "#0284c7", color: "#f0f9ff", icon: "ℹ️" };
    }
  };

  const style = getStyle();

  return (
    <div style={{
      background: style.bg,
      borderLeft: `4px solid ${style.border}`,
      color: style.color,
      borderRadius: "0.5rem",
      padding: "0.85rem 1.1rem",
      boxShadow: "0 10px 25px rgba(0, 0, 0, 0.4)",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "0.75rem",
      pointerEvents: "auto",
      fontSize: "0.9rem",
      fontWeight: "600",
      animation: "slideInRight 0.3s cubic-bezier(0.16, 1, 0.3, 1)"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
        <span>{style.icon}</span>
        <span>{toast.message}</span>
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        style={{
          background: "transparent",
          border: "none",
          color: style.color,
          cursor: "pointer",
          fontSize: "1rem",
          padding: 0,
          opacity: 0.7
        }}
      >
        ✕
      </button>
    </div>
  );
}

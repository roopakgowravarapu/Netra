"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("App Router Error Boundary Caught:", error);
  }, [error]);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        textAlign: "center",
        background: "var(--bg-page, #f8fafc)",
        color: "var(--text-main, #0f172a)",
      }}
    >
      <h2 style={{ fontSize: "1.8rem", marginBottom: "1rem", fontWeight: 700 }}>
        Something went wrong!
      </h2>
      <p style={{ color: "var(--text-muted, #475569)", marginBottom: "1.5rem", maxWidth: "500px" }}>
        {error.message || "An unexpected error occurred while rendering the page."}
      </p>
      <button
        onClick={() => reset()}
        style={{
          background: "var(--primary, #0284c7)",
          color: "#ffffff",
          border: "none",
          padding: "0.75rem 1.5rem",
          borderRadius: "8px",
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        Try again
      </button>
    </div>
  );
}

"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body
        style={{
          fontFamily: "system-ui, -apple-system, sans-serif",
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "2rem",
          textAlign: "center",
          backgroundColor: "#090d16",
          color: "#f8fafc",
        }}
      >
        <h2 style={{ fontSize: "1.8rem", marginBottom: "1rem", fontWeight: 700 }}>
          Application Error
        </h2>
        <p style={{ color: "#94a3b8", marginBottom: "1.5rem", maxWidth: "500px" }}>
          {error?.message || "A critical application error occurred."}
        </p>
        <button
          onClick={() => reset()}
          style={{
            background: "#0284c7",
            color: "#ffffff",
            border: "none",
            padding: "0.75rem 1.5rem",
            borderRadius: "8px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Reset Application
        </button>
      </body>
    </html>
  );
}

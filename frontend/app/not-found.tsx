import Link from "next/link";

export default function NotFound() {
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
      <h1 style={{ fontSize: "4rem", fontWeight: 800, color: "var(--primary, #0284c7)", marginBottom: "0.5rem" }}>
        404
      </h1>
      <h2 style={{ fontSize: "1.5rem", marginBottom: "1rem" }}>Page Not Found</h2>
      <p style={{ color: "var(--text-muted, #475569)", marginBottom: "2rem" }}>
        The page you are looking for does not exist or has been moved.
      </p>
      <Link
        href="/"
        style={{
          background: "var(--primary, #0284c7)",
          color: "#ffffff",
          padding: "0.75rem 1.5rem",
          borderRadius: "8px",
          fontWeight: 600,
          textDecoration: "none",
        }}
      >
        Return to Home
      </Link>
    </div>
  );
}

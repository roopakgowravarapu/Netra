"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";

export function Header() {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const savedTheme = (localStorage.getItem("netra_theme") as "light" | "dark") || "light";
    setTheme(savedTheme);
    document.documentElement.setAttribute("data-theme", savedTheme);
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem("netra_theme", nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
  };

  return (
    <header style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "1.1rem 2rem",
      borderBottom: "1px solid var(--header-border)",
      background: "var(--header-bg)",
      backdropFilter: "blur(12px)",
      position: "sticky",
      top: 0,
      zIndex: 100,
      transition: "background 0.3s ease, border-color 0.3s ease"
    }}>
      <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <div style={{
          width: "36px",
          height: "36px",
          borderRadius: "8px",
          background: "linear-gradient(135deg, #0284c7, #059669)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: "800",
          color: "#ffffff",
          fontSize: "1.2rem",
          boxShadow: "0 2px 8px rgba(2, 132, 199, 0.3)"
        }}>
          N
        </div>
        <span style={{ fontSize: "1.35rem", fontWeight: "800", color: "var(--text-main)", letterSpacing: "-0.02em" }}>
          NETRA <span style={{ fontSize: "0.75rem", color: "var(--primary)", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: "700" }}>XAI</span>
        </span>
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
        <nav style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
          <Link href="/" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: "0.95rem", fontWeight: "500" }}>
            Overview
          </Link>
          <Link href="/screening" style={{ color: "var(--primary)", textDecoration: "none", fontSize: "0.95rem", fontWeight: "600" }}>
            Screening Portal
          </Link>
          <Link href="/dashboard" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: "0.95rem", fontWeight: "500" }}>
            Telemedicine
          </Link>
        </nav>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          type="button"
          aria-label="Toggle Theme"
          style={{
            background: "var(--bg-card-subtle)",
            color: "var(--text-main)",
            border: "1px solid var(--border-card)",
            padding: "0.4rem 0.8rem",
            borderRadius: "8px",
            fontSize: "0.85rem",
            fontWeight: "600",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "0.4rem",
            transition: "all 0.2s ease"
          }}
        >
          <span>{theme === "light" ? "☀️" : "🌙"}</span>
          <span>{theme === "light" ? "Light" : "Dark"}</span>
        </button>
      </div>
    </header>
  );
}

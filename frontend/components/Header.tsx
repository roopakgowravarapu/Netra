"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";
import { Language, translations } from "../lib/translations";

export function Header() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [lang, setLang] = useState<Language>("en");
  const [isOnline, setIsOnline] = useState<boolean>(true);

  useEffect(() => {
    // Theme initialization
    const savedTheme = (localStorage.getItem("netra_theme") as "light" | "dark") || "light";
    setTheme(savedTheme);
    document.documentElement.setAttribute("data-theme", savedTheme);

    // Language initialization
    const savedLang = (localStorage.getItem("netra_lang") as Language) || "en";
    setLang(savedLang);

    // Online / Offline status
    if (typeof window !== "undefined") {
      setIsOnline(navigator.onLine);
      const handleOnline = () => setIsOnline(true);
      const handleOffline = () => setIsOnline(false);

      window.addEventListener("online", handleOnline);
      window.addEventListener("offline", handleOffline);

      return () => {
        window.removeEventListener("online", handleOnline);
        window.removeEventListener("offline", handleOffline);
      };
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem("netra_theme", nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
  };

  const handleLanguageChange = (newLang: Language) => {
    setLang(newLang);
    localStorage.setItem("netra_lang", newLang);
    window.dispatchEvent(new CustomEvent("netra_language_changed", { detail: newLang }));
  };

  const t = translations[lang] || translations.en;

  return (
    <header style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0.9rem 2rem",
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
        <div style={{ display: "flex", flexDirection: "column" }}>
          <span style={{ fontSize: "1.25rem", fontWeight: "800", color: "var(--text-main)", letterSpacing: "-0.02em", lineHeight: 1.1 }}>
            NETRA <span style={{ fontSize: "0.7rem", color: "var(--primary)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: "700" }}>XAI</span>
          </span>
          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: "500" }}>
            Clinical DR Screening
          </span>
        </div>
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
        <nav style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
          <Link href="/" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: "0.92rem", fontWeight: "500" }}>
            {t.navHome}
          </Link>
          <Link href="/screening" style={{ color: "var(--primary)", textDecoration: "none", fontSize: "0.92rem", fontWeight: "600" }}>
            {t.navScreening}
          </Link>
          <Link href="/doctor" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: "0.92rem", fontWeight: "500" }}>
            {t.navDoctor}
          </Link>
        </nav>

        {/* Connectivity Status Badge */}
        <div
          title={isOnline ? "Backend & Cloud Sync Connected" : "Operating in offline mode. Recapture/retry available upon reconnect."}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.4rem",
            padding: "0.25rem 0.65rem",
            borderRadius: "9999px",
            fontSize: "0.75rem",
            fontWeight: "600",
            background: isOnline ? "rgba(16, 185, 129, 0.12)" : "rgba(239, 68, 68, 0.15)",
            color: isOnline ? "#059669" : "#dc2626",
            border: `1px solid ${isOnline ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
          }}
        >
          <span
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              backgroundColor: isOnline ? "#10b981" : "#ef4444",
              display: "inline-block",
            }}
          />
          <span>{isOnline ? t.online : t.offline}</span>
        </div>

        {/* Language Selector */}
        <div style={{ position: "relative" }}>
          <select
            value={lang}
            onChange={(e) => handleLanguageChange(e.target.value as Language)}
            aria-label="Select Language"
            style={{
              background: "var(--bg-card-subtle)",
              color: "var(--text-main)",
              border: "1px solid var(--border-card)",
              padding: "0.35rem 0.65rem",
              borderRadius: "8px",
              fontSize: "0.82rem",
              fontWeight: "600",
              cursor: "pointer",
              outline: "none",
            }}
          >
            <option value="en">English (EN)</option>
            <option value="te">తెలుగు (Telugu)</option>
            <option value="hi">हिन्दी (Hindi)</option>
          </select>
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          type="button"
          aria-label="Toggle Theme"
          style={{
            background: "var(--bg-card-subtle)",
            color: "var(--text-main)",
            border: "1px solid var(--border-card)",
            padding: "0.35rem 0.7rem",
            borderRadius: "8px",
            fontSize: "0.82rem",
            fontWeight: "600",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "0.35rem",
            transition: "all 0.2s ease"
          }}
        >
          <span>{theme === "light" ? "☀️" : "🌙"}</span>
        </button>
      </div>
    </header>
  );
}

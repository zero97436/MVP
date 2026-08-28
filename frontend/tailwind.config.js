/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Palette pilotée par variables CSS (voir index.css) -> thème clair/sombre.
        bg: {
          DEFAULT: "rgb(var(--bg) / <alpha-value>)",
          soft: "rgb(var(--bg-soft) / <alpha-value>)",
          elevated: "rgb(var(--card) / <alpha-value>)",
        },
        card: "rgb(var(--card) / <alpha-value>)",
        border: {
          DEFAULT: "rgb(var(--border) / <alpha-value>)",
          soft: "rgb(var(--border-soft) / <alpha-value>)",
        },
        ink: {
          DEFAULT: "rgb(var(--ink) / <alpha-value>)",
          soft: "rgb(var(--ink-soft) / <alpha-value>)",
          faint: "rgb(var(--ink-faint) / <alpha-value>)",
        },
        status: {
          ok: "#10B981",
          warning: "#F59E0B",
          critical: "#EF4444",
          unknown: "#64748B",
          info: "#3B82F6",
        },
        brand: {
          // Surchargeable par le branding (plan Professional) via variables CSS.
          DEFAULT: "rgb(var(--brand-rgb, 59 130 246) / <alpha-value>)",
          soft: "rgb(var(--brand-soft-rgb, 29 78 216) / <alpha-value>)",
        },
      },
      boxShadow: {
        card: "0 1px 2px 0 rgba(0,0,0,0.4), 0 1px 3px 0 rgba(0,0,0,0.3)",
        glow: "0 0 0 1px rgba(59,130,246,0.4), 0 8px 30px -8px rgba(59,130,246,0.35)",
      },
      keyframes: {
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgba(16,185,129,0.5)" },
          "70%": { boxShadow: "0 0 0 6px rgba(16,185,129,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(16,185,129,0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "pulse-ring": "pulse-ring 2s infinite",
        shimmer: "shimmer 1.5s infinite",
      },
    },
  },
  plugins: [],
};

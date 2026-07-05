import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../api/client";

export interface BrandingInfo {
  display_name: string;
  tagline: string;
  logo_url: string | null;
  accent_color: string | null;
  custom: boolean;
}

export const DEFAULT_BRANDING: BrandingInfo = {
  display_name: "Opsora",
  tagline: "Surveillez. Comprenez. Agissez.",
  logo_url: null,
  accent_color: null,
  custom: false,
};

const BrandingContext = createContext<{ branding: BrandingInfo; reload: () => void }>({
  branding: DEFAULT_BRANDING,
  reload: () => {},
});

function hexToRgb(hex: string): [number, number, number] | null {
  const m = /^#([0-9a-fA-F]{6})$/.exec(hex);
  if (!m) return null;
  const n = parseInt(m[1], 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function applyBranding(b: BrandingInfo) {
  document.title = `${b.display_name} — Supervision`;
  const root = document.documentElement;
  if (b.accent_color) {
    const rgb = hexToRgb(b.accent_color);
    if (rgb) {
      root.style.setProperty("--brand-rgb", rgb.join(" "));
      // Variante "soft" = même teinte assombrie (~25 %).
      root.style.setProperty("--brand-soft-rgb", rgb.map((v) => Math.round(v * 0.75)).join(" "));
    }
  } else {
    root.style.removeProperty("--brand-rgb");
    root.style.removeProperty("--brand-soft-rgb");
  }
}

export function BrandingProvider({ children }: { children: ReactNode }) {
  const [branding, setBranding] = useState<BrandingInfo>(DEFAULT_BRANDING);

  const reload = () => {
    api.get<BrandingInfo>("/branding")
      .then((r) => { setBranding(r.data); applyBranding(r.data); })
      .catch(() => applyBranding(DEFAULT_BRANDING));
  };
  useEffect(reload, []);

  return (
    <BrandingContext.Provider value={{ branding, reload }}>
      {children}
    </BrandingContext.Provider>
  );
}

export function useBranding() {
  return useContext(BrandingContext);
}

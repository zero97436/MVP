/** Gestion du thème : sombre / clair / système (adaptatif). Persisté en localStorage. */
export type Theme = "dark" | "light" | "system";

const KEY = "orbisys_theme";

export function getTheme(): Theme {
  try {
    const t = localStorage.getItem(KEY);
    if (t === "light" || t === "dark" || t === "system") return t;
  } catch { /* localStorage indisponible */ }
  return "dark"; // défaut = sombre (préserve l'apparence historique)
}

export function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  if (theme === "system") {
    root.removeAttribute("data-theme"); // -> suit prefers-color-scheme
  } else {
    root.setAttribute("data-theme", theme);
  }
  try { localStorage.setItem(KEY, theme); } catch { /* ignore */ }
}

/** À appeler au démarrage (avant le rendu) pour éviter tout flash. */
export function initTheme(): void {
  applyTheme(getTheme());
}

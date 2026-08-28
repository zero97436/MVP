import type { User } from "../types";

/** Peut modifier : admin, opérateur, ou un rôle personnalisé (≠ lecteur).
 *  Le contrôle fin par section est appliqué côté serveur. */
export const canEdit = (user?: User | null): boolean =>
  !!user && user.role !== "viewer";

/** Administration (utilisateurs, canaux de notification). */
export const isAdmin = (user?: User | null): boolean => user?.role === "admin";

const BUILTIN_ROLE_LABEL: Record<string, string> = {
  admin: "Administrateur",
  operator: "Opérateur",
  viewer: "Lecture seule",
};

/** Libellé d'un rôle : intégré traduit, personnalisé affiché tel quel. */
export const roleLabel = (role: string): string => BUILTIN_ROLE_LABEL[role] ?? role;

/** Compat : ancien accès type-map. Retombe sur le nom brut pour un rôle custom. */
export const ROLE_LABEL: Record<string, string> = new Proxy(BUILTIN_ROLE_LABEL, {
  get: (t, p: string) => t[p] ?? p,
});

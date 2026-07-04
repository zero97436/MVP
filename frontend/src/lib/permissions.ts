import type { User, UserRole } from "../types";

/** Peut modifier (CRUD hôtes/checks, run, acquittement) : opérateur ou admin. */
export const canEdit = (user?: User | null): boolean =>
  user?.role === "admin" || user?.role === "operator";

/** Administration (utilisateurs, canaux de notification). */
export const isAdmin = (user?: User | null): boolean => user?.role === "admin";

export const ROLE_LABEL: Record<UserRole, string> = {
  admin: "Administrateur",
  operator: "Opérateur",
  viewer: "Lecture seule",
};

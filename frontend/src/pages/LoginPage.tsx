import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2, LogIn, KeyRound } from "lucide-react";
import { api, tokenStore } from "../api/client";
import { BrandLogo } from "../components/ui/BrandLogo";
import { useBranding } from "../lib/branding";
import { useAuth } from "../lib/auth";

export default function LoginPage() {
  const { branding } = useBranding();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@local");
  const [password, setPassword] = useState("admin1234");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [ssoEnabled, setSsoEnabled] = useState(false);

  // SSO : bouton si activé côté serveur + réception du token au retour du fournisseur.
  useEffect(() => {
    api.get<{ enabled: boolean }>("/auth/sso/info").then((r) => setSsoEnabled(r.data.enabled)).catch(() => {});
    const params = new URLSearchParams(window.location.search);
    const ssoToken = params.get("sso_token");
    const ssoError = params.get("sso_error");
    if (ssoToken) {
      tokenStore.set(ssoToken);
      window.location.replace("/dashboard");
    } else if (ssoError) {
      setError(`SSO : ${ssoError}`);
      window.history.replaceState(null, "", "/login");
    }
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch {
      setError("Identifiants invalides");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-bg px-4">
      {/* Halo décoratif */}
      <div className="pointer-events-none absolute -top-40 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-brand/20 blur-[120px]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-80 w-80 rounded-full bg-status-ok/10 blur-[120px]" />

      <motion.form
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        onSubmit={onSubmit}
        className="card relative w-full max-w-sm p-8"
      >
        <div className="mb-6 flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-brand/15 text-brand">
            <BrandLogo className="h-9 w-9" />
          </span>
          <div>
            <div>
              <h1 className="text-lg font-semibold text-ink">{branding.display_name}</h1>
              <p className="text-[11px] uppercase tracking-[0.18em] text-ink-faint">{branding.tagline}</p>
            </div>
            <p className="text-xs text-ink-faint">Plateforme de supervision</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-status-critical/30 bg-status-critical/10 p-2.5 text-sm text-status-critical">
            {error}
          </div>
        )}

        <label className="mb-1 block text-sm font-medium text-ink-soft">Email</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input mb-4 w-full" />

        <label className="mb-1 block text-sm font-medium text-ink-soft">Mot de passe</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input mb-6 w-full" />

        <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogIn className="h-4 w-4" />}
          {loading ? "Connexion..." : "Se connecter"}
        </button>

        {ssoEnabled && (
          <>
            <div className="my-4 flex items-center gap-3 text-[11px] uppercase tracking-wide text-ink-faint">
              <span className="h-px flex-1 bg-border" /> ou <span className="h-px flex-1 bg-border" />
            </div>
            <a href="/api/auth/sso/login" className="btn-ghost w-full justify-center py-2.5">
              <KeyRound className="h-4 w-4" /> Connexion entreprise (SSO)
            </a>
          </>
        )}
      </motion.form>
    </div>
  );
}

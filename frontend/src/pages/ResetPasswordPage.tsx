import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2, KeyRound, CheckCircle2 } from "lucide-react";
import { resetPassword } from "../api/endpoints";
import { BrandLogo } from "../components/ui/BrandLogo";
import { useBranding } from "../lib/branding";

export default function ResetPasswordPage() {
  const { branding } = useBranding();
  const navigate = useNavigate();
  const token = new URLSearchParams(window.location.search).get("token") ?? "";
  const [pw, setPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!token) { setError("Lien invalide (jeton manquant)."); return; }
    if (pw !== confirm) { setError("Les deux mots de passe ne correspondent pas."); return; }
    if (pw.length < 6) { setError("Le mot de passe doit faire au moins 6 caractères."); return; }
    setBusy(true);
    try {
      await resetPassword(token, pw);
      setDone(true);
      setTimeout(() => navigate("/login"), 2500);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? "Réinitialisation impossible.");
    } finally { setBusy(false); }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-bg px-4">
      <div className="pointer-events-none absolute -top-40 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-brand/20 blur-[120px]" />
      <motion.form
        initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
        onSubmit={submit} className="card relative w-full max-w-sm p-8"
      >
        <div className="mb-6 flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-brand/15 text-brand"><BrandLogo className="h-9 w-9" /></span>
          <div>
            <h1 className="text-lg font-semibold text-ink">{branding.display_name}</h1>
            <p className="text-xs text-ink-faint">Nouveau mot de passe</p>
          </div>
        </div>

        {done ? (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <CheckCircle2 className="h-12 w-12 text-status-ok" />
            <p className="text-sm font-medium text-status-ok">Mot de passe réinitialisé ✅</p>
            <p className="text-xs text-ink-faint">Redirection vers la connexion…</p>
          </div>
        ) : (
          <>
            {error && <div className="mb-4 rounded-lg border border-status-critical/30 bg-status-critical/10 p-2.5 text-sm text-status-critical">{error}</div>}
            <label className="mb-1 block text-sm font-medium text-ink-soft">Nouveau mot de passe</label>
            <input type="password" value={pw} onChange={(e) => setPw(e.target.value)} className="input mb-4 w-full" autoComplete="new-password" />
            <label className="mb-1 block text-sm font-medium text-ink-soft">Confirmer</label>
            <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)}
                   className={`input mb-6 w-full ${confirm && pw !== confirm ? "ring-1 ring-status-critical" : ""}`} autoComplete="new-password" />
            <button type="submit" disabled={busy} className="btn-primary w-full py-2.5">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
              Définir le mot de passe
            </button>
          </>
        )}
      </motion.form>
    </div>
  );
}

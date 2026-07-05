import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2, LogIn } from "lucide-react";
import { Logo } from "../components/ui/Logo";
import { useAuth } from "../lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@local");
  const [password, setPassword] = useState("admin1234");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
            <Logo className="h-9 w-9" />
          </span>
          <div>
            <div>
              <h1 className="text-lg font-semibold text-ink">Opsora</h1>
              <p className="text-[11px] uppercase tracking-[0.18em] text-ink-faint">Surveillez. Comprenez. Agissez.</p>
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
      </motion.form>
    </div>
  );
}

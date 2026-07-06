import { useState } from "react";
import { Upload, Eye, CheckCircle2, AlertTriangle, FileUp } from "lucide-react";
import { api } from "../api/client";
import { Card, SectionTitle } from "./ui/Card";

interface PreviewHost {
  name: string;
  hostname_or_ip: string;
  environment: string | null;
  location: string | null;
  template: string | null;
  parent: string | null;
  checks: string[];
}
interface MigrateResult {
  dry_run: boolean;
  hosts?: PreviewHost[];
  created?: string[];
  skipped?: string[];
  checks_created?: number;
  warnings: string[];
}

const CSV_EXAMPLE = `name;ip;environment;site;latitude;longitude;template;parent
Routeur Paris;192.168.1.1;production;Agence Paris;48.85;2.35;Équipement réseau (basique);
Serveur Paris;192.168.1.10;production;Agence Paris;;;Serveur Linux;Routeur Paris`;

export function ImportPanel({ onImported }: { onImported: () => void }) {
  const [format, setFormat] = useState<"csv" | "nagios">("csv");
  const [content, setContent] = useState("");
  const [preview, setPreview] = useState<MigrateResult | null>(null);
  const [result, setResult] = useState<MigrateResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async (dryRun: boolean) => {
    setBusy(true);
    setError(null);
    try {
      const { data } = await api.post<MigrateResult>("/migrate", { format, content, dry_run: dryRun });
      if (dryRun) {
        setPreview(data);
        setResult(null);
      } else {
        setResult(data);
        setPreview(null);
        onImported();
      }
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Import impossible");
    } finally {
      setBusy(false);
    }
  };

  const onFile = (f: File | undefined) => {
    if (!f) return;
    f.text().then((t) => {
      setContent(t);
      if (f.name.endsWith(".cfg")) setFormat("nagios");
      if (f.name.endsWith(".csv")) setFormat("csv");
    });
  };

  return (
    <Card>
      <SectionTitle title="Migration — importer des hôtes" icon={Upload} />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <select value={format} onChange={(e) => setFormat(e.target.value as "csv" | "nagios")} className="input">
          <option value="csv">CSV (universel)</option>
          <option value="nagios">Fichiers de configuration (.cfg)</option>
        </select>
        <label className="btn-ghost cursor-pointer justify-center">
          <FileUp className="h-4 w-4" /> Choisir un fichier…
          <input type="file" accept=".csv,.cfg,.txt" className="hidden" onChange={(e) => onFile(e.target.files?.[0])} />
        </label>
        <button onClick={() => setContent(CSV_EXAMPLE)} className="btn-ghost text-xs" type="button">
          Exemple CSV
        </button>
      </div>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={7}
        placeholder={format === "csv"
          ? "Colle ton CSV ici (colonnes : name, ip, environment, site, latitude, longitude, template, parent)"
          : "Colle le contenu de tes fichiers de configuration .cfg (hosts + services concaténés)"}
        className="input mt-3 w-full font-mono text-xs"
      />
      <div className="mt-3 flex items-center gap-2">
        <button onClick={() => run(true)} disabled={busy || !content.trim()} className="btn-ghost disabled:opacity-40">
          <Eye className="h-4 w-4" /> Prévisualiser
        </button>
        <button onClick={() => run(false)} disabled={busy || !preview} className="btn-primary disabled:opacity-40"
                title={!preview ? "Prévisualise d'abord" : "Créer les hôtes"}>
          <Upload className="h-4 w-4" /> Importer {preview?.hosts ? `(${preview.hosts.length} hôtes)` : ""}
        </button>
      </div>

      {error && <p className="mt-3 text-sm text-status-critical">⚠️ {error}</p>}

      {/* Prévisualisation */}
      {preview?.hosts && (
        <div className="mt-4 overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-xs">
            <thead className="bg-bg-soft/60 text-left uppercase tracking-wide text-ink-faint">
              <tr>
                <th className="px-3 py-2">Hôte</th><th className="px-3 py-2">IP</th>
                <th className="px-3 py-2">Site</th><th className="px-3 py-2">Template</th>
                <th className="px-3 py-2">Parent</th><th className="px-3 py-2">Checks</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {preview.hosts.map((h) => (
                <tr key={h.hostname_or_ip}>
                  <td className="px-3 py-2 font-medium text-ink">{h.name}</td>
                  <td className="px-3 py-2 text-ink-soft">{h.hostname_or_ip}</td>
                  <td className="px-3 py-2 text-ink-faint">{h.location ?? "—"}</td>
                  <td className="px-3 py-2 text-ink-faint">{h.template ?? "—"}</td>
                  <td className="px-3 py-2 text-ink-faint">{h.parent ?? "—"}</td>
                  <td className="px-3 py-2 text-ink-faint">{h.checks.length ? h.checks.join(", ") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Résultat */}
      {result && (
        <p className="mt-3 flex items-center gap-1.5 text-sm text-status-ok">
          <CheckCircle2 className="h-4 w-4" />
          {result.created?.length ?? 0} hôte(s) créé(s), {result.checks_created ?? 0} check(s)
          {result.skipped?.length ? ` · ${result.skipped.length} déjà présent(s), ignoré(s)` : ""}
        </p>
      )}

      {(preview?.warnings?.length || result?.warnings?.length) ? (
        <div className="mt-2 space-y-1">
          {(preview?.warnings ?? result?.warnings ?? []).map((w, i) => (
            <p key={i} className="flex items-center gap-1.5 text-xs text-status-warning">
              <AlertTriangle className="h-3 w-3 shrink-0" /> {w}
            </p>
          ))}
        </div>
      ) : null}
    </Card>
  );
}

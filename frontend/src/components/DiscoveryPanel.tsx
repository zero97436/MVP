import { useState } from "react";
import { Radar, Loader2, Download, CheckCircle2 } from "lucide-react";
import { scanNetwork, importDiscovered, type DiscoveredHost } from "../api/endpoints";
import { Card, SectionTitle } from "./ui/Card";

export function DiscoveryPanel({ onImported }: { onImported?: () => void }) {
  const [target, setTarget] = useState("192.168.1.0/24");
  const [scanning, setScanning] = useState(false);
  const [results, setResults] = useState<DiscoveredHost[] | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [done, setDone] = useState<number | null>(null);

  const scan = async (e: React.FormEvent) => {
    e.preventDefault();
    setScanning(true); setError(null); setResults(null); setDone(null);
    try {
      const { data } = await scanNetwork(target);
      setResults(data.results);
      // Présélectionne les non encore supervisés.
      setSelected(new Set(data.results.filter((r) => !r.already_monitored).map((r) => r.ip)));
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Scan impossible.");
    } finally {
      setScanning(false);
    }
  };

  const toggle = (ip: string) =>
    setSelected((s) => { const n = new Set(s); n.has(ip) ? n.delete(ip) : n.add(ip); return n; });

  const doImport = async () => {
    if (!results) return;
    setImporting(true);
    try {
      const items = results
        .filter((r) => selected.has(r.ip) && !r.already_monitored)
        .map((r) => ({ name: r.ip, hostname_or_ip: r.ip, environment: "decouvert", checks: r.suggested_checks }));
      const { data } = await importDiscovered(items);
      setDone(data.imported);
      onImported?.();
    } finally {
      setImporting(false);
    }
  };

  return (
    <Card>
      <SectionTitle title="Découverte réseau" icon={Radar} />
      <form onSubmit={scan} className="mb-3 flex flex-wrap gap-2">
        <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="192.168.1.0/24"
          className="input flex-1 font-mono" />
        <button className="btn-primary" disabled={scanning}>
          {scanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Radar className="h-4 w-4" />}
          {scanning ? "Scan en cours..." : "Scanner"}
        </button>
      </form>

      {error && <p className="text-sm text-status-critical">{error}</p>}
      {done !== null && (
        <p className="mb-2 flex items-center gap-2 text-sm text-status-ok">
          <CheckCircle2 className="h-4 w-4" /> {done} hôte(s) importé(s).
        </p>
      )}

      {results && (
        results.length === 0 ? (
          <p className="py-4 text-center text-sm text-ink-faint">Aucun équipement trouvé sur cette plage.</p>
        ) : (
          <>
            <div className="max-h-80 space-y-1 overflow-y-auto">
              {results.map((r) => (
                <label key={r.ip} className="flex items-center gap-3 rounded-lg border border-border bg-bg-soft/50 px-3 py-2 text-sm">
                  <input type="checkbox" disabled={r.already_monitored}
                    checked={selected.has(r.ip)} onChange={() => toggle(r.ip)} />
                  <span className="font-mono text-ink">{r.ip}</span>
                  <span className="flex flex-wrap gap-1">
                    {r.open_ports.map((p) => <span key={p} className="rounded bg-bg px-1.5 py-0.5 text-[11px] text-ink-faint">{p}</span>)}
                  </span>
                  <span className="ml-auto text-xs">
                    {r.already_monitored
                      ? <span className="text-ink-faint">déjà supervisé</span>
                      : <span className="text-status-ok">{r.suggested_checks.length} check(s)</span>}
                  </span>
                </label>
              ))}
            </div>
            <button onClick={doImport} disabled={importing || selected.size === 0} className="btn-primary mt-3 px-3 py-1.5 text-xs">
              {importing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
              Importer {selected.size} sélectionné(s)
            </button>
          </>
        )
      )}
      <p className="mt-3 text-xs text-ink-faint">
        Ping + sonde des ports courants sur la plage (max /24). Les hôtes choisis sont créés avec leurs checks suggérés.
      </p>
    </Card>
  );
}

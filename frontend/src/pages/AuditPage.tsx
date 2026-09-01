import { useEffect, useState } from "react";
import { ShieldCheck, Search, RefreshCw } from "lucide-react";
import { listAudit, type AuditEntry } from "../api/endpoints";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Loading } from "../components/States";
import { timeAgo } from "../lib/format";
import { cn } from "../lib/cn";
import { useI18n } from "../lib/i18n";

const METHOD_COLOR: Record<string, string> = {
  POST: "#10B981", PUT: "#F59E0B", PATCH: "#F59E0B", DELETE: "#EF4444",
};

export default function AuditPage() {
  const { t } = useI18n();
  const [rows, setRows] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [enterpriseOnly, setEnterpriseOnly] = useState(false);
  const [user, setUser] = useState("");
  const [q, setQ] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try {
      const { data } = await listAudit({ user: user || undefined, q: q || undefined, limit: 200 });
      setRows(data);
      setEnterpriseOnly(false);
    } catch (e: unknown) {
      if ((e as { response?: { status?: number } })?.response?.status === 403) setEnterpriseOnly(true);
    }
  };
  useEffect(() => { load().finally(() => setLoading(false)); /* eslint-disable-next-line */ }, []);

  const refresh = async () => {
    setRefreshing(true);
    await load().finally(() => setRefreshing(false));
  };

  if (loading) return <Loading />;

  return (
    <div className="space-y-6">
      <PageHeader
        helpTopic="audit"
        titleKey="page.audit.title"
        subtitleKey="page.audit.sub"
        actions={
          <button onClick={refresh} disabled={refreshing} className="btn-ghost">
            <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} /> {t("aud.refresh")}
          </button>
        }
      />

      {enterpriseOnly ? (
        <Card>
          <div className="flex flex-col items-center gap-3 py-14 text-center">
            <ShieldCheck className="h-12 w-12 text-ink-faint" />
            <p className="text-sm font-medium text-ink">{t("aud.entTitle")}</p>
            <p className="max-w-md text-xs text-ink-faint">{t("aud.entDesc")}</p>
          </div>
        </Card>
      ) : (
        <>
          <Card className="flex flex-wrap items-center gap-3">
            <div className="relative min-w-[180px] flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
              <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()}
                     placeholder={t("aud.filterPath")} className="input w-full pl-9" />
            </div>
            <input value={user} onChange={(e) => setUser(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()}
                   placeholder={t("aud.filterUser")} className="input min-w-[180px]" />
            <button onClick={load} className="btn-primary">{t("aud.filter")}</button>
          </Card>

          <Card className="overflow-hidden p-0">
            <table className="w-full text-xs">
              <thead className="border-b border-border bg-bg-soft/60 text-left uppercase tracking-wide text-ink-faint">
                <tr>
                  <th className="px-4 py-2.5">{t("aud.when")}</th>
                  <th className="px-4 py-2.5">{t("aud.user")}</th>
                  <th className="px-4 py-2.5">{t("aud.action")}</th>
                  <th className="px-4 py-2.5">{t("aud.request")}</th>
                  <th className="px-4 py-2.5">{t("aud.code")}</th>
                  <th className="px-4 py-2.5">IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {rows.map((r) => (
                  <tr key={r.id} className="hover:bg-bg-soft/40">
                    <td className="whitespace-nowrap px-4 py-2 text-ink-faint" title={r.created_at ?? ""}>
                      {r.created_at ? timeAgo(r.created_at) : "—"}
                    </td>
                    <td className="px-4 py-2 font-medium text-ink">{r.user_email ?? t("aud.anonymous")}</td>
                    <td className="px-4 py-2"><code className="rounded bg-bg-soft px-1.5 py-0.5 text-brand">{r.action}</code></td>
                    <td className="max-w-[260px] truncate px-4 py-2 text-ink-soft">
                      <span className="mr-1.5 font-semibold" style={{ color: METHOD_COLOR[r.method] ?? "#64748B" }}>{r.method}</span>
                      {r.path}
                    </td>
                    <td className="px-4 py-2">
                      <span className={cn("font-semibold tabular-nums",
                        r.status_code < 300 ? "text-status-ok" : r.status_code < 500 ? "text-status-warning" : "text-status-critical")}>
                        {r.status_code}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-ink-faint">{r.ip ?? "—"}</td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-ink-faint">{t("aud.noEntry")}</td></tr>
                )}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </div>
  );
}

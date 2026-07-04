import type { CheckResult, CheckStatus } from "../types";

export interface BucketPoint {
  t: number; // timestamp (ms)
  label: string;
  availability: number; // %
  ok: number;
  fail: number;
}

/**
 * Disponibilité agrégée par tranches, dérivée des VRAIS check_results.
 * availability = % de résultats OK dans la tranche.
 */
export function availabilityBuckets(
  results: CheckResult[],
  windowMs: number,
  buckets: number,
): BucketPoint[] {
  const now = Date.now();
  const start = now - windowMs;
  const size = windowMs / buckets;
  const slots: { ok: number; fail: number }[] = Array.from({ length: buckets }, () => ({
    ok: 0,
    fail: 0,
  }));

  for (const r of results) {
    const ts = new Date(r.checked_at).getTime();
    if (ts < start || ts > now) continue;
    const idx = Math.min(buckets - 1, Math.floor((ts - start) / size));
    if (r.status === "OK") slots[idx].ok++;
    else slots[idx].fail++;
  }

  return slots.map((s, i) => {
    const total = s.ok + s.fail;
    const t = start + i * size + size / 2;
    return {
      t,
      label: bucketLabel(t, windowMs),
      availability: total === 0 ? 100 : Math.round((s.ok / total) * 1000) / 10,
      ok: s.ok,
      fail: s.fail,
    };
  });
}

function bucketLabel(t: number, windowMs: number): string {
  const d = new Date(t);
  if (windowMs <= 24 * 3600 * 1000)
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return d.toLocaleDateString([], { day: "2-digit", month: "2-digit" });
}

/** Temps de réponse réel (duration_ms) en série chronologique. */
export function responseTimeSeries(results: CheckResult[]) {
  return [...results]
    .filter((r) => r.duration_ms != null)
    .sort((a, b) => +new Date(a.checked_at) - +new Date(b.checked_at))
    .map((r) => ({
      t: new Date(r.checked_at).getTime(),
      label: new Date(r.checked_at).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      ms: Math.round(r.duration_ms as number),
      status: r.status,
    }));
}

/** Disponibilité globale (%) sur un lot de résultats. */
export function availabilityRatio(results: CheckResult[]): number {
  if (results.length === 0) return 100;
  const ok = results.filter((r) => r.status === "OK").length;
  return Math.round((ok / results.length) * 1000) / 10;
}

/* ------------------------------------------------------------------ *
 * Séries [DEMO] — sources non disponibles côté backend (pas d'agent  *
 * de collecte). Marquées explicitement ; à remplacer par un vrai     *
 * endpoint d'ingestion CPU/RAM/disk/latence.                          *
 * ------------------------------------------------------------------ */
export function demoMetricSeries(seed: number, points = 48, base = 40, amp = 25) {
  let x = seed * 9301;
  const rand = () => {
    x = (x * 9301 + 49297) % 233280;
    return x / 233280;
  };
  const now = Date.now();
  return Array.from({ length: points }, (_, i) => {
    const t = now - (points - 1 - i) * 30 * 60 * 1000;
    const wave = Math.sin(i / 5 + seed) * amp;
    const value = Math.max(2, Math.min(99, base + wave + (rand() - 0.5) * amp));
    return {
      t,
      label: new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      value: Math.round(value * 10) / 10,
    };
  });
}

export const DEMO_TAG = "[DEMO]";

/** Couleur d'une valeur de métrique selon seuils génériques. */
export function metricStatus(v: number): CheckStatus {
  if (v >= 90) return "CRITICAL";
  if (v >= 75) return "WARNING";
  return "OK";
}

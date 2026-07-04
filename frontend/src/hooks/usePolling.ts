import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Rafraîchissement intelligent : poll périodique qui se met en pause
 * quand l'onglet n'est pas visible (économie réseau / NOC-friendly).
 */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs = 15000,
): { data: T | null; error: string | null; loading: boolean; refresh: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const savedFetcher = useRef(fetcher);
  savedFetcher.current = fetcher;

  const run = useCallback(async () => {
    try {
      const result = await savedFetcher.current();
      setData(result);
      setError(null);
    } catch {
      setError("Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(() => {
    run();
  }, [run]);

  useEffect(() => {
    run();
    let id: ReturnType<typeof setInterval> | null = null;
    const start = () => {
      if (id == null) id = setInterval(run, intervalMs);
    };
    const stop = () => {
      if (id != null) {
        clearInterval(id);
        id = null;
      }
    };
    const onVisibility = () => {
      if (document.hidden) stop();
      else {
        run();
        start();
      }
    };
    start();
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      stop();
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [run, intervalMs]);

  return { data, error, loading, refresh };
}

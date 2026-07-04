import { useEffect, useRef, useState } from "react";
import { getIncidents } from "../api/endpoints";
import type { CheckStatus, Incident } from "../types";

export interface LiveEvent {
  id: string;
  kind: "new" | "resolved" | "changed";
  hostName: string;
  checkName: string;
  status: CheckStatus;
  message?: string | null;
  at: number;
}

/**
 * Flux d'événements temps réel par DIFF de polling sur /dashboard/incidents.
 * NOTE: le backend n'expose pas de WebSocket — cette abstraction émule un
 * stream et peut être remplacée par un vrai WS sans changer l'UI consommatrice.
 */
export function useLiveEvents(intervalMs = 8000, max = 40) {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const prev = useRef<Map<number, Incident> | null>(null);

  useEffect(() => {
    let active = true;

    const tick = async () => {
      try {
        const { data } = await getIncidents();
        if (!active) return;
        setConnected(true);
        const current = new Map(data.map((i) => [i.alert_id, i]));
        const before = prev.current;

        if (before) {
          const fresh: LiveEvent[] = [];
          for (const [id, inc] of current) {
            const old = before.get(id);
            if (!old) {
              fresh.push(evt("new", inc));
            } else if (old.status !== inc.status) {
              fresh.push(evt("changed", inc));
            }
          }
          for (const [id, inc] of before) {
            if (!current.has(id)) fresh.push(evt("resolved", { ...inc, status: "OK" }));
          }
          if (fresh.length) {
            setEvents((e) => [...fresh.sort((a, b) => b.at - a.at), ...e].slice(0, max));
          }
        }
        prev.current = current;
      } catch {
        if (active) setConnected(false);
      }
    };

    tick();
    const id = setInterval(tick, intervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [intervalMs, max]);

  return { events, connected };
}

function evt(kind: LiveEvent["kind"], inc: Incident): LiveEvent {
  return {
    id: `${kind}-${inc.alert_id}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    kind,
    hostName: inc.host_name,
    checkName: inc.check_name,
    status: inc.status,
    message: inc.message,
    at: Date.now(),
  };
}

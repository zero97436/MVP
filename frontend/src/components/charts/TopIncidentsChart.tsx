import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AXIS, ChartTooltip } from "./ChartTooltip";
import { statusMeta } from "../../lib/status";
import type { CheckStatus } from "../../types";

export interface TopIncidentRow {
  name: string;
  count: number;
  status: CheckStatus;
}

export function TopIncidentsChart({ data, height = 220 }: { data: TopIncidentRow[]; height?: number }) {
  if (data.length === 0) {
    return (
      <div className="flex h-[220px] items-center justify-center text-sm text-ink-faint">
        Aucun incident sur la période 🎉
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart layout="vertical" data={data} margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
        <XAxis type="number" stroke={AXIS.stroke} tick={AXIS.tick} allowDecimals={false} />
        <YAxis
          type="category"
          dataKey="name"
          stroke={AXIS.stroke}
          tick={{ fill: "#94A3B8", fontSize: 11 }}
          width={120}
        />
        <Tooltip cursor={{ fill: "rgba(148,163,184,0.06)" }} content={<ChartTooltip />} />
        <Bar dataKey="count" name="Incidents" radius={[0, 4, 4, 0]} animationDuration={600}>
          {data.map((d, i) => (
            <Cell key={i} fill={statusMeta(d.status).color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

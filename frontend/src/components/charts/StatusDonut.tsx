import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { CheckStatus } from "../../types";
import { STATUS } from "../../lib/status";
import { ChartTooltip } from "./ChartTooltip";

export function StatusDonut({
  counts,
  height = 220,
}: {
  counts: Record<CheckStatus, number>;
  height?: number;
}) {
  const data = (Object.keys(STATUS) as CheckStatus[])
    .map((s) => ({ name: STATUS[s].label, status: s, value: counts[s] ?? 0, color: STATUS[s].color }))
    .filter((d) => d.value > 0);

  const total = data.reduce((a, d) => a + d.value, 0);

  if (total === 0) {
    return (
      <div className="flex h-[220px] items-center justify-center text-sm text-ink-faint">
        Aucune donnée de statut
      </div>
    );
  }

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius="62%"
            outerRadius="90%"
            paddingAngle={2}
            stroke="none"
            animationDuration={600}
          >
            {data.map((d) => (
              <Cell key={d.status} fill={d.color} />
            ))}
          </Pie>
          <Tooltip content={<ChartTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-semibold text-ink">{total}</span>
        <span className="text-xs text-ink-faint">checks</span>
      </div>
    </div>
  );
}

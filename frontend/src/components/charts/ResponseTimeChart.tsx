import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AXIS, ChartTooltip } from "./ChartTooltip";

export function ResponseTimeChart({
  data,
  height = 220,
}: {
  data: { label: string; ms: number }[];
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={AXIS.stroke} vertical={false} />
        <XAxis dataKey="label" stroke={AXIS.stroke} tick={AXIS.tick} minTickGap={28} />
        <YAxis stroke={AXIS.stroke} tick={AXIS.tick} width={44} unit="ms" />
        <Tooltip content={<ChartTooltip unit=" ms" />} />
        <Line
          type="monotone"
          dataKey="ms"
          name="Temps de réponse"
          stroke="#3B82F6"
          strokeWidth={2}
          dot={false}
          animationDuration={600}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

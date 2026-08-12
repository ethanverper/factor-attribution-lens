import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { fmtNum, fmtPvalue } from "@/lib/format"

export interface DivergingBarRow {
  name: string
  label: string
  value: number
  stdError?: number
  tStat?: number
  pValue?: number
  ciLower?: number
  ciUpper?: number
}

interface DivergingBarChartProps {
  rows: DivergingBarRow[]
  valueFormat: (v: number) => string
  showCI?: boolean
}

const chartConfig: ChartConfig = {
  value: { label: "Value", color: "var(--color-chart-1)" },
}

/** Diverging horizontal bar chart with an optional 95% CI whisker, ported
 * from `viz.py::diverging_bar_chart`/`_hbar_path` — used for Fama-French
 * factor loadings and return attribution. The whisker uses Recharts'
 * "floating bar" pattern: a second, thin `Bar` whose `dataKey` resolves to
 * a `[ciLower, ciUpper]` tuple is positioned by the same numeric x-scale
 * as the value bar, so its pixel geometry lines up exactly. */
export function DivergingBarChart({ rows, valueFormat, showCI = true }: DivergingBarChartProps) {
  const data = rows.map((r) => ({
    ...r,
    ciRange: r.ciLower !== undefined && r.ciUpper !== undefined ? [r.ciLower, r.ciUpper] : undefined,
  }))
  const values = data.flatMap((d) => [d.value, d.ciLower ?? d.value, d.ciUpper ?? d.value])
  const maxAbs = Math.max(0.001, ...values.map((v) => Math.abs(v)))
  const domain: [number, number] = [-maxAbs * 1.15, maxAbs * 1.15]

  return (
    <ChartContainer config={chartConfig} className="h-auto w-full" style={{ height: rows.length * 52 + 24 }}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke="var(--border)" />
        <XAxis type="number" domain={domain} tickFormatter={(v) => valueFormat(v)} className="tabular" fontSize={11} />
        <YAxis type="category" dataKey="label" width={140} className="tabular" fontSize={12} tickLine={false} axisLine={false} />
        <ReferenceLine x={0} stroke="var(--muted-foreground)" />
        <ChartTooltip
          cursor={{ fill: "var(--accent)" }}
          content={
            <ChartTooltipContent
              formatter={(_value, _name, item) => {
                const row = item.payload as DivergingBarRow
                return (
                  <div className="grid gap-0.5">
                    <span className="font-medium">{row.label}</span>
                    <span className="tabular">{valueFormat(row.value)}</span>
                    {row.stdError !== undefined ? (
                      <span className="text-muted-foreground tabular text-[11px]">
                        SE {fmtNum(row.stdError, 4)} · t={fmtNum(row.tStat, 2)} · p={fmtPvalue(row.pValue ?? 1)}
                      </span>
                    ) : null}
                    {row.ciLower !== undefined ? (
                      <span className="text-muted-foreground tabular text-[11px]">
                        95% CI [{fmtNum(row.ciLower, 3)}, {fmtNum(row.ciUpper, 3)}]
                      </span>
                    ) : null}
                  </div>
                )
              }}
            />
          }
        />
        {showCI && (
          <Bar dataKey="ciRange" barSize={2} isAnimationActive={false} fill="var(--muted-foreground)">
            {data.map((d) => (
              <Cell key={d.name} fill="var(--muted-foreground)" />
            ))}
          </Bar>
        )}
        <Bar dataKey="value" radius={4} barSize={22} isAnimationActive animationDuration={500}>
          {data.map((d) => (
            <Cell key={d.name} fill={d.value >= 0 ? "var(--color-chart-1)" : "var(--color-chart-5)"} />
          ))}
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}

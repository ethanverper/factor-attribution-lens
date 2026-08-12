import { useMemo } from "react"
import { CartesianGrid, ComposedChart, Line, Scatter, XAxis, YAxis } from "recharts"
import type { DotProps } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { apertureRings } from "@/lib/aperture"
import { fmtPct, fmtRatio } from "@/lib/format"

export interface FrontierPointVM {
  volatility: number
  ret: number
  sharpe: number | null
}

interface Marker {
  key: string
  label: string
  point: FrontierPointVM
  isCurrent?: boolean
}

interface FrontierChartProps {
  frontier: FrontierPointVM[]
  current: FrontierPointVM
  gmv: FrontierPointVM
  maxSharpe: FrontierPointVM | null
}

const chartConfig: ChartConfig = {
  ret: { label: "Frontier", color: "var(--color-chart-1)" },
}

// Two markers "coincide" (decision 0011's degenerate/near-identical case) when
// they're within this fraction of the plotted domain's span on *both* axes --
// a domain-normalized analogue of the original pixel-threshold union-find
// clustering in `viz.py::frontier_chart`, since this component doesn't own a
// fixed pixel scale the way the old hand-drawn SVG chart did.
const CLUSTER_THRESHOLD = 0.03

function clusterMarkers(markers: Marker[], volSpan: number, retSpan: number): Map<string, string> {
  const parent = new Map(markers.map((m) => [m.key, m.key]))
  function find(k: string): string {
    while (parent.get(k) !== k) k = parent.get(k)!
    return k
  }
  function union(a: string, b: string) {
    const ra = find(a)
    const rb = find(b)
    if (ra !== rb) parent.set(ra, rb)
  }
  for (let i = 0; i < markers.length; i++) {
    for (let j = i + 1; j < markers.length; j++) {
      const a = markers[i]
      const b = markers[j]
      const dx = volSpan > 0 ? Math.abs(a.point.volatility - b.point.volatility) / volSpan : 0
      const dy = retSpan > 0 ? Math.abs(a.point.ret - b.point.ret) / retSpan : 0
      if (dx < CLUSTER_THRESHOLD && dy < CLUSTER_THRESHOLD) union(a.key, b.key)
    }
  }
  const result = new Map<string, string>()
  for (const m of markers) result.set(m.key, find(m.key))
  return result
}

/** Long-only Markowitz efficient frontier with the current-portfolio, GMV,
 * and max-Sharpe points marked -- ported from `viz.py::frontier_chart`.
 * Coincident/near-identical markers (decision 0011) get one merged label
 * instead of stacking illegibly; the current-portfolio marker is the
 * aperture-ring glyph (its one functional, non-decorative use). */
export function FrontierChart({ frontier, current, gmv, maxSharpe }: FrontierChartProps) {
  const sorted = useMemo(() => [...frontier].sort((a, b) => a.volatility - b.volatility), [frontier])

  const markers: Marker[] = useMemo(() => {
    const list: Marker[] = [{ key: "gmv", label: "Global min-variance", point: gmv }]
    if (maxSharpe) list.push({ key: "maxSharpe", label: "Max Sharpe (tangency)", point: maxSharpe })
    list.push({ key: "current", label: "Your portfolio", point: current, isCurrent: true })
    return list
  }, [gmv, maxSharpe, current])

  const allPoints = [...sorted, ...markers.map((m) => m.point)]
  const volValues = allPoints.map((p) => p.volatility)
  const retValues = allPoints.map((p) => p.ret)
  const volSpan = Math.max(...volValues) - Math.min(...volValues)
  const retSpan = Math.max(...retValues) - Math.min(...retValues)
  const volPad = Math.max(volSpan * 0.12, 0.01)
  const retPad = Math.max(retSpan * 0.12, 0.01)
  const xDomain: [number, number] = [Math.min(...volValues) - volPad, Math.max(...volValues) + volPad]
  const yDomain: [number, number] = [Math.min(...retValues) - retPad, Math.max(...retValues) + retPad]

  const clusterOf = clusterMarkers(markers, volSpan || 1, retSpan || 1)
  const seenClusters = new Set<string>()
  const primaryOf = new Map<string, boolean>()
  for (const m of markers) {
    const c = clusterOf.get(m.key)!
    primaryOf.set(m.key, !seenClusters.has(c))
    seenClusters.add(c)
  }
  const mergedLabel = (m: Marker): string => {
    const c = clusterOf.get(m.key)!
    const members = markers.filter((mk) => clusterOf.get(mk.key) === c)
    return members.map((mk) => mk.label).join(" = ")
  }

  return (
    <ChartContainer config={chartConfig} className="aspect-auto h-[340px] w-full">
      <ComposedChart margin={{ left: 8, right: 24, top: 16, bottom: 8 }}>
        <CartesianGrid stroke="var(--border)" />
        <XAxis
          type="number"
          dataKey="volatility"
          domain={xDomain}
          tickFormatter={(v) => fmtPct(v, 1)}
          className="tabular"
          fontSize={11}
          label={{ value: "Volatility (annualized)", position: "insideBottom", offset: -4, fontSize: 11, fill: "var(--muted-foreground)" }}
        />
        <YAxis
          type="number"
          dataKey="ret"
          domain={yDomain}
          tickFormatter={(v) => fmtPct(v, 1)}
          className="tabular"
          fontSize={11}
          label={{ value: "Return (annualized)", angle: -90, position: "insideLeft", fontSize: 11, fill: "var(--muted-foreground)" }}
        />
        <ChartTooltip
          cursor={{ strokeDasharray: "3 3" }}
          content={
            <ChartTooltipContent
              labelKey="ret"
              formatter={(_value, _name, item) => {
                const p = item.payload as FrontierPointVM & { __label?: string }
                return (
                  <div className="grid gap-0.5">
                    {p.__label ? <span className="font-medium">{p.__label}</span> : null}
                    <span className="tabular text-[11px]">
                      Return {fmtPct(p.ret, 2)} · Vol {fmtPct(p.volatility, 2)} · Sharpe {fmtRatio(p.sharpe)}
                    </span>
                  </div>
                )
              }}
            />
          }
        />
        <Line
          data={sorted}
          type="monotone"
          dataKey="ret"
          stroke="var(--color-chart-1)"
          strokeWidth={2}
          dot={false}
          isAnimationActive
          animationDuration={700}
          name="Efficient frontier"
        />
        {markers.map((m) => (
          <Scatter
            key={m.key}
            data={[{ ...m.point, __label: m.label }]}
            fill={m.isCurrent ? "var(--primary)" : "var(--muted-foreground)"}
            shape={(props: unknown) => (
              <MarkerShape
                {...(props as DotProps & { cx: number; cy: number })}
                isCurrent={!!m.isCurrent}
                showLabel={primaryOf.get(m.key) ?? true}
                label={mergedLabel(m)}
              />
            )}
          />
        ))}
      </ComposedChart>
    </ChartContainer>
  )
}

function MarkerShape({
  cx,
  cy,
  isCurrent,
  showLabel,
  label,
}: {
  cx: number
  cy: number
  isCurrent: boolean
  showLabel: boolean
  label: string
}) {
  if (isCurrent) {
    const { outerR, midR, coreR, outerStroke, midStroke } = apertureRings(18, 1.6)
    return (
      <g>
        <circle cx={cx} cy={cy} r={15} fill="var(--primary)" opacity={0.16} />
        <circle cx={cx} cy={cy} r={outerR} fill="none" stroke="var(--primary)" strokeWidth={outerStroke} />
        <circle cx={cx} cy={cy} r={midR} fill="none" stroke="var(--primary)" strokeWidth={midStroke} />
        <circle cx={cx} cy={cy} r={coreR} fill="var(--primary)" />
        {showLabel && (
          <text x={cx + 14} y={cy + 4} fontSize={11.5} fontWeight={600} fill="var(--foreground)" className="tabular">
            {label}
          </text>
        )}
      </g>
    )
  }
  return (
    <g>
      <circle cx={cx} cy={cy} r={4.5} fill="var(--muted-foreground)" stroke="var(--card)" strokeWidth={1.5} />
      {showLabel && (
        <text x={cx + 10} y={cy - 8} fontSize={11} fill="var(--muted-foreground)" className="tabular">
          {label}
        </text>
      )}
    </g>
  )
}

import { fmtPct } from "@/lib/format"

interface RiskSplitBarProps {
  factorExplained: number
  idiosyncratic: number
}

/** Two-segment proportion meter for the factor-explained vs. idiosyncratic
 * risk split -- ported from `viz.py::risk_split_bar`. A simple styled meter,
 * not a full axis-bearing chart, so it stays a plain component rather than
 * a Recharts chart (nothing here needs an axis/scale/legend beyond the two
 * segment labels themselves). */
export function RiskSplitBar({ factorExplained, idiosyncratic }: RiskSplitBarProps) {
  const explainedPct = Math.max(0, Math.min(100, factorExplained * 100))
  return (
    <div className="mt-1">
      <div className="border-border flex h-9 w-full overflow-hidden rounded-md border">
        <div
          className="flex items-center justify-center text-[11px] font-medium text-white transition-[width] duration-700 ease-out"
          style={{ width: `${explainedPct}%`, backgroundColor: "var(--color-chart-1)" }}
        >
          {explainedPct > 14 ? fmtPct(factorExplained, 1) : ""}
        </div>
        <div
          className="text-muted-foreground bg-muted flex items-center justify-center text-[11px] font-medium transition-[width] duration-700 ease-out"
          style={{ width: `${100 - explainedPct}%` }}
        >
          {100 - explainedPct > 14 ? fmtPct(idiosyncratic, 1) : ""}
        </div>
      </div>
    </div>
  )
}

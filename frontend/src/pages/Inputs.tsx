import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card } from "@/components/ui/card"
import { SectionHeader } from "@/components/SectionHeader"
import { TickerCombobox } from "@/components/TickerCombobox"
import { useTickers } from "@/hooks/use-tickers"
import { fetchSamplePortfolio } from "@/lib/api"
import { buildResultsSearchParams } from "@/lib/query"
import type { FactorModel, Frequency } from "@/lib/types"
import { cn } from "@/lib/utils"

interface Row {
  id: number
  symbol: string
  weightPct: string
}

let nextId = 4
function emptyRows(): Row[] {
  return [
    { id: 0, symbol: "", weightPct: "" },
    { id: 1, symbol: "", weightPct: "" },
    { id: 2, symbol: "", weightPct: "" },
    { id: 3, symbol: "", weightPct: "" },
  ]
}

function defaultDates() {
  const end = new Date()
  end.setDate(end.getDate() - 1)
  const start = new Date(end)
  start.setDate(start.getDate() - 365)
  return { start: start.toISOString().slice(0, 10), end: end.toISOString().slice(0, 10) }
}

export function Inputs() {
  const navigate = useNavigate()
  const { data: tickers } = useTickers()
  const [rows, setRows] = useState<Row[]>(emptyRows)
  const [benchmark, setBenchmark] = useState("^GSPC")
  const [{ start, end }] = useState(defaultDates)
  const [startDate, setStartDate] = useState(start)
  const [endDate, setEndDate] = useState(end)
  const [factorModel, setFactorModel] = useState<FactorModel>("3")
  const [frequency, setFrequency] = useState<Frequency>("daily")
  const [error, setError] = useState<string | null>(null)
  const [sampleLoading, setSampleLoading] = useState(false)

  const total = useMemo(() => rows.reduce((sum, r) => sum + (Number(r.weightPct) || 0), 0), [rows])
  const roundedTotal = Math.round(total * 100) / 100
  const diff = Math.round((100 - roundedTotal) * 100) / 100
  const state: "empty" | "exact" | "under" | "over" = !rows.some((r) => r.symbol || r.weightPct)
    ? "empty"
    : Math.abs(diff) < 0.05
      ? "exact"
      : diff > 0
        ? "under"
        : "over"

  function updateRow(id: number, patch: Partial<Row>) {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, ...patch } : r)))
  }

  function addRow() {
    setRows((prev) => [...prev, { id: nextId++, symbol: "", weightPct: "" }])
  }

  function removeRow(id: number) {
    setRows((prev) => prev.filter((r) => r.id !== id))
  }

  function activeRows() {
    return rows.filter((r) => r.symbol)
  }

  function splitEvenly() {
    const active = activeRows()
    if (!active.length) return
    const base = Math.floor((100 / active.length) * 100) / 100
    let assigned = 0
    const updates = new Map<number, string>()
    active.forEach((r, i) => {
      const val = i === active.length - 1 ? Math.round((100 - assigned) * 100) / 100 : base
      assigned = Math.round((assigned + val) * 100) / 100
      updates.set(r.id, String(val))
    })
    setRows((prev) => prev.map((r) => (updates.has(r.id) ? { ...r, weightPct: updates.get(r.id)! } : r)))
  }

  function normalize() {
    const active = activeRows()
    if (!active.length) return
    const values = active.map((r) => {
      const v = Number(r.weightPct)
      return !Number.isNaN(v) && v > 0 ? v : 0
    })
    const sum = values.reduce((a, b) => a + b, 0)
    if (sum <= 0) {
      splitEvenly()
      return
    }
    let assigned = 0
    const updates = new Map<number, string>()
    active.forEach((r, i) => {
      const val = i === active.length - 1 ? Math.round((100 - assigned) * 100) / 100 : Math.round((values[i] / sum) * 100 * 100) / 100
      assigned = Math.round((assigned + val) * 100) / 100
      updates.set(r.id, String(val))
    })
    setRows((prev) => prev.map((r) => (updates.has(r.id) ? { ...r, weightPct: updates.get(r.id)! } : r)))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    const active = activeRows()
    if (active.length === 0) {
      setError("Enter at least one holding.")
      return
    }
    if (active.some((r) => !r.weightPct || Number(r.weightPct) <= 0)) {
      setError("Every holding needs an allocation greater than 0%.")
      return
    }
    const symbols = active.map((r) => r.symbol)
    if (new Set(symbols).size !== symbols.length) {
      setError("Each holding must be a distinct ticker.")
      return
    }
    if (state !== "exact") {
      setError(`Your allocations add up to ${roundedTotal}%, not 100%. Adjust the weights so they total 100% before submitting.`)
      return
    }
    if (!benchmark) {
      setError("Choose a benchmark.")
      return
    }
    if (startDate >= endDate) {
      setError("Start date must be before end date.")
      return
    }
    const params = buildResultsSearchParams({
      holdings: active.map((r) => ({ symbol: r.symbol, weightPct: Number(r.weightPct) })),
      benchmark,
      startDate,
      endDate,
      factorModel,
      frequency,
    })
    navigate(`/results?${params.toString()}`)
  }

  async function runSample() {
    setSampleLoading(true)
    try {
      const sample = await fetchSamplePortfolio()
      const params = buildResultsSearchParams({
        holdings: sample.holdings.map((h) => ({ symbol: h.symbol, weightPct: h.weight_pct })),
        benchmark: sample.benchmark,
        startDate: sample.start_date,
        endDate: sample.end_date,
        factorModel: sample.factor_model,
        frequency: sample.frequency,
      })
      navigate(`/results?${params.toString()}`)
    } finally {
      setSampleLoading(false)
    }
  }

  return (
    <div>
      <SectionHeader
        path="/inputs"
        eyebrow="Inputs"
        title="Portfolio & benchmark"
        lede="Choose holdings and a benchmark from the curated large-cap universe below (search by ticker or company name), a date range, and a Fama-French model."
      />

      <div className="bg-card mb-5 flex flex-col items-start justify-between gap-3 rounded-lg border p-4 sm:flex-row sm:items-center">
        <p className="text-muted-foreground max-w-[46ch] text-[13px]">
          No tickers in mind? <strong className="text-foreground font-mono">AAPL 40% / MSFT 30% / GOOGL 20% / AMZN 10%</strong> vs. the
          S&amp;P 500, run instantly on live data.
        </p>
        <Button variant="outline" size="sm" onClick={runSample} disabled={sampleLoading} className="flex-none font-mono">
          {sampleLoading ? "Loading…" : "▸ Run the sample portfolio"}
        </Button>
      </div>

      <Card className="p-6">
        {error ? (
          <div className="bg-destructive/10 border-destructive/40 text-foreground mb-4 rounded-md border p-3 text-[13px]">
            <strong>Could not run this analysis.</strong> {error}
          </div>
        ) : null}
        <form onSubmit={handleSubmit}>
          <div className="mb-1 font-mono text-[11.5px] tracking-wide text-muted-foreground uppercase">Holdings</div>
          <p className="text-muted-foreground mb-3 max-w-[62ch] text-[12.5px] leading-relaxed">
            <strong className="text-foreground font-mono">Allocation</strong> is the percentage of your total
            portfolio each holding makes up &mdash; e.g. enter <strong className="text-foreground font-mono">25</strong> if
            a holding is a quarter of your portfolio. All holdings' allocations together must add up to exactly 100%.
          </p>
          <div className="bg-muted/40 mb-3 rounded-md border border-dashed p-3 text-[12px] leading-relaxed">
            <span className="text-muted-foreground mr-1 rounded border px-1.5 py-0.5 font-mono text-[10px]">source</span>
            <span className="text-muted-foreground">
              Ticker and benchmark options are drawn from a curated S&amp;P 500 constituent snapshot (~496 symbols)
              plus a small set of major index/ETF benchmarks &mdash; not a live index-membership feed, so it can
              drift from the current roster over time. See{" "}
              <code className="bg-background rounded px-1 py-0.5">docs/decisions/0005-phase7-ticker-universe.md</code>.
            </span>
          </div>

          <div className="flex flex-col gap-3">
            {rows.map((row) => (
              <HoldingRow
                key={row.id}
                row={row}
                options={tickers?.tickers.map((t) => ({ symbol: t.symbol, name: t.name })) ?? []}
                onChange={(patch) => updateRow(row.id, patch)}
                onRemove={() => removeRow(row.id)}
              />
            ))}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Button type="button" variant="outline" size="sm" onClick={addRow}>
              + Add holding
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={splitEvenly}>
              Split evenly
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={normalize}>
              Normalize to 100%
            </Button>
          </div>

          <div
            className={cn(
              "mt-4 flex flex-wrap items-baseline gap-2 rounded-lg border p-3",
              state === "exact" && "border-success/45 bg-success/10",
              state === "under" && "border-warning/45 bg-warning/10",
              state === "over" && "border-destructive/45 bg-destructive/10"
            )}
          >
            <span className="text-muted-foreground font-mono text-[11px] uppercase">Total allocated</span>
            <span
              className={cn(
                "tabular text-[15px] font-bold",
                state === "exact" && "text-success",
                state === "under" && "text-warning",
                state === "over" && "text-destructive"
              )}
            >
              {roundedTotal}%
            </span>
            <span className="text-muted-foreground text-[12.5px]">
              {state === "empty" && "Enter an allocation for each holding — they must add up to 100%."}
              {state === "exact" && "Ready to submit."}
              {state === "under" && `Add ${diff}% more to reach 100%.`}
              {state === "over" && `Remove ${Math.abs(diff)}% to reach 100%.`}
            </span>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="flex flex-col gap-1.5">
              <Label className="text-muted-foreground font-mono text-[11px] uppercase">Benchmark</Label>
              <TickerCombobox
                options={tickers?.benchmarks.map((b) => ({ symbol: b.symbol, name: b.name })) ?? []}
                value={benchmark}
                onChange={setBenchmark}
                placeholder="Search benchmark…"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label className="text-muted-foreground font-mono text-[11px] uppercase">Fama-French model</Label>
              <Select value={factorModel} onValueChange={(v) => setFactorModel(v as FactorModel)}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="3">3-factor</SelectItem>
                  <SelectItem value="5">5-factor</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label className="text-muted-foreground font-mono text-[11px] uppercase">Frequency</Label>
              <Select value={frequency} onValueChange={(v) => setFrequency(v as Frequency)}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label className="text-muted-foreground font-mono text-[11px] uppercase">Start date</Label>
              <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label className="text-muted-foreground font-mono text-[11px] uppercase">End date</Label>
              <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
          </div>

          <Button type="submit" className="mt-6" size="lg" disabled={state !== "exact" || !benchmark}>
            Run analysis
          </Button>
        </form>
        <p className="text-muted-foreground mt-5 max-w-[60ch] text-[12px]">
          Data sources: yfinance (via the OpenBB Open Data Platform) for equity/benchmark prices, Kenneth French's
          Data Library for factor returns. The efficient frontier is long-only by default. Holdings and benchmark
          are limited to a curated large-cap ticker universe.
        </p>
      </Card>
    </div>
  )
}

function HoldingRow({
  row,
  options,
  onChange,
  onRemove,
}: {
  row: Row
  options: { symbol: string; name: string }[]
  onChange: (patch: Partial<Row>) => void
  onRemove: () => void
}) {
  const numeric = Number(row.weightPct) || 0
  return (
    <div className="flex items-start gap-2.5">
      <div className="flex-1">
        <TickerCombobox options={options} value={row.symbol} onChange={(symbol) => onChange({ symbol })} placeholder="Search ticker or company…" />
      </div>
      <div className="w-44 flex-none">
        <div className="flex flex-col gap-1.5">
          <Input
            type="number"
            inputMode="decimal"
            step="0.01"
            min={0}
            max={100}
            placeholder="e.g. 25"
            aria-label="Allocation percentage"
            value={row.weightPct}
            onChange={(e) => onChange({ weightPct: e.target.value })}
            className="tabular"
          />
          <Slider
            value={[numeric]}
            min={0}
            max={100}
            step={0.5}
            onValueChange={([v]) => onChange({ weightPct: String(v) })}
            aria-label="Allocation percentage (drag)"
          />
        </div>
      </div>
      <Button type="button" variant="outline" size="icon" aria-label="Remove holding" onClick={onRemove} className="flex-none">
        <X className="size-4" />
      </Button>
    </div>
  )
}

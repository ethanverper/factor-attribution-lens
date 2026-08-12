import { useEffect, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Target, Layers, LineChart as LineChartIcon, type LucideIcon } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { FrontierChart } from "@/components/charts/FrontierChart"
import { fetchSamplePortfolio } from "@/lib/api"
import { useAnalysis } from "@/hooks/use-analysis"
import { buildResultsSearchParams, resultsConfigToRequestBody, type ResultsConfig } from "@/lib/query"
import { fmtNum, fmtPct } from "@/lib/format"
import type { SamplePortfolioResponse } from "@/lib/types"

export function Overview() {
  const navigate = useNavigate()
  const [sample, setSample] = useState<SamplePortfolioResponse | null>(null)

  useEffect(() => {
    fetchSamplePortfolio().then(setSample).catch(() => {})
  }, [])

  const sampleConfig: ResultsConfig | null = sample
    ? {
        holdings: sample.holdings.map((h) => ({ symbol: h.symbol, weightPct: h.weight_pct })),
        benchmark: sample.benchmark,
        startDate: sample.start_date,
        endDate: sample.end_date,
        factorModel: sample.factor_model,
        frequency: sample.frequency,
      }
    : null
  const body = sampleConfig ? resultsConfigToRequestBody(sampleConfig) : null
  const { data, loading } = useAnalysis(body)

  function runLiveExample() {
    if (!sampleConfig) return
    const params = buildResultsSearchParams(sampleConfig)
    navigate(`/results?${params.toString()}`)
  }

  return (
    <div>
      <div className="text-primary mb-2.5 inline-flex items-center gap-2 font-mono text-[11px] tracking-wide uppercase">
        <span className="bg-primary inline-block size-1.5 rounded-full" />
        [01] Overview
      </div>
      <h1 className="font-display mb-6 text-[27px] font-medium tracking-tight sm:text-[30px]">Factor Lens</h1>

      <div className="grid grid-cols-1 items-center gap-8 lg:grid-cols-[55fr_45fr]">
        <div>
          <h2 className="font-display mb-3 text-[22px] leading-snug font-medium tracking-tight sm:text-[25px]">
            Factor Lens explains why a portfolio behaves the way it does.
          </h2>
          <p className="text-muted-foreground mb-4 max-w-[54ch] text-[14.5px] leading-relaxed">
            Enter your holdings and a benchmark — Factor Lens runs CAPM, Fama-French, and Markowitz optimization on
            live market data and returns your beta, factor loadings, and frontier position, each with full
            statistical diagnostics.
          </p>
          <div className="mb-6 flex flex-wrap items-center gap-x-2 gap-y-1.5">
            <span className="text-muted-foreground mr-0.5 font-mono text-[10.5px] tracking-wide uppercase">You provide</span>
            <Badge variant="outline" className="font-mono text-[10.5px] font-normal">
              Holdings (tickers + %)
            </Badge>
            <Badge variant="outline" className="font-mono text-[10.5px] font-normal">
              Benchmark
            </Badge>
            <Badge variant="outline" className="font-mono text-[10.5px] font-normal">
              Date range
            </Badge>
            <Badge variant="outline" className="font-mono text-[10.5px] font-normal">
              Factor model (3- or 5-factor)
            </Badge>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/inputs">Enter your holdings →</Link>
            </Button>
            <Button variant="outline" size="lg" onClick={runLiveExample} disabled={!sampleConfig}>
              ▸ Run a live example
            </Button>
          </div>
        </div>

        <Card className="border-t-primary overflow-hidden border-t-2 py-4">
          <CardContent className="px-4">
            <div className="text-muted-foreground mb-2 font-mono text-[10.5px] tracking-wide uppercase">
              Live preview · sample portfolio
            </div>
            {loading || !data ? (
              <Skeleton className="h-[220px] w-full" />
            ) : (
              <FrontierChart
                frontier={data.analysis.efficient_frontier.frontier.map((p) => ({
                  volatility: p.volatility_annualized,
                  ret: p.expected_return_annualized,
                  sharpe: p.sharpe_ratio,
                }))}
                current={{
                  volatility: data.analysis.efficient_frontier.current_portfolio.volatility_annualized,
                  ret: data.analysis.efficient_frontier.current_portfolio.expected_return_annualized,
                  sharpe: data.analysis.efficient_frontier.current_portfolio.sharpe_ratio,
                }}
                gmv={{
                  volatility: data.analysis.efficient_frontier.global_min_variance.volatility_annualized,
                  ret: data.analysis.efficient_frontier.global_min_variance.expected_return_annualized,
                  sharpe: data.analysis.efficient_frontier.global_min_variance.sharpe_ratio,
                }}
                maxSharpe={
                  data.analysis.efficient_frontier.max_sharpe
                    ? {
                        volatility: data.analysis.efficient_frontier.max_sharpe.volatility_annualized,
                        ret: data.analysis.efficient_frontier.max_sharpe.expected_return_annualized,
                        sharpe: data.analysis.efficient_frontier.max_sharpe.sharpe_ratio,
                      }
                    : null
                }
              />
            )}
            {data ? (
              <div className="mt-2 border-t pt-3 font-mono">
                <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
                  <span className="text-primary text-[22px] font-semibold">
                    CAPM β {fmtNum(data.analysis.capm.beta.estimate, 2)}
                  </span>
                  <span className="text-muted-foreground text-[13px]">
                    R² {fmtPct(data.analysis.capm.r_squared, 1)} · AAPL/MSFT/GOOGL/AMZN vs. S&amp;P 500
                  </span>
                </div>
                <div className="text-muted-foreground/70 mt-1.5 text-[9.5px] tracking-wide uppercase">
                  Source: OpenBB (yfinance) · Kenneth French Data Library
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <div className="mt-10 grid grid-cols-1 gap-3.5 sm:grid-cols-3">
        <MethodCard
          icon={Target}
          mark="CAPM"
          title="Market beta"
          body="Single-factor exposure to your chosen benchmark, with confidence intervals and significance."
        />
        <MethodCard
          icon={Layers}
          mark="Fama-French"
          title="Factor loadings"
          body="3- or 5-factor exposure (market, size, value, and optionally profitability/investment)."
        />
        <MethodCard
          icon={LineChartIcon}
          mark="Markowitz"
          title="Efficient frontier"
          body="Where your as-entered portfolio sits against the modeled long-only efficient set."
        />
      </div>

      <p className="text-muted-foreground mt-8 border-t pt-4 text-[12px] leading-relaxed">
        Computed live from OpenBB (yfinance provider) equity/benchmark prices and Kenneth French's Data Library
        factor series — see Tools &amp; Technologies for the full stack, and References &amp; Formulas for the
        exact math, formula-by-formula, with sources — Built by Ethan Verduzco.
      </p>
    </div>
  )
}

function MethodCard({ icon: Icon, mark, title, body }: { icon: LucideIcon; mark: string; title: string; body: string }) {
  return (
    <div className="bg-background rounded-lg border p-4">
      <div className="text-muted-foreground flex items-center gap-1.5 font-mono text-[10.5px] tracking-wide uppercase">
        <Icon className="text-primary size-3.5" />
        {mark}
      </div>
      <h3 className="font-display mt-1.5 mb-1 text-[15px] font-medium">{title}</h3>
      <p className="text-muted-foreground text-[12.5px] leading-relaxed">{body}</p>
    </div>
  )
}

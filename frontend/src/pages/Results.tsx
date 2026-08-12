import { useMemo } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty"
import { SectionHeader } from "@/components/SectionHeader"
import { InterpretationSection } from "@/components/InterpretationSection"
import { StatTile, StatRow } from "@/components/StatTile"
import { DivergingBarChart, type DivergingBarRow } from "@/components/charts/DivergingBarChart"
import { FrontierChart } from "@/components/charts/FrontierChart"
import { RiskSplitBar } from "@/components/charts/RiskSplitBar"
import { TableViewTwin } from "@/components/TableViewTwin"
import { RevealSection } from "@/components/RevealSection"
import { useAnalysis } from "@/hooks/use-analysis"
import { parseResultsSearchParams, resultsConfigToRequestBody } from "@/lib/query"
import { factorLabel, fmtBps, fmtNum, fmtPct, fmtPvalue, fmtRatio, significanceNote } from "@/lib/format"
import { AlertTriangle, ArrowRight, Copy, Info, Printer } from "lucide-react"

export function Results() {
  const [searchParams] = useSearchParams()
  const config = useMemo(() => parseResultsSearchParams(searchParams), [searchParams])
  const body = config ? resultsConfigToRequestBody(config) : null
  const { data, error, loading } = useAnalysis(body)

  if (!config) {
    return (
      <div>
        <SectionHeader path="/results" eyebrow="Results" title="Results" />
        <Empty className="border">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <Info />
            </EmptyMedia>
            <EmptyTitle>No analysis yet</EmptyTitle>
            <EmptyDescription>
              Enter holdings and a benchmark on the Inputs tab and run the analysis to see CAPM beta, Fama-French
              factor loadings, the efficient frontier, and a return/risk attribution breakdown here.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button asChild>
              <Link to="/inputs">
                Go to Inputs <ArrowRight className="size-4" />
              </Link>
            </Button>
          </EmptyContent>
        </Empty>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <SectionHeader path="/results" eyebrow="Results" title="Results" />
        <Empty className="border-destructive/40 border">
          <EmptyHeader>
            <EmptyMedia variant="icon" className="bg-destructive/10 text-destructive">
              <AlertTriangle />
            </EmptyMedia>
            <EmptyTitle>Could not run this analysis</EmptyTitle>
            <EmptyDescription>{error}</EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Button asChild variant="outline">
              <Link to="/inputs">Back to Inputs</Link>
            </Button>
          </EmptyContent>
        </Empty>
      </div>
    )
  }

  if (loading || !data) {
    return (
      <div>
        <SectionHeader path="/results" eyebrow="Results" title="Attribution results" />
        <div className="flex flex-col gap-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    )
  }

  const { meta, analysis, return_attribution, risk_attribution, interpretation } = data
  const holdingsStr = meta.holdings.map((h) => `${h.symbol} ${fmtPct(h.weight, 1)}`).join(", ")
  const shareUrl = typeof window !== "undefined" ? window.location.href : ""

  const capm = analysis.capm
  const ff = analysis.factor_model
  const ef = analysis.efficient_frontier
  const cp = ef.current_portfolio

  const loadingRows: DivergingBarRow[] = ff.factor_loadings.map((c) => ({
    name: c.name,
    label: factorLabel(c.name),
    value: c.estimate,
    stdError: c.std_error,
    tStat: c.t_stat,
    pValue: c.p_value,
    ciLower: c.ci_lower_95,
    ciUpper: c.ci_upper_95,
  }))

  const contribRows: DivergingBarRow[] = return_attribution.contributions.map((c) => ({
    name: c.name,
    label: c.label,
    value: c.contribution_periodic,
  }))

  const frontierIsDegenerate = ef.frontier.length === 0 || (() => {
    const vols = ef.frontier.map((p) => p.volatility_annualized)
    return Math.max(...vols) - Math.min(...vols) < 1e-6
  })()

  const gap = cp.return_gap_to_frontier
  const gapSub = cp.is_on_frontier
    ? "your portfolio is (numerically) on the modeled frontier for its return level"
    : gap !== null
      ? `the frontier offers ${fmtPct(gap, 2)} more return at your volatility level`
      : "outside the computed frontier's volatility range"

  return (
    <div>
      <SectionHeader path="/results" eyebrow="Results" title="Attribution results" />

      <div className="border-l-primary bg-card mb-4 rounded-lg border border-l-2 p-4 text-[12.5px] leading-relaxed">
        <div>
          <strong className="font-mono text-[12px]">Portfolio:</strong> {holdingsStr} &nbsp;·&nbsp;{" "}
          <strong className="font-mono text-[12px]">Benchmark:</strong> {meta.benchmark} &nbsp;·&nbsp;{" "}
          <strong className="font-mono text-[12px]">Model:</strong> Fama-French {meta.factor_model}-factor, {meta.frequency}
        </div>
        <div className="text-muted-foreground mt-1">
          <strong className="text-foreground font-mono text-[12px]">Data as of:</strong> {meta.aligned_start_date} to{" "}
          {meta.aligned_end_date} ({meta.n_periods} {meta.frequency} observations; requested {meta.requested_start_date} to{" "}
          {meta.requested_end_date}) &nbsp;·&nbsp; Sources: {meta.equity_provider}; {meta.factor_provider} &nbsp;·&nbsp;
          Standard errors: {capm.standard_error_convention}
        </div>
        <div className="text-muted-foreground mt-2 text-[12px]">
          Internal decision-support analytics only. This is not investment advice, not a recommendation to buy,
          sell, or rebalance, and not a signal of any kind.
        </div>
      </div>

      <InterpretationSection interpretation={interpretation} />

      <div className="bg-muted/40 mb-5 flex flex-wrap items-center gap-2.5 rounded-lg border p-3">
        <span className="text-muted-foreground font-mono text-[10.5px] tracking-wide uppercase">Share this result</span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            navigator.clipboard?.writeText(shareUrl)
            toast.success("Shareable link copied")
          }}
        >
          <Copy className="size-3.5" /> Copy shareable link
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={() => window.print()}>
          <Printer className="size-3.5" /> Export as PDF
        </Button>
      </div>

      <RevealSection>
        <div className="text-muted-foreground mt-8 mb-3 border-b pb-2 font-mono text-[11px] tracking-wide uppercase">
          1. Factor exposure
        </div>
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>CAPM beta vs. {capm.benchmark}</CardTitle>
            <p className="text-muted-foreground text-[13px]">
              Single-factor market exposure and its statistical diagnostics — not a bare point estimate.
            </p>
          </CardHeader>
          <CardContent>
            <StatRow>
              <StatTile
                label={`CAPM beta vs ${capm.benchmark}`}
                value={fmtNum(capm.beta.estimate, 2)}
                numericValue={capm.beta.estimate}
                format={(n) => fmtNum(n, 2)}
                sub={`95% CI [${fmtNum(capm.beta.ci_lower_95, 2)}, ${fmtNum(capm.beta.ci_upper_95, 2)}] · t=${fmtNum(capm.beta.t_stat, 2)}, p=${fmtPvalue(capm.beta.p_value)}`}
              />
              <StatTile
                label="CAPM alpha (annualized)"
                value={fmtPct(capm.alpha_annualized, 2, true)}
                sub={`periodic t=${fmtNum(capm.alpha.t_stat, 2)}, p=${fmtPvalue(capm.alpha.p_value)} (${significanceNote(capm.alpha.p_value)})`}
              />
              <StatTile label="CAPM R²" value={fmtPct(capm.r_squared, 1)} sub={`n=${capm.n_obs} ${capm.frequency} obs`} />
            </StatRow>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Fama-French {ff.factor_model}-factor loadings</CardTitle>
            <p className="text-muted-foreground text-[13px]">
              Exposure to each factor, with a 95% confidence-interval whisker under every bar.
            </p>
          </CardHeader>
          <CardContent>
            <DivergingBarChart rows={loadingRows} valueFormat={(v) => fmtNum(v, 2, true)} />
            <TableViewTwin
              headers={["Factor", "Loading", "Std. error", "t-stat", "p-value", "95% CI"]}
              rows={ff.factor_loadings.map((c) => [
                factorLabel(c.name),
                fmtNum(c.estimate, 3, true),
                fmtNum(c.std_error, 4),
                fmtNum(c.t_stat, 2),
                fmtPvalue(c.p_value),
                `[${fmtNum(c.ci_lower_95, 3)}, ${fmtNum(c.ci_upper_95, 3)}]`,
              ])}
            />
            <StatRow>
              <StatTile label="Fama-French alpha (annualized)" value={fmtPct(ff.alpha_annualized, 2, true)} />
              <StatTile label="Fama-French R²" value={fmtPct(ff.r_squared, 1)} sub={`adj. ${fmtPct(ff.adj_r_squared, 1)}`} />
              <StatTile label="F-statistic" value={fmtNum(ff.f_statistic, 1)} sub={`p=${fmtPvalue(ff.f_p_value)}, n=${ff.n_obs} ${ff.frequency} obs`} />
            </StatRow>
          </CardContent>
        </Card>
      </RevealSection>

      <RevealSection>
        <div className="text-muted-foreground mt-8 mb-3 border-b pb-2 font-mono text-[11px] tracking-wide uppercase">
          2. Efficient frontier
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Your portfolio vs. the modeled efficient frontier</CardTitle>
            <p className="text-muted-foreground text-[13px]">
              Long-only Markowitz frontier ({ef.n_obs} {ef.frequency} obs across {ef.symbols.length} holdings). This
              shows where your as-entered portfolio sits — it is not a rebalancing recommendation.
            </p>
          </CardHeader>
          <CardContent>
            {ef.covariance_regularized ? (
              <div className="bg-warning/10 border-warning/40 mb-3 flex gap-2 rounded-md border p-2.5 text-[12.5px]">
                <AlertTriangle className="text-warning size-4 flex-none" />
                Covariance matrix regularized (condition number {fmtNum(ef.covariance_condition_number, 1)}) — see
                the data-quality flag in Interpretation &amp; Key Takeaways above for why and what it means for this
                frontier.
              </div>
            ) : null}
            {frontierIsDegenerate ? (
              <div className="bg-chart-1/10 border-chart-1/40 mb-3 flex gap-2 rounded-md border p-2.5 text-[12.5px]">
                <Info className="text-chart-1 size-4 flex-none" />
                {ef.symbols.length < 2
                  ? "Efficient frontier requires 2+ distinct holdings — showing your single position only."
                  : "Your holdings' return/risk profiles are effectively identical, so there's no continuum of feasible portfolios to trace a frontier from — showing your position only."}
              </div>
            ) : (
              <FrontierChart
                frontier={ef.frontier.map((p) => ({ volatility: p.volatility_annualized, ret: p.expected_return_annualized, sharpe: p.sharpe_ratio }))}
                current={{ volatility: cp.volatility_annualized, ret: cp.expected_return_annualized, sharpe: cp.sharpe_ratio }}
                gmv={{
                  volatility: ef.global_min_variance.volatility_annualized,
                  ret: ef.global_min_variance.expected_return_annualized,
                  sharpe: ef.global_min_variance.sharpe_ratio,
                }}
                maxSharpe={
                  ef.max_sharpe
                    ? { volatility: ef.max_sharpe.volatility_annualized, ret: ef.max_sharpe.expected_return_annualized, sharpe: ef.max_sharpe.sharpe_ratio }
                    : null
                }
              />
            )}
            <StatRow>
              <StatTile label="Your annualized return" value={fmtPct(cp.expected_return_annualized, 2)} />
              <StatTile label="Your annualized volatility" value={fmtPct(cp.volatility_annualized, 2)} />
              <StatTile label="Your Sharpe ratio" value={fmtRatio(cp.sharpe_ratio)} />
              <StatTile label="Return gap at matched volatility" value={fmtPct(gap, 2, true)} sub={gapSub} />
            </StatRow>
            <TableViewTwin
              headers={["Point", "Volatility (ann.)", "Return (ann.)", "Sharpe"]}
              rows={[
                ["Your portfolio", fmtPct(cp.volatility_annualized, 2), fmtPct(cp.expected_return_annualized, 2), fmtRatio(cp.sharpe_ratio)],
                [
                  "Global min-variance",
                  fmtPct(ef.global_min_variance.volatility_annualized, 2),
                  fmtPct(ef.global_min_variance.expected_return_annualized, 2),
                  fmtRatio(ef.global_min_variance.sharpe_ratio),
                ],
                ...(ef.max_sharpe
                  ? [[
                      "Max Sharpe (tangency)",
                      fmtPct(ef.max_sharpe.volatility_annualized, 2),
                      fmtPct(ef.max_sharpe.expected_return_annualized, 2),
                      fmtRatio(ef.max_sharpe.sharpe_ratio),
                    ]]
                  : []),
                ...ef.frontier.map((p, i) => [
                  `Frontier point ${i + 1}`,
                  fmtPct(p.volatility_annualized, 2),
                  fmtPct(p.expected_return_annualized, 2),
                  fmtRatio(p.sharpe_ratio),
                ]),
              ]}
            />
          </CardContent>
        </Card>
      </RevealSection>

      <RevealSection>
        <div className="text-muted-foreground mt-8 mb-3 border-b pb-2 font-mono text-[11px] tracking-wide uppercase">
          3. Return &amp; risk attribution
        </div>
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Return attribution</CardTitle>
            <p className="text-muted-foreground text-[13px]">
              Alpha plus each factor's own contribution — an exact decomposition of your realized mean per-
              {return_attribution.frequency} excess return, not an approximation. Values are per-period.
            </p>
          </CardHeader>
          <CardContent>
            <DivergingBarChart rows={contribRows} valueFormat={(v) => fmtBps(v, 1)} showCI={false} />
            <TableViewTwin
              headers={["Source", `Mean ${return_attribution.frequency} contribution`]}
              rows={[
                ...return_attribution.contributions.map((c) => [c.label, fmtBps(c.contribution_periodic, 2)]),
                ["Total (= realized mean excess return)", fmtBps(return_attribution.total_periodic, 2)],
              ]}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Risk attribution</CardTitle>
            <p className="text-muted-foreground text-[13px]">
              Share of your portfolio's return variance the {ff.factor_model}-factor model explains (R²) vs.
              idiosyncratic.
            </p>
          </CardHeader>
          <CardContent>
            <div className="mb-2 flex gap-4 font-mono text-[12.5px]">
              <span className="text-chart-1">Factor-explained ({fmtPct(risk_attribution.factor_explained_share, 1)})</span>
              <span className="text-muted-foreground">Idiosyncratic ({fmtPct(risk_attribution.idiosyncratic_share, 1)})</span>
            </div>
            <RiskSplitBar factorExplained={risk_attribution.factor_explained_share} idiosyncratic={risk_attribution.idiosyncratic_share} />
            <p className="text-muted-foreground mt-3 text-[12.5px] leading-relaxed">
              Methodology note: per-period return contributions here use the compounding-vs-linear-scaling
              annualization split — they are deliberately left per-period rather than re-annualized piecewise.
            </p>
          </CardContent>
        </Card>
      </RevealSection>
    </div>
  )
}

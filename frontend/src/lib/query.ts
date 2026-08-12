import type { FactorModel, Frequency, PortfolioRequestBody } from "@/lib/types"

export interface HoldingFormRow {
  symbol: string
  weightPct: string
}

export interface ResultsConfig {
  holdings: { symbol: string; weightPct: number }[]
  benchmark: string
  startDate: string
  endDate: string
  factorModel: FactorModel
  frequency: Frequency
}

/** Builds the `/results?...` query string that is this app's shareable link
 * mechanism (decision 0017: "a real architectural specific" — URL state
 * replaces the old server-side `GET /dashboard/view` replay). */
export function buildResultsSearchParams(config: ResultsConfig): URLSearchParams {
  const params = new URLSearchParams()
  for (const h of config.holdings) {
    params.append("symbol", h.symbol)
    params.append("weight", String(h.weightPct))
  }
  params.set("benchmark", config.benchmark)
  params.set("start_date", config.startDate)
  params.set("end_date", config.endDate)
  params.set("factor_model", config.factorModel)
  params.set("frequency", config.frequency)
  return params
}

export function parseResultsSearchParams(searchParams: URLSearchParams): ResultsConfig | null {
  const symbols = searchParams.getAll("symbol")
  const weights = searchParams.getAll("weight")
  const benchmark = searchParams.get("benchmark")
  const startDate = searchParams.get("start_date")
  const endDate = searchParams.get("end_date")
  const factorModel = (searchParams.get("factor_model") ?? "3") as FactorModel
  const frequency = (searchParams.get("frequency") ?? "daily") as Frequency

  if (symbols.length === 0 || symbols.length !== weights.length || !benchmark || !startDate || !endDate) {
    return null
  }
  const holdings = symbols.map((symbol, i) => ({ symbol, weightPct: Number(weights[i]) }))
  if (holdings.some((h) => Number.isNaN(h.weightPct))) return null

  return { holdings, benchmark, startDate, endDate, factorModel, frequency }
}

export function resultsConfigToRequestBody(config: ResultsConfig): PortfolioRequestBody {
  return {
    holdings: config.holdings.map((h) => ({ symbol: h.symbol, weight: h.weightPct / 100 })),
    benchmark: config.benchmark,
    start_date: config.startDate,
    end_date: config.endDate,
    factor_model: config.factorModel,
    frequency: config.frequency,
  }
}

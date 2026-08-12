// Mirrors `app/schemas.py`, `app/models/schemas.py`, and `app/api/schemas.py`.
// Kept as one hand-written source of truth rather than a generated client --
// the API surface is small (3 endpoints) and stable.

export type FactorModel = "3" | "5"
export type Frequency = "daily" | "monthly"

export interface HoldingInput {
  symbol: string
  weight: number // fraction, 0 < w <= 1
}

export interface PortfolioRequestBody {
  holdings: HoldingInput[]
  benchmark: string
  start_date: string // YYYY-MM-DD
  end_date: string
  factor_model: FactorModel
  frequency: Frequency
}

export interface RequestMeta {
  holdings: HoldingInput[]
  benchmark: string
  factor_model: FactorModel
  frequency: Frequency
  requested_start_date: string
  requested_end_date: string
  aligned_start_date: string
  aligned_end_date: string
  n_periods: number
  equity_provider: string
  factor_provider: string
}

export interface RegressionCoefficient {
  name: string
  estimate: number
  std_error: number
  t_stat: number
  p_value: number
  ci_lower_95: number
  ci_upper_95: number
}

export interface CAPMResult {
  benchmark: string
  frequency: Frequency
  n_obs: number
  alpha: RegressionCoefficient
  beta: RegressionCoefficient
  alpha_annualized: number
  r_squared: number
  adj_r_squared: number
  residual_std_error: number
  standard_error_convention: string
}

export interface FactorModelResult {
  factor_model: FactorModel
  frequency: Frequency
  n_obs: number
  alpha: RegressionCoefficient
  factor_loadings: RegressionCoefficient[]
  alpha_annualized: number
  r_squared: number
  adj_r_squared: number
  residual_std_error: number
  standard_error_convention: string
  f_statistic: number
  f_p_value: number
}

export interface FrontierPoint {
  expected_return_annualized: number
  volatility_annualized: number
  weights: Record<string, number>
  sharpe_ratio: number | null
}

export interface PortfolioPosition {
  expected_return_annualized: number
  volatility_annualized: number
  sharpe_ratio: number | null
  weights: Record<string, number>
  frontier_return_at_same_volatility: number | null
  return_gap_to_frontier: number | null
  is_on_frontier: boolean
}

export interface EfficientFrontierResult {
  frequency: Frequency
  n_obs: number
  symbols: string[]
  allow_short_selling: boolean
  risk_free_rate_annualized: number
  covariance_regularized: boolean
  covariance_condition_number: number
  frontier: FrontierPoint[]
  global_min_variance: FrontierPoint
  max_sharpe: FrontierPoint | null
  current_portfolio: PortfolioPosition
}

export interface PortfolioAnalysis {
  capm: CAPMResult
  factor_model: FactorModelResult
  efficient_frontier: EfficientFrontierResult
}

export interface AttributionContribution {
  name: string
  label: string
  contribution_periodic: number
}

export interface ReturnAttribution {
  contributions: AttributionContribution[]
  total_periodic: number
  frequency: Frequency
}

export interface RiskAttribution {
  factor_explained_share: number
  idiosyncratic_share: number
  r_squared_raw: number
}

export interface InterpretationTakeaway {
  id: "beta" | "style_tilt" | "explanatory_power" | "frontier_position"
  title: string
  body: string
  is_headline: boolean
}

export interface InterpretationFlag {
  id: "covariance_regularized" | "short_data_window"
  severity: "info" | "warning"
  message: string
}

export interface Interpretation {
  headline: string
  takeaways: InterpretationTakeaway[]
  flags: InterpretationFlag[]
}

export interface AnalysisResponse {
  meta: RequestMeta
  analysis: PortfolioAnalysis
  return_attribution: ReturnAttribution
  risk_attribution: RiskAttribution
  interpretation: Interpretation
}

export interface TickerInfo {
  symbol: string
  name: string
  sector: string
}

export interface BenchmarkInfo {
  symbol: string
  name: string
}

export interface TickerUniverseResponse {
  tickers: TickerInfo[]
  benchmarks: BenchmarkInfo[]
  source_note: string
}

export interface SampleHolding {
  symbol: string
  weight_pct: number
}

export interface SamplePortfolioResponse {
  holdings: SampleHolding[]
  benchmark: string
  start_date: string
  end_date: string
  factor_model: FactorModel
  frequency: Frequency
}

export interface ApiErrorBody {
  detail: string
}

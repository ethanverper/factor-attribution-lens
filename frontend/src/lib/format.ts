// Number formatting, ported 1:1 from the removed `app/dashboard/viz.py`'s
// `fmt_*` helpers (same rounding/sign/dash conventions).

export function fmtPct(x: number | null | undefined, decimals = 2, signed = false): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—"
  const sign = signed && x > 0 ? "+" : ""
  return `${sign}${(x * 100).toFixed(decimals)}%`
}

export function fmtNum(x: number | null | undefined, decimals = 3, signed = false): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—"
  const sign = signed && x > 0 ? "+" : ""
  return `${sign}${x.toFixed(decimals)}`
}

export function fmtBps(x: number | null | undefined, decimals = 1, signed = true): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—"
  const sign = signed && x > 0 ? "+" : ""
  return `${sign}${(x * 10000).toFixed(decimals)} bps`
}

export function fmtRatio(x: number | null | undefined, decimals = 2): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—"
  return x.toFixed(decimals)
}

export function fmtPvalue(p: number): string {
  if (p < 0.001) return "<0.001"
  return p.toFixed(3)
}

/** "p<0.001" / "p=0.023" — use in place of a literal "p=" prefix, which
 * produces the wrong "p=<0.001" reading once fmtPvalue's own "<" kicks in. */
export function pvalueLabel(p: number): string {
  return `p${p < 0.001 ? "<" : "="}${fmtPvalue(p)}`
}

export function significanceNote(p: number): string {
  return p < 0.05 ? "significant at 95% (p<0.05)" : "not significant at 95% (p≥0.05)"
}

export const FACTOR_LABELS: Record<string, string> = {
  alpha: "Alpha (unexplained)",
  mkt_rf: "Market (Mkt-RF)",
  smb: "Size (SMB)",
  hml: "Value (HML)",
  rmw: "Profitability (RMW)",
  cma: "Investment (CMA)",
}

export function factorLabel(name: string): string {
  return FACTOR_LABELS[name] ?? name
}

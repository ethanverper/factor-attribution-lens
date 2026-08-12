"""Interpretation & Key Takeaways -- synthesis logic for Phase 10k/10m.

This is the content spec from `docs/decisions/0019-phase10k-interpretation-content.md`
implemented directly, thresholds and template text included. It mirrors
`attribution.py`'s shape exactly: a pure function of the already-computed
`PortfolioAnalysis` in, plain dataclasses out, no new fields on
`app/models/schemas.py`'s stable Phase 2 contract, and no I/O of its own.

Every judgment call (what counts as "wide", "material", "large") is a named
module-level constant so it is visible and independently checkable, not
buried inline -- exactly the point of writing this as an implementable rule
set rather than generic narrative text.

Every template string here was written, then re-read against the standing
hard limit (`docs/project-standards.md` rule 9a): does this explain a
pattern/implication, or does it tell the reader what to do with their money?
Only the former is permitted. See `tests/test_interpretation.py` for the
guardrail test asserting no advice-coded language appears in any generated
output, and decision 0019 section 7 for the sentence-by-sentence compliance
read this module's text was checked against.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import EfficientFrontierResult, PortfolioAnalysis, RegressionCoefficient

# --- Thresholds (decision 0019 section 2) -----------------------------------

R2_VERY_LOW = 0.15
R2_MATERIAL_LIFT = 0.03
BETA_CI_WIDTH_TIGHT = 0.30
BETA_CI_WIDTH_WIDE = 0.60
STYLE_LOADING_MATERIAL = 0.30
FRONTIER_GAP_NEGLIGIBLE = 0.02
FRONTIER_GAP_LARGE = 0.08
SHORT_WINDOW_OBS = {"daily": 60, "monthly": 24}
COV_REG_THIN_DATA_RATIO = 20

# (label if loading positive, label if loading negative)
FACTOR_TILT_LABELS: dict[str, tuple[str, str]] = {
    "smb": ("small-cap", "large-cap"),
    "hml": ("value", "growth"),
    "rmw": ("high-profitability / quality", "low-profitability"),
    "cma": ("conservative-investment", "aggressive-investment"),
}

# Direction-neutral concept word for a factor, used when a loading is *not*
# significant (there is no direction to report, only "no signal detected").
FACTOR_ROOT_LABELS: dict[str, str] = {
    "smb": "size",
    "hml": "value/growth",
    "rmw": "profitability",
    "cma": "investment",
}

# Same display names `app/api/attribution.py::FACTOR_LABELS` already uses,
# duplicated here rather than imported so this module has no dependency on
# the presentation-layer attribution module -- both are pure functions of
# Phase 2 output, neither should depend on the other.
FACTOR_LABELS: dict[str, str] = {
    "mkt_rf": "Market (Mkt-RF)",
    "smb": "Size (SMB)",
    "hml": "Value (HML)",
    "rmw": "Profitability (RMW)",
    "cma": "Investment (CMA)",
}

_FACTOR_ORDER = ("smb", "hml", "rmw", "cma")

TakeawayId = str  # "beta" | "style_tilt" | "explanatory_power" | "frontier_position"
FlagId = str  # "covariance_regularized" | "short_data_window"


@dataclass(frozen=True)
class Takeaway:
    id: TakeawayId
    title: str
    body: str
    is_headline: bool


@dataclass(frozen=True)
class Flag:
    id: FlagId
    severity: str  # "info" | "warning"
    message: str


@dataclass(frozen=True)
class Interpretation:
    headline: str
    takeaways: list[Takeaway]
    flags: list[Flag]


def compute_interpretation(analysis: PortfolioAnalysis) -> Interpretation:
    capm = analysis.capm
    ff = analysis.factor_model
    ef = analysis.efficient_frontier

    beta = capm.beta
    significant_vs_zero = _significant(beta)
    distinguishable_from_market = not (beta.ci_lower_95 <= 1.0 <= beta.ci_upper_95)

    non_market = [loading for loading in ff.factor_loadings if loading.name != "mkt_rf"]
    significant_loadings = [loading for loading in non_market if _significant(loading)]
    material_significant = [
        loading for loading in significant_loadings if abs(loading.estimate) >= STYLE_LOADING_MATERIAL
    ]

    degenerate = _is_degenerate(ef)
    gap = None if degenerate else ef.current_portfolio.return_gap_to_frontier

    headline_id, headline_text = _select_headline(
        capm_r_squared=capm.r_squared,
        beta=beta,
        significant_vs_zero=significant_vs_zero,
        distinguishable_from_market=distinguishable_from_market,
        material_significant=material_significant,
        gap=gap,
        benchmark=capm.benchmark,
    )

    takeaways = [
        Takeaway(
            id="beta",
            title="Market sensitivity (beta)",
            body=_beta_body(beta, capm.benchmark, capm.n_obs, capm.frequency, significant_vs_zero, distinguishable_from_market),
            is_headline=headline_id == "beta",
        ),
        Takeaway(
            id="style_tilt",
            title="Style tilt",
            body=_style_tilt_body(ff, capm, non_market, significant_loadings),
            is_headline=headline_id == "style_tilt",
        ),
        Takeaway(
            id="explanatory_power",
            title="Explanatory power",
            body=_explanatory_power_body(capm, ff),
            is_headline=headline_id == "explanatory_power",
        ),
        Takeaway(
            id="frontier_position",
            title="Frontier position",
            body=_frontier_position_body(ef, degenerate, gap),
            is_headline=headline_id == "frontier_position",
        ),
    ]

    flags = _compute_flags(capm, ff, ef)

    return Interpretation(headline=headline_text, takeaways=takeaways, flags=flags)


# --- Shared helpers -----------------------------------------------------


def _significant(coef: RegressionCoefficient) -> bool:
    return coef.ci_lower_95 > 0 or coef.ci_upper_95 < 0


def _fmt_p(p: float) -> str:
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def _is_degenerate(ef: EfficientFrontierResult) -> bool:
    if len(ef.symbols) < 2:
        return True
    if not ef.frontier:
        return True
    vols = [point.volatility_annualized for point in ef.frontier]
    return (max(vols) - min(vols)) < 1e-6


def _style_words_slash(factor_model: str) -> str:
    return "size/value" + ("/profitability/investment" if factor_model == "5" else "")


def _style_words_comma(factor_model: str) -> str:
    return "size/value" + (", profitability, investment" if factor_model == "5" else "")


# --- 3a. beta -------------------------------------------------------------


def _beta_body(
    beta: RegressionCoefficient,
    benchmark: str,
    n_obs: int,
    frequency: str,
    significant_vs_zero: bool,
    distinguishable_from_market: bool,
) -> str:
    lo, hi, estimate = beta.ci_lower_95, beta.ci_upper_95, beta.estimate
    if not significant_vs_zero:
        return (
            f"The 95% confidence interval for beta ([{lo:.2f}, {hi:.2f}]) includes zero — at this window's sample "
            f"size ({n_obs} {frequency} observations), the data cannot rule out that this portfolio has no "
            f"reliable linear relationship with {benchmark} at all. Read the point estimate ({estimate:.2f}) as "
            f"suggestive, not established."
        )

    width = hi - lo
    clause1 = (
        f"Beta is statistically distinguishable from zero (t={beta.t_stat:.2f}, p={_fmt_p(beta.p_value)}) — "
        f"there is real, measurable co-movement with {benchmark}."
    )
    if width < BETA_CI_WIDTH_TIGHT:
        clause2 = (
            f"The interval is narrow (width {width:.2f}), so {estimate:.2f} is a reasonably precise read of this "
            f"portfolio's market sensitivity over this window."
        )
    elif width >= BETA_CI_WIDTH_WIDE:
        clause2 = (
            f"The interval is wide (width {width:.2f}) relative to the point estimate — {estimate:.2f} is this "
            f"window's best estimate, but the data doesn't pin down market sensitivity tightly; a longer window "
            f"would narrow this."
        )
    else:
        clause2 = (
            f"The interval (width {width:.2f}) is moderate — treat {estimate:.2f} as a reasonable central "
            f"estimate, but true market sensitivity could plausibly sit noticeably higher or lower."
        )
    if distinguishable_from_market:
        clause3 = (
            f"It's also statistically distinguishable from beta = 1 — this portfolio's market sensitivity is "
            f"genuinely different from simply holding {benchmark} itself, not just noisier."
        )
    else:
        clause3 = (
            f"The interval also includes 1.0, so beta isn't statistically distinguishable from moving in lockstep "
            f"with {benchmark} either."
        )
    return f"{clause1} {clause2} {clause3}"


# --- 3b. style_tilt ---------------------------------------------------------


def _style_tilt_body(
    ff, capm, non_market: list[RegressionCoefficient], significant_loadings: list[RegressionCoefficient]
) -> str:
    if not significant_loadings:
        names = ", ".join(FACTOR_LABELS.get(loading.name, loading.name) for loading in non_market)
        return (
            f"None of the non-market factors ({names}) are statistically distinguishable from zero at the 95% "
            f"level. This portfolio's behavior is explained by broad market exposure, not a detectable "
            f"{_style_words_slash(ff.factor_model)} tilt — whatever style characteristics these holdings have "
            f"individually, they don't show up as a statistically reliable factor exposure over this window."
        )

    ordered = [loading for name in _FACTOR_ORDER for loading in non_market if loading.name == name]
    clauses = [_factor_clause(loading, loading in significant_loadings) for loading in ordered]

    sig_ordered = [loading for loading in ordered if loading in significant_loadings]
    if len(sig_ordered) == 1:
        closing = (
            f"With only {len(sig_ordered)}/{len(non_market)} non-market factors clearing the 95% bar, "
            f"{_axis_phrase(sig_ordered[0])} is this portfolio's one statistically reliable style signal beyond "
            f"overall market exposure."
        )
    else:
        phrases = ", ".join(_axis_phrase(loading) for loading in sig_ordered[:-1])
        phrases = f"{phrases} and {_axis_phrase(sig_ordered[-1])}" if phrases else _axis_phrase(sig_ordered[-1])
        closing = (
            f"With {len(sig_ordered)}/{len(non_market)} non-market factors clearing the 95% bar, {phrases} are "
            f"this portfolio's statistically reliable style signals beyond overall market exposure."
        )
    clauses.append(closing)

    divergence = _mkt_rf_divergence_note(ff, capm)
    if divergence:
        clauses.append(divergence)

    return " ".join(clauses)


def _factor_clause(loading: RegressionCoefficient, significant: bool) -> str:
    name = FACTOR_LABELS.get(loading.name, loading.name)
    lo, hi, estimate = loading.ci_lower_95, loading.ci_upper_95, loading.estimate
    tilt_pair = FACTOR_TILT_LABELS.get(loading.name, (loading.name, loading.name))
    tilt_word = tilt_pair[0] if estimate > 0 else tilt_pair[1]
    if significant:
        return (
            f"{name} loading is {estimate:.2f} (95% CI [{lo:.2f}, {hi:.2f}]), excluding zero — a statistically "
            f"real {tilt_word} tilt."
        )
    root = FACTOR_ROOT_LABELS.get(loading.name, loading.name)
    if 0.05 <= loading.p_value < 0.10:
        reason = (
            f"falls just short of the 95% bar (p={loading.p_value:.3f}) — a possible {tilt_word} lean, not confirmed"
        )
    else:
        reason = f"is not statistically distinguishable from zero — no reliable {root} signal detected"
    return f"{name} ({estimate:.2f}, 95% CI [{lo:.2f}, {hi:.2f}]) {reason}."


def _axis_phrase(loading: RegressionCoefficient) -> str:
    tilt_pair = FACTOR_TILT_LABELS.get(loading.name, (loading.name, loading.name))
    tilt_word, other_word = (tilt_pair[0], tilt_pair[1]) if loading.estimate > 0 else (tilt_pair[1], tilt_pair[0])
    return f"{tilt_word}-vs-{other_word} positioning"


def _mkt_rf_divergence_note(ff, capm) -> str | None:
    mkt_rf = next((loading for loading in ff.factor_loadings if loading.name == "mkt_rf"), None)
    if mkt_rf is None:
        return None
    if abs(mkt_rf.estimate - capm.beta.estimate) <= 0.10:
        return None
    return (
        f"Note: the market loading estimated jointly with the other factors ({mkt_rf.estimate:.2f}) differs from "
        f"the plain CAPM beta ({capm.beta.estimate:.2f}) — expected when, as here, one of the other factors' "
        f"returns correlates with the market's own over this window."
    )


# --- 3c. explanatory_power ---------------------------------------------


def _bucket_r2(r2: float) -> str:
    if r2 < 0.15:
        return "very low"
    if r2 < 0.30:
        return "low"
    if r2 < 0.60:
        return "moderate"
    if r2 < 0.85:
        return "high"
    return "very high"


def _explanatory_power_body(capm, ff) -> str:
    r2 = capm.r_squared
    incremental = ff.r_squared - r2

    clause1 = (
        f"The single-factor CAPM model explains {r2:.1%} of this portfolio's return variance "
        f"({_bucket_r2(r2)} for an equity portfolio) — the remaining {1 - r2:.1%} is idiosyncratic (stock-specific) "
        f"movement the market factor alone doesn't capture."
    )

    style_comma = _style_words_comma(ff.factor_model)
    if incremental >= R2_MATERIAL_LIFT:
        prefix = "a modest absolute lift, but proportionally large: " if r2 < R2_VERY_LOW else ""
        clause2 = (
            f"Adding {style_comma} lifts explained variance to {ff.r_squared:.1%} (adjusted {ff.adj_r_squared:.1%}) "
            f"— {prefix}a real, {incremental:.1%}-point improvement attributable to those style factors, not the "
            f"market alone."
        )
    else:
        clause2 = (
            f"Adding {style_comma} only lifts explained variance to {ff.r_squared:.1%} — a marginal "
            f"{incremental:.1%}-point improvement; most of what these factors could explain, the market factor "
            f"alone already captured."
        )

    if ff.f_p_value < 0.05:
        suffix = (
            ", even where R² itself is low — a genuine but small relationship, not noise" if ff.r_squared < R2_VERY_LOW else ""
        )
        clause3 = (
            f"The joint F-test (F={ff.f_statistic:.1f}, p={_fmt_p(ff.f_p_value)}) confirms the factor model as a "
            f"whole explains statistically real variance{suffix}."
        )
    else:
        clause3 = (
            f"The joint F-test does not clear the conventional 5% bar (p={_fmt_p(ff.f_p_value)}) — treat the "
            f"whole factor-model fit, not just the individual loadings above, cautiously here."
        )

    return f"{clause1} {clause2} {clause3}"


# --- 3d. frontier_position -----------------------------------------------


def _frontier_position_body(ef: EfficientFrontierResult, degenerate: bool, gap: float | None) -> str:
    cp = ef.current_portfolio
    n = len(ef.symbols)

    if degenerate:
        reason = (
            "only one holding"
            if n < 2
            else "holdings whose historical return/risk profiles are effectively identical"
        )
        return (
            f"With {reason}, there's no meaningful spread of alternative portfolios to compare against — a "
            f"frontier comparison isn't informative here."
        )

    if gap is None:
        return (
            f"This portfolio's volatility ({cp.volatility_annualized:.1%}) falls outside the range the modeled "
            f"frontier covers for this holding set ({ef.n_obs} observations, {n} holdings), so a same-volatility "
            f"return comparison isn't available."
        )

    if cp.is_on_frontier or gap <= 0:
        return (
            f"This portfolio's specific weighting is numerically on the modeled frontier for its return level — "
            f"among all long-only re-weightings of exactly these {n} holdings, none would have delivered more "
            f"return at this same risk level, historically."
        )

    if gap < FRONTIER_GAP_NEGLIGIBLE:
        return (
            f"The gap to the frontier is small ({gap:.1%}) — small enough to be within the range explainable by "
            f"estimation noise over a {ef.n_obs}-observation window, not a structurally meaningful mismatch "
            f"between these weights and this holding set's own risk/return relationships."
        )

    lead_in = (
        f"At this portfolio's volatility ({cp.volatility_annualized:.1%}), the modeled frontier's return is "
        f"{cp.frontier_return_at_same_volatility:.1%} versus this portfolio's realized "
        f"{cp.expected_return_annualized:.1%} — a {gap:.1%}-point gap"
    )
    if gap < FRONTIER_GAP_LARGE:
        return (
            f"{lead_in}. That's moderate: some of the historical return/risk relationship among just these {n} "
            f"holdings wasn't captured by this specific weighting, without being a dramatic mismatch."
        )

    return (
        f"{lead_in} — large by this analysis's own standard. Historically, some combination of these same {n} "
        f"holdings, long-only, could have delivered meaningfully more return for the same volatility (or the "
        f"same return for meaningfully less volatility) than the as-entered weights — not a suggestion to "
        f"reweight, and not a signal to act on, just a description of the historical relationship among the "
        f"holdings you entered."
    )


# --- 4. Headline selection ------------------------------------------------


def _select_headline(
    *,
    capm_r_squared: float,
    beta: RegressionCoefficient,
    significant_vs_zero: bool,
    distinguishable_from_market: bool,
    material_significant: list[RegressionCoefficient],
    gap: float | None,
    benchmark: str,
) -> tuple[str, str]:
    if capm_r_squared < R2_VERY_LOW:
        text = (
            f"Despite being built from individual equities, this portfolio's returns are only weakly explained "
            f"by {benchmark} — R² of {capm_r_squared:.1%} means the benchmark's own moves account for only about "
            f"{capm_r_squared:.0%} of this portfolio's return variance; the rest comes from something other than "
            f"broad market direction."
        )
        return "explanatory_power", text

    if significant_vs_zero and distinguishable_from_market:
        estimate, lo, hi = beta.estimate, beta.ci_lower_95, beta.ci_upper_95
        direction = "more" if estimate > 1 else "less"
        text = (
            f"This portfolio's market sensitivity (beta {estimate:.2f}, 95% CI [{lo:.2f}, {hi:.2f}]) is "
            f"statistically distinguishable from both zero and from 1.0 — it moves {direction} than one-for-one "
            f"with {benchmark}, and that's a measured relationship, not just noise around beta = 1."
        )
        return "beta", text

    if material_significant:
        biggest = max(material_significant, key=lambda loading: abs(loading.estimate))
        name = FACTOR_LABELS.get(biggest.name, biggest.name)
        tilt_pair = FACTOR_TILT_LABELS.get(biggest.name, (biggest.name, biggest.name))
        tilt_word = tilt_pair[0] if biggest.estimate > 0 else tilt_pair[1]
        text = (
            f"This portfolio carries a statistically significant {tilt_word} tilt ({name} loading "
            f"{biggest.estimate:.2f}, 95% CI [{biggest.ci_lower_95:.2f}, {biggest.ci_upper_95:.2f}]) — a real, "
            f"measurable style exposure beyond plain market direction."
        )
        return "style_tilt", text

    if gap is not None and gap >= FRONTIER_GAP_LARGE:
        text = (
            f"At the volatility this portfolio is already carrying, the modeled frontier's historical return was "
            f"{gap:.1%} points higher — a gap this size (this analysis's own bar for 'large' is "
            f"{FRONTIER_GAP_LARGE:.0%}) means the specific combination of correlations and weights here left "
            f"real room on the table within just these holdings' own historical risk/return relationship."
        )
        return "frontier_position", text

    text = (
        f"Nothing here is statistically extreme: beta sits within range of {benchmark}-average risk (or isn't "
        f"reliably estimated as different), no individual style factor clears both significance and a material "
        f"magnitude, and this portfolio's realized return/risk sits close to what its own holdings' history "
        f"could support. That combination is itself the finding — a fairly plain, market-tracking allocation "
        f"with no strong, statistically detectable secondary bet."
    )
    return "explanatory_power", text


# --- 5. Flags ---------------------------------------------------------------


def _compute_flags(capm, ff, ef: EfficientFrontierResult) -> list[Flag]:
    flags: list[Flag] = []

    if ef.covariance_regularized:
        n_symbols = len(ef.symbols)
        ratio = ef.n_obs / n_symbols if n_symbols else 0
        likely_cause = (
            "the data window is short relative to the number of holdings"
            if ratio < COV_REG_THIN_DATA_RATIO
            else "these holdings move in an unusually tightly correlated way (e.g. near-duplicate exposures or "
            "single-sector concentration)"
        )
        flags.append(
            Flag(
                id="covariance_regularized",
                severity="warning",
                message=(
                    f"The covariance matrix for these {n_symbols} holdings needed regularization (condition "
                    f"number {ef.covariance_condition_number:.1e}) before the frontier could be computed — "
                    f"likely because {likely_cause}. Read the frontier comparison above as indicative, not "
                    f"precise."
                ),
            )
        )

    frequency = capm.frequency
    threshold = SHORT_WINDOW_OBS.get(frequency)
    min_n = min(capm.n_obs, ff.n_obs, ef.n_obs)
    if threshold is not None and min_n < threshold:
        flags.append(
            Flag(
                id="short_data_window",
                severity="info",
                message=(
                    f"This analysis rests on {min_n} {frequency} observations — thinner than this analysis's own "
                    f"bar for an ample sample ({threshold}). All estimates above should be read as provisional; "
                    f"a longer window is what would narrow the confidence intervals."
                ),
            )
        )

    return flags

"""Unit tests for `app/api/interpretation.py` (decision 0019 / Phase 10m).

Live-data spot checks against the three worked examples in decision 0019
were run manually during implementation and matched (branch selection and
sentence structure; exact numbers drift with the trading calendar, as the
decision doc itself anticipates). These tests instead build synthetic
`PortfolioAnalysis` fixtures so every conditional branch -- including ones
decision 0019 itself flagged as hard or impossible to hit with real tickers
(`covariance_regularized`, the priority-5 "nothing stands out" headline) --
gets a real, deterministic, reference-value test rather than a live spot
check alone.
"""
from __future__ import annotations

import re

import pytest

from app.api.interpretation import (
    FRONTIER_GAP_LARGE,
    R2_VERY_LOW,
    compute_interpretation,
)
from app.models.schemas import (
    CAPMResult,
    EfficientFrontierResult,
    FactorModelResult,
    FrontierPoint,
    PortfolioAnalysis,
    PortfolioPosition,
    RegressionCoefficient,
)


def _coef(name: str, estimate: float, lo: float, hi: float, p_value: float = 0.01, t_stat: float = 3.0) -> RegressionCoefficient:
    return RegressionCoefficient(
        name=name, estimate=estimate, std_error=(hi - lo) / 4, t_stat=t_stat, p_value=p_value, ci_lower_95=lo, ci_upper_95=hi
    )


def _capm(beta_estimate=1.0, beta_lo=0.85, beta_hi=1.15, r_squared=0.5, n_obs=200, frequency="daily", benchmark="^GSPC") -> CAPMResult:
    return CAPMResult(
        benchmark=benchmark,
        frequency=frequency,
        n_obs=n_obs,
        alpha=_coef("alpha", 0.0001, -0.0005, 0.0007, p_value=0.6, t_stat=0.5),
        beta=_coef("mkt_rf", beta_estimate, beta_lo, beta_hi),
        alpha_annualized=0.02,
        r_squared=r_squared,
        adj_r_squared=r_squared - 0.01,
        residual_std_error=0.01,
        standard_error_convention="HAC (Newey-West)",
    )


def _ff(loadings: list[RegressionCoefficient], r_squared=0.55, adj_r_squared=0.54, f_statistic=20.0, f_p_value=0.001, n_obs=200, frequency="daily", factor_model="3") -> FactorModelResult:
    return FactorModelResult(
        factor_model=factor_model,
        frequency=frequency,
        n_obs=n_obs,
        alpha=_coef("alpha", 0.0001, -0.0005, 0.0007, p_value=0.6, t_stat=0.5),
        factor_loadings=loadings,
        alpha_annualized=0.02,
        r_squared=r_squared,
        adj_r_squared=adj_r_squared,
        residual_std_error=0.01,
        standard_error_convention="HAC (Newey-West)",
        f_statistic=f_statistic,
        f_p_value=f_p_value,
    )


def _point(vol: float, ret: float) -> FrontierPoint:
    return FrontierPoint(expected_return_annualized=ret, volatility_annualized=vol, weights={"A": 0.5, "B": 0.5}, sharpe_ratio=1.0)


def _ef(
    symbols=("AAPL", "MSFT"),
    frontier=None,
    gap=0.01,
    is_on_frontier=False,
    frontier_return_at_same_vol=0.20,
    portfolio_vol=0.15,
    portfolio_ret=0.19,
    covariance_regularized=False,
    condition_number=5.0,
    n_obs=200,
    frequency="daily",
) -> EfficientFrontierResult:
    if frontier is None:
        frontier = [_point(0.10, 0.15), _point(0.15, 0.20), _point(0.20, 0.24)]
    return EfficientFrontierResult(
        frequency=frequency,
        n_obs=n_obs,
        symbols=list(symbols),
        allow_short_selling=False,
        risk_free_rate_annualized=0.04,
        covariance_regularized=covariance_regularized,
        covariance_condition_number=condition_number,
        frontier=frontier,
        global_min_variance=_point(0.10, 0.14),
        max_sharpe=_point(0.16, 0.22),
        current_portfolio=PortfolioPosition(
            expected_return_annualized=portfolio_ret,
            volatility_annualized=portfolio_vol,
            sharpe_ratio=0.9,
            weights={s: 1 / len(symbols) for s in symbols},
            frontier_return_at_same_volatility=frontier_return_at_same_vol,
            return_gap_to_frontier=gap,
            is_on_frontier=is_on_frontier,
        ),
    )


def _analysis(capm=None, ff=None, ef=None) -> PortfolioAnalysis:
    return PortfolioAnalysis(
        capm=capm or _capm(),
        factor_model=ff
        or _ff(
            [
                _coef("mkt_rf", 0.9, 0.7, 1.1),
                _coef("smb", -0.1, -0.3, 0.1, p_value=0.3, t_stat=1.0),
                _coef("hml", 0.1, -0.1, 0.3, p_value=0.3, t_stat=1.0),
            ]
        ),
        efficient_frontier=ef or _ef(),
    )


def _base_ff_no_significant():
    return [
        _coef("mkt_rf", 0.9, 0.7, 1.1),
        _coef("smb", -0.1, -0.3, 0.1, p_value=0.3, t_stat=1.0),
        _coef("hml", 0.1, -0.1, 0.3, p_value=0.3, t_stat=1.0),
    ]


# --- Takeaway shape invariants -------------------------------------------


def test_always_four_takeaways_in_fixed_order():
    interp = compute_interpretation(_analysis())
    ids = [t.id for t in interp.takeaways]
    assert ids == ["beta", "style_tilt", "explanatory_power", "frontier_position"]


def test_exactly_one_takeaway_is_headline():
    interp = compute_interpretation(_analysis())
    headline_flags = [t.is_headline for t in interp.takeaways]
    assert sum(headline_flags) == 1


# --- 3a. beta ---------------------------------------------------------------


def test_beta_ci_includes_zero_gives_suggestive_only_body():
    analysis = _analysis(capm=_capm(beta_estimate=0.2, beta_lo=-0.1, beta_hi=0.5))
    body = compute_interpretation(analysis).takeaways[0].body
    assert "includes zero" in body
    assert "suggestive, not established" in body
    # The refining vs.-1.0 clause is explicitly skipped once significance vs. zero fails.
    assert "beta = 1" not in body and "lockstep" not in body


def test_beta_significant_tight_ci_and_includes_one():
    analysis = _analysis(capm=_capm(beta_estimate=1.0, beta_lo=0.9, beta_hi=1.1))
    body = compute_interpretation(analysis).takeaways[0].body
    assert "distinguishable from zero" in body
    assert "interval is narrow" in body
    assert "isn't statistically distinguishable from moving in lockstep" in body


def test_beta_significant_wide_ci_and_distinguishable_from_one():
    analysis = _analysis(capm=_capm(beta_estimate=1.8, beta_lo=1.3, beta_hi=2.2))
    body = compute_interpretation(analysis).takeaways[0].body
    assert "interval is wide" in body
    assert "genuinely different from simply holding" in body


def test_beta_moderate_ci_width():
    analysis = _analysis(capm=_capm(beta_estimate=1.0, beta_lo=0.75, beta_hi=1.2))  # width 0.45
    body = compute_interpretation(analysis).takeaways[0].body
    assert "is moderate" in body


# --- 3b. style_tilt ---------------------------------------------------------


def test_style_tilt_no_significant_factors():
    analysis = _analysis(ff=_ff(_base_ff_no_significant()))
    body = compute_interpretation(analysis).takeaways[1].body
    assert "None of the non-market factors" in body
    assert "not a detectable size/value tilt" in body


def test_style_tilt_five_factor_no_significant_lists_all_four_words():
    loadings = [
        _coef("mkt_rf", 0.9, 0.7, 1.1),
        _coef("smb", -0.05, -0.2, 0.1, p_value=0.4, t_stat=0.8),
        _coef("hml", 0.05, -0.15, 0.25, p_value=0.4, t_stat=0.8),
        _coef("rmw", 0.05, -0.15, 0.25, p_value=0.4, t_stat=0.8),
        _coef("cma", -0.05, -0.2, 0.1, p_value=0.4, t_stat=0.8),
    ]
    analysis = _analysis(ff=_ff(loadings, factor_model="5"))
    body = compute_interpretation(analysis).takeaways[1].body
    assert "not a detectable size/value/profitability/investment tilt" in body


def test_style_tilt_one_significant_factor_positive_value_and_divergence_note():
    loadings = [_coef("mkt_rf", 0.6, 0.4, 0.8), _coef("smb", 0.05, -0.15, 0.25, p_value=0.5, t_stat=0.7), _coef("hml", 0.4, 0.2, 0.6)]
    analysis = _analysis(capm=_capm(beta_estimate=1.0), ff=_ff(loadings))
    body = compute_interpretation(analysis).takeaways[1].body
    assert "a statistically real value tilt" in body
    assert "value-vs-growth positioning is this portfolio's one statistically reliable style signal" in body
    # |0.6 (mkt_rf loading) - 1.0 (capm beta)| = 0.4 > 0.10 -> divergence note fires.
    assert "differs from the plain CAPM beta" in body


def test_style_tilt_marginal_pvalue_gets_falls_short_language():
    loadings = [_coef("mkt_rf", 0.9, 0.7, 1.1), _coef("smb", 0.2, -0.02, 0.42, p_value=0.08, t_stat=1.7), _coef("hml", 0.35, 0.1, 0.6)]
    analysis = _analysis(ff=_ff(loadings))
    body = compute_interpretation(analysis).takeaways[1].body
    assert "falls just short of the 95% bar (p=0.080)" in body
    assert "a possible small-cap lean, not confirmed" in body


def test_style_tilt_two_significant_factors_joined_with_and():
    loadings = [_coef("mkt_rf", 0.9, 0.7, 1.1), _coef("smb", 0.4, 0.1, 0.7), _coef("hml", -0.4, -0.7, -0.1)]
    analysis = _analysis(ff=_ff(loadings))
    body = compute_interpretation(analysis).takeaways[1].body
    assert "style signals beyond overall market exposure" in body
    assert " and " in body


def test_style_tilt_no_divergence_note_when_loadings_close():
    loadings = [_coef("mkt_rf", 0.95, 0.75, 1.15), _coef("smb", 0.05, -0.15, 0.25, p_value=0.5, t_stat=0.7), _coef("hml", 0.4, 0.2, 0.6)]
    analysis = _analysis(capm=_capm(beta_estimate=1.0), ff=_ff(loadings))
    body = compute_interpretation(analysis).takeaways[1].body
    assert "differs from the plain CAPM beta" not in body


# --- 3c. explanatory_power ---------------------------------------------


def test_explanatory_power_very_low_r2_material_lift_and_significant_f_test():
    capm = _capm(r_squared=0.02)
    ff = _ff(_base_ff_no_significant(), r_squared=0.08, adj_r_squared=0.06, f_statistic=4.0, f_p_value=0.01)
    body = compute_interpretation(_analysis(capm=capm, ff=ff)).takeaways[2].body
    assert "very low for an equity portfolio" in body
    assert "a modest absolute lift, but proportionally large" in body
    assert "even where R² itself is low" in body


def test_explanatory_power_marginal_lift_and_failed_f_test():
    capm = _capm(r_squared=0.5)
    ff = _ff(_base_ff_no_significant(), r_squared=0.51, adj_r_squared=0.5, f_statistic=1.2, f_p_value=0.3)
    body = compute_interpretation(_analysis(capm=capm, ff=ff)).takeaways[2].body
    assert "a marginal" in body
    assert "does not clear the conventional 5% bar" in body


def test_explanatory_power_bucket_labels():
    from app.api.interpretation import _bucket_r2

    assert _bucket_r2(0.05) == "very low"
    assert _bucket_r2(0.20) == "low"
    assert _bucket_r2(0.45) == "moderate"
    assert _bucket_r2(0.70) == "high"
    assert _bucket_r2(0.90) == "very high"


# --- 3d. frontier_position ---------------------------------------------


def test_frontier_degenerate_single_holding():
    analysis = _analysis(ef=_ef(symbols=("AAPL",), frontier=[]))
    body = compute_interpretation(analysis).takeaways[3].body
    assert "only one holding" in body


def test_frontier_degenerate_identical_vol_multiple_holdings():
    same_vol_frontier = [_point(0.15, 0.10), _point(0.15, 0.12), _point(0.15, 0.14)]
    analysis = _analysis(ef=_ef(symbols=("AAPL", "MSFT"), frontier=same_vol_frontier))
    body = compute_interpretation(analysis).takeaways[3].body
    assert "effectively identical" in body


def test_frontier_gap_none_outside_range():
    analysis = _analysis(ef=_ef(gap=None, frontier_return_at_same_vol=None))
    body = compute_interpretation(analysis).takeaways[3].body
    assert "falls outside the range the modeled frontier covers" in body


def test_frontier_on_frontier():
    analysis = _analysis(ef=_ef(is_on_frontier=True, gap=0.0))
    body = compute_interpretation(analysis).takeaways[3].body
    assert "numerically on the modeled frontier" in body


def test_frontier_negative_gap_also_reads_as_on_frontier():
    analysis = _analysis(ef=_ef(is_on_frontier=False, gap=-0.01))
    body = compute_interpretation(analysis).takeaways[3].body
    assert "numerically on the modeled frontier" in body


def test_frontier_negligible_gap():
    analysis = _analysis(ef=_ef(gap=0.01))
    body = compute_interpretation(analysis).takeaways[3].body
    assert "small enough to be within the range explainable by estimation noise" in body


def test_frontier_moderate_gap():
    analysis = _analysis(ef=_ef(gap=0.05, portfolio_vol=0.15, portfolio_ret=0.19, frontier_return_at_same_vol=0.24))
    body = compute_interpretation(analysis).takeaways[3].body
    assert "That's moderate" in body


def test_frontier_large_gap_carries_no_action_disclaimer():
    analysis = _analysis(ef=_ef(gap=0.10, portfolio_vol=0.15, portfolio_ret=0.10, frontier_return_at_same_vol=0.20))
    body = compute_interpretation(analysis).takeaways[3].body
    assert "large by this analysis's own standard" in body
    assert "not a suggestion to reweight, and not a signal to act on" in body


# --- 4. Headline priority ---------------------------------------------------


def test_headline_priority_1_very_low_r2_wins_even_with_other_signals():
    capm = _capm(r_squared=0.05, beta_estimate=1.8, beta_lo=1.5, beta_hi=2.1)
    ff = _ff([_coef("mkt_rf", 1.6, 1.3, 1.9), _coef("smb", 0.5, 0.2, 0.8), _coef("hml", 0.1, -0.1, 0.3, p_value=0.4, t_stat=0.8)])
    ef = _ef(gap=0.5)
    interp = compute_interpretation(_analysis(capm=capm, ff=ff, ef=ef))
    assert interp.takeaways[2].is_headline  # explanatory_power
    assert "only weakly explained" in interp.headline


def test_headline_priority_2_beta_distinguishable_from_zero_and_one():
    capm = _capm(r_squared=0.5, beta_estimate=1.8, beta_lo=1.5, beta_hi=2.1)
    ff = _ff(_base_ff_no_significant(), r_squared=0.52)
    interp = compute_interpretation(_analysis(capm=capm, ff=ff))
    assert interp.takeaways[0].is_headline  # beta
    assert "distinguishable from both zero and from 1.0" in interp.headline
    assert "moves more than one-for-one" in interp.headline


def test_headline_priority_3_style_tilt_picks_largest_material_loading():
    capm = _capm(r_squared=0.5, beta_estimate=1.0, beta_lo=0.9, beta_hi=1.1)
    loadings = [_coef("mkt_rf", 0.9, 0.8, 1.0), _coef("smb", 0.35, 0.1, 0.6), _coef("hml", -0.6, -0.9, -0.3)]
    ff = _ff(loadings, r_squared=0.6)
    interp = compute_interpretation(_analysis(capm=capm, ff=ff))
    assert interp.takeaways[1].is_headline  # style_tilt, hml is bigger than smb
    assert "growth tilt" in interp.headline
    assert "-0.60" in interp.headline


def test_headline_priority_3_skips_significant_but_immaterial_loading():
    # smb is significant (CI excludes zero) but |estimate| < STYLE_LOADING_MATERIAL (0.30) --
    # must not hijack the headline (decision 0019's own stated purpose for this threshold).
    capm = _capm(r_squared=0.5, beta_estimate=1.0, beta_lo=0.9, beta_hi=1.1)
    loadings = [_coef("mkt_rf", 0.9, 0.8, 1.0), _coef("smb", 0.1, 0.02, 0.18), _coef("hml", 0.05, -0.1, 0.2, p_value=0.5, t_stat=0.6)]
    ff = _ff(loadings, r_squared=0.55)
    ef = _ef(gap=0.01)
    interp = compute_interpretation(_analysis(capm=capm, ff=ff, ef=ef))
    assert not interp.takeaways[1].is_headline


def test_headline_priority_4_large_frontier_gap():
    capm = _capm(r_squared=0.5, beta_estimate=1.0, beta_lo=0.9, beta_hi=1.1)
    ff = _ff(_base_ff_no_significant(), r_squared=0.52)
    ef = _ef(gap=0.10, portfolio_vol=0.15, portfolio_ret=0.10, frontier_return_at_same_vol=0.20)
    interp = compute_interpretation(_analysis(capm=capm, ff=ff, ef=ef))
    assert interp.takeaways[3].is_headline  # frontier_position
    assert "left real room on the table" in interp.headline


def test_headline_priority_5_default_nothing_stands_out():
    capm = _capm(r_squared=0.5, beta_estimate=1.0, beta_lo=0.9, beta_hi=1.1)
    ff = _ff(_base_ff_no_significant(), r_squared=0.52)
    ef = _ef(gap=0.01)
    interp = compute_interpretation(_analysis(capm=capm, ff=ff, ef=ef))
    assert interp.takeaways[2].is_headline  # explanatory_power id, "nothing stands out" text
    assert "That combination is itself the finding" in interp.headline
    assert interp.headline != interp.takeaways[2].body


# --- 5. Flags ----------------------------------------------------------


def test_flag_covariance_regularized_thin_data():
    ef = _ef(symbols=("A", "B", "C", "D", "E"), covariance_regularized=True, condition_number=1e9, n_obs=50)
    interp = compute_interpretation(_analysis(ef=ef))
    flag = next(f for f in interp.flags if f.id == "covariance_regularized")
    assert flag.severity == "warning"
    assert "the data window is short relative to the number of holdings" in flag.message
    assert "1.0e+09" in flag.message


def test_flag_covariance_regularized_correlation_structure():
    ef = _ef(symbols=("A", "B"), covariance_regularized=True, condition_number=1e9, n_obs=500)
    interp = compute_interpretation(_analysis(ef=ef))
    flag = next(f for f in interp.flags if f.id == "covariance_regularized")
    assert "unusually tightly correlated" in flag.message


def test_flag_short_data_window_daily():
    capm = _capm(n_obs=45)
    ff = _ff(_base_ff_no_significant(), n_obs=45)
    ef = _ef(n_obs=45)
    interp = compute_interpretation(_analysis(capm=capm, ff=ff, ef=ef))
    flag = next(f for f in interp.flags if f.id == "short_data_window")
    assert flag.severity == "info"
    assert "45 daily observations" in flag.message
    assert "(60)" in flag.message


def test_no_flags_when_data_is_ample_and_clean():
    interp = compute_interpretation(_analysis())
    assert interp.flags == []


def test_both_flags_can_fire_together():
    capm = _capm(n_obs=45)
    ff = _ff(_base_ff_no_significant(), n_obs=45)
    ef = _ef(n_obs=45, covariance_regularized=True, condition_number=1e9, symbols=("A", "B", "C"))
    interp = compute_interpretation(_analysis(capm=capm, ff=ff, ef=ef))
    ids = {f.id for f in interp.flags}
    assert ids == {"covariance_regularized", "short_data_window"}


# --- No-advice hard limit (docs/project-standards.md rule 9a) --------------

_BANNED_PATTERNS = [
    r"\byou should\b",
    r"\bwe recommend\b",
    r"\brebalance\b",
    r"\bconsider (buying|selling|holding)\b",
    r"\bbuy\b",
    r"\bsell\b",
    r"\bhold\b(?!ing|ings)",  # "hold" as an instruction, not "holding(s)"
]


def _all_text(interp) -> list[str]:
    texts = [interp.headline]
    texts.extend(t.body for t in interp.takeaways)
    texts.extend(f.message for f in interp.flags)
    return texts


@pytest.mark.parametrize(
    "analysis",
    [
        _analysis(),
        _analysis(capm=_capm(beta_estimate=0.2, beta_lo=-0.1, beta_hi=0.5), ef=_ef(gap=0.10, portfolio_vol=0.15, portfolio_ret=0.10, frontier_return_at_same_vol=0.20)),
        _analysis(
            capm=_capm(r_squared=0.02),
            ff=_ff(_base_ff_no_significant(), r_squared=0.08, adj_r_squared=0.06, f_statistic=4.0, f_p_value=0.01),
            ef=_ef(gap=0.10, portfolio_vol=0.15, portfolio_ret=0.10, frontier_return_at_same_vol=0.20),
        ),
        _analysis(ef=_ef(symbols=("AAPL",), frontier=[])),
        _analysis(ef=_ef(symbols=("A", "B", "C"), covariance_regularized=True, condition_number=1e9, n_obs=40)),
        _analysis(
            ff=_ff([_coef("mkt_rf", 0.9, 0.7, 1.1), _coef("smb", 0.4, 0.1, 0.7), _coef("hml", -0.4, -0.7, -0.1)])
        ),
    ],
)
def test_no_advice_coded_language(analysis):
    interp = compute_interpretation(analysis)
    for text in _all_text(interp):
        lowered = text.lower()
        for pattern in _BANNED_PATTERNS:
            assert not re.search(pattern, lowered), f"banned pattern {pattern!r} found in: {text}"


def test_headline_priority_5_wording_avoids_the_banned_words_too():
    # The priority-5 default is hand-checked separately since it's the one
    # headline whose text isn't reused from any takeaway body.
    capm = _capm(r_squared=0.5, beta_estimate=1.0, beta_lo=0.9, beta_hi=1.1)
    ff = _ff(_base_ff_no_significant(), r_squared=0.52)
    ef = _ef(gap=0.01)
    interp = compute_interpretation(_analysis(capm=capm, ff=ff, ef=ef))
    lowered = interp.headline.lower()
    for pattern in _BANNED_PATTERNS:
        assert not re.search(pattern, lowered)


# --- Cross-check against decision 0019's threshold constants ---------------


def test_thresholds_match_decision_0019():
    assert R2_VERY_LOW == 0.15
    assert FRONTIER_GAP_LARGE == 0.08

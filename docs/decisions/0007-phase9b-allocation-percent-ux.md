# 0007. Phase 9b: holdings allocation entered as a percent, with live total
feedback and equal-split/normalize helpers

Date: 2026-08-10
Status: accepted

## Context

Ethan's direct feedback after using the live app: *"no me has explicado para
qué son los weights, y aún sigue poco intuitivo para el usuario que hacer o
qué poner ahí"* — the holdings form's "weight" field was unlabeled beyond a
bare placeholder (`0.00–1.00`), had no explanation of what it represented,
gave no feedback while typing, and only revealed a wrong total (or a
generic pydantic validation message) after a full round-trip submit. A user
had to know, unprompted, that this project's weights are 0–1 fractions
that must sum to exactly 1.0, and had to do the arithmetic themselves with
zero help from the UI.

## Decisions

**1. The Inputs form now collects and displays allocation as a percent
(0–100), not the raw 0–1 fraction.** The field is relabeled "Allocation %"
with an inline one-line explainer directly above the holdings rows ("...the
percentage of your total portfolio each holding makes up — e.g. enter 25 if
a holding is a quarter of your portfolio. All holdings' allocations together
must add up to exactly 100%."). Percent is the natural unit for describing a
portfolio split; asking a general user to type `0.25` instead of `25` was
itself part of the "poco intuitivo" complaint, not just the missing
explanation.

**2. This is a presentation-layer conversion, not a change to the Phase 1
API contract.** `app/schemas.py`'s `HoldingInput.weight` (`0 < w <= 1`) and
`PortfolioRequest`'s fraction-sum-to-1.0 validator are untouched — the JSON
`POST /portfolio/returns` API still speaks fractions exactly as Phase 1
defined it. Only the HTML form boundary changed: `app/dashboard/routes.py`'s
`dashboard_submit` now parses each submitted `weight` as a percent, validates
`0 < pct <= 100`, and divides by 100 before constructing `HoldingInput`. The
re-shown Inputs form (after a successful or failed submit) echoes weights
back as percents (`pages.py::_weight_to_pct_str`), converting Phase 1's
stored fraction back for display. This was the option considered against
changing `HoldingInput.weight` itself to a 0–100 range — rejected, since that
would ripple into the JSON API contract, Phase 2's model code, and every
existing test/decision built on "weight is a fraction," for a UX problem that
is entirely about how the *form* presents the number, not what the backend
computes with.

**3. Live running total, not a post-submit surprise.** A single `input`
listener delegated on `#holdings-rows` (matching the file's existing
event-delegation pattern for dynamically-added rows) recomputes a visible
"Total allocated: NN%" badge on every keystroke in any weight field, styled
with three explicit states using the palette's existing status colors
(`--status-good` at exactly 100%, `--status-warning` under, `--diverging-neg`
over) — the same palette Phase 3/7 already use for other status framing, not
a new color introduced for this. The "Run analysis" submit button is
disabled (`aria-disabled` + CSS-muted) until the total is within 0.05 of
100%, so a user cannot submit while the math is wrong purely through the UI
— the state is visible before they ever reach for the button, not discovered
after a round trip.

**4. Two helper actions, both operating only on rows with a ticker actually
selected** (checked via the existing combobox's hidden-value field, so a
blank template row never receives a weight): **"Split evenly"** distributes
`100 / n` across the currently-entered holdings (2-decimal rounding, with the
remainder assigned to the last row so the sum is exactly 100.00, never
99.99/100.01 drift); **"Normalize to 100%"** proportionally scales whatever
weights are already typed so they sum to 100% (same remainder-to-last-row
approach) — and falls back to an equal split if every current weight is
blank/zero, since there is nothing to scale proportionally from zero.

**5. Server-side validation re-worded to match, and kept as a real backstop,
not just client-side trust.** `routes.py` now checks the percent total sums
to 100 (±0.1 percentage points) *before* constructing `PortfolioRequest`,
with a plain-language message ("Your allocations add up to 80.0%, not 100%.
Adjust the weights so they total 100% before submitting.") rather than
surfacing `PortfolioRequest`'s own fraction-based validator message
("...must sum to 1.0 (got 0.9800)"), which would be confusing against a
percent-labeled UI. `PortfolioRequest`'s own validator still runs afterward
unchanged as defense-in-depth for a hand-crafted POST that skips this loop
entirely (verified directly with a raw `fetch` POST bypassing the combobox
and JS total-check, confirmed rejected with 400 and the new message).

## Consequences

- Any future direct caller of `POST /dashboard` (not the JSON API) must send
  `weight` as a percent (e.g. `"25"` for 25%), not a fraction — a behavior
  change to that HTML-form endpoint's wire format. `tests/test_dashboard.py`
  was updated to match (`["50", "30", "20"]` instead of
  `["0.5", "0.3", "0.2"]`), and new tests cover the sum-to-100 rejection,
  the out-of-range rejection, and the pre-filled-percent echo on success.
- The submit-button disable relies on JavaScript, consistent with this
  project's existing convention (the Phase 7 ticker combobox already
  requires JS for its core selection flow — there is no no-JS fallback path
  in this form already, so this doesn't introduce a new JS dependency, just
  extends the existing one).
- `app/schemas.py`, `app/models/`, and the JSON `/portfolio/returns` API are
  completely unchanged — this phase touched only
  `app/dashboard/{pages.py,routes.py,shell.py}` and
  `tests/test_dashboard.py`.

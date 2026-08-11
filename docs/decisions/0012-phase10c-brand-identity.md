# 0012. Real brand identity for Factor Lens

Date: 2026-08-11
Status: accepted

## Context

Three rounds of aesthetic work (v1 bare-bones → "quant terminal" redesign in decision 0008 → chart-level polish in 0009) still read as generic/"just a website" per Ethan's own feedback, despite real technical progress each round. The gap wasn't visual polish — it was a genuine, referenced identity. This decision was produced directly (not by the `brand-creative` agent, which was created this same session and hadn't yet registered with the harness — a one-turn gap; it's the standing owner of this kind of work going forward, per `docs/team.md` and `docs/project-standards.md` rule 4).

## Research — real products actually studied

- **stripe.com** (marketing site, dashboard login wall): bold, custom black condensed wordmark as a real logotype, not just a font choice on the word "Stripe." Clean system sans for body copy. Indigo/violet as the *one* interactive accent against near-white/near-black — not a rainbow of UI color. A live, oddly-precise stat ("Global GDP running on Stripe: 1.69643212%") used as a branding device — precision-as-personality, not decoration. The colorful gradient is a background texture used sparingly (hero only), not smeared across the UI.
- **linear.app**: `getComputedStyle` confirms Inter Variable, background `rgb(8,9,10)` (near-black, not pure black), text `rgb(247,248,248)` (off-white, not pure white) — close to Factor Lens's existing graphite-navy direction, which is validated, not wrong. H1 font-weight is **510** — restrained, not bold-700 shouting. Decimal-numbered section system ("1.0 Intake→", "2.0 Plan→"...) — structurally identical to Factor Lens's own `[NN]` nav marks, which is also validated. Real product screenshots embedded directly, not illustrations. Customer social proof from recognizable, relevant companies (OpenAI, Ramp, Opendoor).
- **mercury.com**: `getComputedStyle` shows a fully **bespoke, commissioned typeface** ("arcadia"/"arcadiaDisplay" — not a Google Font, not available elsewhere) — the single strongest identity signal found in this research. H1 weight **480** — same restrained pattern as Linear.

**The consistent, real pattern across all three, not a guess**: headline type is *medium weight (480-510), not bold* — confidence is conveyed through restraint and precision, not visual loudness. Exactly one functional accent color, used sparingly and consistently, never decoratively. Real, specific numbers/data used as a branding device where possible. The best-differentiated of the three (Mercury) uses actual bespoke type — an identity lever generic "pick a nice Google Font" work can't reach.

## Decision — Factor Lens identity system

**What to preserve from the current "quant terminal" system** (decisions 0008/0009) — it was directionally right, not wrong: the graphite-navy dark mode (already close to Linear's validated near-black/off-white pairing), JetBrains Mono for all data/numbers (data-dense finance tools legitimately lean mono — keep this, it's working), the `[NN]` bracket nav system (structurally the same device Linear uses), and one signal accent color as the sole functional accent.

**What changes:**

1. **Naming/wordmark treatment.** "Factor Lens" gets an actual mark, not just a nice font on two words: a small circular aperture/focus-ring glyph — literally a camera-lens iris — placed before or integrated into the wordmark. This isn't decoration; it becomes the app's recurring visual device (see #4).
2. **Type weight — the single highest-leverage change.** Every large/headline number and section title currently likely leans on Space Grotesk's natural geometric weight, which reads heavier and more "poster-like" than the 480-510 restraint found in both real references. `developer` should drop display weight to Space Grotesk's Medium (500) or Regular for headline-scale text, reserving heavier weights (600+) only for genuinely load-bearing emphasis (a stat that's the literal point of a card), not every heading. This one change does more to close the "still looks like a website" gap than any color change would.
3. **The aperture/lens motif, applied functionally, not decoratively.** The "current portfolio" marker on the frontier chart becomes a literal focus-ring (concentric circle) rather than a generic dot — the app's name made functional. The same ring motif can mark the loading state during OpenBB's slow first fetch (a closing/opening iris instead of a generic spinner) and the favicon/OG mark. This is what separates a genuine identity from a palette: the name itself becomes a visual system, not just a title.
4. **Amber accent — audit for restraint.** Confirm (developer to check in implementation) that the signal amber is used *only* for the single most important element per view (per Stripe/Linear's one-accent discipline) and nowhere decoratively (e.g., not on every card border) — if 9c/9d's amber usage has crept beyond that, pull it back.
5. **Motion — stays restrained, now with one deliberate exception.** No new decorative animation. The one addition: the aperture/iris motif (#3) actually opening/closing is the one place motion is used deliberately and meaningfully, tying the loading state to the brand mark rather than a generic spinner.

**Personality, in one line**: *Factor Lens should feel like looking through a precise instrument — quiet, exact, nothing decorative, everything present because it's doing work.*

## Consequences

- The type-weight change (medium, not bold headlines) touches most of the existing CSS but is a low-risk, high-leverage single change `developer` can make quickly.
- The aperture/lens mark is a genuinely new visual asset (favicon, marker glyph, loading state) — more implementation work than the type change, but it's the piece that actually gives the project a memorable, ownable identity rather than "tasteful defaults."
- Future Cowork OS projects should get this kind of researched, referenced identity pass from `brand-creative` before their first UI build, not as a third-round retrofit — this decision is also the case study for why that agent exists (see decision 0003).

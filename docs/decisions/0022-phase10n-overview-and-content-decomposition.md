# 0022. Phase 10n: Overview 30-second comprehension pass & content decomposition (Real World / Glossary / Tools / References)

Date: 2026-08-12
Status: accepted

## Context

Sixth round of feedback, live-browser-verified by Ethan even after decision 0020's institutional refinement landed (Phase 10m): several sections still read as walls of paragraph text inside otherwise-real shadcn components, and Overview doesn't reliably convey the full picture in ~30 seconds. This produced two new standing rules (`docs/project-standards.md`):

- **Rule 14** — the 30-second comprehension test for every project's landing/Overview screen, owned by `brand-creative`.
- **Rule 15** — content decomposition (bullets / callouts / pull-quotes / examples / a lead line) as a required planning step before `developer` implements, owned by `brand-creative` for everything except Learning (owned by `educator`, tracked separately in decision 0021 — not duplicated here).

This decision is a **refinement**, not a rebuild. Decisions 0012/0017/0020's identity system (graphite-navy/amber tokens, `[NN]` eyebrow marks, JetBrains Mono for data, the aperture mark, restrained type weights) is preserved untouched — this pass only touches content structure and two new shared presentation primitives.

## Audit — live app, driven through the Browser tools, not from memory

Ran the built app locally (`uv run uvicorn app.main:app`, serving `frontend/dist/`) and inspected Overview, Real World, References, Glossary, and Tools & Technologies directly.

- **Overview**: the hero (live frontier-chart miniature + precision-stat callout) and the three method cards are real and already good — preserve exactly. But there is no sentence anywhere on the screen naming the *inputs* a user needs (holdings, benchmark, date range, factor model) — a visitor has to click into Inputs to learn what's required. The subtext paragraph states what the tool computes but not, literally, "give me X, I'll run Y, you get Z." The method-card row has no icons — text-only marks, missing the "icon+label chip" scannability rule 14 asks for.
- **Real World / Corporate Applications** (confirmed live via `get_page_text` and a screenshot): exactly as flagged — four full-width cards in a single-column `flex flex-col gap-4` stack, each with a good stat header but then two dense prose paragraphs with no bullets, no pull-quotes, no visual differentiation between the "what" and the "why it matters." Also found a real, unrelated bug while reading the live-rendered text: `card.stat`/`card.statLabel` are interpolated as plain JSX text (`{card.stat}`), not `dangerouslySetInnerHTML` like the rest of the card — so the third card's HTML-entity arrow renders literally as `"14% &rarr; 30%"` on the page instead of "14% → 30%". Flagged as a concrete fix below, not a matter of taste.
- **References & Formulas**: mostly fine — each card already separates "what" / formula block / legend / note / source into distinct visual zones, most `note` fields are 1–2 sentences. Two real exceptions found: (1) every card's `legend` field is a single middot-separated run-on line defining 2–5 variables in one paragraph — exactly rule 15's "enumerable set of points written as prose" anti-pattern; (2) the Markowitz card's `note` and the ticker/benchmark card's closing paragraph each fuse 3+ distinct ideas (an annualization convention, a default assumption, a numerical method, a safety net / a normalization rule, an enforcement mechanism, a known limitation) into one dense block.
- **Glossary**: audited and found genuinely fine, no fix specified. Entries are already short (mostly 1 sentence per register), grouped by concept into a collapsed-by-default `Accordion`, and each sits inside its own bordered box — this is already the "boxed, not stacked" structure rule 15 asks for. Two entries (Annualization convention, Covariance regularization) run 2–3 sentences in the technical register, which is borderline, but each is inside its own bounded card within a collapsible section a user opens on purpose — not a wall competing for attention on first view. Not touching this section; padding the spec with a fix nobody needs would be its own anti-pattern.
- **Tools & Technologies**: also genuinely fine. Content is already a real `<ul><li>` bulleted list (bold tool name + one sentence of project-specific use) inside category `Card`s with per-category icons (rule 13's prior fix). This already is the decomposed form rule 15 describes — no change.

## Planning method — adapting `information-architecture` to per-section content decomposition

Loaded `information-architecture`. Its native frame is site-structure/nav-hierarchy; per rule 15's explicit instruction, the adaptation used here treats each **page section** the way that skill treats a **site**: a shallow hierarchy of content "nodes" (lead → supporting detail → aside), each node assigned to a specific presentation primitive rather than left as undifferentiated body copy, planned before any component is touched. Every rewrite below states, per paragraph broken apart, which sentence became which primitive — not just "add some bullets."

## Decision — two shared primitives, built once, reused everywhere touched in this pass

Checked `frontend/src/components/FootnoteMarker.tsx` first, per the brief: it is a click-to-reveal `Popover`, correct for an inline citation that shouldn't compete with the sentence it qualifies (already used well in Learning, decision 0020 §2d, `educator`'s territory — not duplicated here). It does **not** cover the always-visible aside/definition need this pass requires (a caveat or "known limitation" that should be visually set apart but not hidden behind a click) — hence a new, always-visible sibling component.

### New: `frontend/src/components/Callout.tsx`

An always-visible aside block, distinct from `FootnoteMarker`'s click-to-reveal pattern. Two variants sharing one layout:

```tsx
import type { ReactNode } from "react"
import { Info, TriangleAlert } from "lucide-react"
import { cn } from "@/lib/utils"

export function Callout({
  variant = "note",
  label,
  children,
}: {
  variant?: "note" | "caveat"
  label?: string
  children: ReactNode
}) {
  const Icon = variant === "caveat" ? TriangleAlert : Info
  return (
    <div
      className={cn(
        "mt-3 flex gap-2.5 rounded-md border-l-2 bg-muted/50 px-3.5 py-3 text-[12.5px] leading-relaxed",
        variant === "caveat" ? "border-l-warning" : "border-l-muted-foreground/40"
      )}
    >
      <Icon className={cn("mt-0.5 size-3.5 flex-none", variant === "caveat" ? "text-warning" : "text-muted-foreground")} />
      <div>
        {label ? (
          <span className="text-muted-foreground mb-1 block font-mono text-[10px] tracking-wide uppercase">{label}</span>
        ) : null}
        <div className="text-muted-foreground" dangerouslySetInnerHTML={typeof children === "string" ? { __html: children } : undefined}>
          {typeof children === "string" ? undefined : children}
        </div>
      </div>
    </div>
  )
}
```

`variant="note"` (muted border/icon) for a definition, cross-reference, or "how this project fits" aside. `variant="caveat"` (`--warning` border/icon — already a wired Tailwind token, `frontend/src/index.css`'s `@theme inline`, no new CSS needed) reserved for a genuine limitation/disclaimer, kept visually distinct from destructive/error red since it isn't an error state. `label` is the small mono eyebrow ("Known limitation," "Not a recommendation," "Safety net") — reuse the existing "Plain"/"Technical" mono-label idiom already established in `Glossary.tsx` rather than inventing a new type treatment.

### New: `frontend/src/components/Highlight.tsx`

Pull-quote / stat-highlight, one component, two variants — replaces the bespoke inline stat markup currently duplicated in `Overview.tsx` and `RealWorld.tsx` with one shared primitive:

```tsx
import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

type HighlightProps =
  | { variant: "stat"; value: string; label?: string; className?: string }
  | { variant: "quote"; children: ReactNode; attribution?: string; className?: string }

export function Highlight(props: HighlightProps) {
  if (props.variant === "stat") {
    return (
      <div className={cn("flex flex-col gap-0.5", props.className)}>
        <span className="text-primary font-mono text-[24px] leading-none font-semibold tracking-tight">{props.value}</span>
        {props.label ? <span className="text-muted-foreground text-[11.5px] leading-snug">{props.label}</span> : null}
      </div>
    )
  }
  return (
    <blockquote className={cn("border-primary/50 border-l-2 py-0.5 pl-4", props.className)}>
      <p className="font-display text-foreground text-[15px] leading-snug font-medium">{props.children}</p>
      {props.attribution ? (
        <footer className="text-muted-foreground mt-1 font-mono text-[10.5px] tracking-wide uppercase">{props.attribution}</footer>
      ) : null}
    </blockquote>
  )
}
```

`variant="stat"` is the mono/amber numeric device already validated in the Overview hero and Real World card headers — now one component instead of two hand-copied instances. `variant="quote"` is new: a genuine pull-quote treatment (display-font, medium weight, left border) for the *single most important claim* in a block of text, per rule 15 — used below wherever a card's prose currently buries its one load-bearing sentence.

Both primitives use only existing tokens (`--primary`, `--warning`, `--muted-foreground`, `--font-display`, `--font-mono`) — no new colors, no new fonts, consistent with decisions 0012/0017/0020's one-accent discipline.

---

## Part A — Overview: closing the rule-14 gap

`frontend/src/pages/Overview.tsx`. Preserve the hero's split layout, the live `FrontierChart` miniature, the precision-stat callout, and the CTA pair exactly as built — those already pass rule 14's "real result preview" and "one-click demo action" checks. Two concrete additions and one small enhancement:

**1. Replace the subtext paragraph with a literal mechanism sentence.** Current text states what the tool computes but not the input→process→output shape rule 14 requires verbatim. Replace lines 53–56:

```tsx
<p className="text-muted-foreground mb-6 max-w-[48ch] text-[14.5px] leading-relaxed">
  CAPM beta, Fama-French loadings, and Markowitz positioning — computed live, with statistical
  diagnostics shown alongside every estimate.
</p>
```

with:

```tsx
<p className="text-muted-foreground mb-4 max-w-[54ch] text-[14.5px] leading-relaxed">
  Enter your holdings and a benchmark — Factor Lens runs CAPM, Fama-French, and Markowitz
  optimization on live market data and returns your beta, factor loadings, and frontier
  position, each with full statistical diagnostics.
</p>
```

(`max-w` widened from 48ch to 54ch to fit the longer sentence without an awkward extra wrap; `mb-6` tightened to `mb-4` since the new inputs row below needs its own margin.) **Judgment call, flagged explicitly**: this runs longer than decision 0017 §3's original "≤20 words" hero-subtext guidance. Rule 14 is newer and more specific than that guidance and explicitly requires the mechanism, the inputs, and the output named in one sentence — that requirement wins here. The inputs row below absorbs the actual enumeration so this sentence itself stays to one clause, not a run-on list.

**2. Add an inputs-named-plainly row, directly below the new sentence and above the CTA buttons** (this is the one genuinely missing rule-14 element — nothing today names required inputs anywhere on Overview):

```tsx
<div className="mb-6 flex flex-wrap items-center gap-x-2 gap-y-1.5">
  <span className="text-muted-foreground mr-0.5 font-mono text-[10.5px] tracking-wide uppercase">You provide</span>
  <Badge variant="outline" className="font-mono text-[10.5px] font-normal">Holdings (tickers + %)</Badge>
  <Badge variant="outline" className="font-mono text-[10.5px] font-normal">Benchmark</Badge>
  <Badge variant="outline" className="font-mono text-[10.5px] font-normal">Date range</Badge>
  <Badge variant="outline" className="font-mono text-[10.5px] font-normal">Factor model (3- or 5-factor)</Badge>
</div>
```

Requires `import { Badge } from "@/components/ui/badge"` (already used elsewhere, e.g. `RealWorld.tsx`/`References.tsx` — not a new dependency).

**3. Give the three method cards real icons** — the current `MethodCard` is text-only (a mono "mark" label, no glyph), missing rule 14's literal "icon+label chips" phrasing. Add `lucide-react` icons, one per card, matching each method's shape: `Target` (CAPM — single-point precision), `Layers` (Fama-French — multiple stacked factors), `LineChart` (Markowitz — the frontier curve itself). Update the component and its three call sites:

```tsx
import { Target, Layers, LineChart as LineChartIcon } from "lucide-react"
// ...
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
// ...
<MethodCard icon={Target} mark="CAPM" title="Market beta" body="Single-factor exposure to your chosen benchmark, with confidence intervals and significance." />
<MethodCard icon={Layers} mark="Fama-French" title="Factor loadings" body="3- or 5-factor exposure (market, size, value, and optionally profitability/investment)." />
<MethodCard icon={LineChartIcon} mark="Markowitz" title="Efficient frontier" body="Where your as-entered portfolio sits against the modeled long-only efficient set." />
```

(`LineChart` aliased on import since it collides with the existing `useAnalysis`-adjacent chart-component naming pattern elsewhere in the codebase — `developer` should confirm no existing import collision at build time.)

**4. Optional, low-priority**: swap the hero's hand-copied stat block (lines 102–115) to use the new `<Highlight variant="stat" value={...} label={...} />` for consistency with Real World's post-fix version below — not required for rule 14 (the existing markup already satisfies the rule), but tightens the shared-primitive story if `developer` has room.

**Result against rule 14's checklist**: mechanism sentence ✓ (new), inputs named plainly ✓ (new chip row), 2–4 core concepts as a scannable icon+label row ✓ (existing cards, now with icons), a real result preview ✓ (existing, untouched), one-click demo action ✓ (existing, untouched).

---

## Part B — Real World / Corporate Applications: full decomposition + layout change

### Data shape change — `frontend/src/data/real-world.ts`

Replace the flat `body: string[]` paragraph array with a structured shape carrying the decomposition:

```ts
export interface RealWorldCard {
  title: string
  stat: string
  statLabel: string
  tags: string[]
  lead: string                 // one sentence, the "so what," HTML-safe
  bullets: string[]            // enumerable points, HTML-safe
  quote: { text: string; attribution?: string }  // the one claim that matters most
  callout?: { variant: "note" | "caveat"; label?: string; text: string }
}
```

**Bug fix, unrelated to the decomposition but found during this audit**: `stat`/`statLabel` are rendered as plain JSX text in `RealWorld.tsx` (`{card.stat}`), not `dangerouslySetInnerHTML` — so any HTML entity in those two fields renders literally instead of decoding. Card 3's `stat` currently reads `"14% &rarr; 30%"` in the data file and renders as that literal string on the live page, not "14% → 30%". Fix by writing the real Unicode arrow directly in the data (`"14% → 30%"`), not by switching the component to `dangerouslySetInnerHTML` (no reason to widen the injection-surface convention for two short fields that never need real markup).

### New card content — literal copy, per card

**Card 1 — Institutional factor-risk desks** (stat/statLabel/tags unchanged):

```ts
lead: "Large asset managers and hedge funds run this exact kind of factor decomposition through commercial multi-factor risk platforms like MSCI Barra and (now Qontigo/SimCorp) Axioma &mdash; just at institutional scale, with proprietary factor sets.",
bullets: [
  "Breaks a portfolio's exposure into named, interpretable factors, the same shape as this app's Results tab",
  "Attributes realized return and risk to those factors versus stock-specific noise",
  "Flags when a portfolio's risk concentration doesn't match the mandate it's supposed to be running against",
],
quote: {
  text: "This project is scoped explicitly as &ldquo;Barra/Axioma-style factor risk tooling, just built transparent and accessible.&rdquo;",
  attribution: "&mdash; project roadmap",
},
callout: {
  variant: "note",
  label: "Why it's a real gap",
  text: "Barra/Axioma-class tooling is licensed to institutions at a price point and integration complexity entirely out of reach for a retail investor or a two-person RIA. The same factor-attribution logic, built open and cheap enough to run for a single portfolio, is the differentiator.",
},
```

**Card 2 — RIA client reporting & the advisor-tech stack**:

```ts
lead: "Small registered investment advisors don't build their own factor models &mdash; they buy reporting and proposal tooling that explains, in client-facing language, why a portfolio performed the way it did.",
bullets: [
  "YCharts' 2026 acquisition of Zephyr added a 21,000+ fund performance-attribution database directly into its advisor platform",
  "Advyzon shipped &ldquo;Advyzon AI&rdquo; for meeting notes and next-action recommendations",
  "Both treat plain-language, defensible explanation of portfolio behavior as a core advisor-tech feature, not a nice-to-have",
],
quote: {
  text: "An advisor explaining why a client's account moved the way it did &mdash; with statistical diagnostics available if the client's own due diligence goes that deep.",
  attribution: "What this project is built for",
},
callout: {
  variant: "note",
  label: "How this project fits",
  text: "Factor Lens pairs the exact math (References &amp; Formulas) with a plain-language read (Learning) &mdash; the same dual-register explanation an advisor gives a client, just self-serve.",
},
```

**Card 3 — Wealthtech optimization & automated rebalancing**:

```ts
lead: "Robo-advisor &ldquo;smart rebalance&rdquo; features (the kind Betterment- and Wealthfront-style platforms market as automated portfolio management) run mean-variance optimization internally &mdash; conceptually the same long-only Markowitz solve this project's <code>optimization.py</code> implements &mdash; just hidden behind a single button.",
bullets: [
  "The efficient frontier itself, not just an &ldquo;optimize&rdquo; action",
  "The global minimum-variance and tangency (max-Sharpe) portfolios",
  "The exact gap between your holdings and the efficient set",
],
quote: {
  text: "The share of U.S. wealth managers on one integrated investment platform rose from 14% (2020) to 30% (2024), and kept climbing through 2026 &mdash; automated rebalancing and AI-driven personalization cited as the differentiators.",
  attribution: "Platform-consolidation trend",
},
callout: {
  variant: "caveat",
  label: "Not a recommendation",
  text: "This is a transparency device, not an automated trade &mdash; Factor Lens shows the tradeoff, it doesn't rebalance anything for you.",
},
```

(Precede the bullets in the rendered card with a short lead-in line, e.g. `<p className="text-muted-foreground mb-1.5 text-[11.5px] font-mono uppercase tracking-wide">What this project keeps visible</p>`, so the bullet list itself doesn't float without a header — matches the treatment given to card 1's bullets below.)

**Card 4 — Where this fits, and why it's worth evaluating the person who built it** (kept structurally distinct per the layout change below — this card is evaluative/recruiting-facing, not a parallel industry example, and should read differently, not just sit in the same grid cell shape):

```ts
lead: "General &ldquo;factor investing explained&rdquo; content is everywhere; concrete, funded products doing factor-model analytics for retail or small-team use are thin on the ground &mdash; this project's own source research brief's explicit finding.",
bullets: [
  "Live market-data integration (OpenBB, Kenneth French's Data Library)",
  "Statistically rigorous diagnostics (Newey-West HAC standard errors, not classical OLS)",
  "A real constrained quadratic program (SLSQP) with covariance regularization for edge cases",
  "A shipped, sectioned web application with a real React/TypeScript frontend &mdash; not a notebook",
],
quote: {
  text: "Read the code, the methodology decision log, and this Learning section as direct evidence of the work &mdash; not a claim about it.",
  attribution: "&mdash; Ethan Verduzco, builder",
},
callout: {
  variant: "note",
  label: "See the evidence",
  text: "Full stack: Tools &amp; Technologies. Full methodology trail: <code>docs/decisions/</code>.",
},
```

(This quote's attribution is a second, natural placement for the builder's name beyond the two already established by decision 0020 §4 — sidebar footer and Overview colophon. Not a substitute for either, an addition, and it lands specifically on the card whose entire point is "evaluate the person who built this," so it's load-bearing here, not decorative.)

`REAL_WORLD_SOURCE_NOTE` is unchanged.

### Component change — `frontend/src/pages/RealWorld.tsx`

Render each card's new shape: lead paragraph → labeled bullet list → `Highlight variant="quote"` → optional `Callout`:

```tsx
<CardContent>
  <p className="text-muted-foreground mb-3 max-w-[62ch] text-[13.5px] leading-relaxed" dangerouslySetInnerHTML={{ __html: card.lead }} />
  <ul className="mb-3 flex flex-col gap-1.5 pl-4 text-[12.5px] leading-relaxed">
    {card.bullets.map((b, i) => (
      <li key={i} className="text-muted-foreground list-disc marker:text-primary/60" dangerouslySetInnerHTML={{ __html: b }} />
    ))}
  </ul>
  <Highlight variant="quote" attribution={card.quote.attribution}>
    <span dangerouslySetInnerHTML={{ __html: card.quote.text }} />
  </Highlight>
  {card.callout ? (
    <Callout variant={card.callout.variant} label={card.callout.label}>
      <span dangerouslySetInnerHTML={{ __html: card.callout.text }} />
    </Callout>
  ) : null}
</CardContent>
```

Also swap the card header's hand-copied stat markup (lines 25–28) for `<Highlight variant="stat" value={card.stat} label={card.statLabel} />` — same visual result, now the shared primitive.

### Layout change — from a single-column stack to real visual variety

Replace the `flex flex-col gap-4` wrapper (line 21) with a **3-up grid for the first three (parallel, comparable) cards, and the fourth (evaluative/recruiting-facing) card pulled out as a distinct, visually-marked spotlight below it** — not a strict "alternating" pattern, because these four cards aren't a narrative sequence; three of them are structurally parallel industry examples (a grid is the right shape for parallel/comparable content per `ui-ux-pro-max`'s card-grid guidance) and the fourth is categorically different in purpose, which the layout should say, not hide by putting it in the same grid cell shape as the others:

```tsx
<div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
  {REAL_WORLD_CARDS.slice(0, 3).map((card) => (
    <Card key={card.title}>{/* unchanged card body per above */}</Card>
  ))}
</div>

{(() => {
  const spotlight = REAL_WORLD_CARDS[3]
  return (
    <Card className="border-l-primary/70 bg-primary/[0.03] mt-4 border-l-4">
      <div className="flex flex-col gap-6 p-6 lg:flex-row lg:items-start">
        <div className="lg:w-[220px] lg:flex-none">
          <Highlight variant="stat" value={spotlight.stat} label={spotlight.statLabel} />
          <CardTitle className="mt-3 text-[16.5px]">{spotlight.title}</CardTitle>
        </div>
        <div className="flex-1">{/* lead / bullets / quote / callout per above */}</div>
      </div>
    </Card>
  )
})()}
```

(Exact spacing/breakpoints are `developer`'s call at implementation time — the structural point that must hold is: three parallel cards in a real grid, the fourth structurally distinct, not four identical full-width blocks in a column.) **Flag for QA**: with bullets + quote + callout added, each of the first three cards is now taller than before — verify live at `lg` (three columns) that none of the added content wraps awkwardly or forces excessive card-height mismatch across the row; drop to `md:grid-cols-2`/`grid-cols-1` sooner if it reads cramped. This is a real call best confirmed against the live rendered page, not guessed from a spec.

---

## Part C — References & Formulas: targeted fixes, not a rebuild

`frontend/src/data/references.ts` / `frontend/src/pages/References.tsx`. Two concrete, scoped changes; everything else in this section (the "what" paragraphs, the formula blocks, the source citations, the overall card structure) was audited and found fine — no change.

### 1. `legend` becomes a real definition list, not a middot run-on line

Every card's `legend` field is currently one paragraph defining 2–5 variables joined by ` &middot; ` — the exact "enumerable set of points written as prose" rule 15 flags. Change the type and render as a `<dl>`:

```ts
// references.ts — interface change
export interface LegendEntry { term: string; def: string }
export interface ReferenceCard {
  tag: string
  title: string
  what: string
  formulas: Formula[]
  legend: LegendEntry[]        // was: string
  legendCaption?: string        // optional trailing note that isn't a term definition (Fama-French card only, see below)
  note: string
  noteBullets?: string[]        // new, optional — Markowitz + ticker cards only
  noteCallout?: { variant: "note" | "caveat"; label?: string; text: string }  // new, optional — Markowitz + ticker cards only
  source: string
}
```

Literal replacement values (all other card fields unchanged):

- **CAPM**: `[{term:"R<sub>p,t</sub>",def:"portfolio return at t"},{term:"R<sub>f,t</sub>",def:"risk-free rate (Ken French Data Library)"},{term:"R<sub>m,t</sub>",def:"benchmark return"},{term:"&beta;",def:"market beta"},{term:"&alpha;",def:"intercept (excess return unexplained by the market)"}]`
- **Fama-French**: `[{term:"SMB",def:"Small Minus Big (size)"},{term:"HML",def:"High Minus Low (value, book-to-market)"},{term:"RMW",def:"Robust Minus Weak (profitability)"},{term:"CMA",def:"Conservative Minus Aggressive (investment)"}]`, with `legendCaption: "Each is itself a spread portfolio return, not a raw price series."` (this sentence isn't a term definition, so it renders as a small caption line below the `<dl>`, not folded into it).
- **Regression diagnostics**: `[{term:"n",def:"number of aligned observations in the regression sample"},{term:"L",def:"number of autocorrelation lags included in the HAC covariance estimate"}]`
- **Markowitz**: `[{term:"w",def:"holding weight vector"},{term:"&mu;",def:"vector of expected (annualized) holding returns"},{term:"&Sigma;",def:"annualized covariance matrix of holding returns"},{term:"R<sub>f</sub>",def:"risk-free rate"}]`
- **Attribution**: `[{term:"&beta;<sub>i</sub>",def:"the fitted loading on factor i"},{term:"mean(factor<sub>i</sub>)",def:"that factor's own realized mean return over the same aligned window"}]`
- **Ticker/benchmark universe**: leave `legend` as its current single explanatory sentence about rule 7 — it's documenting a policy, not defining variables, so it isn't the anti-pattern this fix targets; render it as a plain paragraph exactly as today (add a type-guard or a second optional `legendNote?: string` field rather than forcing this card's prose into the `LegendEntry[]` shape it doesn't fit).

`References.tsx` render change (replaces the current single `<p>` legend line):

```tsx
<dl className="text-muted-foreground grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-[12px]">
  {card.legend.map((e) => (
    <>
      <dt className="text-foreground font-mono" dangerouslySetInnerHTML={{ __html: e.term }} />
      <dd dangerouslySetInnerHTML={{ __html: e.def }} />
    </>
  ))}
</dl>
{card.legendCaption ? <p className="text-muted-foreground mt-1.5 text-[11.5px]" dangerouslySetInnerHTML={{ __html: card.legendCaption }} /> : null}
```

(`developer`: React needs `key`s on the `<>` fragments above — use `<Fragment key={e.term}>` from `"react"`, not the shorthand, since this is inside a `.map`.)

### 2. Markowitz card's `note` — lead sentence kept, two ideas pulled into bullets, the safety-net pulled into a `Callout`

Current `note` fuses the annualization-convention explanation with the long-only default, the numerical solve method, and the regularization safety net in one block. Keep the first sentence as `note` (it's one coherent claim, no change needed there); move the rest:

```ts
note: "&mu; and &Sigma; are annualized by <em>linear scaling</em> (periodic mean/covariance &times; periods per year) &mdash; the textbook i.i.d.-returns convention mean-variance optimization assumes by construction, and deliberately different from CAPM/Fama-French alpha's compounding convention above (decision 0003).",
noteBullets: [
  "Long-only (w<sub>i</sub> &ge; 0) is this app's default, reflecting how retail/small-RIA holdings are actually held",
  "Each frontier point is solved numerically via SLSQP, since long-only mean-variance optimization has no closed form",
],
noteCallout: {
  variant: "note",
  label: "Safety net",
  text: "If the sample covariance matrix is ill-conditioned or non-PSD, it's regularized by eigenvalue clipping before solving &mdash; the Results tab flags this explicitly (&ldquo;covariance regularized&rdquo;) whenever it happens.",
},
```

### 3. Ticker/benchmark card's closing paragraph — lead + bullets ("Enforced at two layers") + a `Callout(variant="caveat")` for the known limitation

```ts
note: "Share-class tickers are normalized to <code>yfinance</code> dash form (not the source dataset's dot form) at data-entry time, so every entry is directly usable by the price-fetch path with no translation layer needed downstream.",
noteBullets: [
  "The frontend's submitted field is only ever set by selecting a real option from this list &mdash; never raw typed text",
  "<code>app/api/routes.py</code> independently re-validates every submitted symbol/benchmark against <code>tickers.is_valid_ticker</code>/<code>is_valid_benchmark</code> server-side before any analysis runs",
],
noteCallout: {
  variant: "caveat",
  label: "Known limitation",
  text: "This is a static snapshot, not a live index-membership feed &mdash; it will drift from the real S&amp;P 500 roster as constituents change (several times a year), and a holding outside this list (a small-cap, an ADR, a non-US listing) can't be entered even if it's perfectly valid on <code>yfinance</code>/OpenBB. Refreshing it requires re-running the sourcing process by hand, not a live sync.",
},
```

`References.tsx` render: after the existing `note` paragraph, conditionally render bullets and the callout:

```tsx
{card.noteBullets ? (
  <ul className="mt-2 flex flex-col gap-1 pl-4 text-[12.5px] leading-relaxed">
    {card.noteBullets.map((b, i) => (
      <li key={i} className="text-muted-foreground list-disc marker:text-primary/60" dangerouslySetInnerHTML={{ __html: b }} />
    ))}
  </ul>
) : null}
{card.noteCallout ? (
  <Callout variant={card.noteCallout.variant} label={card.noteCallout.label}>
    <span dangerouslySetInnerHTML={{ __html: card.noteCallout.text }} />
  </Callout>
) : null}
```

All four other reference cards keep a bare `note` string exactly as today — `noteBullets`/`noteCallout` are optional and only populated for the two cards that actually needed decomposition. This is a targeted fix, not a template forced onto every card.

---

## Glossary & Tools & Technologies — audited, no changes

Stated explicitly per the brief's instruction not to pad the spec: both sections were read fully (`Glossary.tsx`/`data/glossary.ts`, `Tools.tsx`/`data/tools.ts`) and driven live. Glossary's dual-register entries are already short, individually boxed, and grouped inside a collapsed `Accordion` — the "boxed, not stacked" structure this pass is trying to achieve elsewhere already exists there natively (built correctly the first time, Phase 9e/10i). Tools & Technologies is already a real bulleted list with per-category icons (rule 13's prior fix) — also already decomposed. Neither needed a rule-15 pass.

## Consequences / flags for `developer` and `pm`

- **Two new files**: `frontend/src/components/Callout.tsx`, `frontend/src/components/Highlight.tsx`. No new dependencies — both use only already-installed `lucide-react` icons and existing Tailwind tokens (`--warning`/`--success` were already wired into `@theme inline` by decision 0017, just unused until now).
- **Real, scoped implementation surface**: `frontend/src/pages/Overview.tsx` (subtext copy, new inputs-badge row, method-card icons), `frontend/src/pages/RealWorld.tsx` + `frontend/src/data/real-world.ts` (card shape, layout, the entity-decode bug fix), `frontend/src/pages/References.tsx` + `frontend/src/data/references.ts` (legend restructure, two cards' note decomposition). No touch to `Learning.tsx`/`data/learning.ts` (decision 0021, `educator`), no touch to `Glossary.tsx`/`Tools.tsx` (audited fine), no touch to any backend/`app/models`/`app/data` code.
- **One deliberate deviation from decision 0017's hero-subtext word-count guidance**, stated explicitly in Part A above (rule 14 supersedes it for this specific sentence) — flagged so `developer` doesn't read the longer sentence as an oversight.
- **One real bug found and specified, not just a design change**: Real World's `stat`/`statLabel` HTML-entity-vs-plain-text mismatch (Part B). Small, but a genuine correctness fix `developer` should not skip.
- **QA flag**: Real World's 3-up grid needs a live check that the added content (bullets + quote + callout) doesn't produce cramped or mismatched card heights at `lg` — noted in Part B, `developer`/`qa-tester` call to make against the actual rendered page.
- **What must be preserved, not touched**: the entire identity system from decisions 0012/0017/0020 (tokens, type weights, the aperture mark, the `[NN]` eyebrow system, the GSAP motion language), the Results/Inputs/Learning pages, and every validated backend number/methodology.

## Handoff to `developer`

Build Part A first (smallest surface, closes the highest-visibility gap), then Part B (the primitives, then Real World's content/layout — the worst offender per Ethan's screenshots), then Part C (References' two targeted fixes). Glossary and Tools & Technologies need no work. Cross-check against `docs/decisions/0021-phase10n-learning-content-decomposition.md` (`educator`) before starting, so Learning isn't touched twice.

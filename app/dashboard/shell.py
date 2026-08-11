"""App shell: sidebar navigation, tab panels, and the constrained
ticker/benchmark combobox component. Originally built in Phase 7; the visual
design system below is Phase 9c's redesign (`docs/decisions/0008-...md`).

Design system: a "quant terminal / instrument panel" reading -- Space
Grotesk (a geometric, slightly technical display face) for headings,
JetBrains Mono for tickers/numbers/section marks/data (used more
aggressively than Phase 7's mono did -- stat tile values, legends, table
cells), and Inter for body copy, laid out as a persistent left sidebar nav
against a single active content panel with a faint instrument-panel grid
texture on hero/feature surfaces. The color tokens live in
`app/dashboard/viz.py`'s `CHART_STYLE` (shared with the chart layer, not
duplicated here) -- graphite-navy dark mode, cool gray-blue light mode, and
one amber "signal" accent (`--series-2`, the same "current portfolio" chart
color Phase 7 first reused as the site accent) so chart marks and page
chrome read as one system rather than two.

Eight sections, matching `docs/project-standards.md`'s required list:
Overview, Inputs, Results, Learning, Glossary, Tools & Technologies,
References & Formulas, Real World/Corporate Applications. All eight always
render (progressive enhancement: the server marks one panel visible via the
`hidden` attribute; a small vanilla-JS layer below makes tab-switching
instant without a full page reload). References & Formulas was filled in
Phase 8 (`business-intelligence`, `render_references_section`); Learning,
Glossary, and Real World/Corporate Applications were filled in Phase 9
(`educator` -- `render_learning_section`, `render_glossary_section`,
`render_real_world_section`). All eight sections are now real content --
`render_placeholder_section` is kept as a reusable pattern for any future
section that ships incrementally, but nothing currently uses it.
"""
from __future__ import annotations

import json

from app.dashboard.viz import esc

NAV_ITEMS: tuple[tuple[str, str], ...] = (
    ("overview", "Overview"),
    ("inputs", "Inputs"),
    ("results", "Results"),
    ("learning", "Learning"),
    ("glossary", "Glossary"),
    ("tools", "Tools & Technologies"),
    ("references", "References & Formulas"),
    ("real-world", "Real World / Corporate Applications"),
)

FONT_LINKS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
"""

# Inline SVG data-URI favicon (amber "FL" bracket mark on graphite) -- no extra static
# asset needed, matches the masthead mark's shape/color exactly.
FAVICON_LINK = (
    '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
    "%3Crect width='64' height='64' rx='12' fill='%230a0d13'/%3E"
    "%3Crect x='6' y='6' width='52' height='52' rx='8' fill='none' stroke='%23f0a63e' stroke-width='3'/%3E"
    "%3Ctext x='32' y='41' font-family='monospace' font-size='24' font-weight='700' fill='%23f0a63e' "
    "text-anchor='middle'%3EFL%3C/text%3E%3C/svg%3E\">"
)

DEFAULT_META_DESCRIPTION = (
    "Enter a portfolio and get CAPM beta, Fama-French factor loadings, and Markowitz "
    "efficient-frontier positioning, computed live from real market data with full "
    "statistical diagnostics -- not a black-box score."
)

SHELL_STYLE = """
.viz-root {
  --font-display: 'Space Grotesk', ui-sans-serif, system-ui, sans-serif;
  --font-body: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  --signal: var(--series-2);
  --signal-cool: var(--series-1);
  --radius-sm: 6px;
  --radius-md: 9px;
  --radius-lg: 12px;
  font-family: var(--font-body);
}
* { box-sizing: border-box; }
body { margin: 0; }
.app-shell { display: flex; align-items: flex-start; min-height: 100vh; }

/* Faint instrument-panel grid texture, used sparingly behind hero/feature surfaces --
   references the fact that everything this app renders is a point plotted on a chart. */
.grid-texture {
  background-image:
    linear-gradient(color-mix(in srgb, var(--baseline) 32%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--baseline) 32%, transparent) 1px, transparent 1px);
  background-size: 28px 28px;
}

/* ---- Sidebar / masthead / nav ---- */
.app-sidebar { flex: 0 0 264px; position: sticky; top: 0; height: 100vh; overflow-y: auto;
  padding: 24px 18px 18px; border-right: 1px solid var(--border); display: flex; flex-direction: column;
  background: var(--page-plane); }
.masthead { display: flex; align-items: center; gap: 11px; margin-bottom: 24px; }
.masthead-mark { font-family: var(--font-mono); font-size: 13px; font-weight: 600; letter-spacing: 0.02em;
  color: var(--signal); border: 1.5px solid var(--signal); border-radius: var(--radius-sm); width: 34px; height: 34px;
  display: flex; align-items: center; justify-content: center; flex: none;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--signal) 12%, transparent); }
.masthead-title { font-family: var(--font-display); font-size: 18px; font-weight: 700; line-height: 1.15;
  letter-spacing: -0.01em; }
.masthead-tag { font-family: var(--font-mono); text-transform: uppercase; letter-spacing: 0.05em; font-size: 10px;
  color: var(--text-muted); }

.app-nav { display: flex; flex-direction: column; gap: 1px; margin-bottom: auto; }
.nav-item { display: flex; align-items: center; gap: 10px; text-align: left; background: none;
  border: none; border-left: 2px solid transparent; padding: 8px 10px 8px 9px; border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  cursor: pointer; color: var(--text-secondary); font: inherit; font-family: var(--font-body); font-size: 13px; }
.nav-item:hover { background: var(--surface-1); color: var(--text-primary); }
.nav-item .nav-mark { font-family: var(--font-mono); font-size: 10.5px; color: var(--text-muted); flex: none;
  width: 24px; }
.nav-item .nav-pending { margin-left: auto; font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.04em;
  color: var(--text-muted); border: 1px solid var(--border); border-radius: 999px; padding: 1px 6px; }
.nav-item.is-active { background: var(--surface-1); color: var(--text-primary); font-weight: 600;
  border-left-color: var(--signal); }
.nav-item.is-active .nav-mark { color: var(--signal); }
.nav-item:focus-visible { outline: 2px solid var(--signal); outline-offset: -2px; }

.sidebar-foot { margin-top: 20px; padding-top: 14px; border-top: 1px solid var(--border); }
.theme-btn { font-family: var(--font-mono); font-size: 11px; background: var(--surface-1); color: var(--text-secondary);
  border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 6px 10px; cursor: pointer; }
.theme-btn:hover { color: var(--text-primary); border-color: var(--baseline); }
.sidebar-disclaimer { font-size: 10.5px; color: var(--text-muted); margin-top: 10px; line-height: 1.55; }

/* ---- Main content ---- */
.app-main { flex: 1 1 auto; min-width: 0; padding: 34px 28px 80px; }
.app-main-inner { max-width: 760px; margin: 0 auto; }
.tab-panel h1 { font-family: var(--font-display); font-size: 27px; font-weight: 700; letter-spacing: -0.01em;
  margin: 0 0 4px; }
.tab-panel h2 { font-family: var(--font-display); font-weight: 600; }
.section-eyebrow { display: inline-flex; align-items: center; gap: 8px; font-family: var(--font-mono);
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--signal); margin: 0 0 10px; }
.section-eyebrow::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: var(--signal); }
.section-lede { font-size: 14.5px; color: var(--text-secondary); max-width: 62ch; line-height: 1.6; margin: 0 0 24px; }

/* ---- Overview hero ---- */
.hero-card { position: relative; background: var(--surface-1); border: 1px solid var(--border);
  border-top: 2px solid var(--signal); border-radius: var(--radius-lg); box-shadow: var(--shadow-card);
  padding: 30px 30px 26px; margin-bottom: 22px; overflow: hidden; }
.hero-card::before { content: ''; position: absolute; inset: 0; pointer-events: none;
  background-image: linear-gradient(color-mix(in srgb, var(--baseline) 28%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--baseline) 28%, transparent) 1px, transparent 1px);
  background-size: 28px 28px; -webkit-mask-image: linear-gradient(to bottom, black, transparent 65%);
  mask-image: linear-gradient(to bottom, black, transparent 65%); opacity: 0.5; }
.hero-card > * { position: relative; }
.hero-card p { font-size: 15px; line-height: 1.65; color: var(--text-secondary); max-width: 62ch; }
.hero-card p strong { color: var(--text-primary); }
.hero-cta-row { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
.hero-cta { display: inline-flex; align-items: center; gap: 8px; background: var(--signal); color: #fff;
  border: none; border-radius: var(--radius-sm); padding: 11px 20px; font: inherit; font-weight: 600; font-size: 14px;
  cursor: pointer; }
.hero-cta:hover { filter: brightness(1.08); }
.hero-cta-secondary { display: inline-flex; align-items: center; gap: 8px; background: var(--page-plane);
  color: var(--text-primary); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 10px 19px;
  font: inherit; font-family: var(--font-mono); font-weight: 500; font-size: 13px; cursor: pointer; text-decoration: none; }
.hero-cta-secondary:hover { border-color: var(--signal); color: var(--signal); }
.method-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-top: 22px; }
.method-card { border: 1px solid var(--border); border-radius: var(--radius-md); padding: 14px 16px;
  background: var(--page-plane); }
.method-card .method-mark { font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--signal); }
.method-card h3 { font-family: var(--font-display); font-weight: 600; font-size: 15px; margin: 7px 0 4px; }
.method-card p { font-size: 12.5px; color: var(--text-secondary); margin: 0; line-height: 1.5; }
.disclaimer-strip { font-size: 12px; color: var(--text-muted); border-top: 1px solid var(--border); margin-top: 22px;
  padding-top: 14px; }

/* ---- Sample quick-start (rule 8) ---- */
.quickstart-banner { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
  background: color-mix(in srgb, var(--signal) 8%, var(--surface-1)); border: 1px solid color-mix(in srgb, var(--signal) 35%, var(--border));
  border-radius: var(--radius-md); padding: 14px 18px; margin: 0 0 22px; }
.quickstart-banner .qs-copy { font-size: 13px; color: var(--text-secondary); max-width: 46ch; }
.quickstart-banner .qs-copy strong { color: var(--text-primary); font-family: var(--font-mono); }
.quickstart-btn { display: inline-flex; align-items: center; gap: 8px; background: var(--signal); color: #fff;
  border: none; border-radius: var(--radius-sm); padding: 10px 18px; font: inherit; font-weight: 600; font-size: 13.5px;
  cursor: pointer; text-decoration: none; flex: none; white-space: nowrap; }
.quickstart-btn:hover { filter: brightness(1.08); }

/* ---- Share / export bar (rule 8) ---- */
.share-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; background: var(--surface-1);
  border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px 16px; margin: 0 0 18px; }
.share-bar-label { font-family: var(--font-mono); font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--text-muted); flex: none; }
.share-btn { display: inline-flex; align-items: center; gap: 6px; background: var(--page-plane);
  color: var(--text-primary); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 7px 13px;
  font: inherit; font-family: var(--font-mono); font-size: 12.5px; cursor: pointer; text-decoration: none; }
.share-btn:hover { border-color: var(--signal); color: var(--signal); }
.share-link-row { display: none; align-items: center; gap: 8px; width: 100%; margin-top: 4px; }
.share-link-row.is-visible { display: flex; }
.share-link-input { flex: 1 1 auto; font-family: var(--font-mono); font-size: 12px; padding: 7px 10px;
  border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--page-plane); color: var(--text-secondary); }
.share-copied-note { font-size: 11.5px; color: var(--status-good); font-family: var(--font-mono); display: none; }
.share-copied-note.is-visible { display: inline; }

/* ---- Curated-source note (rule 7) ---- */
.source-note { display: flex; gap: 10px; align-items: flex-start; background: var(--page-plane);
  border: 1px dashed var(--baseline); border-radius: var(--radius-sm); padding: 10px 13px; margin: 10px 0 18px;
  font-size: 12px; color: var(--text-secondary); line-height: 1.55; }
.source-note .sn-mark { font-family: var(--font-mono); font-size: 10.5px; color: var(--signal); flex: none;
  border: 1px solid var(--signal); border-radius: 4px; padding: 1px 6px; }
.source-note strong { color: var(--text-primary); }

/* ---- Placeholder sections (Phase 8/9) ---- */
.placeholder-card { border: 1px dashed var(--baseline); border-radius: 12px; padding: 28px 30px; background: var(--surface-1); }
.placeholder-stamp { display: inline-block; font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.05em;
  text-transform: uppercase; color: var(--signal); border: 1px solid var(--signal); border-radius: 999px;
  padding: 3px 10px; margin-bottom: 14px; }
.placeholder-card h2 { font-size: 20px; margin: 0 0 8px; }
.placeholder-card p { font-size: 13.5px; color: var(--text-secondary); max-width: 58ch; line-height: 1.6; }
.placeholder-owner { font-family: var(--font-mono); font-size: 11.5px; color: var(--text-muted); margin-top: 16px; }

/* ---- Tools & Technologies ---- */
.tool-groups { display: flex; flex-direction: column; gap: 18px; }
.tool-group h3 { font-family: var(--font-display); font-size: 15.5px; margin: 0 0 8px; }
.tool-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.tool-list li { font-size: 13px; color: var(--text-secondary); display: flex; gap: 8px; align-items: baseline; }
.tool-list .tool-name { font-family: var(--font-mono); font-size: 12.5px; color: var(--text-primary); font-weight: 600;
  flex: none; min-width: 168px; }

/* ---- References & Formulas ---- */
.ref-groups { display: flex; flex-direction: column; gap: 16px; }
.ref-card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
  padding: 22px 24px 20px; }
.ref-card-head { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-bottom: 4px; }
.ref-card h2 { font-family: var(--font-display); font-size: 17px; margin: 0; font-weight: 600; }
.ref-tag { font-family: var(--font-mono); font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--signal); border: 1px solid var(--signal); border-radius: 999px; padding: 2px 8px; flex: none; }
.ref-what { font-size: 13.5px; color: var(--text-secondary); line-height: 1.6; margin: 8px 0 4px; max-width: 66ch; }
.formula-block { font-family: var(--font-mono); font-size: 15px; line-height: 1.7; background: var(--page-plane);
  border: 1px solid var(--border); border-left: 3px solid var(--signal); border-radius: 6px;
  padding: 14px 18px; margin: 12px 0; overflow-x: auto; }
.formula-block .fb-label { display: block; font-family: var(--font-mono); font-size: 10.5px; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 8px; }
.formula-block .fb-eq { white-space: nowrap; color: var(--text-primary); }
.formula-block .fb-eq + .fb-eq { margin-top: 6px; }
.formula-legend { font-size: 12.5px; color: var(--text-secondary); line-height: 1.75; margin: 10px 0 2px; }
.formula-legend code { font-family: var(--font-mono); font-size: 12px; background: var(--page-plane);
  border: 1px solid var(--border); border-radius: 4px; padding: 1px 5px; color: var(--text-primary); }
.ref-note { font-size: 12.5px; color: var(--text-secondary); line-height: 1.6; margin-top: 10px; max-width: 66ch; }
.ref-source { font-size: 12.5px; color: var(--text-muted); margin-top: 16px; padding-top: 12px;
  border-top: 1px dashed var(--baseline); line-height: 1.6; }
.ref-source strong { color: var(--text-secondary); font-weight: 600; }
.ref-cited-list { list-style: none; margin: 8px 0 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.ref-cited-list li { font-size: 12.5px; color: var(--text-secondary); line-height: 1.6; padding-left: 22px; text-indent: -22px; }

/* ---- Learning (Phase 9) ---- */
.learn-groups { display: flex; flex-direction: column; gap: 16px; }
.learn-card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
  padding: 22px 24px 20px; }
.learn-card-head { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-bottom: 4px; }
.learn-card h2 { font-family: var(--font-display); font-size: 17px; margin: 0; font-weight: 600; }
.learn-tag { font-family: var(--font-mono); font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--text-muted); border: 1px solid var(--border); border-radius: 999px; padding: 2px 8px; flex: none; }
.learn-register { margin: 14px 0 0; }
.learn-register-label { font-family: var(--font-mono); font-size: 10.5px; text-transform: uppercase;
  letter-spacing: 0.05em; margin-bottom: 6px; display: block; }
.learn-register.is-plain .learn-register-label { color: var(--signal-cool); }
.learn-register.is-technical .learn-register-label { color: var(--signal); }
.learn-register p { font-size: 13.5px; color: var(--text-secondary); line-height: 1.65; max-width: 66ch; margin: 0; }
.learn-register.is-plain p { color: var(--text-primary); }
.learn-register p code { font-family: var(--font-mono); font-size: 12.5px; background: var(--page-plane);
  border: 1px solid var(--border); border-radius: 4px; padding: 1px 5px; color: var(--text-primary); }
.learn-xref-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.learn-xref { display: inline-flex; align-items: center; gap: 6px; background: none; border: 1px solid var(--border);
  border-radius: 999px; color: var(--text-secondary); font: inherit; font-family: var(--font-mono); font-size: 11.5px;
  padding: 5px 12px; cursor: pointer; }
.learn-xref:hover { border-color: var(--signal); color: var(--signal); }
.learn-note { font-size: 12.5px; color: var(--text-secondary); line-height: 1.6; margin-top: 12px;
  padding-top: 12px; border-top: 1px dashed var(--baseline); max-width: 66ch; }

/* ---- Glossary (Phase 9) ---- */
.glossary-groups { display: flex; flex-direction: column; gap: 10px; }
.glossary-entry { background: var(--surface-1); border: 1px solid var(--border); border-radius: 9px;
  padding: 16px 18px; }
.glossary-term { font-family: var(--font-display); font-size: 15.5px; font-weight: 600; margin: 0 0 8px;
  color: var(--text-primary); display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.glossary-term .gt-where { font-family: var(--font-mono); font-size: 11px; font-weight: 400; color: var(--text-muted); }
.glossary-row { display: flex; gap: 10px; font-size: 12.5px; line-height: 1.6; margin-top: 6px; }
.glossary-row .gr-label { font-family: var(--font-mono); font-size: 10px; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--text-muted); flex: none; width: 70px; padding-top: 1px; }
.glossary-row.is-plain .gr-label { color: var(--signal-cool); }
.glossary-row.is-technical .gr-label { color: var(--signal); }
.glossary-row p { margin: 0; color: var(--text-secondary); }
.glossary-row.is-plain p { color: var(--text-primary); }
.glossary-row p code { font-family: var(--font-mono); font-size: 12px; background: var(--page-plane);
  border: 1px solid var(--border); border-radius: 4px; padding: 1px 5px; color: var(--text-primary); }

/* ---- Real World / Corporate Applications (Phase 9) ---- */
.rw-groups { display: flex; flex-direction: column; gap: 16px; }
.rw-card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
  padding: 22px 24px 20px; }
.rw-card h2 { font-family: var(--font-display); font-size: 17px; margin: 0 0 8px; font-weight: 600; }
.rw-card p { font-size: 13.5px; color: var(--text-secondary); line-height: 1.65; max-width: 66ch; margin: 0 0 10px; }
.rw-card p:last-of-type { margin-bottom: 0; }
.rw-tag-row { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 12px; }
.rw-tag { font-family: var(--font-mono); font-size: 10.5px; color: var(--text-muted); border: 1px solid var(--border);
  border-radius: 999px; padding: 2px 9px; }
.rw-cta-card { background: var(--page-plane); border: 1px dashed var(--baseline); border-radius: 10px;
  padding: 20px 22px; }
.rw-cta-card h2 { color: var(--text-primary); }
.rw-cta-card p { color: var(--text-secondary); }
.rw-source-note { font-size: 12px; color: var(--text-muted); margin-top: 6px; line-height: 1.6; }

/* ---- Form (Inputs section) ---- */
.form-card { background: var(--surface-1); border: 1px solid var(--border); border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card); padding: 26px; }
.field-row { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.field { flex: 1 1 160px; display: flex; flex-direction: column; gap: 4px; }
.field label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted);
  font-family: var(--font-mono); }
.field input, .field select { font: inherit; font-family: var(--font-body); padding: 9px 11px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); background: var(--page-plane); color: var(--text-primary); }
.field input:focus, .field select:focus, .ticker-search:focus {
  outline: none; border-color: var(--signal); box-shadow: 0 0 0 3px color-mix(in srgb, var(--signal) 16%, transparent); }
.holdings-label { font-family: var(--font-mono); font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--text-secondary); margin: 20px 0 8px; }
.alloc-explainer { font-size: 12.5px; color: var(--text-secondary); line-height: 1.55; margin: 0 0 12px; max-width: 62ch; }
.alloc-explainer strong { color: var(--text-primary); font-family: var(--font-mono); font-weight: 600; }
.holdings-col-labels { display: flex; gap: 10px; margin: 0 0 6px; }
.holdings-col-labels span { font-family: var(--font-mono); font-size: 10px; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--text-muted); }
.holdings-col-labels .hcl-ticker { flex: 1 1 auto; }
.holdings-col-labels .hcl-weight { flex: 0 1 130px; }
.holdings-col-labels .hcl-spacer { flex: 0 0 34px; }
.holding-row { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 8px; }
.holding-row .field { flex: 1 1 auto; }
.holding-row input[name="weight"] { width: 100%; font-family: var(--font-mono); }
.weight-field { flex: 0 1 130px; }
.row-remove { background: transparent; border: 1px solid var(--border); border-radius: 6px; color: var(--text-muted);
  width: 34px; height: 38px; cursor: pointer; font-size: 15px; flex: none; }
.row-remove:hover { color: var(--diverging-neg); }
.holdings-toolbar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 2px; }
.add-row-btn, .helper-btn { background: transparent; border: 1px dashed var(--baseline); border-radius: 6px;
  color: var(--text-secondary); padding: 7px 12px; font-size: 12.5px; cursor: pointer; margin-top: 2px; font: inherit; }
.helper-btn { border-style: solid; }
.helper-btn:hover { border-color: var(--signal); color: var(--signal); }
.alloc-total { display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px; margin-top: 14px;
  padding: 10px 14px; border-radius: 8px; border: 1px solid var(--border); background: var(--page-plane); }
.alloc-total-label { font-family: var(--font-mono); font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--text-muted); }
.alloc-total-value { font-family: var(--font-mono); font-weight: 700; font-size: 15px; color: var(--text-primary); }
.alloc-total-msg { color: var(--text-secondary); font-size: 12.5px; }
.alloc-total[data-state="exact"] { border-color: color-mix(in srgb, var(--status-good) 45%, var(--border));
  background: color-mix(in srgb, var(--status-good) 10%, var(--surface-1)); }
.alloc-total[data-state="exact"] .alloc-total-value { color: var(--status-good); }
.alloc-total[data-state="under"] { border-color: color-mix(in srgb, var(--status-warning) 45%, var(--border));
  background: color-mix(in srgb, var(--status-warning) 12%, var(--surface-1)); }
.alloc-total[data-state="under"] .alloc-total-value { color: var(--status-warning); }
.alloc-total[data-state="over"] { border-color: color-mix(in srgb, var(--diverging-neg) 45%, var(--border));
  background: color-mix(in srgb, var(--diverging-neg) 10%, var(--surface-1)); }
.alloc-total[data-state="over"] .alloc-total-value { color: var(--diverging-neg); }
.submit-btn { background: var(--signal); color: white; border: none; border-radius: var(--radius-sm); padding: 12px 24px;
  font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 20px; font: inherit;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--signal) 14%, transparent); }
.submit-btn:hover { filter: brightness(1.06); }
.submit-btn:disabled { opacity: 0.45; cursor: not-allowed; filter: none; box-shadow: none; }
.error-banner { background: color-mix(in srgb, var(--diverging-neg) 12%, var(--surface-1));
  border: 1px solid color-mix(in srgb, var(--diverging-neg) 40%, var(--border)); border-radius: 8px;
  padding: 12px 14px; font-size: 13px; color: var(--text-primary); margin-bottom: 18px; }
.form-footnote { font-size: 12px; color: var(--text-muted); margin-top: 18px; max-width: 60ch; }

/* ---- Ticker / benchmark combobox ---- */
.ticker-combobox { position: relative; }
.ticker-search { width: 100%; }
.ticker-listbox { position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; right: 0; max-height: 240px;
  overflow-y: auto; margin: 0; padding: 4px; list-style: none; background: var(--surface-1);
  border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.14); }
.ticker-option { display: flex; gap: 8px; align-items: baseline; padding: 7px 9px; border-radius: 5px; cursor: pointer;
  font-size: 13px; }
.ticker-option .opt-symbol { font-family: var(--font-mono); font-weight: 600; color: var(--text-primary); flex: none;
  min-width: 52px; }
.ticker-option .opt-name { color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ticker-option.is-active, .ticker-option:hover { background: color-mix(in srgb, var(--signal) 14%, var(--surface-1)); }
.ticker-empty-note { padding: 7px 9px; font-size: 12px; color: var(--text-muted); }

/* ---- Results freshness banner + section numbering (results panel) ---- */
.freshness-banner { background: var(--surface-1); border: 1px solid var(--border); border-left: 2px solid var(--signal);
  border-radius: var(--radius-md); padding: 14px 16px; font-size: 12.5px; color: var(--text-secondary);
  margin: 18px 0 26px; line-height: 1.6; }
.freshness-banner strong { color: var(--text-primary); font-family: var(--font-mono); font-weight: 600; font-size: 12px; }
.freshness-banner .disclaimer { font-size: 12px; color: var(--text-muted); margin-top: 8px; }
.section-title { font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--text-muted); margin: 30px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.section-title:first-of-type { margin-top: 8px; }

/* ---- Results empty state ---- */
.empty-results { border: 1px dashed var(--baseline); border-radius: var(--radius-lg); padding: 32px 30px;
  text-align: left; background: var(--surface-1); }
.empty-results h2 { font-size: 19px; margin: 0 0 8px; font-family: var(--font-display); }
.empty-results p { font-size: 13.5px; color: var(--text-secondary); max-width: 56ch; line-height: 1.6; }

@media (max-width: 860px) {
  /* `align-items: flex-start` (set for the desktop row layout, cross-axis = height) needs to
     become `stretch` once flex-direction flips to column (cross-axis = width) -- otherwise
     `.app-main` sizes to its widest descendant's content (e.g. a chart's 480px min-width SVG)
     instead of the viewport, and the whole page gains a horizontal scrollbar. */
  .app-shell { flex-direction: column; align-items: stretch; }
  .app-sidebar { position: sticky; top: 0; z-index: 30; height: auto; width: 100%; flex: none;
    border-right: none; border-bottom: 1px solid var(--border); padding: 14px 16px; background: var(--page-plane); }
  .masthead { margin-bottom: 12px; }
  .app-nav { flex-direction: row; overflow-x: auto; gap: 6px; padding-bottom: 4px; margin-bottom: 0; }
  .nav-item { flex: none; white-space: nowrap; padding: 7px 10px; border-left: none; border-bottom: 2px solid transparent; }
  .nav-item.is-active { border-left: none; border-bottom-color: var(--signal); }
  .sidebar-foot { display: none; }
  .app-main { padding: 22px 16px 60px; }
  .method-grid { grid-template-columns: 1fr; }
  .quickstart-banner { flex-direction: column; align-items: stretch; }
  .quickstart-btn { justify-content: center; }
  .share-bar { flex-direction: column; align-items: stretch; }
}

/* ---- Print / "Export as PDF" (browser print-to-PDF, see decision 0008) ---- */
@media print {
  :root { color-scheme: light; }
  .viz-root {
    --surface-1: #ffffff !important; --page-plane: #ffffff !important; --text-primary: #0d1117 !important;
    --text-secondary: #333a4a !important; --border: #d8dde6 !important; background: #fff !important;
  }
  .app-sidebar, .hero-cta-row, .quickstart-banner, .share-bar, .theme-btn, .add-row-btn, .helper-btn,
  .row-remove, .submit-btn, .learn-xref-row, .nav-item { display: none !important; }
  .app-shell { display: block; }
  .app-main { padding: 0; }
  .app-main-inner { max-width: none; }
  .hero-card::before { display: none; }
  .tab-panel[hidden] { display: none !important; }
  .viz-card, .ref-card, .learn-card, .glossary-entry, .rw-card { break-inside: avoid; box-shadow: none; }
}
"""


def _shell_script() -> str:
    return """
(function () {
  var buttons = document.querySelectorAll('[data-tab-target]');
  var panels = document.querySelectorAll('[data-tab-panel]');
  function activate(id, pushHash) {
    var found = false;
    panels.forEach(function (p) {
      var match = p.getAttribute('data-tab-panel') === id;
      p.hidden = !match;
      if (match) found = true;
    });
    if (!found) return;
    buttons.forEach(function (b) {
      var active = b.getAttribute('data-tab-target') === id;
      b.classList.toggle('is-active', active);
      b.setAttribute('aria-current', active ? 'true' : 'false');
    });
    if (pushHash) { history.replaceState(null, '', '#' + id); }
    var panel = document.querySelector('[data-tab-panel="' + id + '"]');
    if (panel) panel.scrollIntoView({ block: 'start' });
  }
  buttons.forEach(function (b) {
    b.addEventListener('click', function () { activate(b.getAttribute('data-tab-target'), true); });
  });
  var hash = window.location.hash.replace('#', '');
  if (hash) activate(hash, false);

  function initCombobox(root) {
    var input = root.querySelector('[data-combobox-input]');
    var hiddenField = root.querySelector('[data-combobox-value]');
    var list = root.querySelector('[data-combobox-list]');
    var source = window[root.getAttribute('data-combobox-source')] || [];
    var items = [];
    var activeIndex = -1;

    function render(query) {
      var q = query.trim().toUpperCase();
      items = !q ? [] : source.filter(function (t) {
        return t[0].indexOf(q) === 0 || t[1].toUpperCase().indexOf(q) !== -1;
      }).slice(0, 8);
      activeIndex = -1;
      list.innerHTML = '';
      if (q && items.length === 0) {
        var empty = document.createElement('li');
        empty.className = 'ticker-empty-note';
        empty.textContent = 'No match in the curated list.';
        list.appendChild(empty);
      }
      items.forEach(function (t, i) {
        var li = document.createElement('li');
        li.setAttribute('role', 'option');
        li.className = 'ticker-option';
        li.dataset.index = String(i);
        var sym = document.createElement('span'); sym.className = 'opt-symbol'; sym.textContent = t[0];
        var name = document.createElement('span'); name.className = 'opt-name'; name.textContent = t[1];
        li.appendChild(sym); li.appendChild(name);
        li.addEventListener('mousedown', function (e) { e.preventDefault(); select(i); });
        list.appendChild(li);
      });
      list.hidden = list.children.length === 0;
      input.setAttribute('aria-expanded', list.hidden ? 'false' : 'true');
    }

    function highlight(idx) {
      activeIndex = idx;
      Array.prototype.forEach.call(list.querySelectorAll('.ticker-option'), function (li, i) {
        li.classList.toggle('is-active', i === idx);
      });
    }

    function select(i) {
      var t = items[i];
      if (!t) return;
      input.value = t[0] + ' \\u2014 ' + t[1];
      hiddenField.value = t[0];
      list.hidden = true;
      input.setAttribute('aria-expanded', 'false');
    }

    input.addEventListener('input', function () { hiddenField.value = ''; render(input.value); });
    input.addEventListener('focus', function () { if (input.value) render(input.value); });
    input.addEventListener('keydown', function (e) {
      var options = list.querySelectorAll('.ticker-option');
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (options.length) highlight(Math.min(activeIndex + 1, options.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (options.length) highlight(Math.max(activeIndex - 1, 0));
      } else if (e.key === 'Enter') {
        if (activeIndex >= 0) { e.preventDefault(); select(activeIndex); }
      } else if (e.key === 'Escape') {
        list.hidden = true;
      }
    });
    input.addEventListener('blur', function () {
      window.setTimeout(function () {
        if (!hiddenField.value) input.value = '';
        list.hidden = true;
      }, 120);
    });
  }

  document.querySelectorAll('[data-combobox]').forEach(initCombobox);
  window.__flInitCombobox = initCombobox;

  var addBtn = document.getElementById('add-holding-btn');
  if (addBtn) {
    addBtn.addEventListener('click', function () {
      var tpl = document.getElementById('holding-row-template');
      var frag = tpl.content.cloneNode(true);
      document.getElementById('holdings-rows').appendChild(frag);
      var rows = document.getElementById('holdings-rows').querySelectorAll('[data-combobox]');
      window.__flInitCombobox(rows[rows.length - 1]);
    });
  }

  // ---- Allocation total, "split evenly" / "normalize" helpers (Phase 9b) ----
  var rowsContainer = document.getElementById('holdings-rows');
  var allocTotal = document.getElementById('alloc-total');
  if (rowsContainer && allocTotal) {
    var allocValueEl = document.getElementById('alloc-total-value');
    var allocMsgEl = document.getElementById('alloc-total-msg');
    var submitBtn = document.getElementById('run-analysis-btn');

    function activeWeightRows() {
      return Array.prototype.filter.call(rowsContainer.querySelectorAll('.holding-row'), function (row) {
        var hidden = row.querySelector('[data-combobox-value]');
        return !!(hidden && hidden.value);
      });
    }

    function round2(n) { return Math.round(n * 100) / 100; }

    function recalcAlloc() {
      var inputs = rowsContainer.querySelectorAll('input[name="weight"]');
      var total = 0;
      var anyFilled = false;
      inputs.forEach(function (inp) {
        if (inp.value.trim() !== '') anyFilled = true;
        var v = parseFloat(inp.value);
        if (!isNaN(v)) total += v;
      });
      total = round2(total);
      allocValueEl.textContent = total + '%';
      var diff = round2(100 - total);
      var state;
      if (!anyFilled) {
        state = 'empty';
        allocMsgEl.textContent = 'Enter an allocation for each holding \\u2014 they must add up to 100%.';
      } else if (Math.abs(diff) < 0.05) {
        state = 'exact';
        allocMsgEl.textContent = 'Ready to submit.';
      } else if (diff > 0) {
        state = 'under';
        allocMsgEl.textContent = 'Add ' + diff + '% more to reach 100%.';
      } else {
        state = 'over';
        allocMsgEl.textContent = 'Remove ' + Math.abs(diff) + '% to reach 100%.';
      }
      allocTotal.setAttribute('data-state', state);
      if (submitBtn) {
        submitBtn.disabled = state !== 'exact';
        submitBtn.setAttribute('aria-disabled', state !== 'exact' ? 'true' : 'false');
      }
    }
    window.__flRecalcAlloc = recalcAlloc;

    rowsContainer.addEventListener('input', function (e) {
      if (e.target && e.target.name === 'weight') recalcAlloc();
    });

    var splitBtn = document.getElementById('split-evenly-btn');
    if (splitBtn) {
      splitBtn.addEventListener('click', function () {
        var rows = activeWeightRows();
        if (!rows.length) return;
        var base = Math.floor((100 / rows.length) * 100) / 100;
        var assigned = 0;
        rows.forEach(function (row, i) {
          var input = row.querySelector('input[name="weight"]');
          var val = (i === rows.length - 1) ? round2(100 - assigned) : base;
          assigned = round2(assigned + val);
          input.value = val;
        });
        recalcAlloc();
      });
    }

    var normBtn = document.getElementById('normalize-btn');
    if (normBtn) {
      normBtn.addEventListener('click', function () {
        var rows = activeWeightRows();
        if (!rows.length) return;
        var values = rows.map(function (row) {
          var v = parseFloat(row.querySelector('input[name="weight"]').value);
          return (!isNaN(v) && v > 0) ? v : 0;
        });
        var sum = values.reduce(function (a, b) { return a + b; }, 0);
        if (sum <= 0) {
          if (splitBtn) splitBtn.click();
          return;
        }
        var assigned = 0;
        rows.forEach(function (row, i) {
          var input = row.querySelector('input[name="weight"]');
          var val = (i === rows.length - 1) ? round2(100 - assigned) : round2((values[i] / sum) * 100);
          assigned = round2(assigned + val);
          input.value = val;
        });
        recalcAlloc();
      });
    }

    recalcAlloc();
  }

  // ---- Shareable-link "copy" control (Phase 9c) ----
  document.querySelectorAll('[data-share-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var wrap = btn.closest('.share-bar');
      if (!wrap) return;
      var input = wrap.querySelector('.share-link-input');
      var row = wrap.querySelector('.share-link-row');
      var note = wrap.querySelector('.share-copied-note');
      row.classList.add('is-visible');
      input.select();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(input.value).then(function () {
          note.classList.add('is-visible');
          window.setTimeout(function () { note.classList.remove('is-visible'); }, 2000);
        });
      }
    });
  });
})();
"""


def render_ticker_data_script(tickers: list[tuple[str, str]], benchmarks: list[tuple[str, str]]) -> str:
    """Embed the curated universes as JSON the combobox JS filters client-side.

    `</script`-safe: JSON can't itself contain that sequence for any of our
    curated names, but the slash is escaped anyway as a defensive habit.
    """
    tickers_json = json.dumps([[s, n] for s, n in tickers], ensure_ascii=False)
    benchmarks_json = json.dumps([[s, n] for s, n in benchmarks], ensure_ascii=False)
    tickers_json = tickers_json.replace("</", "<\\/")
    benchmarks_json = benchmarks_json.replace("</", "<\\/")
    return f"<script>window.__FL_TICKERS__={tickers_json};window.__FL_BENCHMARKS__={benchmarks_json};</script>"


def render_combobox(
    *,
    field_name: str,
    source_var: str,
    selected_symbol: str = "",
    selected_label: str = "",
    placeholder: str = "Search ticker or company…",
) -> str:
    display_value = f"{selected_symbol} — {selected_label}" if selected_symbol and selected_label else ""
    return (
        f'<div class="ticker-combobox" data-combobox data-combobox-source="{esc(source_var)}">'
        f'<input type="text" class="ticker-search" data-combobox-input role="combobox" '
        f'aria-expanded="false" aria-autocomplete="list" autocomplete="off" '
        f'placeholder="{esc(placeholder)}" value="{esc(display_value)}">'
        f'<input type="hidden" name="{esc(field_name)}" data-combobox-value value="{esc(selected_symbol)}">'
        f'<ul class="ticker-listbox" role="listbox" data-combobox-list hidden></ul>'
        "</div>"
    )


def render_app_shell(
    *,
    active_tab: str,
    panels: dict[str, str],
    page_title: str,
    ticker_data_script: str,
    request_base_url: str = "",
    meta_description: str = DEFAULT_META_DESCRIPTION,
    canonical_path: str = "/",
) -> str:
    """Assembles the full page shell, including Open Graph/Twitter social-preview meta
    (`docs/project-standards.md` rule 8) -- `request_base_url` (e.g.
    `http://127.0.0.1:8000`, or the deployed origin once Phase 11 ships) is threaded in
    from the route handler so `og:image`/`og:url` are always absolute, which link-unfurling
    crawlers (LinkedIn, Slack) require; a relative URL silently fails to preview. The image
    itself (`app/static/og-image.png`) is a static asset generated once via
    `scripts/generate_og_image.py` -- see decision 0008.
    """
    from app.dashboard import viz  # local import to avoid a cycle at module load

    nav_html = []
    for tab_id, label in NAV_ITEMS:
        pending = '<span class="nav-pending">soon</span>' if tab_id in _PENDING_TABS else ""
        active_cls = " is-active" if tab_id == active_tab else ""
        aria = "true" if tab_id == active_tab else "false"
        idx = NAV_ITEMS.index((tab_id, label)) + 1
        nav_html.append(
            f'<button type="button" class="nav-item{active_cls}" data-tab-target="{esc(tab_id)}" '
            f'aria-current="{aria}"><span class="nav-mark">[{idx:02d}]</span>'
            f'<span class="nav-label">{esc(label)}</span>{pending}</button>'
        )

    panel_html = []
    for tab_id, _label in NAV_ITEMS:
        content = panels.get(tab_id, "")
        hidden_attr = "" if tab_id == active_tab else " hidden"
        panel_html.append(
            f'<section class="tab-panel" data-tab-panel="{esc(tab_id)}"{hidden_attr}>'
            f'<div class="app-main-inner">{content}</div></section>'
        )

    base = request_base_url.rstrip("/")
    image_url = f"{base}/static/og-image.png" if base else "/static/og-image.png"
    page_url = f"{base}{canonical_path}" if base else canonical_path
    meta_html = f"""
<meta name="description" content="{esc(meta_description)}">
<link rel="canonical" href="{esc(page_url)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Factor Lens">
<meta property="og:title" content="{esc(page_title)}">
<meta property="og:description" content="{esc(meta_description)}">
<meta property="og:url" content="{esc(page_url)}">
<meta property="og:image" content="{esc(image_url)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Factor Lens — live CAPM, Fama-French, and Markowitz portfolio attribution">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(page_title)}">
<meta name="twitter:description" content="{esc(meta_description)}">
<meta name="twitter:image" content="{esc(image_url)}">
"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page_title)}</title>
{meta_html}
{FAVICON_LINK}
{FONT_LINKS}
<style>{viz.CHART_STYLE}{SHELL_STYLE}</style>
</head>
<body class="viz-root">
<div class="app-shell">
  <aside class="app-sidebar">
    <div class="masthead">
      <div class="masthead-mark">FL</div>
      <div>
        <div class="masthead-title">Factor Lens</div>
        <div class="masthead-tag">Factor attribution console</div>
      </div>
    </div>
    <nav class="app-nav" aria-label="Report sections">{''.join(nav_html)}</nav>
    <div class="sidebar-foot">
      <button class="theme-btn" type="button" data-theme-toggle>Toggle theme</button>
      <div class="sidebar-disclaimer">Internal decision-support analytics. Not investment advice, not a
      recommendation to buy, sell, or rebalance.</div>
    </div>
  </aside>
  <main class="app-main">{''.join(panel_html)}</main>
</div>
{ticker_data_script}
<script>{viz.CHART_SCRIPT}</script>
<script>{_shell_script()}</script>
</body>
</html>"""


_PENDING_TABS: set[str] = set()


# ---------------------------------------------------------------------------
# Static section content
# ---------------------------------------------------------------------------


def render_overview_section() -> str:
    return """
<div class="section-eyebrow">[01] Overview</div>
<h1>Factor Lens</h1>
<div class="hero-card">
  <p><strong>Factor Lens explains why a portfolio behaves the way it does.</strong> Enter your holdings and
  a benchmark, and it computes your CAPM market beta, Fama-French factor loadings (size, value, and
  optionally profitability/investment), and where your portfolio sits on a modeled Markowitz efficient
  frontier &mdash; all from live market data, with the statistical diagnostics (confidence intervals,
  t-stats, p-values) shown alongside every estimate rather than a bare number.</p>
  <p>This is decision-support analytics for retail investors and small RIAs who want to understand their
  exposures, not a black-box score, a trading signal, or personalized investment advice.</p>
  <div class="hero-cta-row">
    <button type="button" class="hero-cta" data-tab-target="inputs">Enter your holdings →</button>
    <a class="hero-cta-secondary" href="/dashboard/sample">▸ Run a live example</a>
  </div>
  <div class="method-grid">
    <div class="method-card">
      <div class="method-mark">CAPM</div>
      <h3>Market beta</h3>
      <p>Single-factor exposure to your chosen benchmark, with confidence intervals and significance.</p>
    </div>
    <div class="method-card">
      <div class="method-mark">Fama-French</div>
      <h3>Factor loadings</h3>
      <p>3- or 5-factor exposure (market, size, value, and optionally profitability/investment).</p>
    </div>
    <div class="method-card">
      <div class="method-mark">Markowitz</div>
      <h3>Efficient frontier</h3>
      <p>Where your as-entered portfolio sits against the modeled long-only efficient set.</p>
    </div>
  </div>
</div>
<div class="disclaimer-strip">Computed live from OpenBB (yfinance provider) equity/benchmark prices and
Kenneth French's Data Library factor series &mdash; see Tools &amp; Technologies for the full stack, and
References &amp; Formulas for the exact math, formula-by-formula, with sources.</div>
"""


def render_tools_section() -> str:
    def group(title: str, items: list[tuple[str, str]]) -> str:
        rows = "".join(f'<li><span class="tool-name">{esc(n)}</span><span>{esc(d)}</span></li>' for n, d in items)
        return f'<div class="tool-group"><h3>{esc(title)}</h3><ul class="tool-list">{rows}</ul></div>'

    body = "".join(
        [
            group(
                "Application & API",
                [
                    ("Python 3.11", "language runtime"),
                    ("FastAPI", "HTTP layer for the JSON API and the server-rendered dashboard"),
                    ("Pydantic v2", "request/response schema validation, holdings/portfolio contracts"),
                    ("uv", "dependency management and lockfile (`uv.lock`)"),
                ],
            ),
            group(
                "Market & factor data",
                [
                    ("OpenBB Open Data Platform", "equity and benchmark price history (yfinance provider)"),
                    ("Kenneth French's Data Library", "Fama-French 3-/5-factor and risk-free return series, via pandas-datareader"),
                ],
            ),
            group(
                "Quantitative core",
                [
                    ("NumPy / pandas", "return-series alignment and array math"),
                    ("statsmodels", "OLS regression with Newey-West HAC standard errors (CAPM, Fama-French)"),
                    ("SciPy (SLSQP)", "constrained optimization for the long-only Markowitz efficient frontier"),
                ],
            ),
            group(
                "Presentation",
                [
                    ("Hand-built inline SVG", "every chart, no client-side charting library (see decision 0004)"),
                    ("Vanilla JavaScript", "tab navigation, the ticker combobox, theme toggle &mdash; no framework or build step"),
                    ("Server-rendered HTML/CSS", "no Jinja2; pages assembled as plain Python string templates"),
                ],
            ),
            group(
                "Quality & delivery",
                [
                    ("pytest + httpx", "live, non-mocked end-to-end tests against real market data"),
                    ("Railway", "planned deployment target (Phase 11)"),
                ],
            ),
        ]
    )
    return f"""
<div class="section-eyebrow">[06] Tools &amp; Technologies</div>
<h1>What this was actually built with</h1>
<p class="section-lede">Named and specific, not "some data tools" &mdash; this section doubles as a record
of the real stack behind the analysis.</p>
<div class="tool-groups">{body}</div>
"""


def render_references_section() -> str:
    """The actual formulas this app computes, with sources -- see decision 0006.

    Each card follows the same shape: a tag naming the section of code it
    documents, a plain-language "what this computes," the real notation
    (rendered with <sub>/<sup>, not an external math-typesetting library --
    consistent with this project's no-client-library convention, decision
    0004), a short legend for any symbol that isn't self-evident, and a
    primary-source citation. Content is static and trusted (not user
    input), so it isn't passed through `esc()`, matching
    `render_overview_section`/`render_tools_section` above.
    """

    def card(*, tag: str, title: str, what: str, formulas: list[tuple[str, str]], legend: str, note: str, source: str) -> str:
        formula_html = "".join(
            f'<div class="fb-eq"><span class="fb-label">{label}</span>{eq}</div>' for label, eq in formulas
        )
        return f"""
<div class="ref-card">
  <div class="ref-card-head"><span class="ref-tag">{tag}</span><h2>{title}</h2></div>
  <p class="ref-what">{what}</p>
  <div class="formula-block">{formula_html}</div>
  <p class="formula-legend">{legend}</p>
  <p class="ref-note">{note}</p>
  <p class="ref-source">{source}</p>
</div>
"""

    capm_card = card(
        tag="app/models/capm.py",
        title="CAPM &mdash; single-factor market beta",
        what=(
            "Regresses the portfolio's excess return on the chosen benchmark's excess return over the "
            "aligned sample. &beta; is the reported market beta; &alpha; is reported both as the raw "
            "periodic OLS intercept and, annualized by compounding, as &ldquo;CAPM alpha (annualized)&rdquo; "
            "on the Results tab."
        ),
        formulas=[("Regression", "R<sub>p,t</sub> &minus; R<sub>f,t</sub> = &alpha; + &beta;(R<sub>m,t</sub> &minus; R<sub>f,t</sub>) + &epsilon;<sub>t</sub>")],
        legend=(
            "<code>R<sub>p,t</sub></code> portfolio return at t &middot; <code>R<sub>f,t</sub></code> risk-free rate "
            "(Ken French Data Library) &middot; <code>R<sub>m,t</sub></code> benchmark return &middot; "
            "<code>&beta;</code> market beta &middot; <code>&alpha;</code> intercept (excess return unexplained by the market)."
        ),
        note=(
            "Fit by OLS with an intercept, standard errors via Newey-West HAC (see the Regression diagnostics "
            "card below) &mdash; not classical OLS SEs. &alpha; is annualized as "
            "(1 + &alpha;)<sup>periods/yr</sup> &minus; 1 (compounding convention; see decision 0003)."
        ),
        source="<strong>Source:</strong> Sharpe, W.F. (1964). “Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk.” "
        "<em>Journal of Finance</em>, 19(3), 425&ndash;442. Independently derived in Lintner, J. (1965) and Mossin, J. (1966).",
    )

    ff_card = card(
        tag="app/models/fama_french.py",
        title="Fama-French 3-/5-factor model",
        what=(
            "Extends CAPM with additional priced return factors, fit the same way (OLS, HAC standard "
            "errors) on the portfolio's excess return. 3-factor is this app's default; 5-factor is "
            "supported end-to-end whenever selected on the Inputs tab. Factor return series come from "
            "Kenneth French's Data Library, not OpenBB (see decision 0002)."
        ),
        formulas=[
            ("3-factor", "R<sub>p,t</sub> &minus; R<sub>f,t</sub> = &alpha; + &beta;<sub>1</sub>Mkt-RF<sub>t</sub> + &beta;<sub>2</sub>SMB<sub>t</sub> + &beta;<sub>3</sub>HML<sub>t</sub> + &epsilon;<sub>t</sub>"),
            ("5-factor", "R<sub>p,t</sub> &minus; R<sub>f,t</sub> = &alpha; + &beta;<sub>1</sub>Mkt-RF<sub>t</sub> + &beta;<sub>2</sub>SMB<sub>t</sub> + &beta;<sub>3</sub>HML<sub>t</sub> + &beta;<sub>4</sub>RMW<sub>t</sub> + &beta;<sub>5</sub>CMA<sub>t</sub> + &epsilon;<sub>t</sub>"),
        ],
        legend=(
            "<code>SMB</code> Small Minus Big (size) &middot; <code>HML</code> High Minus Low (value, book-to-market) "
            "&middot; <code>RMW</code> Robust Minus Weak (profitability) &middot; <code>CMA</code> Conservative Minus "
            "Aggressive (investment). Each is itself a spread portfolio return, not a raw price series."
        ),
        note=(
            "F-statistic and both R&sup2; and adjusted R&sup2; are reported alongside the loadings on the "
            "Results tab so overall model fit is visible, not just per-coefficient significance."
        ),
        source="<strong>Source:</strong> Fama, E.F. &amp; French, K.R. (1993). “Common Risk Factors in the Returns on Stocks and Bonds.” "
        "<em>Journal of Financial Economics</em>, 33(1), 3&ndash;56. 5-factor extension: Fama, E.F. &amp; French, K.R. (2015). "
        "“A Five-Factor Asset Pricing Model.” <em>Journal of Financial Economics</em>, 116(1), 1&ndash;22.",
    )

    hac_card = card(
        tag="app/models/_regression.py",
        title="Regression diagnostics &mdash; Newey-West HAC standard errors",
        what=(
            "Every coefficient reported by the CAPM and Fama-French regressions above (standard error, "
            "t-stat, p-value, 95% CI) uses this correction, not classical OLS standard errors &mdash; daily "
            "and monthly equity returns are routinely heteroskedastic and mildly autocorrelated, which "
            "classical SEs understate."
        ),
        formulas=[("Newey-West plug-in bandwidth", "L = floor(4 &middot; (n / 100)<sup>2/9</sup>)")],
        legend="<code>n</code> number of aligned observations in the regression sample &middot; <code>L</code> number of autocorrelation lags included in the HAC covariance estimate.",
        note="Reported on every Results page as &ldquo;Standard errors: HAC (Newey-West)&rdquo; so the convention producing a given t-stat/CI is never left implicit.",
        source="<strong>Source:</strong> Newey, W.K. &amp; West, K.D. (1987). “A Simple, Positive Semi-Definite, Heteroskedasticity and "
        "Autocorrelation Consistent Covariance Matrix.” <em>Econometrica</em>, 55(3), 703&ndash;708. Plug-in bandwidth rule: "
        "Newey, W.K. &amp; West, K.D. (1994). “Automatic Lag Selection in Covariance Matrix Estimation.” "
        "<em>Review of Economic Studies</em>, 61(4), 631&ndash;653.",
    )

    markowitz_card = card(
        tag="app/models/optimization.py",
        title="Markowitz mean-variance efficient frontier",
        what=(
            "For the entered holdings, models portfolio expected return and variance as a function of "
            "weights, then solves for the long-only efficient frontier, the global minimum-variance "
            "portfolio, and the max-Sharpe (tangency) portfolio &mdash; and locates the as-entered "
            "portfolio against all three. This is a positioning view, not a rebalancing recommendation."
        ),
        formulas=[
            ("Portfolio return", "R<sub>p</sub> = w<sup>T</sup>&mu;"),
            ("Portfolio variance", "&sigma;<sub>p</sub><sup>2</sup> = w<sup>T</sup>&Sigma;w"),
            ("Efficient point (long-only)", "min<sub>w</sub> w<sup>T</sup>&Sigma;w &nbsp; s.t. &nbsp; w<sup>T</sup>&mu; = target, &nbsp; &Sigma;w<sub>i</sub> = 1, &nbsp; w<sub>i</sub> &ge; 0"),
            ("Max Sharpe (tangency)", "max<sub>w</sub> (w<sup>T</sup>&mu; &minus; R<sub>f</sub>) / &radic;(w<sup>T</sup>&Sigma;w) &nbsp; s.t. &nbsp; same constraints"),
            ("Sharpe ratio", "S = (R<sub>p</sub> &minus; R<sub>f</sub>) / &sigma;<sub>p</sub>"),
        ],
        legend=(
            "<code>w</code> holding weight vector &middot; <code>&mu;</code> vector of expected (annualized) holding "
            "returns &middot; <code>&Sigma;</code> annualized covariance matrix of holding returns &middot; "
            "<code>R<sub>f</sub></code> risk-free rate."
        ),
        note=(
            "&mu; and &Sigma; are annualized by <em>linear scaling</em> (periodic mean/covariance &times; periods per "
            "year) &mdash; the textbook i.i.d.-returns convention mean-variance optimization assumes by construction, "
            "and deliberately different from CAPM/Fama-French alpha's compounding convention above (decision 0003). "
            "Long-only (<code>w<sub>i</sub> &ge; 0</code>) is this app's default, reflecting how retail/small-RIA holdings "
            "are actually held; each frontier point is solved numerically via SLSQP since long-only mean-variance "
            "optimization has no closed form. If the sample covariance matrix is ill-conditioned or non-PSD, it is "
            "regularized by eigenvalue clipping before solving &mdash; the Results tab flags this explicitly "
            "(&ldquo;covariance regularized&rdquo;) whenever it happens."
        ),
        source="<strong>Source:</strong> Markowitz, H. (1952). “Portfolio Selection.” <em>Journal of Finance</em>, 7(1), 77&ndash;91. "
        "Sharpe ratio: Sharpe, W.F. (1966). “Mutual Fund Performance.” <em>Journal of Business</em>, 39(1), 119&ndash;138 "
        "(reframed as “The Sharpe Ratio,” <em>Journal of Portfolio Management</em>, 1994).",
    )

    attribution_card = card(
        tag="app/dashboard/attribution.py",
        title="Return &amp; risk attribution",
        what=(
            "Not a separate model &mdash; an exact algebraic decomposition of the Fama-French regression "
            "above, evaluated at the sample mean. Because OLS with an intercept guarantees the fitted "
            "residual has zero mean over the regression sample, splitting the realized mean excess return "
            "into &alpha; plus each factor's own contribution reproduces the realized total exactly, not "
            "approximately."
        ),
        formulas=[
            ("Return attribution (exact identity)", "mean(R<sub>p</sub> &minus; R<sub>f</sub>) = &alpha; + &Sigma;<sub>i</sub> &beta;<sub>i</sub> &middot; mean(factor<sub>i</sub>)"),
            ("Risk attribution", "factor-explained share = R&sup2; &nbsp;&nbsp; idiosyncratic share = 1 &minus; R&sup2;"),
        ],
        legend="<code>&beta;<sub>i</sub></code> the fitted loading on factor <em>i</em> &middot; <code>mean(factor<sub>i</sub>)</code> that factor's own realized mean return over the same aligned window.",
        note=(
            "Contributions are shown per-period (not re-annualized), since annualizing pieces under two "
            "different conventions and summing them would no longer reconcile to the realized total the "
            "way the per-period identity above does exactly &mdash; see decision 0003."
        ),
        source="<strong>Source:</strong> Direct algebraic consequence of the OLS fit above (standard regression identity, not a separately published result) &mdash; see the derivation in <code>app/dashboard/attribution.py</code>'s module docstring.",
    )

    return f"""
<div class="section-eyebrow">[07] References &amp; Formulas</div>
<h1>The exact math this app computes</h1>
<p class="section-lede">What's actually implemented in <code>app/models/</code> and
<code>app/dashboard/attribution.py</code> &mdash; not a generic textbook summary. Each card names the module
it documents, the real notation used, and a primary source.</p>
<div class="ref-groups">
{capm_card}{ff_card}{hac_card}{markowitz_card}{attribution_card}
</div>
<div class="ref-card">
  <div class="ref-card-head"><h2>Works cited</h2></div>
  <ol class="ref-cited-list">
    <li>Sharpe, W.F. (1964). Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk. <em>Journal of Finance</em>, 19(3), 425&ndash;442.</li>
    <li>Lintner, J. (1965). The Valuation of Risk Assets and the Selection of Risky Investments in Stock Portfolios and Capital Budgets. <em>Review of Economics and Statistics</em>, 47(1), 13&ndash;37.</li>
    <li>Markowitz, H. (1952). Portfolio Selection. <em>Journal of Finance</em>, 7(1), 77&ndash;91.</li>
    <li>Sharpe, W.F. (1966). Mutual Fund Performance. <em>Journal of Business</em>, 39(1), 119&ndash;138.</li>
    <li>Fama, E.F. &amp; French, K.R. (1993). Common Risk Factors in the Returns on Stocks and Bonds. <em>Journal of Financial Economics</em>, 33(1), 3&ndash;56.</li>
    <li>Fama, E.F. &amp; French, K.R. (2015). A Five-Factor Asset Pricing Model. <em>Journal of Financial Economics</em>, 116(1), 1&ndash;22.</li>
    <li>Newey, W.K. &amp; West, K.D. (1987). A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix. <em>Econometrica</em>, 55(3), 703&ndash;708.</li>
    <li>Newey, W.K. &amp; West, K.D. (1994). Automatic Lag Selection in Covariance Matrix Estimation. <em>Review of Economic Studies</em>, 61(4), 631&ndash;653.</li>
  </ol>
  <p class="ref-note">Full methodology rationale (why HAC, why long-only, why linear-scaling vs. compounding
  annualization, why eigenvalue-clipping regularization) is logged in
  <code>docs/decisions/0003-phase2-quant-methodology.md</code>; this section documents the resulting math
  itself, not the tradeoffs behind it.</p>
</div>
"""


def _xref(tab_id: str, label: str) -> str:
    """A pill-styled button that jumps to another tab, reusing the same `[data-tab-target]`
    mechanism the sidebar nav uses (see `_shell_script` -- it queries *all* elements with
    this attribute, not just nav buttons)."""
    return f'<button type="button" class="learn-xref" data-tab-target="{esc(tab_id)}">{esc(label)} &rarr;</button>'


def render_learning_section() -> str:
    """Phase 9: the dual-register 'what does this actually mean' layer -- the project's
    stated core differentiator (roadmap: "Why this project, why this shape"). Deliberately
    static and reference-style, mirroring `render_references_section()`'s shape and card
    structure, so a reader can move between "what's the math" (References & Formulas) and
    "what does it mean for me" (here) without a jarring shift in how the page is built.
    Cross-links to References & Formulas rather than re-deriving any formula -- this
    section's job is plain-language interpretation and the "so what," not notation.
    """

    def card(*, tag: str, title: str, plain: str, technical: str, note: str | None, xrefs: list[tuple[str, str]]) -> str:
        xref_html = (
            '<div class="learn-xref-row">' + "".join(_xref(t, label) for t, label in xrefs) + "</div>" if xrefs else ""
        )
        note_html = f'<p class="learn-note">{note}</p>' if note else ""
        return f"""
<div class="learn-card">
  <div class="learn-card-head"><span class="learn-tag">{tag}</span><h2>{title}</h2></div>
  <div class="learn-register is-plain">
    <span class="learn-register-label">Plain language</span>
    <p>{plain}</p>
  </div>
  <div class="learn-register is-technical">
    <span class="learn-register-label">Technical</span>
    <p>{technical}</p>
  </div>
  {note_html}
  {xref_html}
</div>
"""

    beta_card = card(
        tag="Results · 1. Factor exposure",
        title="CAPM beta &mdash; your market sensitivity",
        plain=(
            "Beta answers one question: when the market moves 1%, how much does your portfolio tend to move? "
            "A beta of 1.20 means your portfolio has historically swung about 20% harder than the benchmark in "
            "both directions &mdash; bigger gains in up markets, bigger losses in down markets. A beta of 0.60 "
            "means the opposite: your portfolio has historically been noticeably calmer than the market. Beta "
            "on its own doesn't say whether that's good or bad &mdash; it says how much of your risk is simply "
            "\"the market, amplified or dampened,\" versus something else."
        ),
        technical=(
            "&beta; is the slope coefficient from regressing your portfolio's excess return on the benchmark's "
            "excess return (see the CAPM regression in References &amp; Formulas). It is a point estimate with "
            "sampling uncertainty, which is why the Results tab always shows it with a 95% confidence interval, "
            "a t-stat, and a p-value rather than the bare number &mdash; a beta of 1.20 with a CI of "
            "<code>[0.4, 2.0]</code> is a much weaker claim than the same 1.20 with a CI of "
            "<code>[1.1, 1.3]</code>. <code>&alpha;</code> (the regression intercept) is the average excess "
            "return <em>not</em> explained by market exposure at all; <code>R&sup2;</code> is the share of your "
            "portfolio's return variance the single market factor explains &mdash; a low CAPM R&sup2; is itself "
            "informative: it means a one-factor market story is incomplete for this portfolio, which is exactly "
            "what the Fama-French model below is for."
        ),
        note=None,
        xrefs=[("references", "See the exact regression"), ("results", "See your beta")],
    )

    ff_card = card(
        tag="Results · 1. Factor exposure",
        title="Fama-French loadings &mdash; what kind of stocks you actually hold",
        plain=(
            "CAPM only asks \"how much market.\" Fama-French asks a follow-up: <em>what kind</em> of market "
            "exposure &mdash; is your portfolio tilted toward small companies or large ones, cheap-relative-to-"
            "book (\"value\") stocks or expensive-growth ones, highly profitable companies or not, "
            "conservatively-run companies or aggressively-expanding ones? Each factor loading is a lean, not a "
            "bet: a positive Size (SMB) loading means your holdings behave more like small-cap stocks than "
            "large-cap ones; a positive Value (HML) loading means they behave more like cheap value stocks than "
            "expensive growth stocks; and so on for Profitability (RMW) and Investment (CMA). None of this is "
            "prescriptive &mdash; it's a description of the exposures you already have, in the same language "
            "professional factor investors use to describe theirs."
        ),
        technical=(
            "Each &beta;<sub>i</sub> is a partial-regression coefficient: your portfolio's sensitivity to that "
            "one factor's spread-portfolio return, holding the other factors in the regression fixed. A "
            "loading is only worth reading as a real exposure &mdash; not noise &mdash; when its 95% CI excludes "
            "zero (equivalently, p &lt; 0.05); the Results tab plots the CI as a whisker under every bar for "
            "exactly this reason, and the table view gives the exact standard error, t-stat, and p-value per "
            "factor. Fama-French R&sup2; (and adjusted R&sup2;, and the overall F-statistic) tell you how much "
            "better this multi-factor story fits than CAPM's single factor did &mdash; a materially higher "
            "Fama-French R&sup2; than CAPM R&sup2; means style tilts (size/value/profitability/investment), not "
            "just raw market exposure, are doing real explanatory work for this portfolio."
        ),
        note=None,
        xrefs=[("references", "See the exact regression"), ("results", "See your loadings")],
    )

    frontier_card = card(
        tag="Results · 2. Efficient frontier",
        title="Frontier position &mdash; are you getting paid for the risk you're taking",
        plain=(
            "Given exactly the holdings you entered (nothing added, nothing swapped out) and how they've "
            "historically moved together, there's a best-achievable return for every level of risk (volatility) "
            "&mdash; just by re-weighting the same holdings, long-only, no leverage, no shorting. That curve is "
            "the modeled efficient frontier. Your as-entered portfolio is one dot; the frontier is the outer "
            "edge of what your own holdings-set could have achieved. If your dot sits noticeably below the "
            "line, it means: at the amount of risk you're already carrying, a different weighting of the exact "
            "same names could historically have earned more return for that same risk &mdash; not a suggestion "
            "to hold different stocks, and not a signal to act on. It's a mirror, not an instruction."
        ),
        technical=(
            "The frontier solves, for each target return, "
            "<code>min<sub>w</sub> w<sup>T</sup>&Sigma;w</code> subject to <code>w<sup>T</sup>&mu; = target</code>, "
            "<code>&Sigma;w<sub>i</sub> = 1</code>, <code>w<sub>i</sub> &ge; 0</code> &mdash; long-only by "
            "default (retail/small-RIA holdings are actually held long; see decision 0003 for the rationale and "
            "for how to get the unconstrained textbook frontier instead). Two other points are marked alongside "
            "your own: the <strong>global minimum-variance</strong> portfolio (lowest possible volatility on "
            "this frontier, regardless of return) and the <strong>max-Sharpe / tangency</strong> portfolio (the "
            "point maximizing return per unit of risk, <code>S = (R<sub>p</sub> &minus; R<sub>f</sub>) / "
            "&sigma;<sub>p</sub></code>). \"Return gap at matched volatility\" is the frontier's return at your "
            "exact volatility minus your own return &mdash; the single cleanest number for how far below the "
            "achievable set your as-entered weights currently sit. A flagged \"covariance regularized\" warning "
            "means your holding set's correlation structure was numerically unstable (few holdings, few "
            "observations, near-duplicate positions) and the frontier should be read as directional, not exact."
        ),
        note=(
            "Long-only means the frontier never assumes you can short a holding or use leverage &mdash; it is "
            "strictly \"the best return achievable by re-weighting exactly the stocks you already picked,\" which "
            "is why it's a narrower, more realistic object than the textbook unconstrained frontier."
        ),
        xrefs=[("references", "See the exact optimization"), ("results", "See your frontier")],
    )

    attribution_card = card(
        tag="Results · 3. Return &amp; risk attribution",
        title="Return &amp; risk attribution &mdash; putting it back together",
        plain=(
            "The three views above are exposures; this one is accounting. Your portfolio's average per-period "
            "return gets split, exactly, into how much came from being exposed to the market, how much from "
            "your size/value/profitability/investment tilts, and how much is unexplained by any of that "
            "(\"alpha\" &mdash; could be stock-picking, could just be noise in this sample). Separately, your "
            "risk (return variance) gets split into how much is explained by those same broad factors versus "
            "how much is <em>idiosyncratic</em> &mdash; specific to the individual names you hold rather than "
            "the market or style tilts they share. A portfolio that's mostly idiosyncratic risk is a bet on "
            "specific companies; a portfolio that's mostly factor risk is, whether you meant it to be or not, "
            "mostly a bet on the market and a couple of style tilts."
        ),
        technical=(
            "Return attribution is an exact algebraic identity, not an approximation: because the Fama-French "
            "OLS fit includes an intercept, the fitted residual has zero mean over the regression sample, so "
            "<code>mean(R<sub>p</sub> &minus; R<sub>f</sub>) = &alpha; + &Sigma;<sub>i</sub> &beta;<sub>i</sub> "
            "&middot; mean(factor<sub>i</sub>)</code> reproduces your realized mean excess return exactly, not "
            "approximately (see the module docstring in <code>app/dashboard/attribution.py</code> for the full "
            "derivation). Risk attribution is simply the factor model's own <code>R&sup2;</code> (factor-"
            "explained share) and <code>1 &minus; R&sup2;</code> (idiosyncratic share) &mdash; no extra "
            "computation beyond what the regression already reports. Contributions are shown per-period, not "
            "re-annualized, because CAPM/Fama-French alpha and the frontier's inputs use two deliberately "
            "different annualization conventions (compounding vs. linear scaling &mdash; decision 0003); summing "
            "already-annualized pieces from different conventions would silently break the identity above."
        ),
        note=None,
        xrefs=[("references", "See the exact identity"), ("results", "See your attribution")],
    )

    return f"""
<div class="section-eyebrow">[04] Learning</div>
<h1>What your numbers actually mean</h1>
<p class="section-lede">This is the idea's core differentiator: not just computing CAPM beta, Fama-French
loadings, and a frontier position, but explaining what each one means for your specific portfolio, in both a
plain-language and a technical register. For the exact notation and sourcing behind every formula referenced
below, see References &amp; Formulas &mdash; this section is deliberately the interpretation layer, not a
second derivation of the math.</p>
<div class="learn-groups">
{beta_card}{ff_card}{frontier_card}{attribution_card}
</div>
<p class="learn-note" style="margin-top:4px;">Macro takeaway: these four views are one story told from four
angles &mdash; how much market you carry (CAPM), what <em>kind</em> of market exposure it is (Fama-French),
whether you're being compensated efficiently for the risk in your specific holdings (the frontier), and how
those pieces actually add up to your realized return and risk (attribution). None of it is advice about what to
buy, sell, or hold &mdash; it's a transparent account of exposures you already have.</p>
"""


def render_glossary_section() -> str:
    """Phase 9 project glossary: terms this project's own UI actually uses, dual-register,
    each tagged with where in the app it shows up. Mirrors the entry format `educator` also
    writes to `docs/glossary.md` (project) and the Cowork OS root `docs/glossary.md`
    (portfolio-wide) -- kept in sync by hand, this is the copy an actual visitor sees.
    """

    def entry(*, term: str, where: str, plain: str, technical: str) -> str:
        return f"""
<div class="glossary-entry">
  <div class="glossary-term">{term}<span class="gt-where">{where}</span></div>
  <div class="glossary-row is-plain"><span class="gr-label">Plain</span><p>{plain}</p></div>
  <div class="glossary-row is-technical"><span class="gr-label">Technical</span><p>{technical}</p></div>
</div>
"""

    entries = [
        entry(
            term="Alpha (&alpha;)",
            where="Results §1, Learning, References",
            plain="The part of your average return that isn't explained by the market (or, in Fama-French, by "
            "any of the named factors) &mdash; whatever's left over.",
            technical="The OLS regression intercept. Reported both as the raw periodic estimate and, "
            "annualized by compounding, as &ldquo;alpha (annualized).&rdquo; A statistically significant "
            "nonzero alpha means the model's factors don't fully account for your realized average return.",
        ),
        entry(
            term="Beta (&beta;)",
            where="Results §1, Learning, References",
            plain="How much your portfolio historically moves for every 1% the benchmark moves.",
            technical="The CAPM regression's slope coefficient on benchmark excess return; reported with a "
            "Newey-West HAC standard error, t-stat, p-value, and 95% confidence interval, not as a bare point "
            "estimate.",
        ),
        entry(
            term="CAPM (Capital Asset Pricing Model)",
            where="Results §1, Learning, References",
            plain="A one-factor way of explaining a portfolio's return: how much of it is just \"the market, "
            "scaled up or down.\"",
            technical="Sharpe (1964)/Lintner (1965)/Mossin (1966): "
            "<code>R<sub>p</sub> &minus; R<sub>f</sub> = &alpha; + &beta;(R<sub>m</sub> &minus; R<sub>f</sub>) "
            "+ &epsilon;</code>, fit by OLS with HAC standard errors in this project.",
        ),
        entry(
            term="Efficient frontier",
            where="Results §2, Learning, References",
            plain="The best return historically achievable, for each level of risk, by re-weighting the exact "
            "holdings you entered &mdash; no new stocks, no leverage, no shorting.",
            technical="The set of long-only portfolios minimizing <code>w<sup>T</sup>&Sigma;w</code> for each "
            "target <code>w<sup>T</sup>&mu;</code>, solved point-by-point via SLSQP since long-only "
            "mean-variance optimization has no closed form (Markowitz, 1952).",
        ),
        entry(
            term="Factor loading",
            where="Results §1, Learning, References",
            plain="How much your portfolio leans toward a particular style of stock &mdash; small vs. large, "
            "cheap vs. expensive, profitable vs. not, conservative vs. aggressive.",
            technical="A partial-regression coefficient in the Fama-French model &mdash; sensitivity to one "
            "factor's spread-portfolio return, holding the other included factors fixed.",
        ),
        entry(
            term="Fama-French 3-/5-factor model",
            where="Results §1, Learning, References",
            plain="An extension of CAPM that explains a portfolio's return using several named style factors "
            "instead of just \"the market.\"",
            technical="Fama &amp; French (1993, 2015). 3-factor adds SMB and HML to CAPM's market factor; "
            "5-factor adds RMW and CMA on top of that. Fit by OLS with HAC standard errors in this project; "
            "factor return series sourced from Kenneth French's Data Library, not OpenBB.",
        ),
        entry(
            term="SMB (Small Minus Big) &mdash; the size factor",
            where="Results §1, Learning, References",
            plain="A positive loading here means your holdings behave more like small-company stocks than "
            "large-company stocks.",
            technical="The return of a portfolio long small-cap stocks and short large-cap stocks; one of the "
            "explanatory variables in the Fama-French regression.",
        ),
        entry(
            term="HML (High Minus Low) &mdash; the value factor",
            where="Results §1, Learning, References",
            plain="A positive loading here means your holdings behave more like \"value\" stocks (cheap "
            "relative to book value) than \"growth\" stocks (expensive relative to book value).",
            technical="The return of a portfolio long high book-to-market stocks and short low book-to-market "
            "stocks.",
        ),
        entry(
            term="RMW (Robust Minus Weak) &mdash; the profitability factor",
            where="Results §1 (5-factor), Learning, References",
            plain="A positive loading here means your holdings behave more like highly profitable companies "
            "than weakly profitable ones.",
            technical="The return of a portfolio long robust-operating-profitability stocks and short weak-"
            "profitability stocks; Fama-French 5-factor only.",
        ),
        entry(
            term="CMA (Conservative Minus Aggressive) &mdash; the investment factor",
            where="Results §1 (5-factor), Learning, References",
            plain="A positive loading here means your holdings behave more like conservatively-run, "
            "slow-growing companies than aggressively-expanding ones.",
            technical="The return of a portfolio long low-investment (conservative) firms and short "
            "high-investment (aggressive) firms; Fama-French 5-factor only.",
        ),
        entry(
            term="Global minimum-variance (GMV) portfolio",
            where="Results §2, Learning",
            plain="Of every way you could re-weight your exact holdings, the single weighting that historically "
            "would have been the calmest (lowest volatility) &mdash; regardless of return.",
            technical="The frontier point with minimum <code>w<sup>T</sup>&Sigma;w</code> subject to the "
            "long-only, sum-to-one constraints; the leftmost point on the plotted frontier.",
        ),
        entry(
            term="Tangency / max-Sharpe portfolio",
            where="Results §2, Learning",
            plain="Of every way you could re-weight your exact holdings, the single weighting with the best "
            "return per unit of risk.",
            technical="The frontier point maximizing "
            "<code>S = (R<sub>p</sub> &minus; R<sub>f</sub>) / &sigma;<sub>p</sub></code> subject to the same "
            "long-only constraints as the rest of the frontier.",
        ),
        entry(
            term="Sharpe ratio",
            where="Results §2, Learning, References",
            plain="Return earned per unit of risk taken, after subtracting the risk-free rate &mdash; higher is "
            "better compensated risk-taking.",
            technical="<code>S = (R<sub>p</sub> &minus; R<sub>f</sub>) / &sigma;<sub>p</sub></code> "
            "(Sharpe, 1966/1994).",
        ),
        entry(
            term="R&sup2; (R-squared)",
            where="Results §1 &amp; §3, Learning, References",
            plain="How much of your portfolio's up-and-down movement is explained by the factor(s) in the "
            "model, versus left unexplained.",
            technical="Coefficient of determination for the CAPM/Fama-French OLS fit; doubles as the risk-"
            "attribution split (factor-explained share = R&sup2;, idiosyncratic share = 1 &minus; R&sup2;).",
        ),
        entry(
            term="Idiosyncratic risk",
            where="Results §3, Learning",
            plain="The part of your portfolio's risk that's specific to the individual companies you hold, not "
            "shared with the market or with any named style factor.",
            technical="<code>1 &minus; R&sup2;</code> of the fitted factor model &mdash; the residual variance "
            "share unexplained by market/size/value/profitability/investment exposure.",
        ),
        entry(
            term="Newey-West HAC standard errors",
            where="Results §1, References",
            plain="A more honest way of measuring how uncertain a beta or factor loading really is, built to "
            "not be fooled by the fact that stock returns are choppier and stickier day-to-day than a textbook "
            "regression assumes.",
            technical="Heteroskedasticity- and autocorrelation-consistent covariance estimator "
            "(Newey &amp; West, 1987/1994) used for every regression standard error/t-stat/p-value/CI in this "
            "project, in place of classical OLS standard errors, which would understate them.",
        ),
        entry(
            term="Statistical significance (t-stat, p-value, 95% CI)",
            where="Results §1, Learning, References",
            plain="A way of telling a real signal apart from noise: if the confidence interval around a number "
            "like beta or a factor loading includes zero, you can't be confident the true exposure isn't zero.",
            technical="Standard OLS-regression diagnostics (t-statistic, two-sided p-value, 95% confidence "
            "interval) computed from the HAC standard error above for every coefficient this project reports.",
        ),
        entry(
            term="Long-only constraint",
            where="Results §2, Learning, References",
            plain="The frontier never assumes you could short a stock or borrow money to invest more than you "
            "have &mdash; only re-weighting among positive holdings of what you actually entered.",
            technical="<code>w<sub>i</sub> &ge; 0</code> for all holdings in the efficient-frontier optimization; "
            "this project's default (see decision 0003), reflecting how retail/small-RIA portfolios are "
            "actually held.",
        ),
    ]

    return f"""
<div class="section-eyebrow">[05] Glossary</div>
<h1>Terms used in this project</h1>
<p class="section-lede">Every term this app's Results, Learning, and References &amp; Formulas sections use,
defined in plain language and technically, with where it shows up. This project glossary also feeds the
Cowork OS portfolio-wide glossary at <code>docs/glossary.md</code>.</p>
<div class="glossary-groups">
{''.join(entries)}
</div>
"""


def render_real_world_section() -> str:
    """Phase 9, required per `docs/project-standards.md` rule 5: a deliberate business-
    development/recruiting-facing section grounded in the project's own source research
    brief (`docs/research/finance/2026-08-10-fintech-ai-quant-wealthtech.md`), not generic
    claims -- written so a company evaluating this project sees a reason to want this
    capability, or to want whoever built it.
    """

    def card(*, title: str, body: str, tags: list[str]) -> str:
        tag_html = '<div class="rw-tag-row">' + "".join(f'<span class="rw-tag">{esc(t)}</span>' for t in tags) + "</div>"
        return f'<div class="rw-card"><h2>{title}</h2>{tag_html}{body}</div>'

    institutional = card(
        title="Institutional factor-risk desks",
        tags=["Multi-factor risk models", "Barra / Axioma / MSCI", "Risk decomposition"],
        body=(
            "<p>Large asset managers and hedge funds run exactly this kind of factor decomposition &mdash; at "
            "far greater scale and with proprietary factor sets &mdash; through commercial multi-factor risk "
            "platforms like MSCI Barra and (now Qontigo/SimCorp) Axioma. A risk desk uses this output the same "
            "way this app's Results tab is structured: break a portfolio's exposure into named, interpretable "
            "factors; attribute realized return and risk to those factors versus stock-specific noise; and "
            "flag when a portfolio's risk concentration doesn't match the mandate it's supposed to be running "
            "against. Those platforms are the direct commercial ancestor of what this project builds, and this "
            "project's roadmap says so explicitly &mdash; it is scoped as \"Barra/Axioma-style factor risk "
            "tooling, just built transparent and accessible.\"</p>"
            "<p>The gap this project targets is real, not invented: Barra/Axioma-class tooling is licensed to "
            "institutions at a price point and integration complexity that puts it entirely out of reach for a "
            "retail investor or a two-person RIA &mdash; the same factor-attribution logic, built open and "
            "cheaply enough to run for a single portfolio, is the differentiator.</p>"
        ),
    )

    advisor_tech = card(
        title="RIA client reporting &amp; the advisor-tech stack",
        tags=["Advisor-tech", "YCharts / Zephyr", "Explainability & suitability"],
        body=(
            "<p>Small registered investment advisors don't build their own factor models &mdash; they buy "
            "reporting and proposal tooling that produces client-facing explanations of \"why did my portfolio "
            "perform this way.\" That category is actively consolidating: YCharts' 2026 acquisition of Zephyr "
            "added a 21,000+ fund performance-attribution database directly into its advisor platform, and "
            "Advyzon shipped \"Advyzon AI\" for meeting notes and next-action recommendations &mdash; both "
            "signals that plain-language, defensible explanation of portfolio behavior is treated as a core "
            "advisor-tech feature, not a nice-to-have. A transparent factor-attribution tool that shows its "
            "exact math (this project's References &amp; Formulas tab) alongside a plain-language read (this "
            "project's Learning tab) is built for exactly that client-conversation use case &mdash; an advisor "
            "explaining to a client why their account moved the way it did, with statistical diagnostics "
            "(t-stats, p-values, confidence intervals) available if the client's own due diligence goes that "
            "deep.</p>"
        ),
    )

    wealthtech = card(
        title="Wealthtech optimization &amp; automated rebalancing",
        tags=["Robo-advisor engines", "Platform consolidation", "Mean-variance optimization"],
        body=(
            "<p>Robo-advisor \"smart rebalance\" features (the kind Betterment- and Wealthfront-style platforms "
            "market as automated portfolio management) run mean-variance optimization internally &mdash; "
            "conceptually the same long-only Markowitz solve this project's <code>optimization.py</code> "
            "implements, just hidden behind a single button with no visibility into the frontier, the "
            "constraints, or the tradeoff being made. The share of U.S. wealth managers consolidated onto a "
            "single integrated investment platform rose from 14% in 2020 to 30% in 2024 and continued climbing "
            "through 2026, with automated rebalancing and AI-driven personalization cited as the differentiating "
            "features driving that consolidation. This project demonstrates the same underlying optimization "
            "engine, deliberately kept visible &mdash; the frontier, the global minimum-variance point, the "
            "tangency portfolio, and the exact gap between a user's holdings and the efficient set are all shown, "
            "not abstracted behind a single \"optimize\" action.</p>"
        ),
    )

    hiring = card(
        title="Where this fits, and why it's worth evaluating the person who built it",
        tags=["Build signal", "Quant + product engineering", "Recruiting-facing"],
        body=(
            "<p>The research brief behind this project flags a specific, real gap: general \"factor investing "
            "explained\" pedagogy is everywhere, but concrete, funded products doing factor-model analytics for "
            "retail or small-team use are thin on the ground &mdash; institutional-grade tooling (Barra, Axioma) "
            "and consumer-grade black-box optimizers (Composer, QuantConnect) exist, with comparatively little "
            "built specifically for the transparent middle. Building this project end-to-end &mdash; live "
            "market-data integration (OpenBB, Kenneth French's Data Library), statistically rigorous regression "
            "diagnostics (Newey-West HAC standard errors, not classical OLS), a real constrained quadratic "
            "program solved numerically (SLSQP) with covariance regularization for edge cases, and a shipped, "
            "sectioned web application rather than a notebook &mdash; demonstrates the same combination of "
            "applied-quant methodology and product engineering that institutional risk desks, RIA platform "
            "vendors, and wealthtech optimization teams hire for. Any team evaluating whether to build or buy "
            "this class of capability, or evaluating a candidate for a quant-adjacent engineering role, can read "
            "this project's code, its methodology decision log (<code>docs/decisions/</code>), and this Learning "
            "section itself as direct evidence of that work, not a claim about it.</p>"
        ),
    )

    return f"""
<div class="section-eyebrow">[08] Real World / Corporate Applications</div>
<h1>How this kind of work is actually used</h1>
<p class="section-lede">Where factor attribution and portfolio optimization like this shows up in real
industry &mdash; and where this project sits in that landscape. Grounded in this project's own source research
brief, not generic claims.</p>
<div class="rw-groups">
{institutional}{advisor_tech}{wealthtech}{hiring}
</div>
<p class="rw-source-note">Sources: this project's own roadmap ("Why this project, why this shape") and
<code>docs/research/finance/2026-08-10-fintech-ai-quant-wealthtech.md</code> &mdash; see that brief's "Gaps /
low-confidence areas" section for the explicit note that retail/small-team factor-model tooling coverage is
thin, and its "Trends" section for the wealthtech-consolidation and advisor-tech figures cited above.</p>
"""


def render_placeholder_section(*, tab_id: str, title: str, phase_label: str, owner: str, body: str) -> str:
    idx = [i for i, (t, _l) in enumerate(NAV_ITEMS, start=1) if t == tab_id][0]
    return f"""
<div class="section-eyebrow">[{idx:02d}] {esc(title)}</div>
<div class="placeholder-card">
  <span class="placeholder-stamp">Coming in {esc(phase_label)}</span>
  <h2>{esc(title)}</h2>
  <p>{body}</p>
  <div class="placeholder-owner">Owner: {esc(owner)}</div>
</div>
"""
